"""provenance_graph built from a real EC ledger must agree, edge for edge, with
the ClaimProposed/Verified/Challenged events and the RunCompleted briefing."""

from _fixtures import ec_provenance_run

from collaborative_hill.domain.claims import provenance_graph
from collaborative_hill.engine.events import EventType


def _graph_and_events(tmp_path):
    _result, events, _paths = ec_provenance_run(tmp_path)
    return provenance_graph(events), events


def test_cites_edges_match_claim_proposed_events(tmp_path):
    graph, events = _graph_and_events(tmp_path)
    for ev in events:
        if ev.event_type != EventType.CLAIM_PROPOSED:
            continue
        cid = ev.payload["claim_id"]
        assert cid in graph["claims"]
        claim = graph["claims"][cid]
        assert claim["proposer"] == ev.payload["agent_id"]
        assert claim["cited"] == list(ev.payload["evidence_ids"])
        for eid in ev.payload["evidence_ids"]:
            assert {"from": eid, "to": cid, "kind": "cites"} in graph["edges"]


def test_verification_and_challenge_attachment(tmp_path):
    graph, events = _graph_and_events(tmp_path)
    for ev in events:
        if ev.event_type == EventType.CLAIM_VERIFIED:
            cid = ev.payload["claim_id"]
            rec = {"agent": ev.payload["agent_id"], "outcome": ev.payload["outcome"]}
            assert rec in graph["claims"][cid]["verifications"]
            assert {"from": cid, "to": ev.payload["agent_id"],
                    "kind": "verified_by"} in graph["edges"]
        elif ev.event_type == EventType.CLAIM_CHALLENGED:
            cid = ev.payload["claim_id"]
            assert {"from": cid, "to": ev.payload["agent_id"],
                    "kind": "challenged_by"} in graph["edges"]
            valids = [c["valid"] for c in graph["claims"][cid]["challenges"]]
            assert ev.payload["valid"] in valids


def test_run_has_meaningful_verification_and_challenge(tmp_path):
    # The fixture is designed to exercise both a supported verification and a
    # valid challenge; assert the graph actually contains them.
    graph, _events = _graph_and_events(tmp_path)
    all_verifs = [v for c in graph["claims"].values() for v in c["verifications"]]
    all_chals = [c for cl in graph["claims"].values() for c in cl["challenges"]]
    assert any(v["outcome"] == "supported" for v in all_verifs)
    assert any(c["valid"] for c in all_chals)


def test_accepted_flags_consistent_with_run_completed_briefing(tmp_path):
    graph, events = _graph_and_events(tmp_path)
    rc = next(e for e in events if e.event_type == EventType.RUN_COMPLETED)
    briefing = rc.payload["briefing"]
    accepted_ids = {e["claim_id"] for e in briefing if e.get("claim_id")}
    for cid, claim in graph["claims"].items():
        assert claim["accepted"] == (cid in accepted_ids)
        if cid in accepted_ids:
            entry = next(e for e in briefing if e.get("claim_id") == cid)
            assert claim["provenance_ok"] == entry.get("provenance_ok")
        else:
            assert claim["provenance_ok"] is None
    # sanity: at least one claim accepted, at least one rejected in this fixture
    assert accepted_ids
    assert any(cid not in accepted_ids for cid in graph["claims"])
