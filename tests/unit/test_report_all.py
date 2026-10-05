"""report_all must not abort when one run ledger is corrupt."""

import importlib.util
import shutil
from pathlib import Path

from collaborative_hill.experiments.study import run_study
from collaborative_hill.reporting import run_report

REPORT_ALL_PATH = Path(__file__).resolve().parents[2] / "scripts" / "report_all.py"


def _load_report_all_module():
    spec = importlib.util.spec_from_file_location("report_all_under_test", str(REPORT_ALL_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_run(repo: Path, study: str, cond: str, run: str) -> Path:
    run_dir = repo / "artifacts" / study / cond / run
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")
    return run_dir


def test_corrupt_first_run_does_not_skip_later_study(tmp_path, monkeypatch, capsys):
    mod = _load_report_all_module()
    _make_run(tmp_path, "study-000", "cond", "run-a")
    _make_run(tmp_path, "study-001", "cond", "run-b")

    calls: list[str] = []

    def fake_run_report(run_dir):
        calls.append(Path(run_dir).name)
        if Path(run_dir).name == "run-a":
            raise ValueError("corrupt ledger")

    studied: list[str] = []

    def fake_study_report(study_dir):
        studied.append(Path(study_dir).name)
        return Path(study_dir) / "study.md"

    monkeypatch.setattr(mod, "run_report", fake_run_report)
    monkeypatch.setattr(mod, "study_report", fake_study_report)
    monkeypatch.setattr(mod, "REPO", tmp_path)

    rc = mod.main()
    captured = capsys.readouterr()
    out = captured.out + captured.err

    assert sorted(calls) == ["run-a", "run-b"]
    assert studied == ["study-001"]
    assert rc != 0
    assert "run-a" in out


def test_all_ok_returns_zero(tmp_path, monkeypatch, capsys):
    mod = _load_report_all_module()
    _make_run(tmp_path, "study-000", "cond", "run-a")
    _make_run(tmp_path, "study-001", "cond", "run-b")

    calls: list[str] = []

    def fake_run_report(run_dir):
        calls.append(Path(run_dir).name)

    studied: list[str] = []

    def fake_study_report(study_dir):
        studied.append(Path(study_dir).name)
        return Path(study_dir) / "study.md"

    monkeypatch.setattr(mod, "run_report", fake_run_report)
    monkeypatch.setattr(mod, "study_report", fake_study_report)
    monkeypatch.setattr(mod, "REPO", tmp_path)

    rc = mod.main()
    capsys.readouterr()

    assert sorted(calls) == ["run-a", "run-b"]
    assert sorted(studied) == ["study-000", "study-001"]
    assert rc == 0


def test_corrupt_ledger_with_cached_metrics_skips_aggregate(tmp_path, monkeypatch, capsys):
    mod = _load_report_all_module()
    study = REPORT_ALL_PATH.parents[1] / "studies" / "001-evidence-commons"
    results = run_study(
        study, tmp_path / "seed", only_condition="agg-priv", replicates_override=1
    )
    assert results[0].status == "completed"
    (source_run,) = (tmp_path / "seed").glob("*/*/*/events.jsonl")
    run_report(source_run.parent)
    bad_study = tmp_path / "artifacts" / "a-corrupt"
    good_study = tmp_path / "artifacts" / "b-intact"
    for target in (bad_study, good_study):
        shutil.copytree(source_run.parent.parent.parent, target)
    (bad_ledger,) = bad_study.glob("*/*/events.jsonl")
    bad_ledger.write_text("not-json\n", encoding="utf-8")
    monkeypatch.setattr(mod, "REPO", tmp_path)

    assert mod.main() == 1
    captured = capsys.readouterr()
    assert str(bad_ledger.parent) in captured.err
    assert not (bad_study / "report.md").exists()
    assert (good_study / "report.md").exists()
    assert f"wrote {good_study / 'report.md'}" in captured.out
    assert f"wrote {bad_study / 'report.md'}" not in captured.out
