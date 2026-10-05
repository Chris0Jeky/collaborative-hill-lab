"""run_study input validation: unknown conditions and replicates < 1 fail fast.

An unknown ``--condition`` or a non-positive ``--replicates`` must raise a
``ValueError`` before any directory or file is created (never a silent
zero-run success), while a normal run still returns results. The CLI maps
these failures to exit code 2. Drives the shipped study 000 fixture exactly
as the integration suite does — no new fixture invented here.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from collaborative_hill.cli import app
from collaborative_hill.experiments.study import StudySpec, run_study

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_000 = REPO_ROOT / "studies" / "000-legacy-reproduction"
CONDITION = "nb-2ptft-alld-incself"


def test_unknown_condition_raises_and_creates_nothing(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    with pytest.raises(ValueError, match="nope"):
        run_study(STUDY_000, artifacts, only_condition="nope", replicates_override=1)
    assert not artifacts.exists()


@pytest.mark.parametrize("replicates", [0, -3])
def test_non_positive_replicates_raise_and_create_nothing(
    tmp_path: Path, replicates: int
) -> None:
    artifacts = tmp_path / "artifacts"
    with pytest.raises(ValueError, match="replicates must be >= 1"):
        run_study(
            STUDY_000, artifacts, only_condition=CONDITION,
            replicates_override=replicates,
        )
    assert not artifacts.exists()


@pytest.mark.parametrize("replicates", [0, -3])
def test_spec_replicates_bound_rejects_non_positive(replicates: int) -> None:
    with pytest.raises(ValidationError):
        StudySpec(study_id="s", seed=1, replicates=replicates, conditions=())


def test_normal_run_still_returns_results(tmp_path: Path) -> None:
    results = run_study(
        STUDY_000, tmp_path / "artifacts", only_condition=CONDITION,
        replicates_override=1,
    )
    assert len(results) == 1
    assert results[0].status == "completed"


def test_cli_unknown_condition_exits_2(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    result = CliRunner().invoke(
        app, ["run", str(STUDY_000), "--artifacts", str(artifacts),
              "--condition", "nope", "--replicates", "1"],
    )
    assert result.exit_code == 2
    assert not artifacts.exists()


def test_cli_zero_replicates_exits_2(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    result = CliRunner().invoke(
        app, ["run", str(STUDY_000), "--artifacts", str(artifacts),
              "--condition", CONDITION, "--replicates", "0"],
    )
    assert result.exit_code == 2
    assert not artifacts.exists()
