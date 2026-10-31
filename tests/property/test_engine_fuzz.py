"""Hypothesis fuzz tests for the deterministic engine core.

Every example draws a small scenario — legacy NIPD (pairwise and
neighbourhood), graph NIPD over a random connected undirected adjacency
(pairwise and neighbourhood, sum and mean aggregation), or Evidence Commons
(aggregate and attributable accountability, private and shared topology) —
with a random mix of the built-in scripted policies in valid parameter
ranges and a random seed. The run is executed twice with the same seed and
the sealed ledger is replayed; these invariants hold for every run:

1. the run seals ``completed`` with exactly one terminal event, and
   ``verify_chain`` passes on the stored ledger;
2. ``replay_run`` reports ``chains_match`` with no divergence;
3. the second run yields the identical ``final_event_hash``;
4. no observation payload carries hidden-truth field names, and inspected
   evidence facts expose only the documented observable projection;
5. NIPD vote accounting (ranges and eligible-voter totals per world shape);
6. NIPD payoffs parse as exact fractions, cumulative rewards chain exactly,
   and sum-aggregation pairwise round totals equal the sum of pair payoffs;
7. on EC runs, budgets never go negative and each agent has at most one
   accepted action per round.

Scenario assembly uses the public builders in ``tests/metamorphic/_helpers.py``
(loaded by path, see below): ``EC_SLOTS``, ``EC_TRUE``, ``ec_item``,
``execute`` and ``plain_skin``. That helper module's ``nipd_spec`` /
``compile_nipd`` / ``ec_spec`` accept policy *names* only, so parameterized
policy mixes are assembled with the same public ``ScenarioSpec`` /
``compile_scenario`` pattern that ``tests/unit/test_graph_scenario.py`` and
``tests/integration/test_graph_pipeline.py`` use for graph scenarios.

Adaptation notes (engine behavior by design, not defects): hidden-truth
*values* (proposition ids such as ``p1a``) necessarily appear in observations
— claims cite them — so property 4 checks field *names* plus the inspected
facts projection, matching ``tests/unit/test_hidden_truth_leak.py``. NIPD
transition payloads carry moves and vote counts, not payoff strings, so
property 6 parses the per-round ``RewardAssigned`` rewards (the engine's real
payoff records) and checks the cumulative chain.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import ECParams
from collaborative_hill.domain.world.graph_nipd import UndirectedGraph
from collaborative_hill.domain.world.nipd import NIPDParams
from collaborative_hill.engine.events import Event, EventType, verify_chain
from collaborative_hill.engine.replay import replay_run
from collaborative_hill.experiments.scenario import (
    AgentSpec,
    CognitionPlane,
    ECWorld,
    GraphNIPDWorld,
    InformationPlane,
    InteractionPlane,
    NIPDWorld,
    PolicySpec,
    ResolvedScenario,
    ScenarioSpec,
    compile_scenario,
)


@functools.lru_cache(maxsize=1)
def _helpers() -> Any:
    """Load ``tests/metamorphic/_helpers.py`` by path.

    ``tests/property`` is not a package, so a relative import cannot reach the
    metamorphic helpers and no new file may be added to bridge them. The helper
    module uses only absolute imports, so executing it under a private module
    name is equivalent to importing it.
    """
    path = Path(__file__).resolve().parent.parent / "metamorphic" / "_helpers.py"
    spec = importlib.util.spec_from_file_location("engine_fuzz_metamorphic_helpers", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class _FuzzCase:
    """One generated scenario plus the expectations derived at build time."""

    resolved: ResolvedScenario
    family: str  # "legacy" | "graph" | "ec"
    mode: str  # "pairwise" | "neighbourhood" | "commons"
    aggregation: str  # "sum" | "mean" | "" (non-graph worlds)
    roster: tuple[str, ...]
    rounds: int
    expected_total_votes: int  # NIPD eligible-voter total (0 for EC runs)
    inspect_budget: int  # EC initial budgets (0 for NIPD runs)
    verify_budget: int
    seed: int


_TERMINAL_EVENTS = (EventType.RUN_COMPLETED, EventType.RUN_FAILED)
_HIDDEN_FIELD_NAMES = ("true_propositions", "truth_aligned")
_OBSERVABLE_FACT_KEYS = frozenset({
    "evidence_id", "source_id", "version", "slot_id",
    "proposition_id", "stance", "freshness",
})
# Canonical NIPD payoff table for the default NIPDParams() (T=5, R=3, P=1, S=0)
# used by every fuzz scenario; the test checks aggregation, not this table.
_PAIR_PAYOFFS = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}
_EPSILONS = ("0", "0.05", "0.2")


def _connected_graph(draw, agents: list[str]) -> dict[str, tuple[str, ...]]:
    """Draw a random connected undirected adjacency over ``agents``."""
    edges: set[tuple[str, str]] = set()
    for i in range(1, len(agents)):
        j = draw(st.integers(min_value=0, max_value=i - 1))
        edges.add((agents[j], agents[i]))
    for x in range(len(agents)):
        for y in range(x + 1, len(agents)):
            pair = (agents[x], agents[y])
            if pair not in edges and draw(st.booleans()):
                edges.add(pair)
    neighbours: dict[str, set[str]] = {a: set() for a in agents}
    for a, b in edges:
        neighbours[a].add(b)
        neighbours[b].add(a)
    return {a: tuple(sorted(neighbours[a])) for a in agents}


def _nipd_policy(draw, mode: str) -> PolicySpec:
    """Draw one scripted NIPD policy that is legal in ``mode``."""
    if mode == "pairwise":
        name = draw(st.sampled_from(["allc", "alld", "random", "tft_pairwise", "tft_linked"]))
        params = {"epsilon": draw(st.sampled_from(_EPSILONS))} if name.startswith("tft") else {}
    else:
        name = draw(st.sampled_from(["allc", "alld", "random", "ptft", "tft_threshold"]))
        if name == "ptft":
            params = {
                "denominator": draw(st.sampled_from(["exclude_self", "include_self"])),
                "epsilon": draw(st.sampled_from(_EPSILONS)),
            }
        elif name == "tft_threshold":
            denominator = draw(st.integers(min_value=1, max_value=3))
            params = {
                "threshold_num": draw(st.integers(min_value=0, max_value=denominator)),
                "threshold_den": denominator,
                "epsilon": draw(st.sampled_from(_EPSILONS)),
            }
        else:
            params = {}
    return PolicySpec(name=name, params=params)


def _ec_policy(draw) -> PolicySpec:
    """Draw one scripted Evidence Commons policy with valid parameters."""
    name = draw(st.sampled_from([
        "ec_contributor", "ec_freerider", "ec_verifier",
        "ec_misinformer", "ec_conditional_contributor",
    ]))
    if name == "ec_contributor":
        params = {"share_evidence": draw(st.booleans())}
    elif name == "ec_conditional_contributor":
        params = {
            "peer_threshold": draw(st.sampled_from(["0", "1/4", "1/2", "1"])),
            "warmup_rounds": draw(st.integers(min_value=0, max_value=4)),
            "share_evidence": draw(st.booleans()),
        }
    else:
        params = {}
    return PolicySpec(name=name, params=params)


def _ec_evidence(draw, helpers: Any, agents: list[str]) -> list[Any]:
    """Draw a small valid evidence corpus; every agent holds at least one item."""
    slots: dict[str, tuple[str, ...]] = dict(helpers.EC_SLOTS)
    items: list[Any] = []
    total = draw(st.integers(min_value=2, max_value=6))
    for index in range(total):
        slot = draw(st.sampled_from(sorted(slots)))
        proposition = draw(st.sampled_from(list(slots[slot])))
        stance = draw(st.sampled_from(["supports", "contradicts"]))
        freshness = draw(st.sampled_from(["fresh", "fresh", "stale"]))
        holders = {agents[index % len(agents)]}
        for agent in agents:
            if draw(st.booleans()):
                holders.add(agent)
        items.append(helpers.ec_item(
            f"e{index + 1}", f"src_{index + 1}", slot, proposition, stance,
            freshness=freshness, holders=tuple(sorted(holders)),
        ))
    return items


@st.composite
def _cases(draw):
    """Draw one small scenario from the cross product of worlds and policies."""
    helpers = _helpers()
    n_agents = draw(st.integers(min_value=3, max_value=5))
    rounds = draw(st.integers(min_value=2, max_value=8))
    seed = draw(st.integers(min_value=0, max_value=9999))
    family = draw(st.sampled_from(["legacy", "graph", "ec"]))
    agents = [f"a{i + 1}" for i in range(n_agents)]
    if family == "ec":
        institution = InstitutionConfig(
            accountability=draw(st.sampled_from(["aggregate", "attributable"])),
            evidence_topology=draw(st.sampled_from(["private", "shared_ledger"])),
        )
        params = ECParams(rounds=rounds)
        spec = ScenarioSpec(
            scenario_id="fuzz-ec",
            world=ECWorld(
                slots=dict(helpers.EC_SLOTS),
                true_propositions=dict(helpers.EC_TRUE),
                params=params,
            ),
            information=InformationPlane(evidence=tuple(_ec_evidence(draw, helpers, agents))),
            interaction=InteractionPlane(structure="commons"),
            institution=institution,
            cognition=CognitionPlane(
                agents=tuple(
                    AgentSpec(agent_id=a, policy=_ec_policy(draw)) for a in agents
                ),
            ),
        )
        return _FuzzCase(
            resolved=compile_scenario(spec, helpers.plain_skin()),
            family=family, mode="commons", aggregation="",
            roster=tuple(agents), rounds=rounds, expected_total_votes=0,
            inspect_budget=params.inspect_budget, verify_budget=params.verify_budget,
            seed=seed,
        )
    mode = draw(st.sampled_from(["pairwise", "neighbourhood"]))
    cognition = CognitionPlane(
        agents=tuple(
            AgentSpec(agent_id=a, policy=_nipd_policy(draw, mode)) for a in agents
        ),
    )
    if family == "graph":
        aggregation = draw(st.sampled_from(["sum", "mean"]))
        adjacency = _connected_graph(draw, agents)
        spec = ScenarioSpec(
            scenario_id="fuzz-graph",
            world=GraphNIPDWorld(mode=mode, rounds=rounds, payoff_aggregation=aggregation),
            interaction=InteractionPlane(
                structure=mode, graph=UndirectedGraph(adjacency=adjacency)),
            cognition=cognition,
        )
        n_edges = sum(len(v) for v in adjacency.values()) // 2
        non_isolated = sum(1 for v in adjacency.values() if v)
        expected = 2 * n_edges if mode == "pairwise" else non_isolated
    else:
        aggregation = ""
        spec = ScenarioSpec(
            scenario_id="fuzz-legacy",
            world=NIPDWorld(mode=mode, params=NIPDParams(), rounds=rounds),
            interaction=InteractionPlane(structure=mode),
            cognition=cognition,
        )
        expected = n_agents * (n_agents - 1) if mode == "pairwise" else n_agents
    return _FuzzCase(
        resolved=compile_scenario(spec, helpers.plain_skin()),
        family=family, mode=mode, aggregation=aggregation, roster=tuple(agents),
        rounds=rounds, expected_total_votes=expected, inspect_budget=0, verify_budget=0, seed=seed,
    )


def _run_sealed(
    helpers: Any, case: _FuzzCase, run_dir: Path, seed_root: tuple[str, int]
) -> tuple[Any, list[Event]]:
    """Run one episode, then materialise the replay bindings next to the ledger.

    ``replay_run`` reloads the frozen resolved scenario and manifest, mirroring
    what ``run_study`` writes for real runs.
    """
    result, events, _ = helpers.execute(
        case.resolved, run_dir, seed_root=seed_root, study_id="fuzz", run_id="r0")
    (run_dir / "scenario.resolved.json").write_text(
        case.resolved.model_dump_json(indent=2), encoding="utf-8")
    manifest = {
        "study_id": "fuzz",
        "run_id": "r0",
        "status": result.status,
        "event_count": result.event_count,
        "final_event_hash": result.final_event_hash,
        "scenario_hash": case.resolved.scenario_hash,
        "mechanism_hash": case.resolved.mechanism_hash,
        "narrative_hash": case.resolved.narrative_hash,
        "evidence_corpus_hash": case.resolved.evidence_corpus_hash,
        "seed_root": [str(c) for c in seed_root],
        "seed_protocol": "legacy-independent-v1",
        "checkpoint_every": 0,
        "invalid_action_policy": "fail",
        "policies": events[0].payload["policies"],
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return result, events


def _assert_sealed_ok(result: Any, events: list[Event]) -> None:
    terminals = [e for e in events if e.event_type in _TERMINAL_EVENTS]
    assert len(terminals) == 1 and terminals[0] == events[-1]
    assert terminals[0].event_type == EventType.RUN_COMPLETED
    assert result.status == "completed"


def _assert_no_hidden_truth(events: list[Event]) -> None:
    for event in events:
        if event.event_type != EventType.OBSERVATION_ISSUED:
            continue
        serialized = json.dumps(event.payload["observation"], sort_keys=True)
        for name in _HIDDEN_FIELD_NAMES:
            assert name not in serialized
        for entry in event.payload["observation"].get("evidence", []):
            if "facts" in entry:
                assert set(entry["facts"]) <= _OBSERVABLE_FACT_KEYS


def _assert_nipd_invariants(events: list[Event], case: _FuzzCase) -> None:
    transitions = [e for e in events if e.event_type == EventType.WORLD_TRANSITIONED]
    assert len(transitions) == case.rounds
    assert case.expected_total_votes > 0
    for event in transitions:
        assert event.payload["total_votes"] == case.expected_total_votes
        assert 0 <= event.payload["cooperative_votes"] <= case.expected_total_votes
    _assert_nipd_payoffs(events, case)


def _assert_nipd_payoffs(events: list[Event], case: _FuzzCase) -> None:
    rewards: dict[int, dict[str, Fraction]] = {}
    cumulative: dict[int, dict[str, Fraction]] = {}
    for event in events:
        if event.event_type != EventType.REWARD_ASSIGNED:
            continue
        round_index = int(event.payload["round"])
        agent_id = str(event.payload["agent_id"])
        rewards.setdefault(round_index, {})[agent_id] = Fraction(event.payload["reward"])
        cumulative.setdefault(round_index, {})[agent_id] = Fraction(event.payload["cumulative"])
    assert sorted(rewards) == list(range(case.rounds))
    roster = sorted(rewards[0])
    running = dict.fromkeys(roster, Fraction(0))
    for round_index in sorted(rewards):
        assert sorted(rewards[round_index]) == roster
        for agent_id in roster:
            running[agent_id] += rewards[round_index][agent_id]
            assert cumulative[round_index][agent_id] == running[agent_id]
    if case.mode == "pairwise" and (case.family == "legacy" or case.aggregation == "sum"):
        transitions = {
            int(e.payload["round"]): e.payload
            for e in events if e.event_type == EventType.WORLD_TRANSITIONED
        }
        for round_index in sorted(rewards):
            pair_total = Fraction(0)
            for pair in transitions[round_index]["pair_results"]:
                leg_a, leg_b = _PAIR_PAYOFFS[(pair["move_ab"], pair["move_ba"])]
                pair_total += leg_a + leg_b
            assert sum(rewards[round_index].values(), Fraction(0)) == pair_total


def _assert_ec_invariants(events: list[Event], case: _FuzzCase) -> None:
    for event in events:
        if event.event_type != EventType.OBSERVATION_ISSUED:
            continue
        budgets = event.payload["observation"]["my_budgets"]
        assert budgets["inspect"] >= 0
        assert budgets["verify"] >= 0
    remaining_inspect = dict.fromkeys(case.roster, case.inspect_budget)
    remaining_verify = dict.fromkeys(case.roster, case.verify_budget)
    accepted: dict[tuple[int, str], int] = {}
    for event in events:
        if event.event_type == EventType.EVIDENCE_INSPECTED:
            remaining_inspect[str(event.payload["agent_id"])] -= 1
        elif event.event_type == EventType.CLAIM_VERIFIED:
            remaining_verify[str(event.payload["agent_id"])] -= 1
        elif event.event_type == EventType.ACTION_ACCEPTED:
            key = (event.logical_time, str(event.payload["agent_id"]))
            accepted[key] = accepted.get(key, 0) + 1
    assert accepted
    assert all(count <= 1 for count in accepted.values())
    # Budgets only decrease, so non-negative observations plus a non-negative
    # end state cover every intermediate state.
    assert all(left >= 0 for left in remaining_inspect.values())
    assert all(left >= 0 for left in remaining_verify.values())


@given(_cases())
@settings(max_examples=25, deadline=None, derandomize=True)
def test_engine_fuzz_invariants(case: _FuzzCase) -> None:
    helpers = _helpers()
    seed_root = ("fuzz", case.seed)
    with tempfile.TemporaryDirectory() as tmp:
        first = Path(tmp) / "run-a"
        result, events = _run_sealed(helpers, case, first, seed_root)
        _assert_sealed_ok(result, events)
        verify_chain(events)
        report = replay_run(first)
        assert report.chains_match
        assert report.first_divergence_seq is None
        result2, _ = _run_sealed(helpers, case, Path(tmp) / "run-b", seed_root)
        assert result2.final_event_hash == result.final_event_hash
        _assert_no_hidden_truth(events)
        if case.family == "ec":
            _assert_ec_invariants(events, case)
        else:
            _assert_nipd_invariants(events, case)
