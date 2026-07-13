"""Observation topology: EC private vs shared_ledger visibility, and NIPD
neighbourhood (counts only) vs pairwise (moves against me only)."""

from collaborative_hill.domain.actions import (
    InspectEvidenceAction,
    ShareEvidenceAction,
    WithholdAction,
)
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import (
    ECWorldSpec,
    EvidenceCommonsMechanism,
)

from _fixtures import AGENTS, ec_hand_example, make_evidence, neighbourhood_actions, nipd, step


def _evidence_ids(obs):
    return {e["evidence_id"] for e in obs["evidence"]}


# -- EC private topology --------------------------------------------------------


def test_private_topology_hides_item_from_non_holder():
    # e1 held by a1, a2 only.
    mech = ec_hand_example(InstitutionConfig(evidence_topology="private"))
    state = mech.initial_state()
    assert "e1" in _evidence_ids(mech.observe(state, "a1"))
    assert "e1" in _evidence_ids(mech.observe(state, "a2"))
    # a3 is not a holder: the item is absent from its observation entirely.
    a3_obs = mech.observe(state, "a3")
    assert "e1" not in _evidence_ids(a3_obs)
    assert a3_obs["evidence"] == []


def test_share_makes_item_appear_to_non_holder():
    mech = ec_hand_example(InstitutionConfig(evidence_topology="private"))
    state = mech.initial_state()
    assert "e1" not in _evidence_ids(mech.observe(state, "a3"))
    # a1 shares e1 -> becomes visible to all
    state, _ = step(mech, state, {
        "a1": ShareEvidenceAction(evidence_id="e1"),
        "a2": WithholdAction(), "a3": WithholdAction()})
    a3_obs = mech.observe(state, "a3")
    assert "e1" in _evidence_ids(a3_obs)
    # visible but not yet inspected -> no facts leaked
    entry = next(e for e in a3_obs["evidence"] if e["evidence_id"] == "e1")
    assert "facts" not in entry
    assert entry["public"] is True


def test_shared_ledger_lists_all_ids_from_round_zero_facts_only_after_inspection():
    mech = ec_hand_example(InstitutionConfig(evidence_topology="shared_ledger"))
    state = mech.initial_state()
    # every agent sees the item id from round 0, even a non-holder like a3
    a3_obs = mech.observe(state, "a3")
    assert "e1" in _evidence_ids(a3_obs)
    entry = next(e for e in a3_obs["evidence"] if e["evidence_id"] == "e1")
    assert "facts" not in entry  # content still gated by inspection
    # a3 inspects, then facts appear
    state, _ = step(mech, state, {
        "a3": InspectEvidenceAction(evidence_id="e1"),
        "a1": WithholdAction(), "a2": WithholdAction()})
    entry = next(e for e in mech.observe(state, "a3")["evidence"]
                 if e["evidence_id"] == "e1")
    assert "facts" in entry
    assert entry["facts"]["proposition_id"] == "p1a"


# -- NIPD neighbourhood: counts only, no identities -----------------------------


def test_neighbourhood_observation_is_count_not_identity():
    mech = nipd("neighbourhood", rounds=5)
    state = mech.initial_state()
    # first round: no history
    obs0 = mech.observe(state, "a1")
    assert obs0["others_cooperated_last_round"] is None
    assert obs0["my_last_move"] is None
    # play a1=C, a2=C, a3=D
    state, _ = step(mech, state, neighbourhood_actions({"a1": "C", "a2": "C", "a3": "D"}))
    obs = mech.observe(state, "a1")
    # a1 sees a COUNT of other cooperators (a2 cooperated) = 1, and its own move
    assert obs["others_cooperated_last_round"] == 1
    assert obs["my_last_move"] == "C"
    # no other agent's identity or individual move is present anywhere
    flat = repr(obs)
    assert "a2" not in flat and "a3" not in flat
    assert "moves_against_me" not in obs
    assert "last_moves" not in obs


def test_pairwise_observation_only_moves_against_observer():
    mech = nipd("pairwise", rounds=5)
    state = mech.initial_state()
    from collaborative_hill.domain.actions import PairwiseVoteAction
    actions = {
        "a1": PairwiseVoteAction(moves={"a2": "C", "a3": "C"}),
        "a2": PairwiseVoteAction(moves={"a1": "D", "a3": "C"}),
        "a3": PairwiseVoteAction(moves={"a1": "C", "a2": "D"}),
    }
    state, _ = step(mech, state, actions)
    obs = mech.observe(state, "a1")
    # a1 sees what a2 and a3 played AGAINST a1 (a2->a1=D, a3->a1=C)
    assert obs["moves_against_me"] == {"a2": "D", "a3": "C"}
    # a1 sees its own moves too
    assert obs["my_last_moves"] == {"a2": "C", "a3": "C"}
    # a1 must NOT learn the a2<->a3 game (a2->a3 or a3->a2)
    # a2 played C against a3, a3 played D against a2 — neither may appear as a value
    assert obs["moves_against_me"].get("a2") == "D"  # against a1, not against a3
    # opponents list carries ids (that is legal — they are the observer's opponents)
    assert set(obs["opponents"]) == {"a2", "a3"}
    # cross-pair info absent: no nested full move table
    assert "last_moves" not in obs
    assert set(obs["moves_against_me"].keys()) == {"a2", "a3"}
