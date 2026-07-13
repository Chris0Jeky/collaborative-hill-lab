"""Hierarchical deterministic randomness.

There is no global random state anywhere in this codebase. Every consumer of
randomness derives its own ``random.Random`` stream from a *seed path* — an
ordered tuple of components rooted at the study seed:

    (study_seed, condition_id, replicate, scope, entity_id[, ...])

e.g. ``rng_for(42, "pairwise", 3, "agent", "a2")`` or
``rng_for(42, "neighbourhood", 3, "mechanism", "resolution")``.

Derivation is SHA-256 over the version-tagged, unit-separated path, so:
- the same path always yields the same stream (paired comparisons across
  conditions reuse replicate indices);
- adding a new random consumer elsewhere cannot shift any existing stream;
- no component separator collision is possible ("ab","c" != "a","bc").

The scheme is versioned by ``_DOMAIN_TAG``; changing it is a breaking change
to every sealed run and requires an ADR update (see ADR-0005).
"""

import hashlib
import random

_DOMAIN_TAG = b"chl-seed-v1"
_SEP = b"\x1f"  # ASCII unit separator: cannot appear in str(int) and is escaped in ids

SeedPath = tuple[str | int, ...]


def derive_seed(*path: str | int) -> int:
    """Derive a 64-bit seed from a hierarchical path. Deterministic, collision-resistant."""
    if not path:
        raise ValueError("seed path must have at least one component")
    parts = []
    for component in path:
        if not isinstance(component, str | int) or isinstance(component, bool):
            raise TypeError(f"seed path components must be str or int, got {component!r}")
        raw = str(component).encode("utf-8")
        if _SEP in raw:
            raise ValueError(f"seed path component contains reserved separator: {component!r}")
        parts.append(raw)
    digest = hashlib.sha256(_DOMAIN_TAG + _SEP + _SEP.join(parts)).digest()
    return int.from_bytes(digest[:8], "big")


def rng_for(*path: str | int) -> random.Random:
    """A fresh, independent PRNG stream for the given seed path."""
    return random.Random(derive_seed(*path))
