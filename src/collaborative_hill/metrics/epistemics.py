"""Epistemic metrics (v1) — defined for Evidence Commons ledgers.

Counts come from the sealed briefing (RunCompleted) and the provenance graph.
"correct" compares an accepted claim's proposition to environment truth;
"provenance_ok" means the accepted claim cites >=1 existing, fresh,
supporting item — the two axes are independent by design, which is what makes
well-cited misinformation and unsupported-but-true claims both measurable.
"""

from typing import Any

from collaborative_hill.domain.claims import provenance_graph
from collaborative_hill.engine.events import Event, EventType


def epistemic_metrics(events: list[Event]) -> dict[str, Any]:
    briefing: list[dict[str, Any]] = []
    for ev in events:
        if ev.event_type == EventType.RUN_COMPLETED and "briefing" in ev.payload:
            briefing = ev.payload["briefing"]

    graph = provenance_graph(events)
    n_slots = len(briefing)
    accepted = [e for e in briefing if e.get("claim_id")]
    correct = [e for e in accepted if e.get("correct")]
    incorrect = [e for e in accepted if not e.get("correct")]
    provenance_broken = [e for e in accepted if e.get("provenance_ok") is False]

    counts = {"inspect": 0, "share": 0, "propose": 0, "verify": 0, "challenge": 0}
    verify_supported = 0
    challenges_valid = 0
    for ev in events:
        if ev.event_type == EventType.EVIDENCE_INSPECTED:
            counts["inspect"] += 1
        elif ev.event_type == EventType.EVIDENCE_SHARED:
            counts["share"] += 1
        elif ev.event_type == EventType.CLAIM_PROPOSED:
            counts["propose"] += 1
        elif ev.event_type == EventType.CLAIM_VERIFIED:
            counts["verify"] += 1
            if ev.payload.get("outcome") == "supported":
                verify_supported += 1
        elif ev.event_type == EventType.CLAIM_CHALLENGED:
            counts["challenge"] += 1
            if ev.payload.get("valid"):
                challenges_valid += 1

    return {
        "version": "1",
        "slots": n_slots,
        "slots_filled": len(accepted),
        "accepted_correct": len(correct),
        "accepted_incorrect": len(incorrect),
        "accepted_provenance_broken": len(provenance_broken),
        "false_claim_accepted": len(incorrect) > 0,
        "claims_proposed": len(graph["claims"]),
        "action_counts": counts,
        "verifications_supported": verify_supported,
        "challenges_valid": challenges_valid,
        "briefing": briefing,
    }
