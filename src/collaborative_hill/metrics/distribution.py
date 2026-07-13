"""Distributional metrics (v1): who gains, who pays.

- utilities / efforts per agent (from the sealed summary).
- payoff_gini: Gini coefficient over final utilities (0 = equal).
- free_rider_advantage (EC): mean utility of zero-effort agents minus mean
  utility of positive-effort agents; None when a group is empty.
"""

from fractions import Fraction
from typing import Any

from collaborative_hill.engine.events import Event, EventType


def _gini(values: list[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    total = sum(values)
    if total == 0:
        return 0.0
    shifted = values
    if min(values) < 0:  # Gini needs non-negative values; shift and note it
        shift = -min(values)
        shifted = [v + shift for v in values]
        total = sum(shifted)
        if total == 0:
            return 0.0
    sorted_v = sorted(shifted)
    cum = 0.0
    for i, v in enumerate(sorted_v, start=1):
        cum += i * v
    return (2 * cum) / (n * total) - (n + 1) / n


def distribution_metrics(events: list[Event]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for ev in events:
        if ev.event_type == EventType.RUN_COMPLETED:
            summary = ev.payload

    result: dict[str, Any] = {"version": "1"}
    if "utility" in summary:  # Evidence Commons
        utilities = {a: float(Fraction(v)) for a, v in summary["utility"].items()}
        efforts = {a: int(v) for a, v in summary["effort"].items()}
        zero_effort = [utilities[a] for a in utilities if efforts.get(a, 0) == 0]
        pos_effort = [utilities[a] for a in utilities if efforts.get(a, 0) > 0]
        result.update({
            "utilities": utilities,
            "efforts": efforts,
            "payoff_gini": _gini(list(utilities.values())),
            "effort_gini": _gini([float(v) for v in efforts.values()]),
            "free_rider_advantage": (
                (sum(zero_effort) / len(zero_effort)) - (sum(pos_effort) / len(pos_effort))
                if zero_effort and pos_effort else None
            ),
        })
    elif "scores" in summary:  # NIPD
        scores = {a: float(Fraction(v)) for a, v in summary["scores"].items()}
        result.update({
            "utilities": scores,
            "payoff_gini": _gini(list(scores.values())),
        })
    return result
