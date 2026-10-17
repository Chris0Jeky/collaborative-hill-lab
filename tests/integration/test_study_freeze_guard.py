"""A freeze is an immutable commitment, including under competing publication."""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from collaborative_hill.cli import app
from collaborative_hill.experiments import study

from ._helpers import STUDY_001

pytestmark = pytest.mark.integration


@pytest.fixture
def draft(tmp_path):
    return Path(shutil.copytree(STUDY_001, tmp_path / "study"))


def test_refreeze_changed_study_preserves_original_lock(draft, tmp_path):
    study.freeze_study(draft)
    lock = draft / "study.lock.json"
    before = lock.read_bytes()
    scenario = draft / "scenarios" / "agg-priv.json"
    data = json.loads(scenario.read_text(encoding="utf-8"))
    data["world"]["params"]["rounds"] += 1
    scenario.write_text(json.dumps(data), encoding="utf-8")
    artifacts = tmp_path / "artifacts"
    with pytest.raises(ValueError, match="changed after freeze"):
        study.run_study(draft, artifacts, only_condition="agg-priv", replicates_override=1)
    with pytest.raises(ValueError, match="immutable"):
        study.freeze_study(draft)
    assert lock.read_bytes() == before
    with pytest.raises(ValueError, match="changed after freeze"):
        study.run_study(draft, artifacts, only_condition="agg-priv", replicates_override=1)
    assert not artifacts.exists()


def test_identical_refreeze_preserves_timestamp_and_bytes(draft, monkeypatch, tmp_path):
    original_hash = study.freeze_study(draft)
    lock = draft / "study.lock.json"
    before = lock.read_bytes()
    monkeypatch.setattr(study, "utc_now_iso", lambda: "later")
    assert study.freeze_study(draft) == original_hash
    assert lock.read_bytes() == before
    results = study.run_study(
        draft, tmp_path / "artifacts", only_condition="agg-priv", replicates_override=1
    )
    assert results[0].status == "completed"


def test_competing_freeze_cannot_replace_published_lock(draft, monkeypatch):
    import os

    link = os.link
    winner = b'{"study_id":"other","study_hash":"other"}'

    def publish_competitor(source, destination):
        Path(destination).write_bytes(winner)
        link(source, destination)

    monkeypatch.setattr(os, "link", publish_competitor)
    with pytest.raises(ValueError, match="immutable"):
        study.freeze_study(draft)
    assert (draft / "study.lock.json").read_bytes() == winner
    assert not list(draft.glob(".study-lock-*.tmp"))


def test_cli_refreeze_changed_study_is_usage_error(draft):
    runner = CliRunner()
    assert runner.invoke(app, ["study", "freeze", str(draft), "--yes"]).exit_code == 0
    lock = draft / "study.lock.json"
    before = lock.read_bytes()
    spec_path = draft / "study.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["seed"] += 1
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    result = runner.invoke(app, ["study", "freeze", str(draft), "--yes"])

    assert result.exit_code == 2
    assert "error:" in result.output
    assert "immutable" in result.output
    assert "Traceback" not in result.output
    assert lock.read_bytes() == before


@pytest.mark.parametrize("existing", [True, False])
def test_freeze_link_failure_is_clear_and_fail_closed(draft, monkeypatch, existing):
    lock = draft / "study.lock.json"
    if existing:
        study.freeze_study(draft)
    before = lock.read_bytes() if existing else None

    def unsupported_link(*args):
        raise OSError("hard links unavailable")

    monkeypatch.setattr(study.os, "link", unsupported_link)
    with pytest.raises(ValueError, match="cannot atomically publish.*unchanged"):
        study.freeze_study(draft)
    assert (lock.read_bytes() if lock.exists() else None) == before
    assert not list(draft.glob(".study-lock-*.tmp"))
