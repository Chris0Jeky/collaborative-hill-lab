"""Integration: a clean-room run yields a self-consistent, verifiable artifact set.

Runs ``agg-priv`` into a fresh artifacts root and checks the full on-disk
contract: the manifest and resolved-scenario JSON both parse and agree on every
content hash, the derived metrics and report are materialised, and the event
ledger's hash chain verifies end to end.
"""

import json

import pytest

from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.study import run_study
from collaborative_hill.reporting import run_report, write_run_metrics

from ._helpers import STUDY_001, find_run_dirs

pytestmark = pytest.mark.integration

CONDITION = "agg-priv"
HASH_FIELDS = ("scenario_hash", "mechanism_hash", "narrative_hash", "evidence_corpus_hash")


def test_clean_state_manifest_and_ledger(tmp_path):
    artifacts = tmp_path / "fresh-artifacts"
    results = run_study(
        STUDY_001, artifacts, only_condition=CONDITION, replicates_override=1
    )
    assert len(results) == 1
    assert results[0].status == "completed"

    (run_dir,) = find_run_dirs(artifacts)

    # manifest.json parses.
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["condition_id"] == CONDITION
    assert manifest["status"] == "completed"

    # scenario.resolved.json parses and its hashes match the manifest.
    resolved = json.loads((run_dir / "scenario.resolved.json").read_text(encoding="utf-8"))
    for field in HASH_FIELDS:
        assert resolved[field] == manifest[field], f"{field} mismatch"

    # metrics/metrics.json is written by write_run_metrics and equals its return.
    metrics = write_run_metrics(run_dir)
    metrics_path = run_dir / "metrics" / "metrics.json"
    assert metrics_path.exists()
    on_disk = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(metrics, sort_keys=True))
    assert on_disk["metric_versions"]
    assert "operations" in on_disk
    assert "epistemics" in on_disk  # EC run always exposes briefing slots

    # report.md is generated at the run directory.
    report_md = run_report(run_dir)
    assert report_md == run_dir / "report.md"
    assert report_md.exists()

    # events.jsonl chain verifies end to end (load_all raises ChainError otherwise).
    events = FileEventStore(RunPaths(run_dir).events).load_all(verify=True)
    assert events, "empty ledger"
    assert events[-1].event_type == EventType.RUN_COMPLETED
