"""Claims and the provenance graph derived from a sealed ledger.

A claim proposes that a proposition fills a briefing slot, citing evidence.
Its lifecycle is fully event-sourced (ClaimProposed / ClaimVerified /
ClaimChallenged events); the state dict inside the Evidence Commons mechanism
is just the running projection. This module holds the shared vocabulary and
the provenance-graph builder used by epistemic metrics and reports:

    EvidenceItem -> Claim -> Verification/Challenge -> accepted briefing entry

"Supported" here always means *provenance-supported* — cited evidence exists,
was accessible, is fresh, and bears a supporting stance. It deliberately does
NOT mean "true": verification checks provenance, not ground truth, so
well-cited misinformation can be accepted. Truth enters only in final scoring
(world plane), which is how false-claim propagation becomes measurable.
"""

from typing import Any

CLAIM_STATUS = ("open", "accepted", "rejected")


def provenance_graph(events: list[Any]) -> dict[str, Any]:
    """Build the provenance graph from ledger events.

    Returns {claims: {claim_id: {slot, proposition, proposer, cited, verifications,
    challenges, accepted, provenance_ok}}, edges: [...]}. Works on Event objects
    (engine.events.Event) — uses .event_type and .payload only.
    """
    claims: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    for ev in events:
        etype = getattr(ev, "event_type", None)
        payload = getattr(ev, "payload", {})
        if etype == "ClaimProposed":
            cid = payload["claim_id"]
            claims[cid] = {
                "claim_id": cid,
                "slot_id": payload["slot_id"],
                "proposition_id": payload["proposition_id"],
                "proposer": payload["agent_id"],
                "cited": list(payload["evidence_ids"]),
                "verifications": [],
                "challenges": [],
                "accepted": False,
                "provenance_ok": None,
            }
            for eid in payload["evidence_ids"]:
                edges.append({"from": eid, "to": cid, "kind": "cites"})
        elif etype == "ClaimVerified":
            cid = payload["claim_id"]
            if cid in claims:
                claims[cid]["verifications"].append(
                    {"agent": payload["agent_id"], "outcome": payload["outcome"]}
                )
                edges.append({"from": cid, "to": payload["agent_id"], "kind": "verified_by"})
        elif etype == "ClaimChallenged":
            cid = payload["claim_id"]
            if cid in claims:
                claims[cid]["challenges"].append(
                    {"agent": payload["agent_id"], "valid": payload["valid"],
                     "cited": list(payload["evidence_ids"])}
                )
                edges.append({"from": cid, "to": payload["agent_id"], "kind": "challenged_by"})
        elif etype == "RunCompleted":
            for entry in payload.get("briefing", []):
                cid = entry.get("claim_id")
                if cid in claims:
                    claims[cid]["accepted"] = True
                    claims[cid]["provenance_ok"] = entry.get("provenance_ok")
    return {"claims": claims, "edges": edges}
