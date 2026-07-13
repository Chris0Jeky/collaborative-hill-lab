"""Integration: the ``chl`` CLI end to end, driven as a subprocess.

Exercises the operator-facing surface exactly as a user would — doctor, study
validate, run, replay, report, branch — asserting exit codes, that emitted JSON
parses, and that the on-disk artifacts (reports, the byte-identical branch
prefix, and branch provenance) are correct.
"""

import json

import pytest

from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore, RunPaths

from ._helpers import STUDY_000, STUDY_001, find_run_dirs, run_cli

pytestmark = pytest.mark.integration

BRANCH_CONDITION = "nb-2ptft-alld-incself"


def test_doctor_exits_zero():
    proc = run_cli("doctor")
    assert proc.returncode == 0, proc.stderr
    assert "OK  python" in proc.stdout


@pytest.mark.parametrize("study", [STUDY_000, STUDY_001], ids=["000", "001"])
def test_study_validate_emits_parseable_json(study):
    proc = run_cli("study", "validate", str(study))
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["study_id"]
    assert report["conditions"]
    assert report["study_hash"]


def test_run_replay_report_cycle(tmp_path):
    artifacts = tmp_path / "art"
    run = run_cli(
        "run", str(STUDY_001), "--replicates", "1",
        "--condition", "attr-ledger", "--artifacts", str(artifacts),
    )
    assert run.returncode == 0, run.stderr
    assert "completed" in run.stdout

    (run_dir,) = find_run_dirs(artifacts)

    replay = run_cli("replay", str(run_dir))
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["chains_match"] is True

    report = run_cli("report", str(run_dir))
    assert report.returncode == 0, report.stderr
    assert (run_dir / "report.md").exists()


def test_branch_prefix_and_provenance(tmp_path):
    artifacts = tmp_path / "art"
    run = run_cli(
        "run", str(STUDY_000), "--replicates", "1",
        "--condition", BRANCH_CONDITION, "--artifacts", str(artifacts),
    )
    assert run.returncode == 0, run.stderr

    (parent_dir,) = find_run_dirs(artifacts)

    # checkpoint_every=10 in study.json -> intermediate checkpoints exist.
    seqs = FileCheckpointStore(RunPaths(parent_dir).checkpoints).list_seqs()
    assert seqs, "no checkpoints written despite checkpoint_every=10"
    # earliest checkpoint (round 10): a real re-executing fork, not the terminal seal.
    fork_seq = seqs[0]

    child_dir = tmp_path / "child"
    branch = run_cli(
        "branch", str(parent_dir), "--at-event", str(fork_seq),
        "--override", "a3=allc", "--out", str(child_dir),
    )
    assert branch.returncode == 0, branch.stderr

    # (a) byte-identical copy-on-write prefix: lines 0..fork_seq.
    parent_lines = (parent_dir / "events.jsonl").read_bytes().split(b"\n")
    child_lines = (child_dir / "events.jsonl").read_bytes().split(b"\n")
    assert child_lines[: fork_seq + 1] == parent_lines[: fork_seq + 1]

    # (b) branch.json binds the child to its parent faithfully.
    manifest = json.loads((child_dir / "branch.json").read_text(encoding="utf-8"))
    assert manifest["parent_run_id"] == f"{BRANCH_CONDITION}-r000"
    assert manifest["fork_seq"] == fork_seq
    assert manifest["changed_policies"] == {"a3": "allc[neighbourhood]@1"}
    assert set(manifest["unchanged_policies"]) == {"a1", "a2"}

    # The recorded fork hash is exactly the parent's event hash at that seq.
    parent_events = FileEventStore(RunPaths(parent_dir).events).load_all(verify=True)
    assert manifest["parent_event_hash_at_fork"] == parent_events[fork_seq].event_hash
