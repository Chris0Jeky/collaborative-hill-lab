import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest  # noqa: E402
from typer.testing import CliRunner  # noqa: E402

from collaborative_hill.cli import app  # noqa: E402
from collaborative_hill.engine.store import FileEventStore  # noqa: E402
from collaborative_hill.experiments import study  # noqa: E402
from collaborative_hill.experiments.study import run_study  # noqa: E402

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_000 = REPO_ROOT / "studies" / "000-legacy-reproduction"
CONDITION = "nb-2ptft-alld-incself"


def _single_run_dir(artifacts_root: Path) -> Path:
    run_dirs = sorted(p.parent for p in artifacts_root.rglob("events.jsonl"))
    assert len(run_dirs) == 1
    return run_dirs[0]


def test_rerun_into_same_artifacts_is_refused(tmp_path: Path) -> None:
    first = run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)
    assert len(first) == 1
    assert first[0].status == "completed"

    run_dir = _single_run_dir(tmp_path)
    events_before = (run_dir / "events.jsonl").read_bytes()
    manifest_before = (run_dir / "manifest.json").read_bytes()

    with pytest.raises(FileExistsError):
        run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)

    assert (run_dir / "events.jsonl").read_bytes() == events_before
    assert (run_dir / "manifest.json").read_bytes() == manifest_before
    assert sorted(p.parent for p in tmp_path.rglob("events.jsonl")) == [run_dir]


def test_fresh_artifacts_root_still_runs(tmp_path: Path) -> None:
    results = run_study(
        STUDY_000, tmp_path / "art", only_condition=CONDITION, replicates_override=1
    )
    assert len(results) == 1
    assert results[0].status == "completed"


def test_existing_empty_run_dir_is_accepted(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = run_study(
        STUDY_000, first_root, only_condition=CONDITION, replicates_override=1
    )
    assert len(first) == 1
    assert first[0].status == "completed"

    first_run = _single_run_dir(first_root)
    empty_dir = second_root / first_run.relative_to(first_root)
    empty_dir.mkdir(parents=True)

    second = run_study(
        STUDY_000, second_root, only_condition=CONDITION, replicates_override=1
    )
    assert len(second) == 1
    assert second[0].status == "completed"


def test_run_directory_is_reserved_before_policy_construction(tmp_path, monkeypatch):
    build = study.build_policies
    contended = False

    def competing_run(resolved):
        nonlocal contended
        if not contended:
            contended = True
            with pytest.raises(FileExistsError):
                run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)
        return build(resolved)

    monkeypatch.setattr(study, "build_policies", competing_run)
    results = run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)
    assert results[0].status == "completed"
    assert len(FileEventStore(_single_run_dir(tmp_path) / "events.jsonl").load_all()) > 0


def test_cli_occupied_run_is_usage_error(tmp_path):
    run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)
    result = CliRunner().invoke(app, [
        "run", str(STUDY_000), "--artifacts", str(tmp_path),
        "--condition", CONDITION, "--replicates", "1",
    ])
    assert result.exit_code == 2
    assert "error:" in result.output
    assert "refusing" in result.output


def test_atomic_reservation_preserves_competing_writer(tmp_path, monkeypatch):
    original_open = Path.open
    claimed = []

    def claim_first(path, mode="r", *args, **kwargs):
        if path.name == "events.jsonl" and mode in {"x", "w", "a"} and not claimed:
            claimed.append(path)
            with original_open(path, "x", encoding="utf-8", newline="\n") as stream:
                stream.write("competing reservation\n")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", claim_first)
    with pytest.raises(FileExistsError):
        run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)
    (ledger,) = claimed
    assert ledger.read_bytes() == b"competing reservation\n"
    assert not (ledger.parent / "manifest.json").exists()


@pytest.mark.parametrize("failure", [ValueError, KeyboardInterrupt])
def test_pre_manifest_failure_releases_reservation_for_retry(tmp_path, monkeypatch, failure):
    build = study.build_policies
    reserved = []

    def fail(resolved):
        reserved.append(_single_run_dir(tmp_path))
        assert not (reserved[0] / "manifest.json").exists()
        raise failure("synthetic setup failure")

    monkeypatch.setattr(study, "build_policies", fail)
    with pytest.raises(failure, match="synthetic setup failure"):
        run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)
    assert not reserved[0].exists()
    monkeypatch.setattr(study, "build_policies", build)
    assert run_study(
        STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1
    )[0].status == "completed"


def test_post_manifest_failure_preserves_run(tmp_path, monkeypatch):
    before = {}

    def fail(**kwargs):
        run_dir = kwargs["paths"].root
        before.update({p: p.read_bytes() for p in run_dir.rglob("*") if p.is_file()})
        raise KeyboardInterrupt("synthetic interruption")

    monkeypatch.setattr(study, "run_episode", fail)
    with pytest.raises(KeyboardInterrupt):
        run_study(STUDY_000, tmp_path, only_condition=CONDITION, replicates_override=1)
    assert before
    assert {p: p.read_bytes() for p in before} == before
