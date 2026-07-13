"""Integration: Study 001 (Evidence Commons) validation + attr-ledger pipeline.

Validates the shipped study resolves all five conditions, then runs the
``attr-ledger`` condition (contributor + contributor + freerider under
attributable accountability and a shared ledger) end to end and asserts on the
sealed epistemic outcome: at least three slots filled with no accepted
misinformation, every accepted briefing entry carries an explicit
``provenance_ok`` bool, and the provenance graph's ``cites`` edges match each
accepted claim's citations.
"""

import pytest

from collaborative_hill.domain.claims import provenance_graph
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.study import run_study, validate_study
from collaborative_hill.metrics import epistemic_metrics

from ._helpers import STUDY_001, find_run_dirs

pytestmark = pytest.mark.integration

CONDITION = "attr-ledger"
EXPECTED_CONDITIONS = {
    "agg-priv", "agg-ledger", "attr-priv", "attr-ledger", "attr-priv-misinfo",
}


def test_validate_study_001_has_five_conditions():
    report = validate_study(STUDY_001)
    assert report["study_id"] == "001-evidence-commons"
    assert set(report["conditions"]) == EXPECTED_CONDITIONS
    assert len(report["conditions"]) == 5
    # Each condition resolved to a full set of content hashes.
    for hashes in report["conditions"].values():
        assert hashes["scenario_hash"]
        assert hashes["mechanism_hash"]
        assert hashes["evidence_corpus_hash"]


def test_attr_ledger_epistemics_and_provenance(tmp_path):
    artifacts = tmp_path / "artifacts"
    results = run_study(
        STUDY_001, artifacts, only_condition=CONDITION, replicates_override=1
    )
    assert len(results) == 1
    assert results[0].status == "completed"

    (run_dir,) = find_run_dirs(artifacts)
    events = FileEventStore(RunPaths(run_dir).events).load_all(verify=True)

    epi = epistemic_metrics(events)
    # Accountability + shared ledger fills at least three slots, none of them
    # wrong or provenance-broken.
    assert epi["slots_filled"] >= 3
    assert epi["accepted_incorrect"] == 0
    assert epi["accepted_provenance_broken"] == 0

    # Every ACCEPTED briefing entry carries an explicit provenance_ok bool
    # (True or False) — never missing. Unfilled slots carry no claim_id.
    accepted = [e for e in epi["briefing"] if e.get("claim_id")]
    assert accepted, "expected at least one accepted claim"
    for entry in accepted:
        assert "provenance_ok" in entry, f"provenance_ok missing from {entry}"
        assert isinstance(entry["provenance_ok"], bool)

    # Provenance graph: each accepted claim's cited evidence is a `cites` edge,
    # and the graph agrees the claim was accepted.
    graph = provenance_graph(events)
    accepted_ids = {e["claim_id"] for e in accepted}
    assert accepted_ids <= set(graph["claims"])
    for cid in accepted_ids:
        claim = graph["claims"][cid]
        assert claim["accepted"] is True
        assert claim["cited"], f"accepted claim {cid} cites no evidence"
        for eid in claim["cited"]:
            assert {"from": eid, "to": cid, "kind": "cites"} in graph["edges"]
