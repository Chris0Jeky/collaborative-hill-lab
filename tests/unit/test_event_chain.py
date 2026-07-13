"""Hash-linked ledger invariants: verify_chain accepts well-formed chains and
detects tamper/gap/reorder/relink/rehash; meta is excluded from the hash; floats
in payload are rejected at emit time."""

import pytest

from collaborative_hill.engine.events import (
    ChainError,
    EventType,
    make_event,
    verify_chain,
)
from collaborative_hill.engine.hashing import GENESIS_HASH, NonCanonicalValueError


def _chain(n=3):
    events = []
    parent = GENESIS_HASH
    for seq in range(n):
        ev = make_event(
            study_id="S", run_id="R", seq=seq, logical_time=seq, actor="engine",
            event_type=EventType.WORLD_TRANSITIONED, payload={"round": seq},
            parent_hash=parent, meta={"wall": seq},
        )
        events.append(ev)
        parent = ev.event_hash
    return events


def test_well_formed_chain_verifies():
    verify_chain(_chain(4))  # must not raise


def test_payload_tamper_detected():
    events = _chain(3)
    tampered = events[1].model_copy(update={"payload": {"round": 999}})
    events[1] = tampered  # hash no longer matches payload
    with pytest.raises(ChainError, match="hash mismatch"):
        verify_chain(events)


def test_seq_gap_detected():
    events = _chain(3)
    # drop the middle event -> seqs become 0, 2
    broken = [events[0], events[2]]
    with pytest.raises(ChainError, match="seq gap"):
        verify_chain(broken)


def test_reordering_detected():
    events = _chain(3)
    reordered = [events[0], events[2], events[1]]
    with pytest.raises(ChainError):
        verify_chain(reordered)


def test_wrong_parent_detected():
    events = _chain(3)
    # relink event 2 to genesis (wrong parent) but keep its own hash recomputable
    bad = make_event(
        study_id="S", run_id="R", seq=2, logical_time=2, actor="engine",
        event_type=EventType.WORLD_TRANSITIONED, payload={"round": 2},
        parent_hash=GENESIS_HASH,
    )
    events[2] = bad
    with pytest.raises(ChainError, match="parent"):
        verify_chain(events)


def test_wrong_stored_hash_detected():
    events = _chain(3)
    events[1] = events[1].model_copy(update={"event_hash": "deadbeef" * 8})
    with pytest.raises(ChainError, match="hash mismatch"):
        verify_chain(events)


def test_meta_excluded_from_hash():
    a = make_event(
        study_id="S", run_id="R", seq=0, logical_time=0, actor="engine",
        event_type=EventType.RUN_STARTED, payload={"x": 1},
        parent_hash=GENESIS_HASH, meta={"wall_clock": "2026-01-01"},
    )
    b = make_event(
        study_id="S", run_id="R", seq=0, logical_time=0, actor="engine",
        event_type=EventType.RUN_STARTED, payload={"x": 1},
        parent_hash=GENESIS_HASH, meta={"wall_clock": "1999-12-31", "extra": [1, 2]},
    )
    # Different meta, identical everything-else -> identical hash.
    assert a.event_hash == b.event_hash
    assert a.hashed_view() == b.hashed_view()
    assert "meta" not in a.hashed_view()


def test_float_in_payload_rejected_at_emit_time():
    with pytest.raises(NonCanonicalValueError, match="float"):
        make_event(
            study_id="S", run_id="R", seq=0, logical_time=0, actor="engine",
            event_type=EventType.REWARD_ASSIGNED, payload={"reward": 3.5},
            parent_hash=GENESIS_HASH,
        )


def test_nested_float_in_payload_rejected():
    with pytest.raises(NonCanonicalValueError):
        make_event(
            study_id="S", run_id="R", seq=0, logical_time=0, actor="engine",
            event_type=EventType.WORLD_TRANSITIONED,
            payload={"rewards": {"a1": [1, 2.0]}}, parent_hash=GENESIS_HASH,
        )
