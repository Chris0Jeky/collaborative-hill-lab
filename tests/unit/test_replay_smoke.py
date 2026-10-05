"""replay_smoke must replay every run dir (no per-study skipping)."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

SMOKE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "replay_smoke.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("replay_smoke_under_test", str(SMOKE_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_run(repo: Path, study: str, cond: str, run: str) -> Path:
    run_dir = repo / "artifacts" / study / cond / run
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")
    return run_dir


def _report(chains_match: bool) -> SimpleNamespace:
    return SimpleNamespace(
        chains_match=chains_match,
        replayed_events=5,
        first_divergence_seq=None if chains_match else 3,
        detail="" if chains_match else "tampered",
    )


def test_second_tampered_run_under_same_study_fails(tmp_path, monkeypatch, capsys):
    mod = _load_smoke_module()
    _make_run(tmp_path, "studyABC", "cond", "run-a")
    _make_run(tmp_path, "studyABC", "cond", "run-b")

    calls: list[str] = []

    def fake_replay(run_dir):
        calls.append(Path(run_dir).name)
        if Path(run_dir).name == "run-b":
            return _report(False)
        return _report(True)

    monkeypatch.setattr(mod, "replay_run", fake_replay)
    monkeypatch.setattr(mod, "REPO", tmp_path)

    rc = mod.main()
    out = capsys.readouterr().out

    assert sorted(calls) == ["run-a", "run-b"]
    assert "FAIL" in out
    assert rc != 0


def test_all_ok_returns_zero(tmp_path, monkeypatch, capsys):
    mod = _load_smoke_module()
    _make_run(tmp_path, "studyABC", "cond", "run-a")
    _make_run(tmp_path, "studyABC", "cond", "run-b")

    calls: list[str] = []

    def fake_replay(run_dir):
        calls.append(Path(run_dir).name)
        return _report(True)

    monkeypatch.setattr(mod, "replay_run", fake_replay)
    monkeypatch.setattr(mod, "REPO", tmp_path)

    rc = mod.main()
    capsys.readouterr()

    assert sorted(calls) == ["run-a", "run-b"]
    assert rc == 0
