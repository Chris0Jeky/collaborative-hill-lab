"""Coercion for scripted policy params from stringly sources.

Both the CLI ``chl branch --override`` path (every value arrives as a ``str``)
and study specs (JSON params pass through nearly raw) funnel through
:func:`coerce_policy_params` so they behave identically. Strict: bad input
raises ``ValueError`` naming the key, never silently repaired.
"""

from collections.abc import Mapping
from fractions import Fraction

# Every bool-valued param declared by the EC policy constructors in
# ec_policies.py. ECContributorPolicy takes ``share_evidence: bool``; the
# freerider/verifier/misinformer constructors take no params, and there are
# no int-valued EC params to handle.
BOOL_KEYS: frozenset[str] = frozenset({"share_evidence"})


def coerce_policy_params(name: str, params: Mapping[str, object]) -> dict[str, object]:
    """Coerce stringly policy params to their declared types.

    ``name`` is the policy name (reserved for future per-policy keys;
    coercion today dispatches per key). Unknown keys pass through unchanged.
    """
    _ = name
    coerced: dict[str, object] = {}
    for key, value in params.items():
        if key == "epsilon":
            coerced[key] = _coerce_epsilon(key, value)
        elif key in ("threshold_num", "threshold_den"):
            coerced[key] = _coerce_threshold(key, value)
        elif key in BOOL_KEYS:
            coerced[key] = _coerce_bool(key, value)
        else:
            coerced[key] = value
    return coerced


def _coerce_epsilon(key: str, value: object) -> float:
    try:
        return float(Fraction(str(value)))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid {key}: {value!r}") from exc


def _coerce_threshold(key: str, value: object) -> int:
    if isinstance(value, bool):
        raise ValueError(f"invalid {key}: {value!r} (bool not accepted)")
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
