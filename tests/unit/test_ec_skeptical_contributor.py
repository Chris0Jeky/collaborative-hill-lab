"""Hand-derived traces and observation boundary of the skeptical contributor.

The T1-T5 literals are copied from experiments/quality-safeguards/DESIGN.md, which
was committed before the rule existed. Worlds use neutral proposition ids so the
accurate and misleading corpora differ only in hidden fields.
"""

import copy
import random
from fractions import Fraction

import pytest
from _fixtures import make_evidence, step
from pydantic import ValidationError

from collaborative_hill.agents.scripted import ec_policies
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import (
    ChallengeClaimAction,
    InspectEvidenceAction,
    ProposeClaimAction,
    ShareEvidenceAction,
    VerifyClaimAction,
    WithholdAction,
)
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import (
    ECParams,
    ECWorldSpec,
    EvidenceCommonsMechanism,
)
from collaborative_hill.experiments.scenario import PolicySpec

NAME = "ec_skeptical_contributor"
AGENTS = ("a1", "a2", "a3")
HOLDERS = {"a": "a1", "b": "a2", "c": "a3"}
PARAMS = {"min_sources": 2, "peer_threshold": "1", "warmup_rounds": 9, "share_evidence": True}


def world(structure="corroborated", truth="accurate", topology="private",
          accountability="attributable"):
    true_suffix = "p" if truth == "accurate" else "q"
    truths = {s: f"{s}-{true_suffix}" for s in ("s1", "s2")}
    evidence = []
    for slot in ("s1", "s2"):
        for letter, holder in HOLDERS.items():
            stance = "contradicts" if structure == "conflicted" and letter == "c" else "supports"
            source = "src-a" if structure == "echo" else f"src-{letter}"
            evidence.append(make_evidence(f"e{slot[1]}{letter}", slot, f"{slot}-p", stance,
                                          truths[slot], holders=(holder,), source=source))
    return EvidenceCommonsMechanism(
        spec=ECWorldSpec(
            agent_ids=AGENTS, slots={s: (f"{s}-p", f"{s}-q") for s in ("s1", "s2")},
            true_propositions=truths, evidence=tuple(evidence),
            params=ECParams(rounds=14, inspect_budget=6, verify_budget=3),
        ),
        institution=InstitutionConfig(accountability=accountability, evidence_topology=topology),
    )


def skeptical(**overrides):
    return ec_policies.build_ec_policy(NAME, {**PARAMS, **overrides})


def conditional():
    return ec_policies.build_ec_policy(
        "ec_conditional_contributor",
        {"peer_threshold": "1", "warmup_rounds": 9, "share_evidence": True})


def label(action):
    if isinstance(action, InspectEvidenceAction):
        return f"I {action.evidence_id}"
    if isinstance(action, ShareEvidenceAction):
        return f"S {action.evidence_id}"
    if isinstance(action, ProposeClaimAction):
        return f"P {action.slot_id}"
    if isinstance(action, VerifyClaimAction):
        return f"V {action.claim_id}"
    if isinstance(action, ChallengeClaimAction):
        return f"X {action.claim_id}"
    assert isinstance(action, WithholdAction)
    return "-"


def run(mechanism, policies):
    """Full episode through real observations; returns the schedule and rewards."""
    state = mechanism.initial_state()
    schedule = []
    while not mechanism.is_terminal(state):
        actions = {agent: policies[agent].propose(mechanism.observe(state, agent), None).action
                   for agent in AGENTS}
        assert all(mechanism.validate_action(state, agent, action) is None
                   for agent, action in actions.items())
        schedule.append(tuple(label(actions[agent]) for agent in AGENTS))
        state = step(mechanism, state, actions)[0]
    return schedule, mechanism.final_rewards(state)


FREERIDER = ec_policies.ECFreeriderPolicy()
READ_S1 = [("I e1a", "I e1b", "I e1c"), ("I e2a", "I e2b", "I e2c"), ("S e1a", "S e1b", "S e1c"),
           ("I e1b", "I e1a", "I e1a"), ("I e1c", "I e1c", "I e1b"), ("S e2a", "S e2b", "S e2c"),
           ("I e2b", "I e2a", "I e2a"), ("I e2c", "I e2c", "I e2b")]
T1 = READ_S1 + [("P s1",) * 3, ("P s2",) * 3, ("V c2", "V c1", "V c1"),
                ("V c3", "V c3", "V c2"), ("V c5", "V c4", "V c4"), ("-",) * 3]


@pytest.mark.parametrize("truth,quality,utility", [
    ("accurate", 24, {"a1": "-2", "a2": "-4", "a3": "-4"}),
    ("misleading", -24, {"a1": "-30", "a2": "-28", "a3": "-28"}),
])
def test_t1_corroboration_passes_whichever_way_truth_lies(truth, quality, utility):
    schedule, rewards = run(world(truth=truth), dict.fromkeys(AGENTS, skeptical()))
    assert schedule == T1
    assert rewards["collective_quality"] == quality
    assert rewards["utility"] == utility
    assert rewards["effort"] == {"a1": 16, "a2": 16, "a3": 16}


@pytest.mark.parametrize("truth", ["accurate", "misleading"])
@pytest.mark.parametrize("accountability", ["aggregate", "attributable"])
def test_t2_contradiction_vetoes_claims_but_not_the_cost_of_reading(truth, accountability):
    schedule, rewards = run(world("conflicted", truth, accountability=accountability),
                            dict.fromkeys(AGENTS, skeptical()))
    assert schedule == READ_S1 + [("-",) * 3] * 6
    assert rewards["collective_quality"] == 0
    assert rewards["utility"] == dict.fromkeys(AGENTS, "-8")


def test_t3_anonymous_history_stops_the_control_and_attribution_does_not():
    schedule, rewards = run(world(accountability="aggregate"),
                            dict.fromkeys(AGENTS, conditional()))
    assert schedule == READ_S1 + [("P s1",) * 3] + [("-",) * 3] * 5
    assert rewards["collective_quality"] == 0
    assert rewards["effort"] == dict.fromkeys(AGENTS, 9)
    assert run(world(), dict.fromkeys(AGENTS, conditional()))[0] == T1


@pytest.mark.parametrize("truth,quality,utility", [
    ("accurate", 12, {"a1": "-3", "a2": "-4", "a3": "4"}),
    ("misleading", -12, {"a1": "-17", "a2": "-16", "a3": "-4"}),
])
def test_t4_contradiction_held_by_a_free_rider_never_reaches_the_screen(truth, quality, utility):
    policies = {"a1": skeptical(), "a2": skeptical(), "a3": FREERIDER}
    schedule, rewards = run(world("conflicted", truth), policies)
    assert [row[:2] for row in schedule] == [
        ("I e1a", "I e1b"), ("I e2a", "I e2b"), ("S e1a", "S e1b"), ("I e1b", "I e1a"),
        ("S e2a", "S e2b"), ("I e2b", "I e2a"), ("P s1", "P s1"), ("P s2", "P s2"),
        ("V c2", "V c1"), *[("-", "-")] * 5,
    ]
    assert rewards["collective_quality"] == quality
    assert rewards["utility"] == utility
    assert rewards["effort"] == {"a1": 10, "a2": 10, "a3": 0}


def test_t4_shared_ledger_exposes_the_same_contradiction():
    policies = {"a1": skeptical(), "a2": skeptical(), "a3": FREERIDER}
    _, rewards = run(world("conflicted", "misleading", "shared_ledger"), policies)
    assert rewards["collective_quality"] == 0


T5_PREFIX = [("I e1a", "I e1b", "I e1c"), ("I e2a", "I e2b", "I e2c"),
             ("S e1a", "S e1b", "S e1c"), ("I e1b", "I e1a", "I e1a"),
             ("I e1c", "I e1c", "I e1b"), ("S e2a", "S e2b", "S e2c"),
             ("I e2b", "I e2a", "I e2a"), ("I e2c", "I e2c", "I e2b"),
             ("P s1", "P s1", "-")]


def defended(truth, accountability):
    naive = ec_policies.ECContributorPolicy()
    return run(world("conflicted", truth, accountability=accountability),
               {"a1": naive, "a2": naive, "a3": skeptical()})


@pytest.mark.parametrize("truth", ["accurate", "misleading"])
def test_t5_one_named_skeptic_blocks_every_claim_true_or_false(truth):
    schedule, rewards = defended(truth, "attributable")
    assert schedule == T5_PREFIX + [
        ("P s2", "P s2", "X c1"), ("V c2", "V c1", "X c2"), ("V c4", "V c3", "X c3"),
        ("-", "-", "X c4"), ("-", "-", "-"),
    ]
    assert rewards["collective_quality"] == 0
    assert rewards["effort"] == {"a1": 14, "a2": 14, "a3": 12}


@pytest.mark.parametrize("truth,quality", [("accurate", 12), ("misleading", -12)])
def test_t5_anonymous_skeptic_starts_too_late_and_one_claim_survives(truth, quality):
    schedule, rewards = defended(truth, "aggregate")
    assert schedule == T5_PREFIX + [
        ("P s2", "P s2", "-"), ("V c2", "V c1", "-"), ("V c4", "V c3", "X c1"),
        ("-", "-", "X c2"), ("-", "-", "X c3"),
    ]
    assert rewards["collective_quality"] == quality


def test_echoed_source_label_is_not_corroboration():
    schedule, rewards = run(world("echo"), dict.fromkeys(AGENTS, skeptical()))
    assert schedule == READ_S1 + [("-",) * 3] * 6
    assert rewards["collective_quality"] == 0
    assert run(world("echo"), dict.fromkeys(AGENTS, skeptical(min_sources=1)))[0] == T1


def reads(mechanism, agent="a1", *items):
    """Observation in which agent has inspected the items, nothing else done."""
    state = mechanism.initial_state()
    state["inspected"][agent] = list(items)
    return mechanism.observe(state, agent)


def custom(evidence, *, inspect_budget=6):
    """One slot, three candidates, everything held by a1."""
    true_prop = "s1-p"
    return EvidenceCommonsMechanism(
        spec=ECWorldSpec(
            agent_ids=AGENTS, slots={"s1": ("s1-p", "s1-q", "s1-r")},
            true_propositions={"s1": true_prop},
            evidence=tuple(
                make_evidence(eid, "s1", prop, stance, true_prop, holders=("a1",),
                              source=source, freshness=freshness)
                for eid, prop, stance, source, freshness in evidence),
            params=ECParams(rounds=4, inspect_budget=inspect_budget, verify_budget=3),
        ),
        institution=InstitutionConfig(evidence_topology="shared_ledger"),
    )


SUPPORT = [("e1", "s1-p", "supports", "src-1", "fresh"),
           ("e2", "s1-p", "supports", "src-2", "fresh")]


@pytest.mark.parametrize("extra,passes", [
    ([], True),
    ([("e3", "s1-p", "contradicts", "src-3", "fresh")], False),
    ([("e3", "s1-q", "supports", "src-3", "fresh")], False),
    # Stale items carry no engine weight, so they do not veto either.
    ([("e3", "s1-p", "contradicts", "src-3", "stale")], True),
    ([("e3", "s1-q", "supports", "src-3", "stale")], True),
    # Disagreement about a rival is not disagreement with p.
    ([("e3", "s1-q", "contradicts", "src-3", "fresh")], True),
])
def test_screen_clauses(extra, passes):
    mechanism = custom(SUPPORT + extra)
    ids = [item[0] for item in SUPPORT + extra]
    assert skeptical(peer_threshold="0").passes_screen(
        reads(mechanism, "a1", *ids), "s1", "s1-p") is passes


def test_screen_counts_distinct_fresh_labels_at_the_exact_boundary():
    same_source = [("e1", "s1-p", "supports", "src-1", "fresh"),
                   ("e2", "s1-p", "supports", "src-1", "fresh"),
                   ("e3", "s1-p", "supports", "src-2", "stale")]
    observation = reads(custom(same_source), "a1", "e1", "e2", "e3")
    assert skeptical(min_sources=1).passes_screen(observation, "s1", "s1-p")
    assert not skeptical(min_sources=2).passes_screen(observation, "s1", "s1-p")


def test_visible_but_unread_contradiction_is_not_a_signal():
    mechanism = custom(SUPPORT + [("e3", "s1-p", "contradicts", "src-3", "fresh")])
    observation = reads(mechanism, "a1", "e1", "e2")
    assert "facts" not in observation["evidence"][2]
    assert skeptical().passes_screen(observation, "s1", "s1-p")


def test_budget_exhaustion_can_pass_a_claim_reading_would_veto():
    # Declared limit: stops reading at budget, and acts on what was read.
    mechanism = custom(SUPPORT + [("e3", "s1-p", "contradicts", "src-3", "fresh")],
                       inspect_budget=2)
    state = mechanism.initial_state()
    state["inspected"]["a1"] = ["e1", "e2"]
    state["budgets"]["a1"]["inspect"] = 0
    action = skeptical(peer_threshold="0").propose(mechanism.observe(state, "a1"), None).action
    assert action == ProposeClaimAction(slot_id="s1", proposition_id="s1-p",
                                        evidence_ids=("e1", "e2"))


def test_stale_support_is_neither_shared_nor_cited():
    evidence = SUPPORT + [("e3", "s1-p", "supports", "src-3", "stale")]
    mechanism = custom(evidence)
    observation = reads(mechanism, "a1", "e1", "e2", "e3")
    action = skeptical(peer_threshold="0").propose(observation, None).action
    assert action == ProposeClaimAction(slot_id="s1", proposition_id="s1-p",
                                        evidence_ids=("e1", "e2"))


def test_verification_requires_a_cited_item_i_have_read():
    mechanism = world(topology="shared_ledger")
    state = mechanism.initial_state()
    claim = ProposeClaimAction(slot_id="s1", proposition_id="s1-p", evidence_ids=("e1c",))
    state = step(mechanism, state, {"a2": claim})[0]
    state["inspected"]["a1"] = ["e1a", "e1b"]
    state["budgets"]["a1"]["inspect"] = 0
    # The proposition passes my screen, but I read none of the claim's citations.
    observation = mechanism.observe(state, "a1")
    policy = skeptical(peer_threshold="0")
    assert policy.passes_screen(observation, "s1", "s1-p")
    assert policy.propose(observation, None).action == WithholdAction()
    state["inspected"]["a1"].append("e1c")
    assert policy.propose(mechanism.observe(state, "a1"), None).action == (
        VerifyClaimAction(claim_id="c1"))


def test_challenge_cites_all_contradictions_and_precedes_my_own_proposal():
    mechanism = custom(SUPPORT + [("e3", "s1-p", "contradicts", "src-3", "fresh"),
                                  ("e4", "s1-p", "contradicts", "src-4", "fresh")])
    state = mechanism.initial_state()
    state = step(mechanism, state, {"a2": ProposeClaimAction(
        slot_id="s1", proposition_id="s1-p", evidence_ids=("e1",))})[0]
    state["inspected"]["a1"] = ["e1", "e2", "e3", "e4"]
    assert skeptical(peer_threshold="0").propose(mechanism.observe(state, "a1"), None).action == (
        ChallengeClaimAction(claim_id="c1", evidence_ids=("e3", "e4")))


def test_rule_never_challenges_its_own_claim():
    mechanism = custom(SUPPORT + [("e3", "s1-p", "contradicts", "src-3", "fresh")])
    state = mechanism.initial_state()
    state = step(mechanism, state, {"a1": ProposeClaimAction(
        slot_id="s1", proposition_id="s1-p", evidence_ids=("e1",))})[0]
    state["inspected"]["a1"] = ["e1", "e2", "e3"]
    assert skeptical(peer_threshold="0").propose(mechanism.observe(state, "a1"), None).action == (
        WithholdAction())


def test_quorum_gate_matches_the_conditional_rule_after_warmup():
    mechanism = world(accountability="aggregate")
    state = mechanism.initial_state()
    state["round"] = 9
    observation = mechanism.observe(state, "a1")
    assert skeptical().propose(observation, None).action == WithholdAction()
    assert skeptical(peer_threshold="0").propose(observation, None).action == (
        InspectEvidenceAction(evidence_id="e1a"))


@pytest.mark.parametrize("structure", ["corroborated", "conflicted", "echo"])
@pytest.mark.parametrize("topology", ["private", "shared_ledger"])
@pytest.mark.parametrize("accountability", ["aggregate", "attributable"])
def test_truth_flip_leaves_every_observation_of_a_real_episode_identical(
        structure, topology, accountability):
    good = world(structure, "accurate", topology, accountability)
    bad = world(structure, "misleading", topology, accountability)
    policy = skeptical(peer_threshold="0")
    good_state, bad_state = good.initial_state(), bad.initial_state()
    while not good.is_terminal(good_state):
        actions = {}
        for agent in AGENTS:
            observation = good.observe(good_state, agent)
            assert observation == bad.observe(bad_state, agent)
            assert "truth_aligned" not in repr(observation)
            assert "true_propositions" not in repr(observation)
            actions[agent] = policy.propose(observation, None).action
        good_state = step(good, good_state, actions)[0]
        bad_state = step(bad, bad_state, actions)[0]


def test_unused_observation_fields_do_not_change_decisions():
    mechanism = world(structure="conflicted", topology="shared_ledger")
    observation = reads(mechanism, "a1", "e1a", "e1b", "e1c", "e2a", "e2b", "e2c")
    policy = skeptical(peer_threshold="0")
    original = policy.propose(observation, None)
    tampered = copy.deepcopy(observation)
    tampered.update({"accountability": "aggregate", "my_credit": -999, "my_effort_spent": 999})
    for item in tampered["evidence"]:
        item["facts"]["version"] = 7
    assert policy.propose(tampered, None) == original


def test_renaming_actors_sources_and_propositions_preserves_the_decision():
    mechanism = world(structure="conflicted", topology="shared_ledger")
    state = mechanism.initial_state()
    state = step(mechanism, state, {"a2": ProposeClaimAction(
        slot_id="s1", proposition_id="s1-p", evidence_ids=("e1a", "e1b"))})[0]
    state["inspected"]["a1"] = ["e1a", "e1b", "e1c", "e2a", "e2b", "e2c"]
    observation = mechanism.observe(state, "a1")
    renamed = copy.deepcopy(observation)
    actors = {"a1": "z9", "a2": "z1", "a3": "z5"}
    sources = {"src-a": "src-c", "src-b": "src-a", "src-c": "src-b"}
    propositions = {"s1-p": "s1-q", "s1-q": "s1-p", "s2-p": "s2-q", "s2-q": "s2-p"}
    renamed["self_id"] = actors["a1"]
    renamed["slots"] = {slot: [propositions[p] for p in candidates]
                        for slot, candidates in renamed["slots"].items()}
    for item in renamed["evidence"]:
        item["source_id"] = sources[item["source_id"]]
        item["facts"]["source_id"] = sources[item["facts"]["source_id"]]
        item["facts"]["proposition_id"] = propositions[item["facts"]["proposition_id"]]
    for item in renamed["claims"]:
        item["proposition_id"] = propositions[item["proposition_id"]]
        item["proposer"] = actors[item["proposer"]]
    policy = skeptical(peer_threshold="0")
    assert policy.propose(renamed, None).action == policy.propose(observation, None).action == (
        ChallengeClaimAction(claim_id="c1", evidence_ids=("e1c",)))


def test_policy_is_observation_pure_rng_free_and_reconstructible():
    mechanism = world()
    observation = reads(mechanism, "a1", "e1a", "e2a")
    before = copy.deepcopy(observation)
    rng = random.Random(123)
    rng_state = rng.getstate()
    policy = skeptical()
    expected = policy.propose(observation, rng)
    policy.propose(mechanism.observe(mechanism.initial_state(), "a2"), rng)
    assert policy.propose(observation, rng) == expected
    assert skeptical().propose(observation, rng) == expected
    assert observation == before
    assert rng.getstate() == rng_state


@pytest.mark.parametrize("params", [
    {"min_sources": 0}, {"min_sources": -1}, {"min_sources": True}, {"min_sources": 2.0},
    {"min_sources": "two"}, {"peer_threshold": 0.5}, {"peer_threshold": "3/2"},
    {"warmup_rounds": -1}, {"share_evidence": "yes"}, {"min_source": 2},
])
def test_shared_contract_rejects_bad_params_before_policy_use(params):
    key = next(iter(params))
    with pytest.raises(ValueError, match=key):
        coerce_policy_params(NAME, params)
    with pytest.raises(ValidationError, match=key):
        PolicySpec(name=NAME, params=params)
    with pytest.raises(ValueError, match=key):
        ec_policies.build_ec_policy(NAME, params)


def test_identity_is_versioned_canonical_and_leaves_controls_untouched():
    assert ec_policies.build_ec_policy(NAME, {}).policy_id == (
        "ec_skeptical_contributor[min_sources=2,peer_threshold=1/2,warmup=3,share=True]@1")
    assert skeptical(peer_threshold="2/2", min_sources="3").policy_id == (
        "ec_skeptical_contributor[min_sources=3,peer_threshold=1,warmup=9,share=True]@1")
    assert coerce_policy_params(NAME, {"min_sources": "2", "peer_threshold": "1/2"}) == {
        "min_sources": 2, "peer_threshold": Fraction(1, 2)}
    assert conditional().policy_id == (
        "ec_conditional_contributor[peer_threshold=1,warmup=9,share=True]@1")
    assert ec_policies.ECContributorPolicy().policy_id == "ec_contributor[share=True]@1"
