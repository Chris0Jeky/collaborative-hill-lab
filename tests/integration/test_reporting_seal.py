"""Reporting requires a terminal seal, even when the surviving chain is valid."""

import json
import shutil
from pathlib import Path

import pytest

from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import ChainError, EventType, make_event
from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore
from collaborative_hill.experiments import study
from collaborative_hill.reporting import report, run_report, study_report, write_run_metrics

from ._helpers import STUDY_000, STUDY_001, find_run_dirs

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def sealed_run(tmp_path_factory):
    artifacts = tmp_path_factory.mktemp("sealed")
    study.run_study(STUDY_001, artifacts, only_condition="agg-priv", replicates_override=1)
    (run_dir,) = find_run_dirs(artifacts)
    write_run_metrics(run_dir)  # Cached metrics must not bypass seal validation.
    return run_dir


@pytest.mark.parametrize("reporter", [write_run_metrics, run_report, study_report])
@pytest.mark.parametrize("damage", [
    "truncated", "empty", "status", "running", "run_id", "study_id",
    "extra_terminal", "after_terminal", "event_count", "final_event_hash",
])
def test_reporting_refuses_unsealed_or_mismatched_run(tmp_path, sealed_run, reporter, damage):
    run_dir = tmp_path / "study" / "condition" / "run"
    shutil.copytree(sealed_run, run_dir)
    ledger = run_dir / "events.jsonl"
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if damage not in {"event_count", "final_event_hash"}:
        manifest.pop("event_count", None)
        manifest.pop("final_event_hash", None)
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    if damage == "truncated":
        ledger.write_text("".join(lines[:-1]), encoding="utf-8")
    elif damage == "empty":
        ledger.write_text("", encoding="utf-8")
    elif damage in {"extra_terminal", "after_terminal"}:
        store = FileEventStore(ledger)
        store.append(make_event(
            study_id=manifest["study_id"], run_id=manifest["run_id"],
            seq=store.count, logical_time=12, actor="engine",
            event_type=(EventType.RUN_COMPLETED if damage == "extra_terminal"
                        else EventType.CHECKPOINT_CREATED),
            payload={}, parent_hash=store.last_hash,
        ))
    else:
        field = "status" if damage == "running" else damage
        manifest[field] = {"status": "failed", "running": "running", "event_count": 1}.get(
            damage, "mismatch"
        )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    FileEventStore(ledger).load_all(verify=True)  # All damage is hash-valid.
    metrics_path = run_dir / "metrics" / "metrics.json"
    before = metrics_path.read_bytes()

    with pytest.raises(ChainError):
        reporter(run_dir.parent.parent if reporter is study_report else run_dir)

    assert metrics_path.read_bytes() == before
    assert not (run_dir / "report.md").exists()
    assert not (run_dir.parent.parent / "report.md").exists()


def test_new_manifests_pin_seal_and_legacy_sealed_runs_remain_readable(tmp_path, sealed_run):
    run_dir = tmp_path / "run"
    shutil.copytree(sealed_run, run_dir)
    path = run_dir / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    events = FileEventStore(run_dir / "events.jsonl").load_all()
    assert manifest["event_count"] == len(events)
    assert manifest["final_event_hash"] == events[-1].event_hash
    del manifest["event_count"], manifest["final_event_hash"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert "status: **completed**" in run_report(run_dir).read_text(encoding="utf-8")


def test_branch_manifest_pins_child_seal(tmp_path, sealed_run):
    child = tmp_path / "child"
    fork = FileCheckpointStore(sealed_run / "checkpoints").list_seqs()[0]
    result, _ = branch_run(
        parent_dir=sealed_run, fork_seq=fork, child_dir=child,
        child_run_id="sealed-child", policy_overrides={},
    )
    manifest = json.loads((child / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["event_count"] == result.event_count
    assert manifest["final_event_hash"] == result.final_event_hash
    assert "status: **completed**" in run_report(child).read_text(encoding="utf-8")


def test_failed_run_is_reported_as_failed_without_completed_outcomes(tmp_path, monkeypatch):
    build_policies = study.build_policies

    def failing_policies(resolved):
        policies = build_policies(resolved)
        propose = policies["a1"].propose
        calls = 0

        def fail(*args):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise RuntimeError("synthetic outage")
            return propose(*args)

        policies["a1"].propose = fail
        return policies

    monkeypatch.setattr(study, "build_policies", failing_policies)
    results = study.run_study(
        STUDY_000, tmp_path, only_condition="nb-2ptft-alld-incself", replicates_override=1
    )
    assert results[0].status == "failed"
    (run_dir,) = find_run_dirs(tmp_path)
    assert "status: **failed**" in run_report(run_dir).read_text(encoding="utf-8")
    aggregate = study_report(run_dir.parent.parent).read_text(encoding="utf-8")
    assert "failed" in aggregate
    assert "correct" not in aggregate
    assert "mean_coop" not in aggregate


@pytest.mark.parametrize("cached", [True, False])
@pytest.mark.parametrize("later_invalid", [True, False])
def test_study_report_reads_archived_runs_without_writes(
    tmp_path, sealed_run, monkeypatch, cached, later_invalid,
):
    root = tmp_path / "study"
    run_dir = root / "condition" / "a-valid"
    shutil.copytree(sealed_run, run_dir)
    if cached:
        metrics_path = run_dir / "metrics" / "metrics.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["epistemics"]["accepted_correct"] = 9876
        metrics_path.write_text(json.dumps(metrics), encoding="utf-8")
        (run_dir / "metrics" / "events.parquet").write_bytes(b"archived parquet")
    else:
        shutil.rmtree(run_dir / "metrics")
    if later_invalid:
        invalid = root / "condition" / "z-invalid"
        shutil.copytree(sealed_run, invalid)
        ledger = invalid / "events.jsonl"
        ledger.write_text("", encoding="utf-8")
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
              for p in root.rglob("*") if p.is_file()}
    original_open = Path.open

    def readonly_run(path, mode="r", *args, **kwargs):
        if path.is_relative_to(root / "condition") and any(c in mode for c in "wax+"):
            raise PermissionError("archived run is read-only")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", readonly_run)
    monkeypatch.setitem(report.METRIC_VERSIONS, "epistemics", "future")
    if later_invalid:
        with pytest.raises(ChainError):
            study_report(root)
        assert not (root / "report.md").exists()
    else:
        aggregate = study_report(root).read_text(encoding="utf-8")
        assert "completed" in aggregate
        if cached:
            assert "9876" in aggregate
    after = {p: (p.read_bytes(), p.stat().st_mtime_ns)
             for p in (root / "condition").rglob("*") if p.is_file()}
    assert after == before
