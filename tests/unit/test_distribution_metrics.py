"""Pin distribution_metrics Gini and free-rider semantics (v2).

Sensitivity contract: this test must FAIL if the negative-utility shift
is removed (shifted Gini would collapse to 0.0) or if the free-rider
branch is swapped (positive-minus-zero instead of zero-minus-positive).
"""

from collaborative_hill.engine.events import Event, EventType, make_event
from collaborative_hill.engine.hashing import GENESIS_HASH
from collaborative_hill.metrics import METRIC_VERSIONS
from collaborative_hill.metrics.distribution import distribution_metrics


def _ledger(utility: dict[str, str], effort: dict[str, int]) -> list[Event]:
    ev = make_event(
        study_id="S",
        run_id="R",
        seq=0,
        logical_time=0,
        actor="engine",
        event_type=EventType.RUN_COMPLETED,
        payload={"utility": utility, "effort": effort},
        parent_hash=GENESIS_HASH,
    )
    return [ev]


def test_gini_and_free_rider() -> None:
    # Unequal utilities a:1 b:3 -> Gini 0.25.
    m = _ledger({"a": "1", "b": "3"}, {"a": 1, "b": 1})
    assert distribution_metrics(m)["payoff_gini"] == 0.25

    # Negative utilities must be shifted, not zeroed: Gini in [0, 1], not 0.0.
    neg = distribution_metrics(_ledger({"a": "-1", "b": "1"}, {"a": 1, "b": 1}))
    assert 0.0 <= neg["payoff_gini"] <= 1.0
    assert neg["payoff_gini"] != 0.0
    assert neg["payoff_gini"] == 0.5
    assert neg["version"] == METRIC_VERSIONS["distribution"] == "2"

    # Free-rider advantage is zero-effort mean minus positive-effort mean.
    ec = distribution_metrics(_ledger({"a": "4", "b": "1"}, {"a": 0, "b": 2}))
    assert ec["free_rider_advantage"] == ec["utilities"]["a"] - ec["utilities"]["b"]

    # All-equal effort leaves one group empty -> None.
    same = distribution_metrics(_ledger({"a": "2", "b": "2"}, {"a": 1, "b": 1}))
    assert same["free_rider_advantage"] is None
