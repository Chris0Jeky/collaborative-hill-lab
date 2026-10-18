import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest  # noqa: E402

from collaborative_hill.engine.events import ChainError, EventType, make_event  # noqa: E402
from collaborative_hill.engine.hashing import GENESIS_HASH, content_hash  # noqa: E402
from collaborative_hill.engine.store import (  # noqa: E402
    FileCheckpointStore,
    FileEventStore,
    RunPaths,
)

pytestmark = pytest.mark.integration


def _chain(n: int):
    events = []
    parent = GENESIS_HASH
    for seq in range(n):
        ev = make_event(
            study_id="S", run_id="R", seq=seq, logical_time=seq, actor="engine",
            event_type=EventType.WORLD_TRANSITIONED, payload={"round": seq},
            parent_hash=parent,
        )
        events.append(ev)
        parent = ev.event_hash
    return events


@pytest.mark.parametrize("setup", ["missing", "empty"])
def test_missing_and_empty_ledger_read_as_empty(tmp_path: Path, setup: str) -> None:
    ledger = tmp_path / "events.jsonl"
    if setup == "empty":
        ledger.write_text("", encoding="utf-8")
    store = FileEventStore(ledger)
    assert store.count == 0
    assert store.last_hash is None
    assert list(store.iter_events()) == []
    assert store.load_all(verify=True) == []


def test_append_out_of_order_rejected_without_write(tmp_path: Path) -> None:
    ledger = tmp_path / "events.jsonl"
    store = FileEventStore(ledger)
    first = _chain(1)[0]
    store.append(first)
    bad = make_event(
        study_id="S", run_id="R", seq=5, logical_time=5, actor="engine",
        event_type=EventType.WORLD_TRANSITIONED, payload={"round": 5},
        parent_hash=first.event_hash,
    )
    with pytest.raises(ChainError, match="out of order"):
        store.append(bad)
    assert store.count == 1
    assert store.last_hash == first.event_hash
    assert ledger.read_text(encoding="utf-8").count("\n") == 1


def test_reopened_store_resumes_count_and_hash(tmp_path: Path) -> None:
    ledger = tmp_path / "events.jsonl"
    events = _chain(2)
    store = FileEventStore(ledger)
    for ev in events:
        store.append(ev)
    reopened = FileEventStore(ledger)
    assert reopened.count == 2
    assert reopened.last_hash == events[-1].event_hash
    third = make_event(
        study_id="S", run_id="R", seq=2, logical_time=2, actor="engine",
        event_type=EventType.WORLD_TRANSITIONED, payload={"round": 2},
        parent_hash=events[-1].event_hash,
    )
    reopened.append(third)
    assert reopened.count == 3
    assert reopened.last_hash == third.event_hash


def test_iter_skips_blank_lines(tmp_path: Path) -> None:
    ledger = tmp_path / "events.jsonl"
    events = _chain(2)
    store = FileEventStore(ledger)
    for ev in events:
        store.append(ev)
    with ledger.open("a", encoding="utf-8", newline="\n") as f:
        f.write("\n   \n\t\n")
    assert [e.seq for e in store.iter_events()] == [0, 1]
    assert [e.seq for e in store.load_all(verify=True)] == [0, 1]


def test_load_verify_flag_on_tampered_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / "events.jsonl"
    store = FileEventStore(ledger)
    for ev in _chain(2):
        store.append(ev)
    lines = ledger.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[1])
    record["payload"] = {"round": 999}
    lines[1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert len(store.load_all(verify=False)) == 2
    with pytest.raises(ChainError, match="hash mismatch"):
        store.load_all(verify=True)


def test_checkpoint_save_load_roundtrip(tmp_path: Path) -> None:
    store = FileCheckpointStore(tmp_path / "checkpoints")
    state = {"round": 7, "notes": [1, 2]}
    path = store.save(seq=7, logical_time=7, last_event_hash="ab" * 32, state=state)
    assert path.name == "ckpt-000007.json"
    record = store.load(7)
    assert record["seq"] == 7
    assert record["logical_time"] == 7
    assert record["last_event_hash"] == "ab" * 32
    assert record["state"] == state
    assert record["state_hash"] == content_hash(state)
    assert store.list_seqs() == [7]


def test_run_paths_create_is_idempotent(tmp_path: Path) -> None:
    paths = RunPaths(tmp_path / "run")
    paths.create().create()
    assert paths.root.is_dir()
    assert paths.checkpoints.is_dir()
    assert paths.metrics.is_dir()
