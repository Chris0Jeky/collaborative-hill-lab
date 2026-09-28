import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest  # noqa: E402

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
