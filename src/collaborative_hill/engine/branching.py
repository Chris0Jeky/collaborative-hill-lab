"""Counterfactual branching: fork a sealed run at a checkpoint.

A branch shares the parent's history up to the fork: the child's events.jsonl
starts as a BYTE-IDENTICAL copy of the parent's lines 0..fork_seq (copy-on-
write; shared events keep the parent's run_id — that is honest provenance,
and the hash chain does not require run_id constancy). New events link from
the parent event hash at the fork, so the child is cryptographically bound to
its parent (ADR-0002).

Fork points are checkpoint boundaries (``ckpt-<seq>.json``), so the child
resumes from sealed state without re-execution. The only supported override
in v0 is per-agent policy replacement — small and correct over general and
magical; config overrides need a new run, not a branch.

Seed paths are unchanged: unaffected policies draw identical randomness after
the fork, giving paired counterfactuals by construction (ADR-0005).
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from collaborative_hill.engine.events import ChainError
from collaborative_hill.engine.replay import load_run
from collaborative_hill.engine.runner import RunConfig, RunResult, run_episode
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths
from collaborative_hill.engine.validation import effective_policy_ids, validate_checkpoint


class BranchManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 2
    parent_run_id: str
    parent_run_dir: str
    child_run_id: str
    fork_seq: int
    fork_round: int
    parent_event_hash_at_fork: str
    changed_policies: dict[str, str]  # agent_id -> new policy_id
    unchanged_policies: dict[str, str]


def _continuation_provenance(parent_dir: Path) -> dict[str, Any]:
    from collaborative_hill.experiments.manifests import (
        environment_provenance,
        git_provenance,
        lock_hash,
        utc_now_iso,
    )
    from collaborative_hill.experiments.study import _find_repo_root

    repo_root = _find_repo_root(parent_dir)
    commit, dirty = git_provenance(repo_root)
    return {"code_commit": commit, "worktree_dirty": dirty,
            "dependency_lock_sha256": lock_hash(repo_root),
            **environment_provenance(), "started_at": utc_now_iso()}


def _begin_budgeted_continuation(policies: dict[str, Any], budget: Any) -> None:
    """Require one shared budget object, then mark the fork without resetting it."""
    from collaborative_hill.agents.llm import LLMPolicy

    if budget is None:
        return
    for policy in policies.values():
        if (isinstance(policy, LLMPolicy) and hasattr(policy.provider, "budget")
                and policy.provider.budget is not budget):
            raise ValueError("a network-backed policy must share the continuation's "
                             "request_budget object")
    budget.begin("continuation")


def branch_run(
    *,
    parent_dir: Path,
    fork_seq: int,
    child_dir: Path,
    child_run_id: str,
    policy_overrides: dict[str, Any],
    allow_provider_requests: bool = False,
    request_budget: Any = None,
) -> tuple[RunResult, BranchManifest]:
    """Fork the run in ``parent_dir`` at checkpoint ``fork_seq``.

    ``policy_overrides`` maps agent_id -> policy object (with .policy_id and
    .propose). Agents not overridden keep their original scripted policies,
    rebuilt from the resolved scenario. An inherited non-original policy must
    be supplied explicitly; opaque policy IDs are not executable configurations.

    ``request_budget`` (a ``RequestBudget``, operational and unhashed) is NOT reset
    by the fork: its counters continue, so pass the object already used for the
    parent to keep one cumulative limit, or a fresh one for an independent limit.
    A network-backed override must have been constructed with that same object.
    """
    parent_dir = Path(parent_dir)
    child_dir = Path(child_dir)
    parent_paths = RunPaths(parent_dir)
    ckpts = FileCheckpointStore(parent_paths.checkpoints)
    if fork_seq not in ckpts.list_seqs():
        raise ValueError(
            f"fork_seq {fork_seq} is not a checkpoint; available: {ckpts.list_seqs()}"
        )
    parent_events, resolved, manifest = load_run(parent_dir)
    try:
        record = ckpts.load(fork_seq)
    except (KeyError, TypeError) as exc:
        raise ChainError("malformed checkpoint record") from exc
    validate_checkpoint(record, fork_seq, parent_events)
    if parent_events[fork_seq].run_id != manifest["run_id"]:
        raise ValueError("cannot branch an inherited checkpoint with no direct-parent segment")
    state = record["state"]
    if not child_run_id.strip() or child_run_id in {e.run_id for e in parent_events}:
        raise ValueError("child run identity must be non-empty and different from every ancestor")

    from collaborative_hill.agents.llm import LLMPolicy, llm_manifest_fields
    from collaborative_hill.experiments.manifests import utc_now_iso
    from collaborative_hill.experiments.study import (
        _write_llm_transcript,
        build_policies,
    )

    mechanism = resolved.build_mechanism()
    policies = build_policies(
        resolved, allow_provider_requests=allow_provider_requests, overrides=policy_overrides,
        **({"budget": request_budget} if request_budget is not None else {}))
    original_ids = effective_policy_ids(parent_dir, parent_events, manifest)
    for agent, policy in policies.items():
        if agent not in policy_overrides and policy.policy_id != original_ids[agent]:
            raise ValueError(f"inherited policy for {agent} requires an explicit policy override")
    changed: dict[str, str] = {}
    for agent, policy in policy_overrides.items():
        if agent not in policies:
            raise ValueError(f"override for unknown agent {agent}")
        policies[agent] = policy
        changed[agent] = policy.policy_id
    _begin_budgeted_continuation(policies, request_budget)

    usage_offsets = {a: p.call_count for a, p in policies.items() if isinstance(p, LLMPolicy)}
    transcript_offsets = {a: len(p.transcript) for a, p in policies.items()
                          if isinstance(p, LLMPolicy)}
    provenance = _continuation_provenance(parent_dir)

    # copy-on-write prefix: byte-identical lines 0..fork_seq
    child_dir = Path(child_dir)
    with RunPaths(child_dir).reserve() as child_paths:
        with parent_paths.events.open(encoding="utf-8") as src:
            lines = src.readlines()[: fork_seq + 1]
        with child_paths.events.open("w", encoding="utf-8", newline="") as dst:
            dst.writelines(lines)

        config = RunConfig(
            study_id=manifest["study_id"],
            run_id=child_run_id,
            seed_root=tuple(manifest["seed_root"]),
            seed_protocol=manifest["seed_protocol"],
            policy_seed_root=manifest.get("policy_seed_root"),
            scenario_block=manifest.get("scenario_block"),
            checkpoint_every=manifest["checkpoint_every"],
            invalid_action_policy=manifest["invalid_action_policy"],
        )
        result = run_episode(
            mechanism=mechanism, policies=policies, config=config, paths=child_paths,
            start_state=state,
        )
        _write_llm_transcript(policies, child_dir, offsets=transcript_offsets)

        branch_manifest = BranchManifest(
            parent_run_id=manifest["run_id"],
            parent_run_dir=str(parent_dir),
            child_run_id=child_run_id,
            fork_seq=fork_seq,
            fork_round=record["logical_time"],
            parent_event_hash_at_fork=record["last_event_hash"],
            changed_policies=changed,
            unchanged_policies={a: pid for a, pid in original_ids.items() if a not in changed},
        )
        (child_dir / "branch.json").write_text(
            branch_manifest.model_dump_json(indent=2), encoding="utf-8", newline="\n"
        )
        (child_dir / "scenario.resolved.json").write_text(
            resolved.model_dump_json(indent=2), encoding="utf-8", newline="\n"
        )
        # The parent's request_budget record does not describe the child.
        child_manifest = {k: v for k, v in manifest.items() if k != "request_budget"}
        child_manifest.update({
            **llm_manifest_fields(policies, since=usage_offsets, budget=request_budget),
            **provenance,
            "run_id": child_run_id,
            "ended_at": utc_now_iso(),
            "policies": {a: p.policy_id for a, p in sorted(policies.items())},
            "parent_run": manifest["run_id"],
            "parent_event_hash_at_fork": record["last_event_hash"],
            "fork_seq": fork_seq,
            "status": result.status,
            "failure_reason": result.failure_reason,
            # Parent pricing and tokens do not describe the continuation.
            # The helper above includes only this continuation's measured calls.
            "pricing_table_version": None,
            "pricing_table_date": None,
            "event_count": result.event_count,
            "final_event_hash": result.final_event_hash,
        })
        child_paths.manifest.write_text(
            json.dumps(child_manifest, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
        )
    return result, branch_manifest
