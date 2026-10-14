"""Pin operational_metrics fallback and invalid-action-rate semantics.

Ledger: ActionProposed x2, ActionRejected x1, ActionAccepted(fallback=True) x1
  -> actions_rejected == 1, fallback_abstentions == 1, invalid_action_rate == 0.5.
Empty ledger -> invalid_action_rate == 0.0 and run_failed is False.

Sensitivity contract: this test must FAIL if the fallback-flag check
(`payload.get("fallback")` on ActionAccepted) or the zero-proposed guard
for the rate is dropped.
"""

from collaborative_hill.engine.events import Event, EventType, make_event
from collaborative_hill.engine.hashing import GENESIS_HASH
from collaborative_hill.metrics.operations import operational_metrics


def _ev(seq: int, parent: str, event_type: EventType, payload: dict) -> Event:
    ev = make_event(
        study_id="S",
        run_id="R",
        seq=seq,
        logical_time=seq,
        actor="engine",
        event_type=event_type,
        payload=payload,
        parent_hash=parent,
    )
    return ev


def _ledger(specs: list[tuple[EventType, dict]]) -> list[Event]:
    events: list[Event] = []
    parent = GENESIS_HASH
    for i, (etype, payload) in enumerate(specs):
        ev = _ev(i, parent, etype, payload)
        events.append(ev)
        parent = ev.event_hash
    return events


def test_fallback_and_rate():
    events = _ledger(
        [
            (EventType.ACTION_PROPOSED, {}),
            (EventType.ACTION_PROPOSED, {}),
            (EventType.ACTION_REJECTED, {}),
            (EventType.ACTION_ACCEPTED, {"fallback": True}),
        ]
    )
    m = operational_metrics(events)
    assert m["actions_rejected"] == 1
    assert m["fallback_abstentions"] == 1
    assert m["invalid_action_rate"] == 0.5

    # A non-fallback acceptance must not count as a fallback abstention,
    # so weakening the check to count every ActionAccepted fails.
    with_plain_accept = _ledger(
        [
            (EventType.ACTION_PROPOSED, {}),
            (EventType.ACTION_PROPOSED, {}),
            (EventType.ACTION_REJECTED, {}),
            (EventType.ACTION_ACCEPTED, {"fallback": True}),
            (EventType.ACTION_ACCEPTED, {}),
        ]
    )
    m2 = operational_metrics(with_plain_accept)
    assert m2["fallback_abstentions"] == 1

    # Zero-guard: no proposals must yield 0.0, not a ZeroDivisionError,
    # and an empty ledger is not a failed run.
    empty = operational_metrics([])
    assert empty["invalid_action_rate"] == 0.0
    assert empty["run_failed"] is False
