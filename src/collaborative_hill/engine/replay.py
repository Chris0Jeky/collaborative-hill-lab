"""Replay: re-execute a sealed run and verify the event hash chain matches.

Replay rebuilds the mechanism from the run directory's frozen resolved
scenario (written at run time, so replay is self-contained), drives it with
ReplayPolicies fed from the recorded ActionProposed events, and compares the
resulting chain hash-by-hash against the original.

Determinism scope (ADR-0001): replay is deterministic GIVEN recorded typed
actions. For scripted policies a from-scratch rerun also matches (tested);
for LLM policies replay replays the recorded action, not the model call.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from collaborative_hill.agents.replay import (
    ReplayPolicy,
    policy_ids_from_events,
    proposals_from_events,
)
from collaborative_hill.engine.events import Event
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.scenario import ResolvedScenario


class ReplayReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    original_events: int
    replayed_events: int
    chains_match: bool
    first_divergence_seq: int | None = None
    detail: str = ""


def load_run(run_dir: Path) -> tuple[list[Event], ResolvedScenario, dict[str, Any]]:
    """Load (verified events, resolved scenario, manifest) from a run directory."""
    import json

    paths = RunPaths(run_dir)
    events = FileEventStore(paths.events).load_all(verify=True)
    resolved = ResolvedScenario.model_validate_json(
        (run_dir / "scenario.resolved.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    return events, resolved, manifest


def replay_run(run_dir: Path, keep_dir: Path | None = None) -> ReplayReport:
    events, resolved, manifest = load_run(Path(run_dir))
    mechanism = resolved.build_mechanism()
    recorded = proposals_from_events(events)
    original_policy_ids = policy_ids_from_events(events)
    policies = {
        agent: ReplayPolicy(agent, original_policy_ids[agent], recorded.get(agent, {}))
        for agent in mechanism.agent_ids()
    }
    config = RunConfig(
        study_id=manifest["study_id"],
        run_id=manifest["run_id"],
        seed_root=tuple(manifest["seed_root"]),
        checkpoint_every=manifest["checkpoint_every"],
        invalid_action_policy=manifest["invalid_action_policy"],
    )

    workdir = keep_dir or Path(tempfile.mkdtemp(prefix="chl-replay-"))
    try:
        paths = RunPaths(workdir / "replay").create()
        run_episode(mechanism=mechanism, policies=policies, config=config, paths=paths,
                    start_meta={"scenario_hash": resolved.scenario_hash,
                                "mechanism_hash": resolved.mechanism_hash,
                                "narrative_hash": resolved.narrative_hash})
        replayed = FileEventStore(paths.events).load_all(verify=True)
    finally:
        if keep_dir is None:
            shutil.rmtree(workdir, ignore_errors=True)

    return compare_chains(config.run_id, events, replayed)


def compare_chains(run_id: str, original: list[Event], replayed: list[Event]) -> ReplayReport:
    n = min(len(original), len(replayed))
    for i in range(n):
        if original[i].event_hash != replayed[i].event_hash:
            return ReplayReport(
                run_id=run_id, original_events=len(original), replayed_events=len(replayed),
                chains_match=False, first_divergence_seq=i,
                detail=(f"seq {i}: {original[i].event_type} vs {replayed[i].event_type}; "
                        f"payload diff likely — inspect both ledgers"),
            )
    if len(original) != len(replayed):
        return ReplayReport(
            run_id=run_id, original_events=len(original), replayed_events=len(replayed),
            chains_match=False, first_divergence_seq=n,
            detail="chains agree on common prefix but lengths differ",
        )
    return ReplayReport(
        run_id=run_id, original_events=len(original), replayed_events=len(replayed),
        chains_match=True,
    )


def verify_run_chain(run_dir: Path) -> int:
    """Cheap integrity check: verify the stored chain only. Returns event count."""
    paths = RunPaths(Path(run_dir))
    return len(FileEventStore(paths.events).load_all(verify=True))
