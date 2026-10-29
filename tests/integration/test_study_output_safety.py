"""Invalid study designs cannot redirect or partially start artifact writes."""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from collaborative_hill.cli import app
from collaborative_hill.engine.runner import RunConfig
from collaborative_hill.experiments.study import run_study, validate_study

from ._helpers import STUDY_000


def _draft(tmp_path: Path, **updates):
    folder = Path(shutil.copytree(STUDY_000, tmp_path / "study"))
    path = folder / "study.json"
    spec = json.loads(path.read_text())
    spec["replicates"] = 1
    spec["conditions"] = spec["conditions"][:1]
    spec.update(updates)
    path.write_text(json.dumps(spec))
    return folder, spec


@pytest.mark.parametrize("identifier", [
    "", ".", "..", "../escape", "nested/condition", r"nested\condition",
    r"C:\escape", "NUL", "con.txt", "condition.", " condition", "condition ",
    "condition:stream", "a\x1fb", "a?b",
])
def test_unsafe_condition_id_fails_before_output(tmp_path, identifier):
    study, spec = _draft(tmp_path)
    spec["conditions"][0]["condition_id"] = identifier
    (study / "study.json").write_text(json.dumps(spec))
    artifacts = tmp_path / "artifacts"
    with pytest.raises(ValueError, match="condition_id"):
        run_study(study, artifacts)
    assert not artifacts.exists()


def test_absolute_condition_cannot_escape_artifacts(tmp_path):
    study, spec = _draft(tmp_path)
    outside = tmp_path / "escaped"
    spec["conditions"][0]["condition_id"] = str(outside)
    (study / "study.json").write_text(json.dumps(spec))
    result = CliRunner().invoke(app, ["run", str(study), "--artifacts", str(tmp_path / "art")])
    assert result.exit_code == 2
    assert not outside.exists()
    assert not outside.with_name("escaped-r000").exists()
    assert not (tmp_path / "art").exists()


def test_condition_ids_must_not_collide_on_case_insensitive_filesystems(tmp_path):
    study, spec = _draft(tmp_path)
    spec["conditions"] = [dict(spec["conditions"][0], condition_id=name)
                          for name in ("baseline", "BASELINE")]
    (study / "study.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="unique"):
        run_study(study, tmp_path / "artifacts")
    assert not (tmp_path / "artifacts").exists()


def test_empty_study_is_invalid(tmp_path):
    study, _ = _draft(tmp_path, conditions=[])
    with pytest.raises(ValueError, match="conditions"):
        validate_study(study)


@pytest.mark.parametrize("value", [True, 1.5, "2"])
def test_replicate_override_must_be_an_integer_before_writes(tmp_path, value):
    study, _ = _draft(tmp_path)
    with pytest.raises(ValueError, match="replicates"):
        run_study(study, tmp_path / "artifacts", replicates_override=value)
    assert not (tmp_path / "artifacts").exists()


@pytest.mark.parametrize("field,value", [
    ("replicates", True), ("replicates", "2"), ("checkpoint_every", -1),
    ("checkpoint_every", True), ("checkpoint_every", "2"),
])
def test_invalid_execution_counts_fail_study_validation(tmp_path, field, value):
    study, _ = _draft(tmp_path, **{field: value})
    with pytest.raises(ValueError, match=field):
        validate_study(study)


@pytest.mark.parametrize("value", [-1, True, "2"])
def test_episode_config_rejects_invalid_checkpoint_cadence(value):
    with pytest.raises(ValueError, match="checkpoint_every"):
        RunConfig(study_id="test", run_id="test", seed_root=(1,), checkpoint_every=value)


def test_symlinked_condition_cannot_redirect_writes(tmp_path):
    study, spec = _draft(tmp_path)
    artifacts = tmp_path / "artifacts"
    prefix = artifacts / ("DRAFT-" + validate_study(study)["study_hash"][:12])
    prefix.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = prefix / spec["conditions"][0]["condition_id"]
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(ValueError, match="outside.*artifacts"):
        run_study(study, artifacts)
    assert not list(outside.iterdir())
    assert list(prefix.iterdir()) == [link]


def test_selected_artifact_root_may_itself_be_a_symlink(tmp_path):
    study, _ = _draft(tmp_path)
    target = tmp_path / "chosen-target"
    target.mkdir()
    artifacts = tmp_path / "artifacts"
    try:
        artifacts.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    results = run_study(study, artifacts)
    assert len(results) == 1
    assert results[0].status == "completed"
    assert len(list(target.rglob("events.jsonl"))) == 1


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_later_condition_blocker_is_caught_before_any_run(tmp_path, kind):
    study, spec = _draft(tmp_path)
    spec["conditions"] = [dict(spec["conditions"][0], condition_id=name)
                          for name in ("first", "blocked")]
    (study / "study.json").write_text(json.dumps(spec))
    artifacts = tmp_path / "artifacts"
    prefix = artifacts / ("DRAFT-" + validate_study(study)["study_hash"][:12])
    prefix.mkdir(parents=True)
    blocker = prefix / "blocked"
    if kind == "file":
        blocker.write_text("keep this file")
    else:
        try:
            blocker.symlink_to(prefix / "missing", target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(FileExistsError):
        run_study(study, artifacts)
    assert list(prefix.iterdir()) == [blocker]
    if kind == "file":
        assert blocker.read_text() == "keep this file"
    else:
        assert blocker.is_symlink()


@pytest.mark.parametrize("alias", ["same_directory", "nested_directory"])
def test_planned_runs_cannot_alias_or_nest_via_symlinks(tmp_path, alias):
    study, spec = _draft(tmp_path)
    spec["conditions"] = [dict(spec["conditions"][0], condition_id=name)
                          for name in ("first", "second")]
    (study / "study.json").write_text(json.dumps(spec))
    artifacts = tmp_path / "artifacts"
    prefix = artifacts / ("DRAFT-" + validate_study(study)["study_hash"][:12])
    target = artifacts / "shared"
    target.mkdir(parents=True)
    (prefix / "first").mkdir(parents=True)
    try:
        (prefix / "first" / "first-r000").symlink_to(target, target_is_directory=True)
        if alias == "same_directory":
            (prefix / "second").mkdir()
            (prefix / "second" / "second-r000").symlink_to(target, target_is_directory=True)
        else:
            (prefix / "second").symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(ValueError, match="overlap"):
        run_study(study, artifacts)
    assert not list(target.iterdir())
