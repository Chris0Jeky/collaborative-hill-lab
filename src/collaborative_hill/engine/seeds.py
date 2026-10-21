"""Hierarchical deterministic randomness.

There is no global random state anywhere in this codebase. Every consumer of
randomness derives its own ``random.Random`` stream from a *seed path* — an
ordered tuple of components rooted at the study seed. Legacy studies use:

    (study_seed, condition_id, replicate, scope, entity_id[, ...])

e.g. ``rng_for(42, "pairwise", 3, "agent", "a2")`` or
``rng_for(42, "neighbourhood", 3, "mechanism", "resolution")``.

The legacy condition component makes policy streams INDEPENDENT across
conditions, even for the same replicate. ``paired-policy-v2`` instead uses
separate policy and mechanism roots (``study_seed_roots`` below; ADR-0008).

Derivation is SHA-256 over the version-tagged, unit-separated path, so:
- the same path always yields the same stream;
- adding a new random consumer elsewhere cannot shift any existing stream;
- no component separator collision is possible ("ab","c" != "a","bc").

The scheme is versioned by ``_DOMAIN_TAG``; changing it is a breaking change
to every sealed run and requires an ADR update (see ADR-0005).
"""

import hashlib
import random
from collections.abc import Mapping, Sequence
from typing import Any, Literal

_DOMAIN_TAG = b"chl-seed-v1"
_SEP = b"\x1f"  # ASCII unit separator: cannot appear in str(int) and is escaped in ids

SeedPath = tuple[str | int, ...]
SeedProtocol = Literal["legacy-independent-v1", "paired-policy-v2"]
LEGACY_SEED_PROTOCOL: Literal["legacy-independent-v1"] = "legacy-independent-v1"
PAIRED_SEED_PROTOCOL: Literal["paired-policy-v2"] = "paired-policy-v2"


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


def validate_scenario_block(block: str | None) -> None:
    """Blocks are explicit seed-path components, never silently normalised."""
    if block is not None:
        if not block.strip():
            raise ValueError("scenario_block must be a non-empty identifier")
        derive_seed("block", block)  # also rejects the reserved separator


def validate_seed_metadata(
    protocol: SeedProtocol,
    policy_seed_root: Sequence[str | int] | None,
    scenario_block: str | None,
) -> None:
    """Reject ambiguous run metadata instead of guessing whether a run is paired."""
    if protocol not in (LEGACY_SEED_PROTOCOL, PAIRED_SEED_PROTOCOL):
        raise ValueError(f"unknown seed_protocol: {protocol!r}")
    validate_scenario_block(scenario_block)
    if protocol == LEGACY_SEED_PROTOCOL:
        if policy_seed_root is not None or scenario_block is not None:
            raise ValueError(
                "legacy-independent-v1 cannot declare policy_seed_root or scenario_block"
            )
    elif policy_seed_root is None or not policy_seed_root or scenario_block is None:
        raise ValueError("paired-policy-v2 requires policy_seed_root and scenario_block")
    else:
        derive_seed(*policy_seed_root)


def study_seed_roots(
    study_seed: int,
    condition_id: str,
    replicate: int,
    *,
    protocol: SeedProtocol,
    scenario_block: str | None,
) -> tuple[SeedPath, SeedPath | None]:
    """Return (mechanism/legacy root, optional shared policy root).

    The PRNG derivation primitive remains ``chl-seed-v1``. The opt-in v2
    allocation protocol is domain-separated IN THE PATH; old paths and sealed
    runs are unchanged. Agent/round/purpose suffixes are applied by the runner.
    """
    if protocol == LEGACY_SEED_PROTOCOL:
        validate_seed_metadata(protocol, None, scenario_block)
        return (study_seed, condition_id, replicate), None
    if protocol != PAIRED_SEED_PROTOCOL:
        raise ValueError(f"unknown seed_protocol: {protocol!r}")
    if scenario_block is None:
        raise ValueError("paired-policy-v2 requires scenario_block for every condition")
    validate_scenario_block(scenario_block)
    return (
        (study_seed, protocol, "condition", condition_id, "replicate", replicate),
        (study_seed, protocol, "block", scenario_block, "replicate", replicate),
    )


def validate_recorded_seed_metadata(
    manifest: Mapping[str, Any], start_payload: Mapping[str, Any],
) -> None:
    """Do not silently downgrade or change a v2 run's sealed seed allocation."""
    protocol = manifest.get("seed_protocol", LEGACY_SEED_PROTOCOL)
    if protocol != start_payload.get("seed_protocol", LEGACY_SEED_PROTOCOL):
        raise ValueError("seed_protocol disagrees with the sealed RunStarted payload")
    validate_seed_metadata(
        protocol, manifest.get("policy_seed_root"), manifest.get("scenario_block"),
    )
    if protocol == PAIRED_SEED_PROTOCOL:
        for field in ("seed_root", "policy_seed_root", "scenario_block"):
            value = manifest.get(field)
            if field.endswith("_root"):
                value = list(map(str, value or []))
            if value != start_payload.get(field):
                raise ValueError(f"{field} disagrees with the sealed RunStarted payload")
