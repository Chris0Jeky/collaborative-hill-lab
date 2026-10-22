"""Draft SAP estimators: whole-episode/cell or whole-block bootstrap, never turns.

Arithmetic and percentile interpolation are rational. Only the supplementary
Student-t check uses floating point, serialized as decimal strings by the caller.
No model fitting, external statistics dependency, or global random state.
"""

import math
from collections.abc import Sequence
from fractions import Fraction
from typing import Any

from collaborative_hill.engine.hashing import frac_str
from collaborative_hill.engine.seeds import rng_for

CELLS = ("agg-priv", "agg-ledger", "attr-priv", "attr-ledger")
WEIGHTS = {
    "E1": (Fraction(-1, 2), Fraction(-1, 2), Fraction(1, 2), Fraction(1, 2)),
    "E2": (Fraction(-1, 2), Fraction(1, 2), Fraction(-1, 2), Fraction(1, 2)),
    "E3": (Fraction(1), Fraction(-1), Fraction(-1), Fraction(1)),
}


def mean(values: Sequence[Fraction]) -> Fraction:
    return sum(values, Fraction()) / len(values)


def holm(p_values: Sequence[Fraction]) -> list[Fraction]:
    """Holm step-down adjusted p-values, in input order (ties are stable)."""
    if any(not 0 <= p <= 1 for p in p_values):
        raise ValueError("p-values must lie in [0, 1]")
    adjusted = [Fraction()] * len(p_values)
    previous = Fraction()
    for rank, index in enumerate(sorted(range(len(p_values)), key=p_values.__getitem__)):
        previous = min(Fraction(1), max(previous, (len(p_values) - rank) * p_values[index]))
        adjusted[index] = previous
    return adjusted


def percentile(values: Sequence[Fraction], probability: Fraction) -> Fraction:
    """Linear interpolation between sorted order statistics (type 7)."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = position.numerator // position.denominator
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_means(values: Sequence[Fraction], *, seed: int, samples: int,
                    scope: str) -> list[Fraction]:
    rng = rng_for(seed, "chl.analyze.v1", scope)
    return [mean([values[rng.randrange(len(values))] for _ in values])
            for _ in range(samples)]


def interval(draws: Sequence[Fraction]) -> list[str]:
    return [frac_str(percentile(draws, p)) for p in (Fraction(1, 40), Fraction(39, 40))]


def _t_critical(df: int) -> float:
    """Student-t .975 quantile via the cosine-integral CDF and bisection.

    t = sqrt(df) tan(theta); the transformed density is proportional to
    cos(theta)**(df-1). Its integral has an elementary two-step recurrence.
    """
    def area(theta: float) -> float:
        even, odd = theta, math.sin(theta)
        for power in range(2, df):
            value = (math.sin(theta) * math.cos(theta) ** (power - 1) / power
                     + (power - 1) / power * (even if power % 2 == 0 else odd))
            if power % 2 == 0:
                even = value
            else:
                odd = value
        return even if df % 2 else odd

    target = .95 * area(math.pi / 2)
    low, high = 0.0, math.pi / 2
    for _ in range(70):
        midpoint = (low + high) / 2
        if area(midpoint) < target:
            low = midpoint
        else:
            high = midpoint
    return math.sqrt(df) * math.tan((low + high) / 2)


def paired_t_interval(values: Sequence[Fraction]) -> list[str] | None:
    if len(values) < 2 or len(set(values)) == 1:
        return None
    average = mean(values)
    variance = sum((v - average) ** 2 for v in values) / (len(values) - 1)
    half = _t_critical(len(values) - 1) * math.sqrt(float(variance) / len(values))
    return [format(float(average) - half, ".12g"), format(float(average) + half, ".12g")]


def contrasts(cells: dict[str, list[Fraction]], *, seed: int, samples: int,
              blocks: list[dict[str, Fraction]] | None = None,
              unavailable: str | None = None) -> dict[str, Any]:
    """Equal-cell-weight factorial effects; E3 = A effect(shared) - A effect(private).

    The draft two-sided test is the centered bootstrap tail probability with
    a +1 Monte Carlo correction. Holm always covers all three primary tests.
    Degenerate cells suppress inference for the entire family (SAP 4.5).
    """
    if samples < 2:
        raise ValueError("bootstrap samples must be >= 2")
    reason = unavailable
    if any(not cells[c] for c in CELLS):
        reason = "missing_cell"
    elif any(len(set(cells[c])) == 1 for c in CELLS):
        reason = reason or "zero_between_episode_variance"
    draws = ({c: bootstrap_means(cells[c], seed=seed, samples=samples, scope=c)
              for c in CELLS} if reason is None and blocks is None else {})
    result: dict[str, Any] = {}
    raw_p = []
    for name, weights in WEIGHTS.items():
        estimate = (sum((w * mean(cells[c]) for c, w in zip(CELLS, weights, strict=True)),
                        Fraction())
                    if all(cells[c] for c in CELLS) else None)
        per_block = ([sum((w * b[c] for c, w in zip(CELLS, weights, strict=True)), Fraction())
                      for b in blocks] if blocks else [])
        effect_reason = reason
        if per_block and len(set(per_block)) == 1:
            effect_reason = effect_reason or "zero_between_block_contrast_variance"
        contrast_draws = []
        if effect_reason is None:
            if blocks is not None:
                contrast_draws = bootstrap_means(
                    per_block, seed=seed, samples=samples, scope="blocks",
                )
            else:
                contrast_draws = [sum((w * draws[c][i]
                                      for c, w in zip(CELLS, weights, strict=True)), Fraction())
                                  for i in range(samples)]
        p = None
        if contrast_draws and estimate is not None:
            p = Fraction(1 + sum(abs(v - estimate) >= abs(estimate) for v in contrast_draws),
                         samples + 1)
        raw_p.append(p if p is not None else Fraction(1))
        result[name] = {
            "estimate": frac_str(estimate) if estimate is not None else None,
            "ci95": interval(contrast_draws) if contrast_draws else None,
            "p_unadjusted": frac_str(p) if p is not None else None,
            "p_holm": None,
            "inference_unavailable": effect_reason,
            "paired_differences": [frac_str(v) for v in per_block] if blocks else None,
            "t_ci95_check": (paired_t_interval(per_block)
                             if effect_reason is None and blocks else None),
        }
    for name, p in zip(WEIGHTS, holm(raw_p), strict=True):
        if result[name]["p_unadjusted"] is not None:
            result[name]["p_holm"] = frac_str(p)
    return result


def describe(values: list[Fraction], *, seed: int, samples: int, scope: str) -> dict[str, Any]:
    degenerate = bool(values) and len(set(values)) == 1
    return {
        "n": len(values), "n_missing": 0,
        "n_effective": 1 if degenerate else len(values),
        "zero_between_episode_variance": degenerate,
        "mean": frac_str(mean(values)) if values else None,
        "ci95": (interval(bootstrap_means(values, seed=seed, samples=samples, scope=scope))
                 if values and not degenerate else None),
    }
