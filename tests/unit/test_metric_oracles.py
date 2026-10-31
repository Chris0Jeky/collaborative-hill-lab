"""Hand-derived oracles for reported numbers that surviving mutants showed were unpinned.

Each literal below comes from counting the small ledger by hand. `make mutants` found these
sites unprotected by the fast suites; run it after changing them.
"""

import pydantic
import pytest

from collaborative_hill.agents.scripted.ec_policies import ECVerifierPolicy
from collaborative_hill.agents.scripted.nipd_policies import ThresholdTFTPolicy
from collaborative_hill.domain.actions import ChallengeClaimAction, VerifyClaimAction
from collaborative_hill.domain.world.evidence_commons import ECParams
from collaborative_hill.engine.events import Event, EventType, make_event
from collaborative_hill.engine.hashing import GENESIS_HASH
from collaborative_hill.metrics.cooperation import cooperation_metrics
from collaborative_hill.metrics.epistemics import epistemic_metrics


def _ledger(*items: tuple[EventType, dict]) -> list[Event]:
    events: list[Event] = []
    parent = GENESIS_HASH
    for seq, (event_type, payload) in enumerate(items):
        event = make_event(study_id="S", run_id="R", seq=seq, logical_time=seq, actor="engine",
                           event_type=event_type, payload=payload, parent_hash=parent)
        events.append(event)
        parent = event.event_hash
    return events


def test_per_agent_cooperation_counts_every_pairwise_vote():
    # Two rounds of a1-a2: a1 plays C,C (2/2); a2 plays C,D (1/2).
    events = _ledger(*[
        (EventType.WORLD_TRANSITIONED,
         {"round": rnd, "mode": "pairwise", "cooperative_votes": votes, "total_votes": 2,
          "pair_results": [{"a": "a1", "b": "a2", "move_ab": "C", "move_ba": move}]})
        for rnd, (move, votes) in enumerate((("C", 2), ("D", 1)))
    ])
    assert cooperation_metrics(events)["per_agent_cooperation"] == {"a1": 1.0, "a2": 0.5}


def test_per_agent_cooperation_counts_every_neighbourhood_vote():
    # Four rounds: a1 cooperates once, a2 three times.
    moves = (("C", "D"), ("D", "C"), ("D", "C"), ("D", "C"))
    events = _ledger(*[
        (EventType.WORLD_TRANSITIONED,
         {"round": rnd, "mode": "neighbourhood", "cooperative_votes": 1, "total_votes": 2,
          "moves": {"a1": first, "a2": second}})
        for rnd, (first, second) in enumerate(moves)
    ])
    assert cooperation_metrics(events)["per_agent_cooperation"] == {"a1": 0.25, "a2": 0.75}


def test_epistemic_action_counts_each_event_once():
    claim = {"claim_id": "c1", "slot_id": "s1", "proposition_id": "p", "agent_id": "a1",
             "evidence_ids": ["e1"]}
    events = _ledger(
        (EventType.EVIDENCE_INSPECTED, {"agent_id": "a1", "evidence_id": "e1"}),
        (EventType.EVIDENCE_INSPECTED, {"agent_id": "a2", "evidence_id": "e2"}),
        (EventType.EVIDENCE_INSPECTED, {"agent_id": "a3", "evidence_id": "e3"}),
        (EventType.EVIDENCE_SHARED, {"agent_id": "a1", "evidence_id": "e1"}),
        (EventType.CLAIM_PROPOSED, claim),
        (EventType.CLAIM_VERIFIED, {"agent_id": "a2", "claim_id": "c1", "outcome": "supported"}),
        (EventType.CLAIM_VERIFIED,
         {"agent_id": "a3", "claim_id": "c1", "outcome": "not_supported"}),
        (EventType.CLAIM_CHALLENGED,
         {"agent_id": "a3", "claim_id": "c1", "evidence_ids": ["e3"], "valid": False}),
    )
    metrics = epistemic_metrics(events)
    assert metrics["action_counts"] == {"inspect": 3, "share": 1, "propose": 1, "verify": 2,
                                        "challenge": 1}
    assert metrics["verifications_supported"] == 1
    assert metrics["challenges_valid"] == 0


def test_one_wrong_accepted_claim_is_a_false_acceptance():
    briefing = [{"claim_id": "c1", "correct": False, "provenance_ok": True},
                {"claim_id": None}]
    events = _ledger((EventType.RUN_COMPLETED, {"briefing": briefing}))
    metrics = epistemic_metrics(events)
    assert metrics["false_claim_accepted"] is True
    assert (metrics["slots"], metrics["slots_filled"], metrics["accepted_incorrect"]) == (2, 1, 1)


def test_declared_ec_defaults_are_pinned():
    params = ECParams()
    assert params.credit_verify_accepted_wrong == -2
    assert params.credit_verify_accepted_correct == 2
    assert params.credit_propose_accepted_wrong == -3
    assert ECParams(cost_propose=0).cost_propose == 0
    with pytest.raises(pydantic.ValidationError):
        ECParams(cost_propose=-1)


def test_ledger_events_are_immutable():
    event = _ledger((EventType.RUN_STARTED, {}))[0]
    with pytest.raises(pydantic.ValidationError):
        event.seq = 5


def test_threshold_default_is_one_half():
    assert ThresholdTFTPolicy().policy_id == "tft_threshold[1/2,eps=0.0]@1"


def _verifier_view(*, inspect: int, evidence: list[dict], claims: list[dict]) -> dict:
    return {"my_budgets": {"inspect": inspect, "verify": 1}, "evidence": evidence,
            "claims": claims}


def _claim() -> dict:
    return {"claim_id": "c1", "slot_id": "s1", "proposition_id": "p", "proposed_by_me": False,
            "challenged_by_me": False, "verified_by_me": False}


def _item(stance: str, freshness: str) -> dict:
    return {"evidence_id": "e1", "facts": {"slot_id": "s1", "proposition_id": "p",
                                           "stance": stance, "freshness": freshness}}


def test_verifier_with_no_inspect_budget_cannot_inspect_pending_evidence():
    view = _verifier_view(inspect=0, evidence=[{"evidence_id": "e9"}], claims=[_claim()])
    assert isinstance(ECVerifierPolicy().propose(view, None).action, VerifyClaimAction)


@pytest.mark.parametrize(("stance", "freshness", "challenges"), [
    ("contradicts", "fresh", True),
    ("contradicts", "stale", False),
    ("supports", "fresh", False),
])
def test_verifier_challenges_only_on_fresh_contradiction(stance, freshness, challenges):
    view = _verifier_view(inspect=0, evidence=[_item(stance, freshness)], claims=[_claim()])
    action = ECVerifierPolicy().propose(view, None).action
    assert isinstance(action, ChallengeClaimAction) is challenges
