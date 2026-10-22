"""Replay: re-execute a sealed run and verify the event hash chain matches.

Replay rebuilds the mechanism from the run directory's frozen resolved
scenario (written at run time, so replay is self-contained), drives it with
ReplayPolicies fed from recorded ActionProposed events and typed ProviderError
outcomes in RunFailed seals, and compares the resulting chain hash-by-hash
against the original. Failures are raised only at the recorded policy boundary;
the runner independently regenerates the prefix and terminal state hash.

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
    provider_errors_from_events,
)
from collaborative_hill.engine.events import Event, EventType
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.seeds import LEGACY_SEED_PROTOCOL, validate_recorded_seed_metadata
from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore, RunPaths
from collaborative_hill.engine.validation import effective_policy_ids, validate_run
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
    # Label old manifests in memory; never rewrite sealed provenance on disk.
    manifest.setdefault("seed_protocol", LEGACY_SEED_PROTOCOL)
    if events:
        validate_recorded_seed_metadata(manifest, events[0].payload)
    validate_run(events, resolved, manifest)
    effective_policy_ids(run_dir, events, manifest)
    return events, resolved, manifest


class _RoundBoundary:
    """Stop a replay segment at a fork using the unchanged episode lifecycle."""

    def __init__(self, mechanism: Any, stop_round: int) -> None:
        self.mechanism = mechanism
        self.stop_round = stop_round

    def __getattr__(self, name: str) -> Any:
        return getattr(self.mechanism, name)

    def is_terminal(self, state: dict[str, Any]) -> bool:
        return bool(state["round"] >= self.stop_round or self.mechanism.is_terminal(state))


def _replay_segments(events: list[Event], resolved: ResolvedScenario,
                     manifest: dict[str, Any], paths: RunPaths) -> list[Event]:
    mechanism = resolved.build_mechanism()
    recorded = proposals_from_events(events)
    provider_errors = provider_errors_from_events(events)
    original_policy_ids = policy_ids_from_events(events)
    policies = {
        agent: ReplayPolicy(agent, original_policy_ids[agent], recorded.get(agent, {}),
                            provider_errors.get(agent, {}))
        for agent in mechanism.agent_ids()
    }
    starts = [0, *(i for i in range(1, len(events))
                   if events[i].run_id != events[i - 1].run_id)]
    state = None
    replayed: list[Event] = []
    reserved = {"agents", "policies", "seed_root", "invalid_action_policy",
                "seed_protocol", "policy_seed_root", "scenario_block"}
    start_meta = {k: v for k, v in events[0].payload.items() if k not in reserved}
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else None
        config = RunConfig(
            study_id=manifest["study_id"], run_id=events[start].run_id,
            seed_root=tuple(manifest["seed_root"]),
            seed_protocol=manifest["seed_protocol"],
            policy_seed_root=manifest.get("policy_seed_root"),
            scenario_block=manifest.get("scenario_block"),
            checkpoint_every=manifest["checkpoint_every"],
            invalid_action_policy=manifest["invalid_action_policy"],
        )
        engine = mechanism if end is None else _RoundBoundary(mechanism, events[end].logical_time)
        result = run_episode(mechanism=engine, policies=policies, config=config, paths=paths,
                             start_state=state, start_meta=start_meta)
        replayed = FileEventStore(paths.events).load_all(verify=True)
        if end is not None:
            # The boundary adapter produces a temporary completion seal, not an
            # event from the original branch. Remove ONLY that generated seal;
            # all prefix events and state were re-executed, never copied from input.
            if result.status != "completed" or replayed[-1].event_type != EventType.RUN_COMPLETED:
                return replayed
            record = FileCheckpointStore(paths.checkpoints).load(result.event_count - 2)
            state = record["state"]
            lines = paths.events.read_bytes().splitlines(keepends=True)
            paths.events.write_bytes(b"".join(lines[:-1]))
            replayed = FileEventStore(paths.events).load_all(verify=True)
            if not compare_chains(config.run_id, events[:end], replayed).chains_match:
                return replayed
    return replayed


def replay_run(run_dir: Path, keep_dir: Path | None = None) -> ReplayReport:
    """Re-execute every ancestral segment without reading parent paths/checkpoints."""
    run_dir = Path(run_dir)
    events, resolved, manifest = load_run(run_dir)
    workdir = (Path(keep_dir) if keep_dir is not None
               else Path(tempfile.mkdtemp(prefix="chl-replay-")))
    target = workdir / "replay"
    if target.resolve().is_relative_to(run_dir.resolve()):
        raise ValueError("replay output must be outside the source run")
    try:
        with RunPaths(target).reserve() as paths:
            replayed = _replay_segments(events, resolved, manifest, paths)
    finally:
        if keep_dir is None:
            shutil.rmtree(workdir, ignore_errors=True)
    report = compare_chains(manifest["run_id"], events, replayed)
    if not report.chains_match and events[-1].event_type == EventType.RUN_FAILED:
        return report.model_copy(update={
            "detail": f"recorded failure inconsistent with engine replay: {report.detail}",
        })
    return report


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
