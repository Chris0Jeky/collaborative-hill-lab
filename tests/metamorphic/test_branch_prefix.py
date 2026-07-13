"""Metamorphic: a branch is a byte-exact prefix of its parent plus a paired fork.

Run a checkpointed NIPD study, then fork at an intermediate checkpoint:

(a) the child's events.jsonl shares a byte-identical copy-on-write prefix
    (lines 0..fork_seq) with the parent;
(b) the child's first NEW event links to the checkpoint's last event hash;
(c) the branch manifest records the fork faithfully;
(d) a real policy override (swap one agent to alld) makes the child diverge —
    a different sealed summary;
(e) paired seeds: when the override targets a *different* agent AND is
    behaviourally identical to the original, the unchanged agents draw the same
    randomness and re-propose exactly what they did in the parent. Because the
    child carries a fresh run_id, event hashes differ, so we assert equality of
    the ActionProposed *proposal content*, not of the hashes.
"""

import json

import pytest

from collaborative_hill.agents.scripted.nipd_policies import AllCPolicy, AllDPolicy
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.store import (
    FileCheckpointStore,
    FileEventStore,
    RunPaths,
)
from collaborative_hill.experiments.study import run_study

from ._helpers import find_run_dirs, nipd_spec, plain_skin, write_study

pytestmark = pytest.mark.metamorphic

# a1/a2 are random (their moves depend only on their own kernel rng stream, not
# on history), so paired-seed equivalence is a concrete, non-vacuous property.
# a3 is allc, so swapping it to alld deterministically changes the run.
PARENT_AGENTS = (("a1", "random"), ("a2", "random"), ("a3", "allc"))


def _proposals(events, agents, min_round):
    out = {}
    for e in events:
        if (
            e.event_type == EventType.ACTION_PROPOSED
            and e.payload["agent_id"] in agents
            and e.logical_time >= min_round
        ):
            out[(e.payload["agent_id"], e.logical_time)] = e.payload["proposal"]
    return out


@pytest.fixture
def parent_run(tmp_path):
    study_dir = tmp_path / "study"
    artifacts = tmp_path / "artifacts"
    spec = nipd_spec(PARENT_AGENTS, scenario_id="nipd", mode="pairwise", rounds=5)
    write_study(
        study_dir,
        study_id="branch-study",
        seed=99,
        checkpoint_every=2,  # checkpoints at rounds 2 and 4
        conditions=[("nipd", spec, plain_skin())],
    )
    results = run_study(study_dir, artifacts)
    assert len(results) == 1 and results[0].status == "completed"

    (parent_dir,) = find_run_dirs(artifacts)
    parent_paths = RunPaths(parent_dir)
    fork_seq = FileCheckpointStore(parent_paths.checkpoints).list_seqs()[0]

    parent_events = FileEventStore(parent_paths.events).load_all(verify=True)
    return parent_dir, fork_seq, parent_events, results[0]


def test_branch_prefix_and_divergence(tmp_path, parent_run):
    parent_dir, fork_seq, parent_events, parent_result = parent_run

    child_dir = tmp_path / "child_diverge"
    result, manifest = branch_run(
        parent_dir=parent_dir,
        fork_seq=fork_seq,
        child_dir=child_dir,
        child_run_id="nipd-branch-alld",
        policy_overrides={"a3": AllDPolicy("pairwise")},
    )

    # (a) byte-identical copy-on-write prefix: lines 0..fork_seq.
    parent_lines = (parent_dir / "events.jsonl").read_bytes().split(b"\n")
    child_lines = (child_dir / "events.jsonl").read_bytes().split(b"\n")
    assert child_lines[: fork_seq + 1] == parent_lines[: fork_seq + 1]

    # (b) first NEW event links to the checkpoint's last event hash.
    child_events = FileEventStore(RunPaths(child_dir).events).load_all(verify=True)
    first_new = child_events[fork_seq + 1]
    assert first_new.seq == fork_seq + 1
    assert first_new.parent_hash == manifest.parent_event_hash_at_fork
    assert first_new.parent_hash == parent_events[fork_seq].event_hash
    # the shared prefix really is the same event object content
    assert child_events[fork_seq].event_hash == parent_events[fork_seq].event_hash

    # (c) branch manifest is faithful (returned object and the on-disk copy).
    assert manifest.parent_run_id == "nipd-r000"
    assert manifest.child_run_id == "nipd-branch-alld"
    assert manifest.fork_seq == fork_seq
    assert manifest.changed_policies == {"a3": "alld[pairwise]@1"}
    assert set(manifest.unchanged_policies) == {"a1", "a2"}
    assert manifest.unchanged_policies["a1"] == "random[pairwise]@1"

    on_disk = json.loads((child_dir / "branch.json").read_text(encoding="utf-8"))
    assert on_disk["fork_seq"] == fork_seq
    assert on_disk["parent_event_hash_at_fork"] == manifest.parent_event_hash_at_fork
    assert on_disk["fork_round"] == manifest.fork_round
    assert on_disk["changed_policies"] == {"a3": "alld[pairwise]@1"}

    # (d) the override genuinely diverges the run.
    assert result.status == "completed"
    assert result.summary != parent_result.summary
    assert result.summary["scores"]["a3"] != parent_result.summary["scores"]["a3"]


def test_branch_paired_seed_reproduces_unchanged_agents(tmp_path, parent_run):
    parent_dir, fork_seq, parent_events, _ = parent_run

    # Second branch: override a3 with a policy behaviourally IDENTICAL to its
    # original (allc). Unchanged agents a1/a2 must draw identical randomness.
    child_dir = tmp_path / "child_paired"
    _, manifest = branch_run(
        parent_dir=parent_dir,
        fork_seq=fork_seq,
        child_dir=child_dir,
        child_run_id="nipd-branch-paired",
        policy_overrides={"a3": AllCPolicy("pairwise")},
    )
    child_events = FileEventStore(RunPaths(child_dir).events).load_all(verify=True)

    fork_round = manifest.fork_round
    parent_props = _proposals(parent_events, {"a1", "a2"}, fork_round)
    child_props = _proposals(child_events, {"a1", "a2"}, fork_round)

    # There is a genuine post-fork suffix to compare.
    assert parent_props
    assert set(parent_props) == set(child_props)
    # Proposal CONTENT matches exactly (hashes would differ: fresh run_id).
    assert parent_props == child_props

    # And the whole suffix is behaviourally identical here (a3's override is a
    # no-op change), including the overridden agent itself.
    parent_a3 = _proposals(parent_events, {"a3"}, fork_round)
    child_a3 = _proposals(child_events, {"a3"}, fork_round)
    assert parent_a3 == child_a3
