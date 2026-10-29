"""Graph worlds use the actual study, CLI, branch, ledger and replay paths."""

import json

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.scripted.graph_nipd_policies import build_graph_nipd_policy
from collaborative_hill.cli import app
from collaborative_hill.domain.world.graph_nipd import UndirectedGraph
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths
from collaborative_hill.experiments.scenario import (
    AgentSpec,
    CognitionPlane,
    GraphNIPDWorld,
    InteractionPlane,
    NarrativeSkin,
    PolicySpec,
    ScenarioSpec,
)
from collaborative_hill.experiments.seed_audit import audit_study_seeds
from collaborative_hill.experiments.study import ConditionSpec, StudySpec, run_study
from collaborative_hill.metrics.cooperation import cooperation_metrics

pytestmark = pytest.mark.integration

STAR = {"a1": ("a2", "a3", "a4", "a5"),
        "a2": ("a1",), "a3": ("a1",), "a4": ("a1",), "a5": ("a1",)}


def run_graph(tmp_path, mode="neighbourhood", name="ptft", params=None, *,
              adjacency=STAR, policies=None, invalid_action_policy="fail"):
    study = tmp_path / "study"
    study.mkdir()
    roster = policies or {a: PolicySpec(name=name if a != "a5" else "alld",
                                        params=(params or {}) if a != "a5" else {})
                          for a in adjacency}
    scenario = ScenarioSpec(
        scenario_id="graph", world=GraphNIPDWorld(mode=mode, rounds=5, payoff_aggregation="mean"),
        interaction=InteractionPlane(structure=mode, graph=UndirectedGraph(adjacency=adjacency)),
        cognition=CognitionPlane(agents=tuple(AgentSpec(agent_id=a, policy=p)
                                              for a, p in roster.items())),
    )
    (study / "scenario.json").write_text(scenario.model_dump_json(indent=2), encoding="utf-8")
    (study / "skin.json").write_text(NarrativeSkin(skin_id="plain").model_dump_json(),
                                    encoding="utf-8")
    spec = StudySpec(
        study_id="graph-test", seed=735, checkpoint_every=2,
        invalid_action_policy=invalid_action_policy,
        conditions=(ConditionSpec(condition_id="graph", scenario="scenario.json",
                                  skin="skin.json"),),
    )
    (study / "study.json").write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    (result,) = run_study(study, tmp_path / "artifacts")
    (ledger,) = (tmp_path / "artifacts").rglob("events.jsonl")
    return result, ledger.parent


@pytest.mark.parametrize("mode,name,params,prefix", [
    ("pairwise", "tft_pairwise", {}, "tft_pairwise["),
    ("pairwise", "tft_linked", {}, "tft_linked["),
    ("neighbourhood", "tft_threshold", {}, "graph_tft_threshold["),
    ("neighbourhood", "ptft", {"denominator": "include_self"}, "graph_ptft[include_self,"),
    ("neighbourhood", "ptft", {"denominator": "exclude_self"}, "graph_ptft[exclude_self,"),
])
def test_graph_study_registry_seal_and_replay(tmp_path, mode, name, params, prefix):
    result, directory = run_graph(tmp_path, mode, name, params)
    assert result.status == "completed"
    events, resolved, manifest = load_run(directory)
    assert manifest["policies"]["a1"].startswith(prefix)
    assert resolved.spec.world.kind == "nipd_graph"
    assert replay_run(directory).chains_match
    transitions = [e.payload for e in events if e.event_type == EventType.WORLD_TRANSITIONED]
    assert len(transitions) == 5
    assert all(p["total_votes"] == (8 if mode == "pairwise" else 5) for p in transitions)
    assert cooperation_metrics(events)["rounds"] == 5


@pytest.mark.parametrize("mode", ["pairwise", "neighbourhood"])
def test_graph_seed_audit_uses_world_horizon_and_rejects_terminal_round(tmp_path, mode):
    run_graph(tmp_path, mode, name="allc")
    result = audit_study_seeds(tmp_path / "study", round_index=4)
    assert result["conditions"]["graph"]["round_count"] == 5
    assert result["conditions"]["graph"]["mechanism_stream"]["seed_path"][-1] == 4
    with pytest.raises(ValueError, match="scheduled range 0..4"):
        audit_study_seeds(tmp_path / "study", round_index=5)


def proposals(events, agents, first_round):
    return {(e.payload["agent_id"], e.logical_time): e.payload["proposal"] for e in events
            if e.event_type == EventType.ACTION_PROPOSED
            and e.payload["agent_id"] in agents and e.logical_time >= first_round}


@pytest.mark.parametrize("mode", ["pairwise", "neighbourhood"])
def test_graph_branch_prefix_divergence_unchanged_streams_and_replay(tmp_path, mode):
    roster = {a: PolicySpec(name="random" if a in ("a2", "a3") else "allc") for a in STAR}
    parent_result, parent = run_graph(tmp_path, mode, policies=roster)
    parent_events, _, _ = load_run(parent)
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    child = tmp_path / "child"
    result, manifest = branch_run(
        parent_dir=parent, fork_seq=fork, child_dir=child, child_run_id="graph-child",
        policy_overrides={"a1": build_graph_nipd_policy("alld", mode, {})},
    )
    assert result.status == "completed" and result.summary != parent_result.summary
    assert (child / "events.jsonl").read_bytes().splitlines()[:fork + 1] == (
        parent / "events.jsonl").read_bytes().splitlines()[:fork + 1]
    child_events, _, _ = load_run(child)
    assert child_events[fork + 1].parent_hash == parent_events[fork].event_hash
    before = proposals(parent_events, {"a2", "a3"}, manifest.fork_round)
    assert before and before == proposals(child_events, {"a2", "a3"}, manifest.fork_round)
    assert replay_run(child).chains_match


@pytest.mark.parametrize("mode,override,prefix", [
    ("pairwise", "tft_pairwise:epsilon=0", "tft_pairwise["),
    ("neighbourhood", "ptft:denominator=include_self", "graph_ptft[include_self,"),
])
def test_cli_branch_selects_graph_builder(tmp_path, mode, override, prefix):
    _, parent = run_graph(tmp_path, mode, name="allc")
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    child = tmp_path / "cli-child"
    result = CliRunner().invoke(app, ["branch", str(parent), "--at-event", str(fork),
                                     "--override", f"a2={override}", "--out", str(child)])
    assert result.exit_code == 0, result.output
    _, _, manifest = load_run(child)
    assert manifest["policies"]["a2"].startswith(prefix)
    assert replay_run(child).chains_match


@pytest.mark.parametrize("mode", ["pairwise", "neighbourhood"])
def test_isolate_does_not_inflate_existing_cooperation_metrics(tmp_path, mode):
    adjacency = {"a1": ("a2",), "a2": ("a1",), "a3": ()}
    roster = {a: PolicySpec(name="alld" if a == "a2" else "allc") for a in adjacency}
    result, directory = run_graph(tmp_path, mode, adjacency=adjacency, policies=roster)
    events, _, _ = load_run(directory)
    metrics = cooperation_metrics(events)
    assert metrics["cooperation_rate_by_round"] == [0.5] * 5
    assert metrics["per_agent_cooperation"] == {"a1": 1.0, "a2": 0.0}
    assert result.summary["scores"] == {"a1": "0", "a2": "25", "a3": "0"}
    assert replay_run(directory).chains_match


@pytest.mark.parametrize("fallback", ["fail", "abstain"])
def test_nonneighbor_proposal_is_sealed_as_rejected_not_silently_repaired(tmp_path, fallback):
    adjacency = {"a1": ("a2",), "a2": ("a1", "a3"), "a3": ("a2",)}
    script = json.dumps([json.dumps({"action": {"type": "pairwise_vote",
                                                "moves": {"a2": "C", "a3": "C"}}})])
    roster = {"a1": PolicySpec(name="llm_fake", params={"script": script}),
              "a2": PolicySpec(name="allc"), "a3": PolicySpec(name="allc")}
    result, directory = run_graph(tmp_path, "pairwise", adjacency=adjacency, policies=roster,
                                  invalid_action_policy=fallback)
    assert result.status == "failed"
    events, _, _ = load_run(directory)
    rejected = [e for e in events if e.event_type == EventType.ACTION_REJECTED]
    assert len(rejected) == 1 and "extra=['a3']" in rejected[0].payload["reason"]
    assert not any(e.event_type == EventType.WORLD_TRANSITIONED for e in events)
    assert events[-1].event_type == EventType.RUN_FAILED
    assert replay_run(directory).chains_match

