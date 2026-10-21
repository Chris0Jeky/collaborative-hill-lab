"""Read-only inspection of the kernel streams allocated to a study schedule."""

import json
import re
from pathlib import Path
from typing import Any

from collaborative_hill.agents.llm import LLMPolicy
from collaborative_hill.engine.seeds import SeedPath, derive_seed, study_seed_roots
from collaborative_hill.experiments.scenario import NIPDWorld
from collaborative_hill.experiments.study import (
    build_policies,
    load_study,
    study_hash,
)


def _stream(path: SeedPath) -> dict[str, Any]:
    return {
        "seed_path": list(path),
        # Decimal text preserves all 64 bits in JSON consumers with float numbers.
        "derived_seed": str(derive_seed(*path)),
    }


def _audit_frozen_hash(study_dir: Path) -> str | None:
    """Require the canonical hash shape without changing lifecycle lock parsing."""
    lock_path = study_dir / "study.lock.json"
    if not lock_path.exists():
        return None
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    locked = lock.get("study_hash") if isinstance(lock, dict) else None
    if not isinstance(locked, str) or re.fullmatch(r"[0-9a-f]{64}", locked) is None:
        raise ValueError(
            "invalid study.lock.json: expected an object with a study_hash "
            "of 64 lowercase hexadecimal characters"
        )
    return locked


def audit_study_seeds(
    study_dir: Path, *, replicate: int = 0, round_index: int = 0,
) -> dict[str, Any]:
    """Describe one scheduled round without running policies or writing artifacts.

    Both current mechanisms start at zero and advance one round per resolution.
    A terminal state's round has no policy/mechanism stream consumer. Stream
    identities describe allocation, not actual draws or scientific comparability.
    """
    if replicate < 0 or round_index < 0:
        raise ValueError("replicate and round must be >= 0")
    spec, resolved = load_study(study_dir)
    current_hash = study_hash(spec, resolved)
    locked = _audit_frozen_hash(study_dir)
    if locked is not None and locked != current_hash:
        raise ValueError(
            f"study content changed after freeze: lock={locked[:12]} "
            f"current={current_hash[:12]} — audit the unchanged study or a new draft"
        )
    if replicate >= spec.replicates:
        raise ValueError(
            f"replicate {replicate} is outside the study range 0..{spec.replicates - 1}"
        )
    if not spec.conditions:
        raise ValueError("study has no conditions to audit")

    conditions: dict[str, Any] = {}
    for condition in sorted(spec.conditions, key=lambda item: item.condition_id):
        scenario = resolved[condition.condition_id]
        world = scenario.spec.world
        rounds = world.rounds if isinstance(world, NIPDWorld) else world.params.rounds
        if rounds <= 0:
            raise ValueError(f"condition {condition.condition_id!r} has no scheduled rounds")
        if round_index >= rounds:
            raise ValueError(
                f"round {round_index} is outside condition {condition.condition_id!r}'s "
                f"scheduled range 0..{rounds - 1}"
            )
        mechanism_root, paired_policy_root = study_seed_roots(
            spec.seed, condition.condition_id, replicate,
            protocol=spec.seed_protocol, scenario_block=condition.scenario_block,
        )
        policy_root = paired_policy_root or mechanism_root
        policies = build_policies(scenario)
        conditions[condition.condition_id] = {
            "scenario_id": scenario.spec.scenario_id,
            "scenario_hash": scenario.scenario_hash,
            "scenario_block": condition.scenario_block,
            "round_count": rounds,
            "mechanism_stream": _stream((*mechanism_root, "mechanism", "round", round_index)),
            "agents": {
                agent: {
                    "policy_id": policy.policy_id,
                    "kernel_stream": _stream((*policy_root, "agent", agent, "round", round_index)),
                    "kernel_rng_usage": (
                        "unused_by_current_llm_adapter" if isinstance(policy, LLMPolicy)
                        else "supplied_to_policy"
                    ),
                }
                for agent, policy in sorted(policies.items())
            },
        }
    return {
        "schema_version": 1,
        "scope": "kernel_seed_allocation",
        "study_id": spec.study_id,
        "study_hash": current_hash,
        "seed_protocol": spec.seed_protocol,
        "frozen": locked is not None,
        "replicate": replicate,
        "round": round_index,
        "conditions": conditions,
        "notes": [
            "Equal kernel streams do not establish scientific comparability or guarantee "
            "equal observations, actions, outcomes, draw consumption, or reduced variance.",
            "LLMPolicy currently ignores its supplied kernel RNG; "
            "provider randomness is not paired.",
        ],
    }
