"""Read-only operational inventory of sealed and unfinished run artifacts.

This is a filesystem snapshot, not a process monitor or a scientific analysis.
Only a complete run accepted by ``load_run`` earns ``sealed_validated``. An
unsealed prefix can have valid hashes without establishing scenario provenance,
complete accounting, process liveness or a scientific outcome.
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import ChainError, Event, EventType, verify_chain
from collaborative_hill.engine.replay import load_run

SCHEMA_VERSION = "chl-monitor@1"
STATUSES = ("completed", "failed", "unsealed", "broken")
TERMINALS = {EventType.RUN_COMPLETED, EventType.RUN_FAILED}
SNAPSHOT_FILES = ("events.jsonl", "manifest.json", "scenario.resolved.json", "branch.json")


def _signature(root: Path) -> list[tuple[int, int, int, int] | None]:
    """Detect concurrent writes/replacement without recording times in the view."""
    signatures: list[tuple[int, int, int, int] | None] = []
    for name in SNAPSHOT_FILES:
        try:
            stat = (root / name).stat()
            signatures.append((stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns))
        except FileNotFoundError:
            signatures.append(None)
    return signatures


def _manifest(root: Path) -> dict[str, Any]:
    path = root / "manifest.json"
    if not path.exists():
        return {}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ChainError("run manifest must be a JSON object")
    if manifest.get("status") not in {"running", "completed", "failed"}:
        raise ChainError("run manifest has an unsupported status")
    return manifest


def _prefix(root: Path) -> tuple[list[Event], int]:
    path = root / "events.jsonl"
    if not path.exists():
        return [], 0
    # Read only the length observed when opening the file: an active writer
    # cannot turn this snapshot into an unbounded stream.
    with path.open("rb") as stream:
        import os

        data = stream.read(os.fstat(stream.fileno()).st_size)
    boundary = data.rfind(b"\n") + 1
    partial = len(data) - boundary
    events = []
    for number, line in enumerate(data[:boundary].splitlines(), start=1):
        if not line.strip():
            raise ChainError(f"blank complete record at line {number}")
        events.append(Event.model_validate_json(line))
    verify_chain(events)
    if events:
        if events[0].event_type != EventType.RUN_STARTED:
            raise ChainError("prefix requires a RunStarted event at seq 0")
        if sum(event.event_type == EventType.RUN_STARTED for event in events) != 1:
            raise ChainError("prefix requires exactly one RunStarted event")
        terminals = [index for index, event in enumerate(events) if event.event_type in TERMINALS]
        if terminals and terminals != [len(events) - 1]:
            raise ChainError("terminal seal must be the last record")
        if terminals and partial:
            raise ChainError("data follows a terminal seal")
    return events, partial


def _progress(row: dict[str, Any], events: list[Event], partial: int = 0) -> None:
    row.update(event_count=len(events), partial_record_bytes=partial)
    if events:
        last = events[-1]
        row.update(last_seq=last.seq, logical_time=last.logical_time,
                   last_event_type=last.event_type.value, last_event_hash=last.event_hash)


def _inspect(root: Path, relative: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "path": relative, "run_id": root.name, "condition_id": None, "study_id": None,
        "status": "unsealed", "manifest_status": None, "integrity": "not_checked",
        "event_count": 0, "partial_record_bytes": 0, "last_seq": None,
        "logical_time": None, "last_event_type": None, "last_event_hash": None,
        "failure_reason": None, "process_alive": None, "detail": "",
    }
    before = None
    try:
        before = _signature(root)
        manifest = _manifest(root)
        row["manifest_status"] = manifest.get("status")
        for field in ("run_id", "condition_id", "study_id"):
            if field in manifest:
                if not isinstance(manifest[field], str):
                    raise ChainError(f"manifest {field} must be a string")
                row[field] = manifest[field]
        if manifest.get("status") in {"completed", "failed"}:
            events, _, _ = load_run(root)
            _progress(row, events)
            row.update(status=manifest["status"], integrity="sealed_validated",
                       detail="Seal, chain, scenario and branch bindings validated; no replay run.")
            if events[-1].event_type == EventType.RUN_FAILED:
                row["failure_reason"] = events[-1].payload.get("reason")
        else:
            events, partial = _prefix(root)
            _progress(row, events, partial)
            row["integrity"] = "prefix_hashes_only" if events else "not_checked"
            if events and events[-1].event_type in TERMINALS:
                row["detail"] = "Terminal observed; final manifest is not available."
            else:
                row["detail"] = "Unsealed; process liveness and final outcome are unknown."
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        row.update(status="broken", integrity="broken", detail=f"{type(exc).__name__}: {exc}")
    try:
        if before is not None and _signature(root) != before:
            row.update(status="unsealed", integrity="not_checked", failure_reason=None,
                       detail="Artifacts changed during this snapshot; repeat the command.")
    except OSError:
        row.update(status="unsealed", integrity="not_checked", failure_reason=None,
                   detail="Artifacts became unreadable during this snapshot; repeat the command.")
    return row


def monitor_runs(root: Path) -> dict[str, Any]:
    """Inventory each artifact directory once, including manifest-only reservations."""
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"artifact directory does not exist: {root}")
    if any((root / name).exists() for name in ("events.jsonl", "manifest.json")):
        directories = [root]
    else:
        directories = sorted({path.parent for pattern in ("events.jsonl", "manifest.json")
                              for path in root.rglob(pattern)})
    rows = [_inspect(directory, directory.relative_to(root).as_posix())
            for directory in directories]
    counts = Counter(row["status"] for row in rows)
    return {"schema_version": SCHEMA_VERSION,
            "counts": {status: counts[status] for status in STATUSES}, "runs": rows}


def render_monitor(snapshot: dict[str, Any]) -> str:
    """A concise text view; no liveness inference or progress percentage."""
    counts = snapshot["counts"]
    lines = ["Run inventory: " + ", ".join(f"{counts[key]} {key}" for key in STATUSES)]
    for row in snapshot["runs"]:
        progress = (f"{row['event_count']} events, round {row['logical_time']}"
                    if row["last_seq"] is not None else "no complete events")
        lines.append(f"{row['status'].upper():9} {row['path']} | {progress}")
        lines.append(f"  {row['detail']}")
        if row["partial_record_bytes"]:
            lines.append(f"  {row['partial_record_bytes']} bytes in an incomplete final record")
        if row["failure_reason"]:
            lines.append(f"  {row['failure_reason']}")
    lines.append("Snapshot only: unsealed does not establish that a process is still running.")
    return "\n".join(lines) + "\n"
