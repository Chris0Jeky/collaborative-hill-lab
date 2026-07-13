"""Evidence Commons transitions: budgets, effort, deterministic claim ids,
verification/challenge adjudication, acceptance rule, and hand-computed
final_rewards arithmetic (exact Fractions)."""

from _fixtures import AGENTS, ec_hand_example, make_evidence, step

from collaborative_hill.domain.actions import (
    ChallengeClaimAction,
    InspectEvidenceAction,
    ProposeClaimAction,
    VerifyClaimAction,
    WithholdAction,
)
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import (
    ECParams,
    ECWorldSpec,
    EvidenceCommonsMechanism,
)

ATTR = InstitutionConfig(accountability="attributable")
AGG = InstitutionConfig(accountability="aggregate")


def _withhold_all(exclude=()):
    return {a: WithholdAction() for a in AGENTS if a not in exclude}


def test_inspect_decrements_budget_and_accrues_effort():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    assert state["budgets"]["a1"]["inspect"] == ECParams().inspect_budget
    assert state["effort"]["a1"] == 0
    actions = {"a1": InspectEvidenceAction(evidence_id="e1"), **_withhold_all(exclude=("a1",))}
    state, _ = step(mech, state, actions)
    assert state["budgets"]["a1"]["inspect"] == ECParams().inspect_budget - 1
    assert state["effort"]["a1"] == ECParams().cost_inspect
    assert "e1" in state["inspected"]["a1"]


def test_verify_decrements_verify_budget_and_accrues_effort():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    # a1 proposes so a2 has something to verify
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        **_withhold_all(exclude=("a1",))})
    assert state["budgets"]["a2"]["verify"] == ECParams().verify_budget
    state, _ = step(mech, state, {
        "a2": VerifyClaimAction(claim_id="c1"), **_withhold_all(exclude=("a2",))})
    assert state["budgets"]["a2"]["verify"] == ECParams().verify_budget - 1
    assert state["effort"]["a2"] == ECParams().cost_verify


def test_claim_ids_deterministic_in_sorted_agent_order():
    # Two agents propose in the SAME round; ids assigned by sorted agent id.
    e1 = make_evidence("e1", "s1", "p1a", "supports", "p1a", holders=("a1", "a2"))
    spec = ECWorldSpec(agent_ids=AGENTS, slots={"s1": ("p1a", "p1b")},
                       true_propositions={"s1": "p1a"}, evidence=(e1,))
    mech = EvidenceCommonsMechanism(spec=spec, institution=ATTR)
    state = mech.initial_state()
    # a2 listed first in dict on purpose; resolve iterates sorted(actions).
    actions = {
        "a2": ProposeClaimAction(slot_id="s1", proposition_id="p1b", evidence_ids=()),
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        "a3": WithholdAction(),
    }
    state, _ = step(mech, state, actions)
    # a1 sorts before a2 -> a1 gets c1, a2 gets c2
    assert state["claims"]["c1"]["proposer"] == "a1"
    assert state["claims"]["c2"]["proposer"] == "a2"
    assert state["claim_order"] == ["c1", "c2"]


def test_verification_supported_when_evidence_accessible_fresh_supports():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        **_withhold_all(exclude=("a1",))})
    state, _ = step(mech, state, {
        "a2": VerifyClaimAction(claim_id="c1"), **_withhold_all(exclude=("a2",))})
    verifs = state["claims"]["c1"]["verifications"]
    assert verifs == [{"agent": "a2", "outcome": "supported"}]


def test_verification_not_supported_when_evidence_inaccessible():
    # e1 held only by a1; a2 proposes a claim citing nothing, a3 (no access) verifies.
    e1 = make_evidence("e1", "s1", "p1a", "supports", "p1a", holders=("a1",))
    spec = ECWorldSpec(agent_ids=AGENTS, slots={"s1": ("p1a", "p1b")},
                       true_propositions={"s1": "p1a"}, evidence=(e1,))
    mech = EvidenceCommonsMechanism(spec=spec, institution=ATTR)
    state = mech.initial_state()
    # a1 proposes citing e1 (a1 holds it), a3 verifies but cannot access e1 (private).
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        **_withhold_all(exclude=("a1",))})
    state, _ = step(mech, state, {
        "a3": VerifyClaimAction(claim_id="c1"), **_withhold_all(exclude=("a3",))})
    assert state["claims"]["c1"]["verifications"] == [
        {"agent": "a3", "outcome": "not_supported"}]


def test_challenge_valid_only_with_fresh_contradicting_accessible_evidence():
    # e_sup supports p1a (a1); e_con contradicts p1a (a2). a1 proposes, a2 challenges.
    e_sup = make_evidence("e_sup", "s1", "p1a", "supports", "p1a", holders=("a1",))
    e_con = make_evidence("e_con", "s1", "p1a", "contradicts", "p1a", holders=("a2",))
    spec = ECWorldSpec(agent_ids=AGENTS, slots={"s1": ("p1a", "p1b")},
                       true_propositions={"s1": "p1a"}, evidence=(e_sup, e_con))
    mech = EvidenceCommonsMechanism(spec=spec, institution=ATTR)
    state = mech.initial_state()
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e_sup",)),
        **_withhold_all(exclude=("a1",))})
    # valid challenge citing the contradicting item
    state, _ = step(mech, state, {
        "a2": ChallengeClaimAction(claim_id="c1", evidence_ids=("e_con",)),
        **_withhold_all(exclude=("a2",))})
    ch = state["claims"]["c1"]["challenges"]
    assert ch == [{"agent": "a2", "valid": True, "cited": ["e_con"]}]


def test_challenge_invalid_when_no_contradicting_evidence_cited():
    mech = ec_hand_example(ATTR)  # only a supporting item exists
    state = mech.initial_state()
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        **_withhold_all(exclude=("a1",))})
    # a2 challenges citing the supporting item -> not a contradiction -> invalid
    state, _ = step(mech, state, {
        "a2": ChallengeClaimAction(claim_id="c1", evidence_ids=("e1",)),
        **_withhold_all(exclude=("a2",))})
    assert state["claims"]["c1"]["challenges"] == [
        {"agent": "a2", "valid": False, "cited": ["e1"]}]


def test_acceptance_requires_net_support_at_least_one():
    mech = ec_hand_example(ATTR)
    state = mech.initial_state()
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        **_withhold_all(exclude=("a1",))})
    # no verification yet -> net_support 0 -> not accepted
    briefing = mech.final_briefing(state)
    assert briefing == [{"slot_id": "s1", "claim_id": None}]


def test_acceptance_tie_breaks_to_earliest_claim():
    # Two competing claims for the same slot, each net_support 1; earliest wins.
    e_a = make_evidence("e_a", "s1", "p1a", "supports", "p1a", holders=("a1", "a2", "a3"))
    e_b = make_evidence("e_b", "s1", "p1b", "supports", "p1a", holders=("a1", "a2", "a3"))
    spec = ECWorldSpec(agent_ids=AGENTS, slots={"s1": ("p1a", "p1b")},
                       true_propositions={"s1": "p1a"}, evidence=(e_a, e_b))
    mech = EvidenceCommonsMechanism(spec=spec, institution=ATTR)
    state = mech.initial_state()
    # round0: a1 proposes p1a (c1), a2 proposes p1b (c2)
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e_a",)),
        "a2": ProposeClaimAction(slot_id="s1", proposition_id="p1b", evidence_ids=("e_b",)),
        "a3": WithholdAction()})
    # round1: a3 verifies both -> each net_support 1
    state, _ = step(mech, state, {
        "a3": VerifyClaimAction(claim_id="c1"), "a1": WithholdAction(), "a2": WithholdAction()})
    state, _ = step(mech, state, {
        "a3": VerifyClaimAction(claim_id="c2"), "a1": WithholdAction(), "a2": WithholdAction()})
    briefing = mech.final_briefing(state)
    entry = briefing[0]
    assert entry["net_support"] == 1
    assert entry["claim_id"] == "c1"  # earliest wins the tie
    assert entry["proposition_id"] == "p1a"


def _drive_hand_example(institution):
    """a1 proposes c1 citing e1; a2 verifies (supported). Others withhold."""
    mech = ec_hand_example(institution)
    state = mech.initial_state()
    state, _ = step(mech, state, {
        "a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
        **_withhold_all(exclude=("a1",))})
    state, _ = step(mech, state, {
        "a2": VerifyClaimAction(claim_id="c1"), **_withhold_all(exclude=("a2",))})
    return mech, state


def test_final_rewards_attributable_exact_fractions():
    mech, state = _drive_hand_example(ATTR)
    fr = mech.final_rewards(state)
    # quality = +12 (correct slot); credits a1 +3 (propose), a2 +2 (verify supported)
    assert fr["collective_quality"] == 12
    assert fr["individual_credit"] == {"a1": "3", "a2": "2", "a3": "0"}
    assert fr["effort"] == {"a1": 1, "a2": 2, "a3": 0}
    # utility = credit + quality/3 - effort;  quality/3 = 4
    assert fr["utility"] == {"a1": "6", "a2": "4", "a3": "4"}


def test_final_rewards_aggregate_pools_credit_exact_fractions():
    mech, state = _drive_hand_example(AGG)
    fr = mech.final_rewards(state)
    assert fr["collective_quality"] == 12
    # pool = 3 + 2 + 0 = 5, split /3 -> 5/3 each
    assert fr["individual_credit"] == {"a1": "5/3", "a2": "5/3", "a3": "5/3"}
    assert fr["effort"] == {"a1": 1, "a2": 2, "a3": 0}
    # utility = 5/3 + 4 - effort
    assert fr["utility"] == {"a1": "14/3", "a2": "11/3", "a3": "17/3"}
