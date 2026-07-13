"""validate_action: the typed capability gate. Every illegal action returns a
machine-readable reason; legal ones return None."""

from collaborative_hill.domain.actions import (
    ChallengeClaimAction,
    CooperateAction,
    InspectEvidenceAction,
    PairwiseVoteAction,
    ProposeClaimAction,
    ShareEvidenceAction,
    VerifyClaimAction,
)
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import (
    ECWorldSpec,
    EvidenceCommonsMechanism,
)

from _fixtures import AGENTS, ec_hand_example, make_evidence, nipd, step

ATTR = InstitutionConfig(accountability="attributable")


# -- EC capability gate ---------------------------------------------------------


def test_inspect_with_exhausted_budget_rejected():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    state["budgets"]["a1"]["inspect"] = 0
    reason = mech.validate_action(state, "a1", InspectEvidenceAction(evidence_id="e1"))
    assert reason is not None
    assert "budget" in reason


def test_verify_own_claim_rejected():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        "a2": _wh(), "a3": _wh()})
    reason = mech.validate_action(state, "a1", VerifyClaimAction(claim_id="c1"))
    assert reason == "self-verification is not allowed"


def test_share_under_shared_ledger_rejected():
    mech = ec_hand_example(InstitutionConfig(evidence_topology="shared_ledger"))
    state = mech.initial_state()
    reason = mech.validate_action(state, "a1", ShareEvidenceAction(evidence_id="e1"))
    assert reason is not None
    assert "shared_ledger" in reason


def test_propose_citing_invisible_evidence_rejected():
    # e1 held by a1 only; a3 cannot cite it.
    e1 = make_evidence("e1", "s1", "p1a", "supports", "p1a", holders=("a1",))
    spec = ECWorldSpec(agent_ids=AGENTS, slots={"s1": ("p1a", "p1b")},
                       true_propositions={"s1": "p1a"}, evidence=(e1,))
    mech = EvidenceCommonsMechanism(spec=spec, institution=ATTR)
    state = mech.initial_state()
    reason = mech.validate_action(state, "a3", ProposeClaimAction(
        slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)))
    assert reason is not None
    assert "not visible" in reason


def test_unknown_slot_proposition_evidence_claim_rejected():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    assert "unknown slot" in mech.validate_action(state, "a1", ProposeClaimAction(
        slot_id="nope", proposition_id="p1a"))
    assert "not a candidate" in mech.validate_action(state, "a1", ProposeClaimAction(
        slot_id="s1", proposition_id="pZ"))
    assert "does not exist" in mech.validate_action(state, "a1", ProposeClaimAction(
        slot_id="s1", proposition_id="p1a", evidence_ids=("ghost",)))
    assert "unknown claim" in mech.validate_action(state, "a1", VerifyClaimAction(
        claim_id="c999"))
    assert "unknown claim" in mech.validate_action(state, "a1", ChallengeClaimAction(
        claim_id="c999"))


def test_legal_ec_actions_return_none():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    assert mech.validate_action(state, "a1", InspectEvidenceAction(evidence_id="e1")) is None
    assert mech.validate_action(state, "a1", ShareEvidenceAction(evidence_id="e1")) is None
    assert mech.validate_action(state, "a1", ProposeClaimAction(
        slot_id="s1", proposition_id="p1a", evidence_ids=("e1",))) is None


# -- NIPD capability gate -------------------------------------------------------


def test_pairwise_vote_must_cover_exactly_opponents():
    mech = nipd("pairwise")
    state = mech.initial_state()
    # missing a3
    reason = mech.validate_action(state, "a1", PairwiseVoteAction(moves={"a2": "C"}))
    assert reason is not None and "missing=['a3']" in reason
    # extra non-opponent
    reason = mech.validate_action(state, "a1", PairwiseVoteAction(
        moves={"a2": "C", "a3": "C", "zz": "D"}))
    assert reason is not None and "extra=['zz']" in reason
    # exactly the opponents -> legal
    assert mech.validate_action(state, "a1", PairwiseVoteAction(
        moves={"a2": "C", "a3": "D"})) is None


def test_wrong_action_type_per_mode_rejected():
    nb = nipd("neighbourhood")
    pw = nipd("pairwise")
    s_nb = nb.initial_state()
    s_pw = pw.initial_state()
    # pairwise_vote in neighbourhood mode
    reason = nb.validate_action(s_nb, "a1", PairwiseVoteAction(moves={"a2": "C", "a3": "C"}))
    assert reason is not None and "neighbourhood mode accepts" in reason
    # cooperate in pairwise mode
    reason = pw.validate_action(s_pw, "a1", CooperateAction())
    assert reason is not None and "pairwise mode accepts" in reason
    # correct types are legal
    assert nb.validate_action(s_nb, "a1", CooperateAction()) is None
    assert pw.validate_action(s_pw, "a1", PairwiseVoteAction(
        moves={"a2": "C", "a3": "C"})) is None


def _wh():
    from collaborative_hill.domain.actions import WithholdAction
    return WithholdAction()
