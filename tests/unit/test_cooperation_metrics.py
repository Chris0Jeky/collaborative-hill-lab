"""Pin cooperation_metrics collapse / defection-round / window semantics (v1).

Mixed ledger (rounds 0-2, votes 2/2, 0/2, 0/2):
  rates [1.0, 0.0, 0.0] -> mean 1/3, first full-defection round 1,
  final window (window=3) 1/3, collapsed False.
All-defect ledger -> collapsed True.
Boundary ledger (final window exactly 0.1) -> collapsed True (<= 0.1).

Sensitivity contract: this test must FAIL if any of these regress —
the ``<= 0.1`` collapse threshold, the first-zero-coop-votes defection scan,
or the ``min(window, episode length)`` window cap.
"""

from collaborative_hill.engine.events import Event, EventType, make_event
from collaborative_hill.engine.hashing import GENESIS_HASH
from collaborative_hill.metrics.cooperation import cooperation_metrics


def _transitions(coop_per_round: list[int], total_votes: int = 2) -> list[Event]:
    events: list[Event] = []
    parent = GENESIS_HASH
    for rnd, coop in enumerate(coop_per_round):
        ev = make_event(
            study_id="S", run_id="R", seq=rnd, logical_time=rnd, actor="engine",
            event_type=EventType.WORLD_TRANSITIONED,
            payload={"round": rnd, "cooperative_votes": coop, "total_votes": total_votes},
            parent_hash=parent,
        )
        events.append(ev)
        parent = ev.event_hash
    return events


def test_collapsed_and_defection_round():
    events = _transitions([2, 0, 0])  # rounds 0-2: 2/2, 0/2, 0/2
    m = cooperation_metrics(events, window=3)

    assert m["cooperation_rate_by_round"] == [1.0, 0.0, 0.0]
    assert m["mean_cooperation"] == 1 / 3
    assert m["first_full_defection_round"] == 1
    assert m["final_window"] == 3
    assert m["final_window_cooperation"] == 1 / 3
    assert m["collapsed"] is False

    # Window cap: default window=10 exceeds the 3-round episode, so the
    # window must still cover exactly the 3 recorded rounds (not divide by 10).
    capped = cooperation_metrics(events)
    assert capped["final_window"] == 3
    assert capped["final_window_cooperation"] == 1 / 3

    all_defect = cooperation_metrics(_transitions([0, 0, 0]), window=3)
    assert all_defect["mean_cooperation"] == 0.0
    assert all_defect["first_full_defection_round"] == 0
    assert all_defect["collapsed"] is True

    # Threshold boundary: a final window of exactly 0.1 counts as collapsed.
    edge = cooperation_metrics(_transitions([1], total_votes=10), window=3)
    assert edge["final_window_cooperation"] == 0.1
    assert edge["collapsed"] is True
