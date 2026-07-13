"""Canonical serialization and content hashing.

Every scientific artifact in this lab (scenarios, mechanisms, events, manifests)
is content-addressed by the SHA-256 of its canonical JSON form. Two invariants
make replays and cross-machine comparisons exact:

1. Floats are FORBIDDEN in hashed content. Mechanism arithmetic uses
   ``fractions.Fraction``; serialize with :func:`frac_str` ("3/2") before
   hashing. Floats appear only in derived analysis artifacts, which are never
   part of a hash chain.
2. Canonical JSON is byte-stable: sorted keys, compact separators, ASCII-only
   escapes, and only ``None | bool | int | str | list | dict[str, ...]``.
"""

import hashlib
import json
from fractions import Fraction
from typing import Any

GENESIS_HASH = "0" * 64

JsonScalar = None | bool | int | str
Json = JsonScalar | list["Json"] | dict[str, "Json"]


class NonCanonicalValueError(TypeError):
    """Raised when a value cannot be canonically serialized (e.g. a float)."""


def _validate(obj: Any, path: str = "$") -> Json:
    if obj is None or isinstance(obj, bool | int | str):
        return obj
    if isinstance(obj, float):
        raise NonCanonicalValueError(
            f"float at {path}: floats are forbidden in hashed content; "
            "use fractions serialized via frac_str()"
        )
    if isinstance(obj, Fraction):
        raise NonCanonicalValueError(
            f"Fraction at {path}: serialize with frac_str() before hashing"
        )
    if isinstance(obj, list | tuple):
        return [_validate(v, f"{path}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, dict):
        out: dict[str, Json] = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise NonCanonicalValueError(f"non-string key {k!r} at {path}")
            out[k] = _validate(v, f"{path}.{k}")
        return out
    raise NonCanonicalValueError(f"unsupported type {type(obj).__name__} at {path}")


def canonical_json(obj: Any) -> str:
    """Serialize to byte-stable canonical JSON, rejecting non-canonical values."""
    return json.dumps(_validate(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def content_hash(obj: Any) -> str:
    """SHA-256 of the canonical JSON of ``obj``."""
    return sha256_hex(canonical_json(obj))


def frac_str(value: Fraction | int) -> str:
    """Exact, canonical string form of a rational: "7/2", "3", "-1/3"."""
    f = Fraction(value)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def parse_frac(text: str) -> Fraction:
    """Inverse of :func:`frac_str`."""
    return Fraction(text)
