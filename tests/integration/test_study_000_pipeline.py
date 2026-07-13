"""Integration: Study 000 (legacy reproduction) end-to-end pipeline.

Runs the ``pw-2tft-alld`` condition (two pairwise-TFT reciprocators + one AllD)
through ``run_study`` and asserts on the sealed artifacts: both replicate runs
complete, their manifests carry the study/scenario/mechanism hashes that
``load_study`` independently computes, the sealed NIPD scores reproduce the
hand-derived quarantine oracle, and the run/study reports name the condition.

Score oracle (pairwise, T=5 R=3 P=1 S=0, 50 rounds) — hand-derived, NOT read
from the code under test:

  round 0:      the TFT-TFT edge opens C,C -> 3 each; each TFT plays C against
                AllD -> 0; AllD defects both edges -> 5+5. So TFT=3, AllD=10.
  rounds 1..49: each TFT saw AllD defect and quarantines it (D vs AllD) while
                the TFT-TFT edge stays C,C. Per round each TFT scores
                3 (vs TFT) + 1 (D,D vs AllD) = 4; AllD scores 1 + 1 = 2.
  totals:       TFT = 3 + 49*4 = 199 ; AllD = 10 + 49*2 = 108.
"""

import json

import pytest

from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.study import load_study, run_study, study_hash
from collaborative_hill.reporting import run_report, study_report

from ._helpers import STUDY_000, find_run_dirs

pytestmark = pytest.mark.integration

CONDITION = "pw-2tft-alld"
TFT_SCORE = "199"
ALLD_SCORE = "108"


def test_study_000_pipeline(tmp_path):
    artifacts = tmp_path / "artifacts"
    results = run_study(
        STUDY_000, artifacts, only_condition=CONDITION, replicates_override=2
    )

    # Both replicates ran and completed.
    assert [r.run_id for r in results] == [f"{CONDITION}-r000", f"{CONDITION}-r001"]
    assert all(r.status == "completed" for r in results)

    # Sealed summary reproduces the hand-derived quarantine oracle, and the two
    # deterministic replicates are byte-for-byte identical.
    for r in results:
        assert r.summary["scores"]["a1"] == TFT_SCORE  # tft_pairwise
        assert r.summary["scores"]["a2"] == TFT_SCORE  # tft_pairwise
        assert r.summary["scores"]["a3"] == ALLD_SCORE  # alld
    assert results[0].summary == results[1].summary

    # Manifests are present and carry the hashes load_study recomputes.
    spec, resolved = load_study(STUDY_000)
    expected_study_hash = study_hash(spec, resolved)
    expected = resolved[CONDITION]

    run_dirs = find_run_dirs(artifacts)
    assert len(run_dirs) == 2
    for run_dir in run_dirs:
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["study_hash"] == expected_study_hash
        assert manifest["scenario_hash"] == expected.scenario_hash
        assert manifest["mechanism_hash"] == expected.mechanism_hash
        assert manifest["condition_id"] == CONDITION
        assert manifest["status"] == "completed"
        assert manifest["study_frozen"] is False

    # The scores really are sealed into the hash-verified ledger (not just the
    # in-memory RunResult): re-read the RunCompleted event under chain verify.
    one_run = run_dirs[0]
    events = FileEventStore(RunPaths(one_run).events).load_all(verify=True)
    completed = [e for e in events if e.event_type == EventType.RUN_COMPLETED]
    assert len(completed) == 1
    assert completed[0].payload["scores"] == {
        "a1": TFT_SCORE, "a2": TFT_SCORE, "a3": ALLD_SCORE,
    }

    # Reports generate files that name the condition.
    run_md = run_report(one_run)
    assert run_md.exists()
    assert CONDITION in run_md.read_text(encoding="utf-8")

    study_root = one_run.parent.parent  # artifacts/<DRAFT-hash>/
    study_md = study_report(study_root)
    assert study_md.exists()
    assert CONDITION in study_md.read_text(encoding="utf-8")
