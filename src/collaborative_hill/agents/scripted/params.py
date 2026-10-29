"""Shared parameter contracts for the built-in scripted policies.

Both the CLI ``chl branch --override`` path (every value arrives as a ``str``)
and study specs use :func:`coerce_policy_params` to validate the same keys,
types and bounds. Specs discard the coerced result to retain exact hashed
values; policy builders use it at runtime. Bad input raises ``ValueError``
naming the key, never silently repaired. Other policies own their contracts.
"""

from collections.abc import Mapping
from fractions import Fraction

NIPD_POLICY_PARAMS: dict[str, frozenset[str]] = {
    "allc": frozenset(),
    "alld": frozenset(),
    "random": frozenset(),
    "tft_pairwise": frozenset({"epsilon"}),
    "tft_linked": frozenset({"epsilon"}),
    "ptft": frozenset({"denominator", "epsilon"}),
    "tft_threshold": frozenset({"threshold_num", "threshold_den", "epsilon"}),
}
EC_POLICY_PARAMS: dict[str, frozenset[str]] = {
    "ec_contributor": frozenset({"share_evidence"}),
    "ec_conditional_contributor": frozenset({
        "peer_threshold", "warmup_rounds", "share_evidence",
    }),
    "ec_freerider": frozenset(),
    "ec_verifier": frozenset(),
    "ec_misinformer": frozenset(),
}
SCRIPTED_POLICY_PARAMS = NIPD_POLICY_PARAMS | EC_POLICY_PARAMS


def coerce_policy_params(name: str, params: Mapping[str, object]) -> dict[str, object]:
    """Validate built-in parameters and return their runtime representations.

    Unknown policy names remain extension points; their keys and values are
    passed through unchanged. Built-in policies reject unsupported keys.
    """
    allowed = SCRIPTED_POLICY_PARAMS.get(name)
    if allowed is None:
        return dict(params)
    unknown = sorted(set(params) - allowed)
    if unknown:
        raise ValueError(f"unknown param(s) {unknown} for policy {name!r}")
    coerced: dict[str, object] = {}
    for key, value in params.items():
        if key == "epsilon":
            coerced[key] = _coerce_epsilon(key, value)
        elif key == "peer_threshold":
            coerced[key] = _coerce_exact_probability(key, value)
        elif key == "warmup_rounds":
            coerced[key] = _coerce_nonnegative_integer(key, value)
        elif key in ("threshold_num", "threshold_den"):
            coerced[key] = _coerce_threshold(key, value)
        elif key == "share_evidence":
            coerced[key] = _coerce_bool(key, value)
        elif key == "denominator":
            coerced[key] = _coerce_denominator(key, value)
        else:
            coerced[key] = value
    if name == "tft_threshold":
        # Match ThresholdTFTPolicy's defaults without adding keys to the spec.
        numerator = _coerce_threshold("threshold_num", coerced.get("threshold_num", 1))
        denominator = _coerce_threshold("threshold_den", coerced.get("threshold_den", 2))
        if not 0 <= numerator <= denominator:
            raise ValueError("invalid threshold_num/threshold_den: ratio must be in [0, 1]")
    return coerced


def _coerce_exact_probability(key: str, value: object) -> Fraction:
    """Preserve rational quorum boundaries; binary floats are not accepted."""
    if isinstance(value, bool) or not isinstance(value, int | str | Fraction):
        raise ValueError(f"invalid {key}: {value!r} (expected an exact fraction)")
    try:
        exact = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid {key}: {value!r}") from exc
    if not 0 <= exact <= 1:
        raise ValueError(f"invalid {key}: {value!r} (must be in [0, 1])")
    return exact


def _coerce_epsilon(key: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | str | float | Fraction):
        raise ValueError(f"invalid {key}: {value!r} (expected a probability)")
    try:
        exact = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid {key}: {value!r}") from exc
    if not 0 <= exact <= 1:
        raise ValueError(f"invalid {key}: {value!r} (must be in [0, 1])")
    return float(exact)


def _coerce_threshold(key: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ValueError(f"invalid {key}: {value!r} (expected an integer)")
    if isinstance(value, int):
        result = value
    else:
        try:
            result = int(str(value))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid {key}: {value!r}") from exc
    if key == "threshold_den" and result <= 0:
        raise ValueError(f"invalid {key}: {value!r} (must be > 0)")
    return result


def _coerce_denominator(key: str, value: object) -> str:
    if not isinstance(value, str) or value not in ("exclude_self", "include_self"):
        raise ValueError(f"invalid {key}: {value!r} (expected 'exclude_self'/'include_self')")
    return value


def _coerce_nonnegative_integer(key: str, value: object) -> int:
    result = _coerce_threshold(key, value)
    if result < 0:
        raise ValueError(f"invalid {key}: {value!r} (must be >= 0)")
    return result


def _coerce_bool(key: str, value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise ValueError(f"invalid {key}: {value!r} (expected 'true'/'false')")
