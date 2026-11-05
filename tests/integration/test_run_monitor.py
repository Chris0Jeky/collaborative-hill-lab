"""Operational snapshots distinguish unfinished artifacts from verified sealed runs."""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from collaborative_hill.cli import app
from collaborative_hill.experiments.study import run_study

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def completed_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("monitor-complete")
    run_study(REPO / "studies/000-legacy-reproduction", root,
              only_condition="pw-2tft-alld", replicates_override=1)
    return next(root.rglob("events.jsonl")).parent


def _copy_run(source, target):
    shutil.copytree(source, target)
    return target


def _running(run):
    path = run / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(status="running", ended_at=None, event_count=None, final_event_hash=None)
    path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    return manifest


def _snapshot(root):
    from collaborative_hill.reporting.monitor import monitor_runs

    return monitor_runs(root)


def test_monitor_cli_returns_a_machine_readable_verified_snapshot(completed_run):
    result = CliRunner().invoke(app, ["monitor", str(completed_run), "--json"])
    assert result.exit_code == 0, result.output
    snapshot = json.loads(result.stdout)
    assert snapshot["schema_version"] == "chl-monitor@1"
    assert snapshot["counts"] == {"completed": 1, "failed": 0, "unsealed": 0, "broken": 0}
    row, = snapshot["runs"]
    assert row["path"] == "."
    assert row["status"] == "completed"
    assert row["integrity"] == "sealed_validated"
    assert row["last_event_type"] == "RunCompleted"
    assert row["logical_time"] == 50
    assert row["last_seq"] == row["event_count"] - 1
    assert row["process_alive"] is None


def test_unsealed_prefix_is_not_claimed_alive_or_completed(completed_run, tmp_path):
    run = _copy_run(completed_run, tmp_path / "prefix")
    _running(run)
    ledger = run / "events.jsonl"
    lines = ledger.read_bytes().splitlines(keepends=True)
    ledger.write_bytes(b"".join(lines[:8]))
    row, = _snapshot(run)["runs"]
    assert row["status"] == "unsealed"
    assert row["manifest_status"] == "running"
    assert row["event_count"] == 8
    assert row["integrity"] == "prefix_hashes_only"
    assert row["process_alive"] is None
    assert "liveness" in row["detail"]


def test_partial_last_write_does_not_hide_verified_prefix(completed_run, tmp_path):
    run = _copy_run(completed_run, tmp_path / "partial")
    _running(run)
    ledger = run / "events.jsonl"
    lines = ledger.read_bytes().splitlines(keepends=True)
    partial = lines[8][:17]
    ledger.write_bytes(b"".join(lines[:8]) + partial)
    row, = _snapshot(run)["runs"]
    assert row["status"] == "unsealed"
    assert row["event_count"] == 8
    assert row["partial_record_bytes"] == len(partial)
    assert row["last_seq"] == 7


@pytest.mark.parametrize("suffix", [b"not-json\n", b"\n", b"{}\n"])
def test_corrupt_complete_record_is_broken_even_with_running_manifest(
    completed_run, tmp_path, suffix,
):
    run = _copy_run(completed_run, tmp_path / "corrupt")
    _running(run)
    ledger = run / "events.jsonl"
    lines = ledger.read_bytes().splitlines(keepends=True)
    ledger.write_bytes(b"".join(lines[:8]) + suffix)
    row, = _snapshot(run)["runs"]
    assert row["status"] == "broken"
    assert row["integrity"] == "broken"


def test_sealed_manifest_with_truncated_ledger_remains_broken(completed_run, tmp_path):
    run = _copy_run(completed_run, tmp_path / "truncated")
    ledger = run / "events.jsonl"
    ledger.write_bytes(b"".join(ledger.read_bytes().splitlines(keepends=True)[:-1]))
    assert _snapshot(run)["runs"][0]["status"] == "broken"
    assert CliRunner().invoke(app, ["monitor", str(run)]).exit_code == 1


def test_hash_tampering_and_scenario_drift_never_get_verified_label(completed_run, tmp_path):
    root = tmp_path / "runs"
    first = _copy_run(completed_run, root / "a")
    second = _copy_run(completed_run, root / "b")
    ledger = first / "events.jsonl"
    ledger.write_bytes(ledger.read_bytes().replace(b'"C"', b'"D"', 1))
    resolved = second / "scenario.resolved.json"
    data = json.loads(resolved.read_text(encoding="utf-8"))
    data["scenario_hash"] = "0" * 64
    resolved.write_text(json.dumps(data), encoding="utf-8", newline="\n")
    snapshot = _snapshot(root)
    assert snapshot["counts"]["broken"] == 2
    assert [row["path"] for row in snapshot["runs"]] == ["a", "b"]


def test_terminal_before_final_manifest_is_unsealed(completed_run, tmp_path):
    run = _copy_run(completed_run, tmp_path / "finalizing")
    _running(run)
    row, = _snapshot(run)["runs"]
    assert row["status"] == "unsealed"
    assert row["last_event_type"] == "RunCompleted"
    assert "final" in row["detail"]


def test_discovery_includes_manifest_only_and_empty_reserved_ledgers(completed_run, tmp_path):
    root = tmp_path / "inventory"
    root.mkdir()
    reserved = root / "reserved"
    reserved.mkdir()
    (reserved / "events.jsonl").write_bytes(b"")
    manifest_only = root / "manifest-only"
    manifest_only.mkdir()
    shutil.copyfile(completed_run / "manifest.json", manifest_only / "manifest.json")
    _running(manifest_only)
    snapshot = _snapshot(root)
    assert snapshot["counts"]["unsealed"] == 2
    assert {row["path"] for row in snapshot["runs"]} == {"reserved", "manifest-only"}


def test_sealed_manifest_missing_ledger_is_not_silently_omitted(completed_run, tmp_path):
    run = _copy_run(completed_run, tmp_path / "missing")
    (run / "events.jsonl").unlink()
    assert _snapshot(tmp_path)["counts"]["broken"] == 1


def test_monitor_preserves_every_source_byte_and_is_deterministic(completed_run):
    before = {p.relative_to(completed_run): p.read_bytes()
              for p in completed_run.rglob("*") if p.is_file()}
    first = _snapshot(completed_run)
    assert _snapshot(completed_run) == first
    after = {p.relative_to(completed_run): p.read_bytes()
             for p in completed_run.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("manifest", [[], {"status": "invented"}])
def test_malformed_manifest_is_visible_as_broken(completed_run, tmp_path, manifest):
    run = _copy_run(completed_run, tmp_path / "bad-manifest")
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    assert _snapshot(run)["counts"]["broken"] == 1


def test_missing_and_empty_roots_have_explicit_cli_errors(tmp_path):
    runner = CliRunner()
    for target in (tmp_path, tmp_path / "missing"):
        result = runner.invoke(app, ["monitor", str(target), "--json"])
        assert result.exit_code == 2
        assert "error:" in result.output


def test_recorded_failure_is_valid_but_has_a_nonzero_operational_exit(tmp_path):
    study = tmp_path / "study"
    shutil.copytree(REPO / "studies/000-legacy-reproduction", study)
    path = study / "scenarios/pw-2tft-alld.json"
    scenario = json.loads(path.read_text(encoding="utf-8"))
    scenario["cognition"]["agents"][0]["policy"] = {
        "name": "llm_fake", "params": {"script": "[]", "fail_at": 0},
    }
    path.write_text(json.dumps(scenario), encoding="utf-8", newline="\n")
    result, = run_study(study, tmp_path / "runs", only_condition="pw-2tft-alld",
                        replicates_override=1)
    assert result.status == "failed"
    snapshot = _snapshot(tmp_path / "runs")
    row, = snapshot["runs"]
    assert row["status"] == "failed"
    assert row["integrity"] == "sealed_validated"
    assert "simulated provider outage" in row["failure_reason"]
    cli = CliRunner().invoke(app, ["monitor", str(tmp_path / "runs"), "--json"])
    assert cli.exit_code == 1
    assert json.loads(cli.stdout)["counts"]["failed"] == 1


def test_change_during_validation_cannot_earn_a_stable_sealed_label(
    completed_run, tmp_path, monkeypatch,
):
    from collaborative_hill.reporting import monitor

    run = _copy_run(completed_run, tmp_path / "concurrent")
    original = monitor.load_run

    def read_then_update(path):
        loaded = original(path)
        _running(path)
        return loaded

    monkeypatch.setattr(monitor, "load_run", read_then_update)
    row, = _snapshot(run)["runs"]
    assert row["status"] == "unsealed"
    assert row["integrity"] == "not_checked"
    assert "changed during" in row["detail"]


def test_monitor_never_resolves_or_calls_policies(completed_run, monkeypatch):
    from collaborative_hill.experiments import study

    def forbidden(*args, **kwargs):
        pytest.fail("operational inventory must not construct or call a policy")

    monkeypatch.setattr(study, "build_policies", forbidden)
    assert _snapshot(completed_run)["counts"]["completed"] == 1


def test_records_after_terminal_are_broken_even_with_unfinished_manifest(completed_run, tmp_path):
    run = _copy_run(completed_run, tmp_path / "extra")
    _running(run)
    ledger = run / "events.jsonl"
    ledger.write_bytes(ledger.read_bytes() + b'{"incomplete":')
    assert _snapshot(run)["runs"][0]["status"] == "broken"
