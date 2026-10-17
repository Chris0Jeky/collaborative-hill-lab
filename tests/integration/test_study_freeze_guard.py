"""A freeze is an immutable commitment, including under competing publication."""

import json
import shutil
from pathlib import Path

import pytest

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
