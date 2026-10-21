"""Invalid appends must leave both ledger bytes and cached chain state intact."""

import pytest

from collaborative_hill.engine.events import ChainError, EventType, make_event
from collaborative_hill.engine.hashing import GENESIS_HASH
from collaborative_hill.engine.store import FileEventStore


def _event(seq, parent_hash, *, run_id="run"):
    return make_event(
        study_id="study", run_id=run_id, seq=seq, logical_time=seq,
        actor="engine", event_type=EventType.WORLD_TRANSITIONED,
        payload={"round": seq}, parent_hash=parent_hash,
    )


@pytest.mark.parametrize("ledger_state", ["missing", "empty", "populated"])
@pytest.mark.parametrize("invalid", ["sequence", "parent", "payload", "hash"])
def test_invalid_append_preserves_ledger_and_cached_state(tmp_path, ledger_state, invalid):
    path = tmp_path / "events.jsonl"
    if ledger_state == "empty":
        path.touch()
    store = FileEventStore(path)
    if ledger_state == "populated":
        store.append(_event(0, GENESIS_HASH))
        store = FileEventStore(path)
    before_bytes = path.read_bytes() if path.exists() else None
    before_state = (store.count, store.last_hash)
    parent_hash = store.last_hash or GENESIS_HASH
    valid = _event(store.count, parent_hash)

    if invalid == "sequence":
        bad = _event(store.count + 1, parent_hash)
        message = "append out of order"
    elif invalid == "parent":
        wrong_parent = GENESIS_HASH if store.count else "f" * 64
        bad = _event(store.count, wrong_parent)
        message = "parent link"
    elif invalid == "payload":
        bad = _event(store.count, parent_hash)
        bad.payload["round"] = 999
        message = "hash mismatch"
    else:
        bad = valid.model_copy(update={"event_hash": "f" * 64})
        message = "hash mismatch"

    with pytest.raises(ChainError, match=message):
        store.append(bad)

    assert (path.read_bytes() if path.exists() else None) == before_bytes
    assert (store.count, store.last_hash) == before_state
    store.append(valid)
    assert store.count == before_state[0] + 1
    assert store.last_hash == valid.event_hash
    assert store.load_all(verify=True)[-1] == valid


def test_append_accepts_unhashed_metadata_changes(tmp_path):
    store = FileEventStore(tmp_path / "events.jsonl")
    event = _event(0, GENESIS_HASH)
    recorded = event.model_copy(update={"meta": {"duration_seconds": 0.125}})

    store.append(recorded)

    assert store.last_hash == event.event_hash
    assert store.load_all(verify=True) == [recorded]


def test_append_accepts_branch_suffix_with_new_run_id(tmp_path):
    path = tmp_path / "events.jsonl"
    store = FileEventStore(path)
    parent = _event(0, GENESIS_HASH, run_id="parent")
    store.append(parent)
    prefix = path.read_bytes()
    child_store = FileEventStore(path)
    child = _event(1, parent.event_hash, run_id="child")

    child_store.append(child)

    assert path.read_bytes().startswith(prefix)
    assert child_store.count == 2
    assert child_store.last_hash == child.event_hash
    assert child_store.load_all(verify=True) == [parent, child]
