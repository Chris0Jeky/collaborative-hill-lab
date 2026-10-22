"""Read-only descriptive comparisons; no inference from a pair of episodes."""

from fractions import Fraction
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import Event, EventType
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.validation import effective_policy_ids
from collaborative_hill.metrics import METRIC_VERSIONS, operational_metrics
from collaborative_hill.reporting.report import compute_all_metrics


def _run_summary(directory: Path, events: list[Event],
                 manifest: dict[str, Any]) -> dict[str, Any]:
    completed = manifest["status"] == "completed"
    metrics = (compute_all_metrics(events, manifest) if completed else {
        "metric_versions": dict(METRIC_VERSIONS),
        "operations": operational_metrics(events, manifest),
    })
    terminal = events[-1].payload
    utilities = terminal.get("utility", terminal.get("scores", {}))
    return {
        **{key: manifest.get(key) for key in (
            "study_id", "condition_id", "run_id", "status", "scenario_hash",
            "mechanism_hash", "narrative_hash", "evidence_corpus_hash", "seed_protocol",
            "seed_root", "policy_seed_root", "scenario_block", "parent_run", "fork_seq",
        )},
        "event_count": len(events),
        "final_event_hash": events[-1].event_hash,
        "policy_ids": effective_policy_ids(directory, events, manifest),
        "metrics": metrics,
        "utilities_exact": ({a: str(Fraction(value)) for a, value in sorted(utilities.items())}
                            if completed else None),
    }


def _first_action_difference(left: list[Event], right: list[Event]) -> dict[str, Any] | None:
    def actions(events: list[Event]) -> dict[tuple[int, str], Any]:
        return {
            (event.logical_time, event.payload["agent_id"]): event.payload["proposal"]["action"]
            for event in events if event.event_type == EventType.ACTION_PROPOSED
        }

    left_actions, right_actions = actions(left), actions(right)
    for round_index, agent in sorted(left_actions.keys() | right_actions.keys()):
        a = left_actions.get((round_index, agent))
        b = right_actions.get((round_index, agent))
        if a != b:
            return {"round": round_index, "agent_id": agent, "left": a, "right": b}
    return None


def _kernel_streams(manifest: dict[str, Any]) -> tuple[Any, ...]:
    return (
        manifest["seed_protocol"],
        tuple(map(str, manifest["seed_root"])),
        tuple(map(str, manifest.get("policy_seed_root") or manifest["seed_root"])),
    )


def compare_runs(left: Path, right: Path, *, verify_replay: bool = False) -> dict[str, Any]:
    """Compare compatible mechanisms without reading caches or modifying runs.

    Seal/manifest/scenario consistency is always checked. Optional re-execution
    verifies deterministic engine transitions; neither mode re-calls providers.
    Deltas cover the entire episode, including shared pre-fork history.
    """
    left, right = Path(left), Path(right)
    a_events, a_resolved, a_manifest = load_run(left)
    b_events, b_resolved, b_manifest = load_run(right)
    if a_resolved.mechanism_hash != b_resolved.mechanism_hash:
        raise ValueError("run comparison requires the same mechanism hash; units may differ")
    replay_reports = {}
    if verify_replay:
        for label, directory in (("left", left), ("right", right)):
            replay = replay_run(directory)
            if not replay.chains_match:
                raise ValueError(f"replay failed for {replay.run_id}: {replay.detail}")
            replay_reports[label] = replay.model_dump(mode="json")
    a = _run_summary(left, a_events, a_manifest)
    b = _run_summary(right, b_events, b_manifest)
    prefix = 0
    for a_event, b_event in zip(a_events, b_events, strict=False):
        if a_event.event_hash != b_event.event_hash:
            break
        prefix += 1
    delta = None
    if a["utilities_exact"] is not None and b["utilities_exact"] is not None:
        if a["utilities_exact"].keys() != b["utilities_exact"].keys():
            raise ValueError("completed utility vectors have different agent rosters")
        delta = {agent: str(Fraction(b["utilities_exact"][agent]) - Fraction(value))
                 for agent, value in a["utilities_exact"].items()}
    return {
        "schema_version": 1,
        "scope": "descriptive_run_comparison",
        "direction": "right_minus_left",
        "replay_verified": verify_replay,
        "replay_reports": replay_reports,
        "left": a,
        "right": b,
        "common_prefix_events": prefix,
        "first_action_difference": _first_action_difference(a_events, b_events),
        "same_kernel_streams": _kernel_streams(a_manifest) == _kernel_streams(b_manifest),
        "utility_delta": delta,
        "notes": [
            "Two episodes are not statistical evidence of a treatment effect or generalisation.",
            "Utilities and deltas are full-episode totals, including common pre-fork history.",
            "Equal kernel streams do not guarantee equal actions, provider sampling or variance.",
            "Policy labels describe configuration; they do not authenticate executable code.",
            "Failed episodes retain operational metrics but have no outcome delta.",
        ],
    }
