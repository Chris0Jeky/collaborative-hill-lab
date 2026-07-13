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

from collaborative_hill.agents.replay import policy_ids_from_events
from collaborative_hill.engine.runner import RunConfig, RunResult, run_episode
from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore, RunPaths
from collaborative_hill.experiments.scenario import ResolvedScenario


class BranchManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    parent_run_id: str
    parent_run_dir: str
    child_run_id: str
    fork_seq: int
    fork_round: int
    parent_event_hash_at_fork: str
    changed_policies: dict[str, str]  # agent_id -> new policy_id
    unchanged_policies: dict[str, str]


def branch_run(
    *,
    parent_dir: Path,
    fork_seq: int,
    child_dir: Path,
    child_run_id: str,
    policy_overrides: dict[str, Any],
) -> tuple[RunResult, BranchManifest]:
    """Fork the run in ``parent_dir`` at checkpoint ``fork_seq``.

    ``policy_overrides`` maps agent_id -> policy object (with .policy_id and
    .propose). Agents not overridden keep their original scripted policies,
    rebuilt from the resolved scenario.
    """
    parent_dir = Path(parent_dir)
    parent_paths = RunPaths(parent_dir)
    ckpts = FileCheckpointStore(parent_paths.checkpoints)
    if fork_seq not in ckpts.list_seqs():
        raise ValueError(
            f"fork_seq {fork_seq} is not a checkpoint; available: {ckpts.list_seqs()}"
        )
    record = ckpts.load(fork_seq)
    state = record["state"]

    parent_events = FileEventStore(parent_paths.events).load_all(verify=True)
    manifest = json.loads(parent_paths.manifest.read_text(encoding="utf-8"))
    resolved = ResolvedScenario.model_validate_json(
        (parent_dir / "scenario.resolved.json").read_text(encoding="utf-8")
    )

    # copy-on-write prefix: byte-identical lines 0..fork_seq
    child_dir = Path(child_dir)
    child_paths = RunPaths(child_dir).create()
    with parent_paths.events.open(encoding="utf-8") as src:
        lines = src.readlines()[: fork_seq + 1]
    with child_paths.events.open("w", encoding="utf-8", newline="") as dst:
        dst.writelines(lines)

    # rebuild policies: originals from the scenario, overrides on top
    from collaborative_hill.experiments.study import build_policies  # cycle-free at runtime

    mechanism = resolved.build_mechanism()
    policies = build_policies(resolved)
    original_ids = policy_ids_from_events(parent_events)
    changed: dict[str, str] = {}
    for agent, policy in policy_overrides.items():
        if agent not in policies:
            raise ValueError(f"override for unknown agent {agent}")
        policies[agent] = policy
        changed[agent] = policy.policy_id

    config = RunConfig(
        study_id=manifest["study_id"],
        run_id=child_run_id,
        seed_root=tuple(manifest["seed_root"]),
        checkpoint_every=manifest["checkpoint_every"],
        invalid_action_policy=manifest["invalid_action_policy"],
    )
    result = run_episode(
        mechanism=mechanism, policies=policies, config=config, paths=child_paths,
        start_state=state,
    )

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
        branch_manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    (child_dir / "scenario.resolved.json").write_text(
        resolved.model_dump_json(indent=2), encoding="utf-8"
    )
    child_manifest = dict(manifest)
    child_manifest.update({
        "run_id": child_run_id,
        "parent_run": manifest["run_id"],
        "parent_event_hash_at_fork": record["last_event_hash"],
        "fork_seq": fork_seq,
        "status": result.status,
    })
    child_paths.manifest.write_text(
        json.dumps(child_manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return result, branch_manifest
