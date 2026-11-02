"""Execute and audit the predeclared 76-run synthetic audit-feedback design."""

import argparse
import itertools
import json
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(REPO / "src"), str(HERE)]

import audit_closed_form as oracle  # noqa: E402
import audit_readout as readout  # noqa: E402

from collaborative_hill.agents.replay import ReplayPolicy  # noqa: E402
from collaborative_hill.agents.scripted.ec_policies import build_ec_policy  # noqa: E402
from collaborative_hill.domain.actions import ActionProposal  # noqa: E402
from collaborative_hill.domain.institutions import AuditInstitutionConfig  # noqa: E402
from collaborative_hill.engine.branching import branch_run  # noqa: E402
from collaborative_hill.engine.events import Event, EventType  # noqa: E402
from collaborative_hill.engine.hashing import content_hash, sha256_hex  # noqa: E402
from collaborative_hill.engine.replay import load_run, replay_run  # noqa: E402
from collaborative_hill.engine.runner import RunConfig, run_episode  # noqa: E402
from collaborative_hill.engine.seeds import PAIRED_SEED_PROTOCOL  # noqa: E402
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths  # noqa: E402
from collaborative_hill.engine.validation import validate_checkpoint  # noqa: E402
from collaborative_hill.experiments.manifests import (  # noqa: E402
    RunManifest,
    environment_provenance,
    git_provenance,
    lock_hash,
    write_manifest,
)
from collaborative_hill.experiments.scenario import (  # noqa: E402
    NarrativeSkin,
    ResolvedScenario,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import build_policies  # noqa: E402

AGENTS = oracle.AGENTS
ROUNDS = 8
SEED = 20261102
STUDY_ID = "audit-feedback-v1"
SKIN = NarrativeSkin(skin_id="audit-feedback-plain", title="Synthetic evidence review")
POLICY_PARAMS = {
    "min_sources": 2,
    "peer_threshold": "0",
    "warmup_rounds": 0,
    "share_evidence": True,
}
HIDDEN_KEYS = frozenset(
    {
        "true_propositions",
        "truth_aligned",
        "target_is_true",
        "audit_correct",
        "error_bits",
        "availability_draw",
        "verdict_draw",
        "rng_state",
        "future_findings",
        "future_reports",
        "unreleased_findings",
        "accuracy",
        "unavailable_probability",
        "generation",
    }
)


def encode(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def write_json(path: Path, value: Any) -> None:
    path.write_text(encode(value), encoding="utf-8", newline="\n")


def cells() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for truth, report in itertools.product(oracle.TRUTHS, repeat=2):
        base = {"truth": truth, "report": report}
        rows.append(
            {
                **base,
                "kind": "unaudited_behavior",
                "verdict": None,
                "publish_round": None,
                "trace": None,
            }
        )
        for verdict, timing in itertools.product(oracle.VERDICTS, oracle.TIMINGS):
            rows.append(
                {
                    **base,
                    "kind": "audited_behavior",
                    "verdict": verdict,
                    "publish_round": timing,
                    "trace": None,
                }
            )
        for trace in ("B", "C", "D"):
            rows.append(
                {
                    **base,
                    "kind": "unaudited_fixed",
                    "verdict": None,
                    "publish_round": None,
                    "trace": trace,
                }
            )
        for timing in (3, 4, 5):
            rows.append(
                {
                    **base,
                    "kind": "audited_fixed",
                    "verdict": "negative",
                    "publish_round": timing,
                    "trace": "A",
                }
            )
    return rows


def cell_id(cell: dict[str, Any]) -> str:
    if cell not in cells() or (
        cell["publish_round"] is not None and type(cell["publish_round"]) is not int
    ):
        raise ValueError("cell is outside the declared audit-feedback grid")
    world = f"t{cell['truth']}-r{cell['report']}"
    if cell["kind"] == "unaudited_behavior":
        return "base-" + world
    if cell["kind"] == "unaudited_fixed":
        return f"fixed-{world}-{cell['trace']}"
    prefix = "behavior" if cell["kind"] == "audited_behavior" else "forced"
    return f"{prefix}-{world}-{cell['verdict']}-{cell['publish_round']}"


def _audit_config(cell: dict[str, Any]) -> dict[str, Any]:
    accuracy, unavailable = oracle.endpoint_parameters(
        cell["truth"], cell["report"], cell["verdict"]
    )
    return {
        "contract": {
            "contract_version": "ec-audit-observation@1",
            "audit_id": "audit-1",
            "accuracy": accuracy,
            "accuracy_semantics": "symmetric-conditional-on-availability",
            "oracle_kind": "synthetic-trusted-oracle",
            "dependence": "independent-of-source-errors",
            "visibility": "public",
            "selection": "fixed-ex-ante-targets",
            "unavailable_semantics": "explicit-no-verdict",
            "schedule": [
                {
                    "slot_id": "s1",
                    "proposition_id": cell["report"],
                    "publish_round": cell["publish_round"],
                }
            ],
        },
        "generation": {
            "generator_version": "ec-audit-generator@1",
            "unavailable_probability": unavailable,
            "draw_dependence": "independent-per-target",
            "unavailable_dependence": "independent-of-truth-source-errors-and-correctness",
        },
    }


def scenario(cell: dict[str, Any]) -> ScenarioSpec:
    cid = cell_id(cell)
    institution: dict[str, Any] = {
        "accountability": "aggregate",
        "evidence_topology": "shared_ledger",
    }
    if cell["verdict"] is not None:
        institution["audit"] = _audit_config(cell)
    name = (
        "ec_audit_veto_contributor" if cell["verdict"] is not None else "ec_skeptical_contributor"
    )
    raw = {
        "scenario_id": cid,
        "world": {
            "kind": "evidence_commons",
            "slots": {"s1": ["p", "q"]},
            "true_propositions": {"s1": cell["truth"]},
            "params": {
                "rounds": ROUNDS,
                "inspect_budget": 3,
                "verify_budget": 2,
                "cost_inspect": 1,
                "cost_share": 1,
                "cost_propose": 1,
                "cost_verify": 2,
                "cost_challenge": 1,
                "benefit_correct_slot": 12,
                "penalty_wrong_slot": 12,
                "credit_propose_accepted_correct": 3,
                "credit_propose_accepted_wrong": -3,
                "credit_verify_accepted_correct": 2,
                "credit_verify_accepted_wrong": -2,
            },
        },
        "information": {
            "evidence": [
                {
                    "evidence_id": f"e{index}",
                    "source_id": f"src-{index}",
                    "version": 1,
                    "slot_id": "s1",
                    "proposition_id": cell["report"],
                    "stance": "supports",
                    "freshness": "fresh",
                    "truth_aligned": cell["truth"] == cell["report"],
                    "initial_holders": [agent],
                }
                for index, agent in enumerate(AGENTS, 1)
            ]
        },
        "interaction": {"structure": "commons"},
        "institution": institution,
        "cognition": {
            "agents": [
                {"agent_id": agent, "policy": {"name": name, "params": POLICY_PARAMS}}
                for agent in AGENTS
            ]
        },
    }
    return ScenarioSpec.model_validate_json(encode(raw))


def design() -> tuple[dict[str, Any], dict[str, ResolvedScenario]]:
    resolved = {cell_id(cell): compile_scenario(scenario(cell), SKIN) for cell in cells()}
    declaration = {
        "schema": "audit-feedback-inputs-v1",
        "study_id": STUDY_ID,
        "status": "exploratory-unfrozen",
        "cells": cells(),
        "seed": SEED,
        "seed_protocol": PAIRED_SEED_PROTOCOL,
        "checkpoint_every": 1,
        "mechanism_roots": {r: [SEED, "audit-feedback", r] for r in oracle.TRUTHS},
        "policy_roots": {r: [SEED, "audit-feedback", "policy", r] for r in oracle.TRUTHS},
        "scenario_hashes": {cid: value.scenario_hash for cid, value in resolved.items()},
        "design_sha256": sha256_hex((HERE / "DESIGN.md").read_bytes()),
    }
    return {**declaration, "design_hash": content_hash(declaration)}, resolved


def write_inputs(destination: Path) -> tuple[dict[str, Any], dict[str, ResolvedScenario]]:
    declaration, resolved = design()
    (destination / "scenarios").mkdir(parents=True, exist_ok=False)
    write_json(destination / "experiment.json", declaration)
    write_json(destination / "skin.json", SKIN.model_dump(mode="json"))
    for cid, target in resolved.items():
        write_json(destination / "scenarios" / f"{cid}.json", target.spec.model_dump(mode="json"))
    return declaration, resolved


def _literal_policies(cell: dict[str, Any]) -> dict[str, ReplayPolicy]:
    trace = readout.expected_trace(cell)
    rows = oracle.literal_schedule(trace, cell["report"])
    return {
        agent: ReplayPolicy(
            agent,
            f"audit-feedback-literal-{trace}@1",
            {
                row["round"]: ActionProposal.model_validate(
                    {
                        "action": row["action"],
                        "justification": "predeclared literal schedule for a same-action control",
                    }
                )
                for row in rows
                if row["agent"] == agent
            },
        )
        for agent in AGENTS
    }


def _policies(cell: dict[str, Any], target: ResolvedScenario) -> dict[str, Any]:
    return _literal_policies(cell) if cell["kind"].endswith("fixed") else build_policies(target)


def expected_manifest(
    cell: dict[str, Any], target: ResolvedScenario, digest: str
) -> dict[str, Any]:
    return {
        "study_id": STUDY_ID,
        "study_hash": digest,
        "study_frozen": False,
        "condition_id": cell_id(cell),
        "run_id": cell_id(cell),
        "replicate": 0,
        "scenario_hash": target.scenario_hash,
        "mechanism_hash": target.mechanism_hash,
        "narrative_hash": target.narrative_hash,
        "evidence_corpus_hash": target.evidence_corpus_hash,
        "institution": target.spec.institution.model_dump(mode="json"),
        "policies": {a: p.policy_id for a, p in _policies(cell, target).items()},
        "seed_root": [SEED, "audit-feedback", cell["report"]],
        "seed_protocol": PAIRED_SEED_PROTOCOL,
        "policy_seed_root": [SEED, "audit-feedback", "policy", cell["report"]],
        "scenario_block": "audit-feedback-" + cell["report"],
        "checkpoint_every": 1,
        "invalid_action_policy": "fail",
    }


def run_cell(
    cell: dict[str, Any], target: ResolvedScenario, destination: Path, digest: str
) -> None:
    manifest = expected_manifest(cell, target, digest)
    config = RunConfig(
        study_id=STUDY_ID,
        run_id=cell_id(cell),
        seed_root=tuple(manifest["seed_root"]),
        seed_protocol=PAIRED_SEED_PROTOCOL,
        policy_seed_root=tuple(manifest["policy_seed_root"]),
        scenario_block=manifest["scenario_block"],
        checkpoint_every=1,
    )
    commit, dirty = git_provenance(REPO)
    with RunPaths(destination).reserve() as paths:
        write_json(destination / "scenario.resolved.json", target.model_dump(mode="json"))
        result = run_episode(
            mechanism=target.build_mechanism(),
            policies=_policies(cell, target),
            config=config,
            paths=paths,
            start_meta={
                key: manifest[key]
                for key in (
                    "scenario_hash",
                    "mechanism_hash",
                    "narrative_hash",
                    "evidence_corpus_hash",
                )
            },
        )
        environment = environment_provenance()
        write_manifest(
            RunManifest(
                **manifest,
                code_commit=commit,
                worktree_dirty=dirty,
                dependency_lock_sha256=lock_hash(REPO),
                python_version=environment["python_version"],
                platform=environment["platform"],
                status=result.status,
                failure_reason=result.failure_reason,
                event_count=result.event_count,
                final_event_hash=result.final_event_hash,
            ),
            paths.manifest,
        )


def has_hidden_fields(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(HIDDEN_KEYS.intersection(value)) or any(
            has_hidden_fields(v) for v in value.values()
        )
    if isinstance(value, list | tuple):
        return any(has_hidden_fields(item) for item in value)
    return False


def actions_from(events: list[Event]) -> list[dict[str, Any]]:
    return [
        {"round": e.logical_time, "agent": e.payload["agent_id"], "action": e.payload["action"]}
        for e in events
        if e.event_type == EventType.ACTION_ACCEPTED
    ]


def observations_from(events: list[Event]) -> list[dict[str, Any]]:
    return [
        {
            "round": e.logical_time,
            "agent": e.payload["agent_id"],
            "observation": e.payload["observation"],
        }
        for e in events
        if e.event_type == EventType.OBSERVATION_ISSUED
    ]


def _checkpoints(path: Path, events: list[Event]) -> list[dict[str, Any]]:
    store = FileCheckpointStore(path / "checkpoints")
    records = []
    for seq in store.list_seqs():
        record = store.load(seq)
        validate_checkpoint(record, seq, events)
        records.append(record)
    return records


def publication_check(
    events: list[Event],
    checkpoints: list[dict[str, Any]],
    target: ResolvedScenario,
    cell: dict[str, Any],
) -> dict[str, Any]:
    published = [event for event in events if event.event_type.value == "AuditPublished"]
    observations = [event for event in events if event.event_type == EventType.OBSERVATION_ISSUED]
    checks = {
        "ledger_no_hidden_fields": not any(has_hidden_fields(e.payload) for e in events),
        "checkpoints_no_hidden_fields": not any(has_hidden_fields(c["state"]) for c in checkpoints),
    }
    first_report = None
    if isinstance(target.spec.institution, AuditInstitutionConfig):
        config = target.spec.institution.audit.contract
        finding = {
            "slot_id": "s1",
            "proposition_id": cell["report"],
            "publish_round": cell["publish_round"],
            "verdict": cell["verdict"],
        }
        identity = {
            "contract_version": config.contract_version,
            "audit_id": config.audit_id,
            "contract_hash": config.contract_hash(),
        }
        expected_payload = {**identity, "report": finding}
        checks["single_exact_publication"] = (
            len(published) == 1
            and published[0].logical_time == cell["publish_round"]
            and published[0].actor == "engine"
            and published[0].payload == expected_payload
        )
        checks["before_every_observation"] = len(published) == 1 and all(
            e.seq > published[0].seq
            for e in observations
            if e.logical_time >= cell["publish_round"]
        )
        checks["public_persistent_prefix"] = all(
            e.payload["observation"].get("observation_schema_version") == 3
            and e.payload["observation"].get("audit")
            == {**identity, "reports": [finding] if e.logical_time >= cell["publish_round"] else []}
            for e in observations
        )
        checks["released_checkpoint_prefix"] = all(
            c["state"].get("audit_reports")
            == ([finding] if c["state"]["round"] > cell["publish_round"] else [])
            for c in checkpoints
        )
        if published:
            first_report = published[0].payload.get("report")
    else:
        checks["legacy_has_no_channel"] = (
            not published
            and all("audit" not in e.payload["observation"] for e in observations)
            and all("audit_reports" not in c["state"] for c in checkpoints)
        )
    return {
        "held": all(checks.values()),
        "checks": checks,
        "published_count": len(published),
        "first_report_round": published[0].logical_time if published else None,
        "report": first_report,
        "checkpoints_checked": len(checkpoints),
    }


def episode_record(
    path: Path, target: ResolvedScenario, cell: dict[str, Any], digest: str
) -> dict[str, Any]:
    events, actual, manifest = load_run(path)
    if actual != target:
        raise ValueError("stored scenario differs from the declared input")
    for key, expected in expected_manifest(cell, target, digest).items():
        if manifest.get(key) != expected:
            raise ValueError(f"unexpected manifest {key}: {path}")
    if manifest["status"] != "completed" or events[-1].event_type != EventType.RUN_COMPLETED:
        raise ValueError(f"experiment requires completed episodes; failed source retained: {path}")
    actions, observations = actions_from(events), observations_from(events)
    expected_coordinates = list(itertools.product(range(ROUNDS), AGENTS))
    if any(
        [(r["round"], r["agent"]) for r in rows] != expected_coordinates
        for rows in (actions, observations)
    ):
        raise ValueError("incomplete or reordered experiment transcript")
    if any(e.event_type == EventType.ACTION_REJECTED for e in events):
        raise ValueError("rejected action in declared experiment")
    checkpoints = _checkpoints(path, events)
    if [c["state"]["round"] for c in checkpoints] != list(range(1, ROUNDS + 1)):
        raise ValueError("missing or unexpected checkpoint rounds")
    replay = replay_run(path)
    if not replay.chains_match:
        raise ValueError("recorded-ledger replay mismatch")
    summary = events[-1].payload
    counts = Counter(row["action"]["type"] for row in actions)
    contributing = sum(
        count for kind, count in counts.items() if kind not in ("withhold", "abstain")
    )
    return {
        "cell": cell,
        "scenario_hash": actual.scenario_hash,
        "mechanism_hash": actual.mechanism_hash,
        "terminal_hash": events[-1].event_hash,
        "event_count": len(events),
        "replay_verified": replay.chains_match,
        "actions": actions,
        "action_hash": content_hash(actions),
        "observation_hash": content_hash(observations),
        "action_counts": dict(sorted(counts.items())),
        "publication": publication_check(events, checkpoints, target, cell),
        "endpoint_config": target.spec.institution.model_dump(mode="json").get("audit"),
        "budgets": checkpoints[-1]["state"]["budgets"],
        "briefing": summary["briefing"],
        "accepted_slots": sum(r["claim_id"] is not None for r in summary["briefing"]),
        "correct_slots": sum(r.get("correct") is True for r in summary["briefing"]),
        "wrong_slots": sum(r.get("correct") is False for r in summary["briefing"]),
        "collective_quality": summary["collective_quality"],
        "effort": summary["effort"],
        "total_effort": sum(summary["effort"].values()),
        "individual_credit": summary["individual_credit"],
        "utility": summary["utility"],
        "total_credit": str(sum(map(Fraction, summary["individual_credit"].values()), Fraction())),
        "total_utility": str(sum(map(Fraction, summary["utility"].values()), Fraction())),
        "contribution_fraction": str(Fraction(contributing, len(actions))),
    }


def _saved_inputs(root: Path) -> tuple[dict[str, Any], dict[str, ResolvedScenario]]:
    declaration, resolved = design()
    inputs = root / "inputs"
    if json.loads(
        (inputs / "experiment.json").read_text(encoding="utf-8")
    ) != declaration or json.loads(
        (inputs / "skin.json").read_text(encoding="utf-8")
    ) != SKIN.model_dump(mode="json"):
        raise ValueError("saved inputs differ from the declared design")
    if {p.name for p in (inputs / "scenarios").iterdir()} != {cid + ".json" for cid in resolved}:
        raise ValueError("saved inputs have missing or additional scenarios")
    for cid, target in resolved.items():
        actual = json.loads((inputs / "scenarios" / f"{cid}.json").read_text(encoding="utf-8"))
        if actual != target.spec.model_dump(mode="json"):
            raise ValueError("saved inputs differ from the declared scenario")
    return declaration, resolved


def same_action_checks(records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    controls = {
        (r["cell"]["truth"], r["cell"]["report"], readout.expected_trace(r["cell"])): cid
        for cid, r in records.items()
        if r["cell"]["verdict"] is None
    }
    checks = []
    for cid, record in records.items():
        cell = record["cell"]
        if cell["verdict"] is None:
            continue
        control_id = controls[(cell["truth"], cell["report"], readout.expected_trace(cell))]
        control = records[control_id]
        fields = {field: record[field] == control[field] for field in readout.TASK_FIELDS}
        checks.append(
            {
                "audited_cell": cid,
                "unaudited_shared_control": control_id,
                "held": all(fields.values()),
                "checks": fields,
            }
        )
    return checks


def _truth_pair(
    left_id: str,
    right_id: str,
    observations: dict[str, list[dict[str, Any]]],
    records: dict[str, dict[str, Any]],
    *,
    fixed: bool,
) -> dict[str, Any]:
    left, right = records[left_id], records[right_id]
    timing = left["cell"]["publish_round"]
    left_obs, right_obs = observations[left_id], observations[right_id]

    def before(row: dict[str, Any]) -> bool:
        return timing is None or bool(row["round"] < timing)

    first_difference = next(
        (x["round"] for x, y in zip(left_obs, right_obs, strict=True) if x != y), None
    )
    first_action = next(
        (x["round"] for x, y in zip(left["actions"], right["actions"], strict=True) if x != y), None
    )
    checks = {
        "prepublication_observations_equal": [r for r in left_obs if before(r)]
        == [r for r in right_obs if before(r)],
        "prepublication_actions_equal": [r for r in left["actions"] if before(r)]
        == [r for r in right["actions"] if before(r)],
    }
    if timing is not None and left["cell"]["verdict"] != "unavailable":
        checks["first_observation_difference_at_release"] = first_difference == timing
    else:
        checks["no_observation_difference"] = first_difference is None
    if fixed:

        def ordinary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return [
                {**r, "observation": {k: v for k, v in r["observation"].items() if k != "audit"}}
                for r in rows
            ]

        checks["fixed_actions_equal"] = left["actions"] == right["actions"]
        checks["only_audit_observations_differ"] = ordinary(left_obs) == ordinary(right_obs)
    return {
        "left": left_id,
        "right": right_id,
        "fixed_actions": fixed,
        "held": all(checks.values()),
        "checks": checks,
        "first_observation_difference": first_difference,
        "first_action_difference": first_action,
    }


def truth_checks(root: Path, records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    observations = {cid: observations_from(load_run(root / "runs" / cid)[0]) for cid in records}
    index = {
        (
            r["cell"]["kind"],
            r["cell"]["truth"],
            r["cell"]["report"],
            r["cell"]["verdict"],
            r["cell"]["publish_round"],
        ): cid
        for cid, r in records.items()
        if r["cell"]["kind"] != "unaudited_fixed"
    }
    checks = []
    for report in oracle.TRUTHS:
        base = [index[("unaudited_behavior", truth, report, None, None)] for truth in oracle.TRUTHS]
        left_id, right_id = base
        checks.append(_truth_pair(left_id, right_id, observations, records, fixed=True))
        for timing in oracle.TIMINGS:
            unavailable = [
                index[("audited_behavior", t, report, "unavailable", timing)] for t in oracle.TRUTHS
            ]
            left_id, right_id = unavailable
            checks.append(_truth_pair(left_id, right_id, observations, records, fixed=True))
            for accuracy in (0, 1):
                pair = []
                forced_pair = []
                for truth in oracle.TRUTHS:
                    verdict = "positive" if (truth == report) == bool(accuracy) else "negative"
                    pair.append(index[("audited_behavior", truth, report, verdict, timing)])
                    kind = (
                        "audited_fixed"
                        if verdict == "negative" and timing < 6
                        else "audited_behavior"
                    )
                    forced_pair.append(index[(kind, truth, report, verdict, timing)])
                left_id, right_id = pair
                checks.append(_truth_pair(left_id, right_id, observations, records, fixed=False))
                left_id, right_id = forced_pair
                checks.append(_truth_pair(left_id, right_id, observations, records, fixed=True))
    return checks


def _checkpoint_round(path: Path, round_index: int) -> int:
    store = FileCheckpointStore(path / "checkpoints")
    return next(
        seq for seq in store.list_seqs() if store.load(seq)["state"]["round"] == round_index
    )


def _branch_check(
    parent: Path, child: Path, fork: int, target: ResolvedScenario, cell: dict[str, Any], trace: str
) -> dict[str, Any]:
    events, actual, manifest = load_run(child)
    if actual != target:
        raise ValueError("branch scenario differs from the declared fixture")
    original_ids = {agent: policy.policy_id for agent, policy in build_policies(target).items()}
    overridden_ids = {
        agent: build_ec_policy("ec_skeptical_contributor", POLICY_PARAMS).policy_id
        for agent in AGENTS
    }
    changed_ids = overridden_ids if trace == "A" else {}
    unchanged_ids = {} if trace == "A" else original_ids
    branch = json.loads((child / "branch.json").read_text(encoding="utf-8"))
    if (
        manifest["policies"] != {**unchanged_ids, **changed_ids}
        or branch["changed_policies"] != changed_ids
        or branch["unchanged_policies"] != unchanged_ids
    ):
        raise ValueError("branch fixture policy identity or override partition differs")
    parent_events, _, parent_manifest = load_run(parent)
    prefix = parent.joinpath("events.jsonl").read_bytes().splitlines(keepends=True)[: fork + 1]
    child_prefix = child.joinpath("events.jsonl").read_bytes().splitlines(keepends=True)[: fork + 1]
    summary = events[-1].payload
    expected = oracle.literal_outcome(trace, cell["truth"], cell["report"])
    publication = publication_check(events, _checkpoints(child, events), target, cell)
    replay = replay_run(child).chains_match
    seed_fields = ("seed_root", "seed_protocol", "policy_seed_root", "scenario_block")
    checks = {
        "prefix_bytes": prefix == child_prefix,
        "fork_hash": events[fork].event_hash == parent_events[fork].event_hash,
        "seed_identity": all(manifest[k] == parent_manifest[k] for k in seed_fields),
        "literal_actions": actions_from(events) == oracle.literal_schedule(trace, cell["report"]),
        "task_outcomes": all(
            summary[k] == expected[k]
            for k in ("briefing", "collective_quality", "effort", "individual_credit", "utility")
        ),
        "publication": publication["held"],
        "replay": replay,
        "policy_identity": True,
    }
    return {
        "held": all(checks.values()),
        "checks": checks,
        "replay_verified": replay,
        "fork_round": events[fork + 1].logical_time,
        "fork_seq": fork,
        "terminal_hash": events[-1].event_hash,
        "active_policy_ids": manifest["policies"],
        "changed_policies": branch["changed_policies"],
        "unchanged_policies": branch["unchanged_policies"],
        "new_publications": sum(e.event_type.value == "AuditPublished" for e in events[fork + 1 :]),
        "collective_quality": summary["collective_quality"],
        "total_effort": sum(summary["effort"].values()),
    }


def branch_checks(
    destination: Path, parent: Path, target: ResolvedScenario, cell: dict[str, Any]
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    records = {}
    cases = (
        ("before_publication", parent, 4, False),
        ("after_publication", parent, 5, False),
        ("nested", destination / "before_publication", 6, False),
        ("old_policy_override", parent, 4, True),
    )
    for label, source, round_index, override in cases:
        fork = _checkpoint_round(source, round_index)
        policies = {a: build_ec_policy("ec_skeptical_contributor", POLICY_PARAMS) for a in AGENTS}
        child = destination / label
        branch_run(
            parent_dir=source,
            fork_seq=fork,
            child_dir=child,
            child_run_id="audit-feedback-fixture-" + label,
            policy_overrides=policies if override else {},
        )
        records[label] = _branch_check(source, child, fork, target, cell, "A" if override else "C")
    return records


def audit_branches(
    destination: Path, parent: Path, target: ResolvedScenario, cell: dict[str, Any]
) -> dict[str, Any]:
    """Recompute stored branch evidence; a saved success flag is not authority."""
    cases = (
        ("before_publication", parent, 4, "C"),
        ("after_publication", parent, 5, "C"),
        ("nested", destination / "before_publication", 6, "C"),
        ("old_policy_override", parent, 4, "A"),
    )
    if {path.name for path in destination.iterdir()} != {case[0] for case in cases}:
        raise ValueError("branch fixture set differs from the declaration")
    records = {}
    for label, source, round_index, trace in cases:
        child = destination / label
        fork = _checkpoint_round(source, round_index)
        _, _, manifest = load_run(child)
        if manifest["run_id"] != "audit-feedback-fixture-" + label or manifest["fork_seq"] != fork:
            raise ValueError("branch fixture identity differs from the declaration")
        records[label] = _branch_check(source, child, fork, target, cell, trace)
    return records


def branch_parent() -> dict[str, Any]:
    return {
        "kind": "audited_behavior",
        "truth": "q",
        "report": "p",
        "verdict": "negative",
        "publish_round": 4,
        "trace": None,
    }


def _hex_digest(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _validated_source(provenance: Any) -> dict[str, Any]:
    fields = {
        "schema",
        "local_commit",
        "worktree_dirty",
        "python_version",
        "platform",
        "dependency_lock_sha256",
        "files_sha256",
    }
    if not isinstance(provenance, dict) or set(provenance) != fields:
        raise ValueError("source provenance has an invalid object shape")
    if (
        provenance["schema"] != "audit-feedback-source-v1"
        or provenance["worktree_dirty"] is not False
        or not _hex_digest(provenance["local_commit"], 40)
        or not _hex_digest(provenance["dependency_lock_sha256"], 64)
        or any(
            not isinstance(provenance[key], str) or not provenance[key].strip()
            for key in ("python_version", "platform")
        )
    ):
        raise ValueError("source provenance must identify clean committed, locked source")
    files = provenance["files_sha256"]
    if not isinstance(files, dict) or not files:
        raise ValueError("source provenance requires file digests")
    for name, digest in files.items():
        if (
            not isinstance(name, str)
            or not name
            or "\\" in name
            or ":" in name
            or PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or str(PurePosixPath(name)) != name
            or not _hex_digest(digest, 64)
        ):
            raise ValueError("source provenance contains an invalid path or digest")
    if files.get("requirements-lock.txt") != provenance["dependency_lock_sha256"]:
        raise ValueError("source provenance lock digest is not bound to the file digest")
    return dict(provenance)


def _source_bindings(root: Path, ids: set[str]) -> None:
    provenance_path = root / "SOURCE_PROVENANCE.json"
    if not provenance_path.exists():
        return
    provenance = _validated_source(json.loads(provenance_path.read_text(encoding="utf-8")))
    expected = {
        "code_commit": provenance["local_commit"],
        "worktree_dirty": False,
        "dependency_lock_sha256": provenance["dependency_lock_sha256"],
    }
    for cid in ids:
        manifest = json.loads((root / "runs" / cid / "manifest.json").read_text(encoding="utf-8"))
        if (
            not isinstance(manifest, dict)
            or manifest.get("worktree_dirty") is not False
            or any(manifest.get(k) != v for k, v in expected.items())
        ):
            raise ValueError("run source provenance differs from the clean original execution")


def collect(root: Path) -> dict[str, Any]:
    declaration, resolved = _saved_inputs(root)
    if {p.name for p in (root / "runs").iterdir()} != set(resolved):
        raise ValueError("experiment requires exactly the declared run set")
    _source_bindings(root, set(resolved))
    records = {
        cell_id(cell): episode_record(
            root / "runs" / cell_id(cell), resolved[cell_id(cell)], cell, declaration["design_hash"]
        )
        for cell in cells()
    }
    parent = branch_parent()
    parent_id = cell_id(parent)
    branches = audit_branches(
        root / "integrity-branches", root / "runs" / parent_id, resolved[parent_id], parent
    )
    if branches != json.loads((root / "branch_checks.json").read_text(encoding="utf-8")):
        raise ValueError("saved branch checks differ from actual sealed branch evidence")
    result = {
        "schema": "audit-feedback-results-v1",
        "status": "exploratory-unfrozen",
        "design_hash": declaration["design_hash"],
        "design_sha256": declaration["design_sha256"],
        "seed_protocol": PAIRED_SEED_PROTOCOL,
        "rounds_per_episode": ROUNDS,
        "behavioral_episodes": sum(c["kind"].endswith("behavior") for c in cells()),
        "fixed_action_episodes": sum(c["kind"].endswith("fixed") for c in cells()),
        "verified_replays": len(records),
        "episodes": records,
        "inference": "exact conditional response mixtures; no sample-based uncertainty",
        "same_action_integrity": same_action_checks(records),
        "truth_controls": truth_checks(root, records),
        "exact_mixtures": readout.mixtures(records),
        "branch_checks": branches,
    }
    result["predictions"] = readout.predictions(result)
    return result


def _retain_execution_failure(root: Path, phase: str, error: Exception) -> None:
    retained: dict[str, Any] = {}
    for cell in cells():
        cid = cell_id(cell)
        directory = root / "runs" / cid
        row: dict[str, Any] = {
            "cell": cell,
            "expected_trace": readout.expected_trace(cell),
            "artifact_status": "not-written",
        }
        ledger = directory / "events.jsonl"
        if ledger.exists():
            row.update(
                artifact_status="ledger-retained", ledger_sha256=sha256_hex(ledger.read_bytes())
            )
        manifest_path = directory / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                row.update(
                    artifact_status="manifest-retained",
                    recorded_status=manifest["status"],
                    recorded_failure=manifest.get("failure_reason"),
                )
            except (ValueError, KeyError, TypeError) as exc:
                row["manifest_read_error"] = type(exc).__name__
        retained[cid] = row
    write_json(
        root / "FAILED_EXECUTION.json",
        {
            "schema": "audit-feedback-execution-failure-v1",
            "phase": phase,
            "error_type": type(error).__name__,
            "error": str(error),
            "cells": retained,
            "prediction_readout_complete": False,
            "predictions": {
                f"P{i}": {"held": None, "status": "complete-readout-blocked"} for i in range(1, 9)
            },
            "interpretation": "Artifacts retained; incomplete predictions remain null.",
        },
    )


def execute(destination: Path, provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    phase = "inputs"
    try:
        declaration, resolved = write_inputs(destination / "inputs")
        if provenance is not None:
            write_json(destination / "SOURCE_PROVENANCE.json", provenance)
        phase = "episodes"
        for cell in cells():
            cid = cell_id(cell)
            run_cell(cell, resolved[cid], destination / "runs" / cid, declaration["design_hash"])
        phase = "branch-fixtures"
        parent = branch_parent()
        parent_id = cell_id(parent)
        branches = branch_checks(
            destination / "integrity-branches",
            destination / "runs" / parent_id,
            resolved[parent_id],
            parent,
        )
        write_json(destination / "branch_checks.json", branches)
        phase = "prediction-readout"
        result = collect(destination)
        write_json(destination / "RESULTS.json", result)
        (destination / "RESULTS.md").write_text(
            readout.render_report(result), encoding="utf-8", newline="\n"
        )
        return result
    except Exception as exc:
        _retain_execution_failure(destination, phase, exc)
        raise


def source_provenance() -> dict[str, Any]:
    commit, dirty = git_provenance(REPO)
    if commit is None or dirty is not False:
        raise ValueError("original execution requires clean committed source")
    inputs = sorted(
        [
            *REPO.glob("src/**/*.py"),
            *HERE.glob("*.py"),
            HERE / "DESIGN.md",
            REPO / "docs/adr/0017-noisy-corpus-and-audit-contract.md",
            REPO / "docs/adr/0018-opt-in-evidence-commons-audits.md",
            REPO / "requirements-lock.txt",
            REPO / "pyproject.toml",
        ]
    )
    return {
        "schema": "audit-feedback-source-v1",
        "local_commit": commit,
        "worktree_dirty": dirty,
        **environment_provenance(),
        "dependency_lock_sha256": lock_hash(REPO),
        "files_sha256": {
            path.relative_to(REPO).as_posix(): sha256_hex(path.read_bytes()) for path in inputs
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", type=Path)
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="chl-audit-feedback-") as temporary:
            target = Path(temporary) / "reproduction"
            result = execute(target)
            for filename in ("RESULTS.json", "RESULTS.md"):
                if (target / filename).read_bytes() != (HERE / filename).read_bytes():
                    raise SystemExit(f"{filename} differs from the retained audit-feedback readout")
        print(
            f"Verified {len(result['episodes'])} runs, {result['verified_replays']} original-chain "
            f"replays, {len(result['branch_checks'])} branch fixtures and 720 exact-law rows."
        )
    else:
        provenance = source_provenance()
        result = execute(args.out, provenance)
        print(f"Wrote sealed audit-feedback evidence and readout to {args.out}")
    if not all(row["held"] for row in result["predictions"].values()):
        raise SystemExit("audit-feedback predictions failed; all cells and misses retained")


if __name__ == "__main__":
    main()
