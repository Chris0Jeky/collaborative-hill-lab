"""Literal oracles committed in ec-rule-ablation/DESIGN.md before execution."""

import copy
import itertools
from fractions import Fraction

import pytest
from _fixtures import make_evidence, step

from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
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

NAME = "ec_ablation_contributor"
AGENTS = ("a1", "a2", "a3")
FACTORS = ("evidence_screen", "share_contradictions", "challenge_claims",
           "require_read_citation")
BITS = tuple(itertools.product((False, True), repeat=4))
PARAMS = {"min_sources": 2, "peer_threshold": "1", "warmup_rounds": 9,
          "share_evidence": True}


def policy(bits=(True,) * 4, **overrides):
    return build_ec_policy(NAME, {**PARAMS, **dict(zip(FACTORS, bits, strict=True)), **overrides})


def world(structure="corroborated", topology="private", accountability="attributable",
          truth="accurate", probe=False):
    slots = ("s1",) if probe else ("s1", "s2")
    true = {s: f"{s}-{'p' if truth == 'accurate' else 'q'}" for s in slots}
    evidence = []
    for slot in slots:
        for letter, original_holder in zip("abc", AGENTS, strict=True):
            stance = "contradicts" if structure == "conflicted" and letter == "c" else "supports"
            holder = original_holder
            if probe:
                holder = "a1" if letter == "c" else "a3"
            evidence.append(make_evidence(
                f"e{slot[1]}{letter}", slot, f"{slot}-p", stance, true[slot],
                holders=(holder,), source="src-a" if structure == "echo" else f"src-{letter}"))
    return EvidenceCommonsMechanism(
        spec=ECWorldSpec(agent_ids=AGENTS, slots={s: (f"{s}-p", f"{s}-q") for s in slots},
                    true_propositions=true, evidence=tuple(evidence),
                    params=ECParams(rounds=14, inspect_budget=2 if probe else 6, verify_budget=3)),
        institution=InstitutionConfig(accountability=accountability, evidence_topology=topology),
    )


def label(action):
    if isinstance(action, InspectEvidenceAction):
        return f"I {action.evidence_id}"
    if isinstance(action, ShareEvidenceAction):
        return f"S {action.evidence_id}"
    if isinstance(action, ProposeClaimAction):
        return f"P {action.slot_id}:{','.join(action.evidence_ids)}"
    if isinstance(action, VerifyClaimAction):
        return f"V {action.claim_id}"
    if isinstance(action, ChallengeClaimAction):
        return f"X {action.claim_id}"
    assert isinstance(action, WithholdAction)
    return "-"


def run(mechanism, policies, shadow=None):
    state = mechanism.initial_state()
    schedule = []
    while not mechanism.is_terminal(state):
        actions = {}
        for agent in AGENTS:
            observation = mechanism.observe(state, agent)
            actions[agent] = policies[agent].propose(observation, None).action
            if shadow:
                assert actions[agent] == shadow.propose(observation, None).action
            assert mechanism.validate_action(state, agent, actions[agent]) is None
        schedule.append(tuple(label(actions[a]) for a in AGENTS))
        state = step(mechanism, state, actions)[0]
    return schedule, mechanism.final_rewards(state)


@pytest.mark.parametrize("bits", BITS)
@pytest.mark.parametrize("truth", ("accurate", "misleading"))
def test_t1_unread_citation_literal_trace(bits, truth):
    policies = {"a1": build_ec_policy("ec_contributor", {}),
                "a2": build_ec_policy("ec_freerider", {}), "a3": policy(bits)}
    schedule, rewards = run(world(probe=True, truth=truth), policies)
    assert schedule == [
        ("I e1c", "-", "I e1a"), ("S e1c", "-", "I e1b"),
        ("P s1:e1c", "-", "S e1a"), ("I e1a", "-", "S e1b"),
        ("-", "-", "-" if bits[3] else "V c1"), *[("-",) * 3] * 9,
    ]
    if bits[3]:
        assert rewards["collective_quality"] == 0
        assert rewards["effort"] == {"a1": 4, "a2": 0, "a3": 4}
        assert rewards["utility"] == {"a1": "-4", "a2": "0", "a3": "-4"}
    else:
        assert rewards["collective_quality"] == (12 if truth == "accurate" else -12)
        assert rewards["effort"] == {"a1": 4, "a2": 0, "a3": 6}
        assert rewards["utility"] == (
            {"a1": "3", "a2": "4", "a3": "0"} if truth == "accurate"
            else {"a1": "-11", "a2": "-4", "a3": "-12"})


@pytest.mark.parametrize("on,legacy", [(False, "ec_conditional_contributor"),
                                      (True, "ec_skeptical_contributor")])
@pytest.mark.parametrize("structure", ("corroborated", "conflicted", "echo"))
@pytest.mark.parametrize("topology", ("private", "shared_ledger"))
@pytest.mark.parametrize("accountability", ("aggregate", "attributable"))
def test_endpoints_match_unchanged_v1_actions(on, legacy, structure, topology, accountability):
    params = PARAMS if on else {k: v for k, v in PARAMS.items() if k != "min_sources"}
    oracle = build_ec_policy(legacy, params)
    candidate = policy((on,) * 4)
    assert candidate.policy_id != oracle.policy_id
    run(world(structure, topology, accountability), dict.fromkeys(AGENTS, candidate), oracle)


@pytest.mark.parametrize("factor", FACTORS)
@pytest.mark.parametrize("bad", (0, 1, None, "yes", "", 1.0, [], {}))
def test_factor_contract_rejects_truthiness(factor, bad):
    with pytest.raises(ValueError, match=factor):
        coerce_policy_params(NAME, {factor: bad})
    with pytest.raises(ValueError, match=factor):
        policy(**{factor: bad})


def test_registry_canonical_identity_without_normalizing_spec():
    params = {"evidence_screen": "FALSE", "require_read_citation": "false",
              "peer_threshold": "2/4", "min_sources": "2"}
    assert PolicySpec(name=NAME, params=params).params == params
    candidate = build_ec_policy(NAME, params)
    assert candidate.policy_id == (
        "ec_ablation_contributor[screen=False,share_contradictions=True,challenge=True,"
        "read_citation=False,min_sources=2,peer_threshold=1/2,warmup=3,share=True]@1")
    assert coerce_policy_params(NAME, {"require_read_citation": "TrUe"}) == {
        "require_read_citation": True}
    with pytest.raises(ValueError, match="unknown param"):
        policy(unknown=True)


def ready_observation(structure="corroborated", *, citation="e1c", read=("e1a", "e1b")):
    mechanism = world(structure, "shared_ledger", probe=True)
    state = step(mechanism, mechanism.initial_state(), {"a1": ProposeClaimAction(
        slot_id="s1", proposition_id="s1-p", evidence_ids=(citation,))})[0]
    state["inspected"]["a3"] = list(read)
    state["budgets"]["a3"]["inspect"] = 0
    return mechanism.observe(state, "a3")


@pytest.mark.parametrize("screen,read_gate", tuple(itertools.product((False, True), repeat=2)))
def test_screen_and_read_gate_are_independent(screen, read_gate):
    observation = ready_observation()
    action = policy((screen, False, False, read_gate)).propose(observation, None).action
    assert action == (WithholdAction() if read_gate else VerifyClaimAction(claim_id="c1"))
    observation = ready_observation("echo", citation="e1a")
    action = policy((screen, False, False, read_gate)).propose(observation, None).action
    assert action == (WithholdAction() if screen else VerifyClaimAction(claim_id="c1"))


@pytest.mark.parametrize("screen,read_gate", tuple(itertools.product((False, True), repeat=2)))
def test_challenge_toggle_is_independent_and_self_excluding(screen, read_gate):
    observation = ready_observation("conflicted", read=("e1a", "e1b", "e1c"))
    assert policy((screen, False, True, read_gate)).propose(observation, None).action == (
        ChallengeClaimAction(claim_id="c1", evidence_ids=("e1c",)))
    disabled = policy((screen, False, False, read_gate))
    assert not isinstance(disabled.propose(observation, None).action, ChallengeClaimAction)
    for field in ("proposed_by_me", "challenged_by_me"):
        changed = copy.deepcopy(observation)
        changed["claims"][0][field] = True
        assert not isinstance(policy((screen, False, True, read_gate)).propose(
            changed, None).action, ChallengeClaimAction)


def test_read_gate_checks_fresh_support_for_this_slot_and_proposition():
    observation = ready_observation(citation="e1a")
    assert policy((False, False, False, True)).propose(observation, None).action == (
        VerifyClaimAction(claim_id="c1"))
    for field, value in (("freshness", "stale"), ("stance", "contradicts"),
                         ("proposition_id", "s1-q"), ("slot_id", "other")):
        changed = copy.deepcopy(observation)
        changed["evidence"][0]["facts"][field] = value
        assert policy((False, False, False, True)).propose(changed, None).action != (
            VerifyClaimAction(claim_id="c1"))


def test_sharing_switch_adds_only_fresh_contradictions():
    mechanism = world("conflicted", probe=True)
    state = mechanism.initial_state()
    state["inspected"]["a1"] = ["e1c"]
    observation = mechanism.observe(state, "a1")
    assert policy((False, True, False, False)).propose(observation, None).action == (
        ShareEvidenceAction(evidence_id="e1c"))
    assert policy((False, False, False, False)).propose(observation, None).action == (
        WithholdAction())
    assert policy(share_evidence=False).propose(observation, None).action == WithholdAction()
    observation["evidence"][0]["facts"]["freshness"] = "stale"
    assert policy().propose(observation, None).action == WithholdAction()


def test_exact_quorum_boundary_and_budget_gate_precede_actions():
    observation = ready_observation(citation="e1a")
    observation["round"] = 9
    assert policy(peer_threshold="1/2").propose(observation, None).action == (
        VerifyClaimAction(claim_id="c1"))
    assert policy(peer_threshold="5001/10000").propose(observation, None).action == WithholdAction()
    observation["my_budgets"]["verify"] = 0
    assert policy(peer_threshold=Fraction(1, 2)).propose(observation, None).action == (
        WithholdAction())


def test_pure_observation_rule_ignores_rng_truth_reward_and_reconstruction():
    observation = ready_observation(citation="e1a")
    before = copy.deepcopy(observation)
    candidate = policy()
    first = candidate.propose(observation, object())
    assert candidate.propose(observation, object()) == first
    assert policy().propose(observation, object()) == first
    assert observation == before
    observation.update(true_propositions={"s1": "s1-q"}, reward_weight=-1000)
    assert candidate.propose(observation, object()) == first
