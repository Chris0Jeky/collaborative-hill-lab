"""File-backed run artifacts: event ledger, checkpoints, run directory layout.

Layout (transparency over scale, by design — see ADR-0002):

    artifacts/
      <study_hash>/
        <condition_id>/
          <run_id>/
            manifest.json        # RunManifest (experiments/manifests.py)
            events.jsonl         # one canonical-JSON event per line, append-only
            checkpoints/
              ckpt-<seq>.json    # sealed engine state at a boundary
            metrics/             # derived tables (parquet/csv), never hashed
            report.md            # generated, derived from the sealed ledger

Event lines are serialized canonically (sorted keys, compact separators), so
a branched run's copied prefix is byte-identical to its parent — a property
tested directly (acceptance scenario F).
"""

import json
import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import ChainError, Event, verify_chain
from collaborative_hill.engine.hashing import content_hash


class RunPaths:
    """Resolved locations of one run's artifacts."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.manifest = root / "manifest.json"
        self.events = root / "events.jsonl"
        self.checkpoints = root / "checkpoints"
        self.metrics = root / "metrics"
        self.report = root / "report.md"

    def create(self) -> "RunPaths":
        self.root.mkdir(parents=True, exist_ok=True)
        self.checkpoints.mkdir(exist_ok=True)
        self.metrics.mkdir(exist_ok=True)
        return self

    @contextmanager
    def reserve(self) -> Iterator["RunPaths"]:
        """Claim an empty run directory; clean up owned, unmanifested failures.

        If the filesystem cannot identify the reserved ledger, retain the
        artifacts for manual inspection rather than risk deleting a new owner.
        """
        created_root = False
        try:
            self.root.mkdir(parents=True)
            created_root = True
        except FileExistsError:
            if not self.root.is_dir():
                raise
        if any(self.root.iterdir()):
            raise FileExistsError(
                f"refusing to write into occupied run directory: {self.root}; "
                "choose a fresh output directory"
            )
        reservation = None
        try:
            with self.events.open("x", encoding="utf-8") as stream:
                try:
                    reservation = os.fstat(stream.fileno())
                except OSError:
                    # Recover identity only from the still-open descriptor:
                    # the pathname may already name a competing reservation.
                    with suppress(OSError):
                        reservation = os.fstat(stream.fileno())
                    raise
            yield self.create()
        except BaseException:
            with suppress(OSError):  # Cleanup must not hide the original failure.
                if (reservation is not None and reservation.st_ino != 0
                        and not self.manifest.exists()
                        and os.path.samestat(reservation, self.events.lstat())):
                    for path in (self.root / "scenario.resolved.json", self.root / "branch.json"):
                        path.unlink(missing_ok=True)
                    for directory in (self.checkpoints, self.metrics):
                        if directory.exists():
                            shutil.rmtree(directory)
                    # Release the ledger last; a new reservation then prevents rmdir.
                    self.events.unlink()
                    if created_root:
                        self.root.rmdir()
            raise


def _event_line(event: Event) -> str:
    """Deterministic single-line serialization of a full event (incl. hash and meta)."""
    return json.dumps(
        event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )


class FileEventStore:
    """Append-only JSONL event ledger for a single run."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._last_hash: str | None = None
        self._count = 0
        if path.exists():
            events = self.load_all(verify=True)
            self._count = len(events)
            self._last_hash = events[-1].event_hash if events else None

    @property
    def count(self) -> int:
        return self._count

    @property
    def last_hash(self) -> str | None:
        return self._last_hash

    def append(self, event: Event) -> None:
        if event.seq != self._count:
            raise ChainError(f"append out of order: expected seq {self._count}, got {event.seq}")
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(_event_line(event) + "\n")
        self._count += 1
        self._last_hash = event.event_hash

    def iter_events(self, *, reject_blank_records: bool = False) -> Iterator[Event]:
        """Read events; lenient inspection may skip blanks, verified loads may not."""
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                if not line.strip():
                    if reject_blank_records:
                        raise ChainError(f"blank record at line {line_number}")
                    continue
                yield Event.model_validate(json.loads(line))

    def load_all(self, verify: bool = True) -> list[Event]:
        events = list(self.iter_events(reject_blank_records=verify))
        if verify:
            verify_chain(events)
        return events


class FileCheckpointStore:
    """Sealed engine-state snapshots at configured boundaries.

    A checkpoint stores the canonical-JSON-safe engine state plus enough chain
    context (seq, last event hash) to branch or resume without replaying from
    seq 0. The state dict's content hash is stored alongside for integrity.
    """

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def save(self, *, seq: int, logical_time: int, last_event_hash: str,
             state: dict[str, Any]) -> Path:
        record = {
            "seq": seq,
            "logical_time": logical_time,
            "last_event_hash": last_event_hash,
            "state": state,
            "state_hash": content_hash(state),
        }
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"ckpt-{seq:06d}.json"
        path.write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
            encoding="utf-8",
        )
        return path

    def load(self, seq: int) -> dict[str, Any]:
        path = self.directory / f"ckpt-{seq:06d}.json"
        record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        if content_hash(record["state"]) != record["state_hash"]:
            raise ChainError(f"checkpoint {path.name} state hash mismatch")
        return record

    def list_seqs(self) -> list[int]:
        if not self.directory.exists():
            return []
        seqs: list[int] = []
        for p in self.directory.glob("ckpt-*.json"):
            suffix = p.stem.partition("-")[2]
            if suffix.isdigit():
                seqs.append(int(suffix))
        return sorted(seqs)
