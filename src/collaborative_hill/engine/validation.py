"""Read-only checks tying run manifests and checkpoint snapshots to sealed events."""

import json
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import ChainError, Event, EventType
from collaborative_hill.engine.hashing import content_hash
from collaborative_hill.engine.seeds import validate_recorded_seed_metadata
from collaborative_hill.experiments.scenario import ResolvedScenario, compile_scenario


def validate_run(events: list[Event], resolved: ResolvedScenario,
                 manifest: dict[str, Any]) -> None:
    """Validate the seal and scenario bindings after the event chain is checked."""
    if not events or events[0].event_type != EventType.RUN_STARTED:
        raise ChainError("run requires a RunStarted event at seq 0")
    if sum(e.event_type == EventType.RUN_STARTED for e in events) != 1:
        raise ChainError("run requires exactly one RunStarted event")
    terminals = [e for e in events
                 if e.event_type in {EventType.RUN_COMPLETED, EventType.RUN_FAILED}]
    if len(terminals) != 1 or terminals[0] != events[-1]:
        raise ChainError("run requires exactly one terminal seal at the end")
    terminal = events[-1]
    expected = {"completed": EventType.RUN_COMPLETED, "failed": EventType.RUN_FAILED}
    status = manifest.get("status")
    if not isinstance(status, str) or terminal.event_type != expected.get(status):
        raise ChainError("manifest status does not match the terminal seal")
    if terminal.run_id != manifest.get("run_id") or any(
        event.study_id != manifest.get("study_id") for event in events
    ):
        raise ChainError("manifest study/run identity does not match the sealed ledger")
    for field, actual in (("event_count", len(events)), ("final_event_hash", terminal.event_hash)):
        if manifest.get(field) is not None and manifest[field] != actual:
            raise ChainError(f"manifest {field} does not match the sealed ledger")
    _validate_scenario_bindings(events, resolved, manifest)
    _validate_ancestry(events, manifest)


def _validate_scenario_bindings(events: list[Event], resolved: ResolvedScenario,
                                manifest: dict[str, Any]) -> None:
    canonical = compile_scenario(resolved.spec, resolved.skin)
    for field in ("scenario_hash", "mechanism_hash", "narrative_hash", "evidence_corpus_hash"):
        actual = getattr(canonical, field)
        if getattr(resolved, field) != actual or manifest.get(field) != actual:
            raise ChainError(f"manifest or resolved scenario {field} mismatch")
        if field in events[0].payload and events[0].payload[field] != actual:
            raise ChainError(f"RunStarted {field} does not match the resolved scenario")
    validate_recorded_seed_metadata(manifest, events[0].payload)
    if list(map(str, manifest.get("seed_root", []))) != events[0].payload.get("seed_root"):
        raise ChainError("manifest seed_root disagrees with RunStarted")
    if manifest.get("invalid_action_policy") != events[0].payload.get("invalid_action_policy"):
        raise ChainError("manifest invalid_action_policy disagrees with RunStarted")
    roster = sorted(a.agent_id for a in resolved.spec.cognition.agents)
    if roster != events[0].payload.get("agents"):
        raise ChainError("RunStarted agent roster does not match the resolved scenario")


def _validate_ancestry(events: list[Event], manifest: dict[str, Any]) -> None:
    # A run ID may occupy only one contiguous segment. Reusing an ancestor ID
    # makes the fork boundary ambiguous and is not a supported branch format.
    seen: set[str] = set()
    previous: str | None = None
    for event in events:
        if event.run_id != previous:
            if event.run_id in seen:
                raise ChainError("reused run identity in branch ancestry")
            seen.add(event.run_id)
            previous = event.run_id
    if not manifest.get("parent_run") and len(seen) != 1:
        raise ChainError("mixed run identities require branch provenance")


def effective_policy_ids(run_dir: Path, events: list[Event],
                         manifest: dict[str, Any]) -> dict[str, str]:
    """Read the direct parent's effective labels without following parent paths.

    Labels describe the configured policies; they are not serialized executable
    implementations. Old branch manifests stored root labels in manifest.json,
    so branch.json remains the compatibility source for those runs.
    """
    root_ids: dict[str, str] = dict(events[0].payload["policies"])
    if not manifest.get("parent_run"):
        if manifest.get("policies") != root_ids:
            raise ChainError("manifest policies disagree with RunStarted")
        return root_ids
    branch = json.loads((Path(run_dir) / "branch.json").read_text(encoding="utf-8"))
    if not isinstance(branch, dict):
        raise ChainError("branch provenance must be a JSON object")
    version = branch.get("schema_version", 1)
    if type(version) is not int or version not in (1, 2):
        raise ChainError("unsupported branch schema_version")
    fork = branch.get("fork_seq")
    if type(fork) is not int or not 0 <= fork < len(events) - 1:
        raise ChainError("invalid branch fork_seq")
    checks = {
        "parent_run_id": manifest.get("parent_run"),
        "child_run_id": manifest.get("run_id"),
        "fork_seq": manifest.get("fork_seq"),
        "parent_event_hash_at_fork": events[fork].event_hash,
        "fork_round": events[fork + 1].logical_time,
    }
    if any(branch.get(key) != value for key, value in checks.items()):
        raise ChainError("branch provenance disagrees with manifest or sealed fork")
    if (manifest.get("parent_event_hash_at_fork") != events[fork].event_hash
            or events[fork].run_id != manifest.get("parent_run")
            or any(e.run_id == manifest["run_id"] for e in events[:fork + 1])
            or any(e.run_id != manifest["run_id"] for e in events[fork + 1:])):
        raise ChainError("branch run identities or fork hash do not match the ledger")
    changed, unchanged = branch.get("changed_policies"), branch.get("unchanged_policies")
    if (not isinstance(changed, dict) or not isinstance(unchanged, dict)
            or set(changed) & set(unchanged) or set(changed) | set(unchanged) != set(root_ids)):
        raise ChainError("branch policy labels must partition the agent roster")
    active = {**unchanged, **changed}
    if any(not isinstance(value, str) or not value for value in active.values()):
        raise ChainError("branch policy labels must be non-empty strings")
    if version >= 2 and manifest.get("policies") != active:
        raise ChainError("manifest policies disagree with branch effective policies")
    return active


def validate_checkpoint(record: dict[str, Any], fork_seq: int, events: list[Event]) -> None:
    """A self-hash is insufficient: bind the snapshot to the next sealed event."""
    if type(fork_seq) is not int or not 0 <= fork_seq < len(events) - 1:
        raise ChainError("checkpoint sequence is outside the sealed ledger")
    try:
        boundary = events[fork_seq + 1]
        if (type(record["seq"]) is not int or record["seq"] != fork_seq
                or record["last_event_hash"] != events[fork_seq].event_hash
                or type(record["logical_time"]) is not int
                or record["logical_time"] != record["state"]["round"]
                or record["logical_time"] != boundary.logical_time
                or content_hash(record["state"]) != record["state_hash"]):
            raise ChainError("checkpoint identity, round or state hash mismatch")
        if boundary.event_type == EventType.CHECKPOINT_CREATED:
            valid = (boundary.payload["at_seq"] == fork_seq
                     and boundary.payload["round"] == record["logical_time"]
                     and boundary.payload["state_hash"] == record["state_hash"])
        else:
            valid = (boundary.event_type == EventType.RUN_COMPLETED
                     and boundary.payload.get("final_state_hash") == record["state_hash"])
        if not valid:
            raise ChainError("checkpoint is not bound to a sealed checkpoint or final state")
    except (KeyError, TypeError) as exc:
        raise ChainError("malformed checkpoint record") from exc
