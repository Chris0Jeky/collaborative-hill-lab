"""Literal small traces for the observation-only contribution quorum."""

import copy
import random
from fractions import Fraction

import pytest
from _fixtures import make_evidence, step
from pydantic import ValidationError

from collaborative_hill.agents.scripted import ec_policies
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import (
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
from collaborative_hill.experiments.scenario import PolicySpec

NAME = "ec_conditional_contributor"
AGENTS = ("a1", "a2", "a3")


def world(accountability="attributable", topology="private", *, accurate=True):
    truth = {f"s{i}": f"p{i}{'a' if accurate else 'b'}" for i in range(1, 4)}
    return EvidenceCommonsMechanism(
        spec=ECWorldSpec(
            agent_ids=AGENTS,
            slots={f"s{i}": (f"p{i}a", f"p{i}b") for i in range(1, 4)},
            true_propositions=truth,
            evidence=tuple(
                make_evidence(f"e{i}", f"s{i}", f"p{i}a", "supports", truth[f"s{i}"],
                              holders=(f"a{i}",))
                for i in range(1, 4)
            ),
            params=ECParams(rounds=8, inspect_budget=3, verify_budget=3),
        ),
        institution=InstitutionConfig(accountability=accountability, evidence_topology=topology),
    )


def advance(mechanism, state, **active):
    actions = {agent: active.get(agent, WithholdAction()) for agent in AGENTS}
    assert all(mechanism.validate_action(state, agent, action) is None
               for agent, action in actions.items())
    return step(mechanism, state, actions)[0]


def claim(number):
    return ProposeClaimAction(slot_id=f"s{number}", proposition_id=f"p{number}a",
                              evidence_ids=(f"e{number}",))


def conditional(**params):
    return ec_policies.build_ec_policy(NAME, params)


def peer_claims(mechanism):
    return advance(mechanism, mechanism.initial_state(),
                   a1=InspectEvidenceAction(evidence_id="e1"), a2=claim(2), a3=claim(3))


def test_distinct_peer_proposals_enable_named_quorum_but_not_anonymous_quorum():
    policy = conditional(peer_threshold="1", warmup_rounds=0, share_evidence=False)
    for accountability, count, action in (
        ("attributable", 2, claim(1)), ("aggregate", 1, WithholdAction()),
    ):
        mechanism = world(accountability)
        observation = mechanism.observe(peer_claims(mechanism), "a1")
        assert ec_policies.visible_peer_contributor_count(observation) == count
        assert policy.propose(observation, None).action == action


@pytest.mark.parametrize("threshold,expected", [
    ("0", "propose_claim"), ("1/2", "propose_claim"),
    ("500000000000000001/1000000000000000000", "withhold"), ("1", "withhold"),
])
def test_anonymous_quorum_uses_exact_inclusive_fraction(threshold, expected):
    mechanism = world("aggregate")
    observation = mechanism.observe(peer_claims(mechanism), "a1")
    policy = conditional(peer_threshold=threshold, warmup_rounds=0, share_evidence=False)
    assert policy.propose(observation, None).action.type == expected


@pytest.mark.parametrize("accountability", ["aggregate", "attributable"])
def test_self_actions_do_not_count_and_a_peer_verification_can_complete_quorum(accountability):
    mechanism = world(accountability, "shared_ledger")
    state = advance(mechanism, mechanism.initial_state(), a1=claim(1), a2=claim(2))
    # c1 is mine, c2 belongs to a2. My verification of c2 adds no peer.
    state = advance(mechanism, state, a1=VerifyClaimAction(claim_id="c2"),
                    a2=VerifyClaimAction(claim_id="c1"))
    assert ec_policies.visible_peer_contributor_count(mechanism.observe(state, "a1")) == 1
    state = advance(mechanism, state, a3=VerifyClaimAction(claim_id="c1"))
    assert ec_policies.visible_peer_contributor_count(mechanism.observe(state, "a1")) == 2


def test_single_anonymous_claim_certifies_a_distinct_peer_proposer_and_verifier():
    mechanism = world("aggregate", "shared_ledger")
    state = advance(mechanism, mechanism.initial_state(), a2=claim(2))
    state = advance(mechanism, state, a3=VerifyClaimAction(claim_id="c1"))
    observation = mechanism.observe(state, "a1")
    assert "proposer" not in observation["claims"][0]
    assert "verifiers" not in observation["claims"][0]
    # Self-verification is illegal: one other proposer plus one other verifier
    # certifies two distinct peers even without knowing their names.
    assert ec_policies.visible_peer_contributor_count(observation) == 2
    assert conditional(peer_threshold="1", warmup_rounds=0).propose(
        observation, None,
    ).action == InspectEvidenceAction(evidence_id="e1")


def test_repeated_proposals_by_one_peer_never_count_as_distinct_contributors():
    for accountability in ("attributable", "aggregate"):
        mechanism = world(accountability, "shared_ledger")
        state = advance(mechanism, mechanism.initial_state(), a2=claim(2))
        state = advance(mechanism, state, a2=claim(3))
        assert ec_policies.visible_peer_contributor_count(mechanism.observe(state, "a1")) == 1


def test_attribution_is_used_as_evidence_not_as_a_treatment_label():
    mechanism = world()
    observation = mechanism.observe(peer_claims(mechanism), "a1")
    policy = conditional(peer_threshold="1", warmup_rounds=0, share_evidence=False)
    original = policy.propose(observation, None)
    observation["accountability"] = "aggregate"
    observation["my_credit"] = -999
    observation["my_effort_spent"] = 999
    assert policy.propose(observation, None) == original
    # Removing the identity fields changes what can be established, regardless
    # of the label. Count fields and self-knowledge remain available.
    for item in observation["claims"]:
        item.pop("proposer")
        item.pop("verifiers")
    observation["accountability"] = "attributable"
    assert policy.propose(observation, None).action == WithholdAction()


def test_warmup_boundary_and_later_visible_activity_reopen_contribution():
    mechanism = world("aggregate")
    policy = conditional(peer_threshold="1/2", warmup_rounds=2)
    state = mechanism.initial_state()
    for _ in range(2):
        assert policy.propose(mechanism.observe(state, "a1"), None).action == (
            InspectEvidenceAction(evidence_id="e1")
        )
        state = advance(mechanism, state)
    assert policy.propose(mechanism.observe(state, "a1"), None).action == WithholdAction()
    state = advance(mechanism, state, a2=claim(2))
    assert policy.propose(mechanism.observe(state, "a1"), None).action == (
        InspectEvidenceAction(evidence_id="e1")
    )


@pytest.mark.parametrize("accountability", ["aggregate", "attributable"])
@pytest.mark.parametrize("topology", ["private", "shared_ledger"])
def test_zero_threshold_matches_legacy_contributor_through_a_real_episode(accountability, topology):
    mechanism = world(accountability, topology)
    legacy = ec_policies.ECContributorPolicy()
    control = conditional(peer_threshold="0", warmup_rounds=0)
    state = mechanism.initial_state()
    while not mechanism.is_terminal(state):
        actions = {}
        for agent in AGENTS:
            observation = mechanism.observe(state, agent)
            expected = legacy.propose(observation, None)
            assert control.propose(observation, None) == expected
            actions[agent] = expected.action
        state = advance(mechanism, state, **actions)


def test_short_warmup_can_stop_before_any_public_claim_history_exists():
    mechanism = world("attributable", "private")
    policies = {agent: conditional(peer_threshold="1/2", warmup_rounds=2) for agent in AGENTS}
    state = mechanism.initial_state()
    trace = []
    for _ in range(4):
        actions = {agent: policy.propose(mechanism.observe(state, agent), None).action
                   for agent, policy in policies.items()}
        trace.append([actions[agent].type for agent in AGENTS])
        state = advance(mechanism, state, **actions)
    assert trace == [["inspect_evidence"] * 3, ["share_evidence"] * 3,
                     ["withhold"] * 3, ["withhold"] * 3]
    assert state["claims"] == {}


def test_hidden_truth_and_invisible_evidence_do_not_change_decisions():
    good, bad = world(accurate=True), world(accurate=False)
    good_state, bad_state = peer_claims(good), peer_claims(bad)
    good_observation = good.observe(good_state, "a1")
    bad_observation = bad.observe(bad_state, "a1")
    assert good_observation == bad_observation
    assert [item["evidence_id"] for item in good_observation["evidence"]] == ["e1"]
    assert "truth_aligned" not in repr(good_observation)
    assert "true_propositions" not in repr(good_observation)
    policy = conditional(peer_threshold="1", warmup_rounds=0, share_evidence=False)
    assert policy.propose(good_observation, None) == policy.propose(bad_observation, None)


def test_actor_renaming_and_claim_list_order_preserve_the_signal_and_unique_action():
    mechanism = world()
    observation = mechanism.observe(peer_claims(mechanism), "a1")
    renamed = copy.deepcopy(observation)
    mapping = {"a1": "z9", "a2": "z1", "a3": "z5"}
    renamed["self_id"] = mapping[renamed["self_id"]]
    renamed["claims"].reverse()
    for item in renamed["claims"]:
        item["proposer"] = mapping[item["proposer"]]
        for field in ("verifiers", "challengers"):
            item[field] = [mapping[agent] for agent in item[field]]
    policy = conditional(peer_threshold="1", warmup_rounds=0, share_evidence=False)
    assert ec_policies.visible_peer_contributor_count(renamed) == 2
    assert policy.propose(renamed, None) == policy.propose(observation, None)


def test_policy_is_observation_pure_rng_free_and_reconstructible():
    mechanism = world()
    observation = mechanism.observe(peer_claims(mechanism), "a1")
    before = copy.deepcopy(observation)
    rng = random.Random(123)
    rng_before = rng.getstate()
    policy = conditional(peer_threshold="1", warmup_rounds=0)
    expected = policy.propose(observation, rng)
    policy.propose(mechanism.observe(mechanism.initial_state(), "a1"), rng)
    assert policy.propose(observation, rng) == expected
    assert conditional(peer_threshold="1", warmup_rounds=0).propose(observation, rng) == expected
    assert observation == before
    assert rng.getstate() == rng_before


def test_single_agent_has_no_peer_requirement():
    original = world()
    spec = original.spec.model_copy(update={
        "agent_ids": ("a1",), "evidence": (original.spec.evidence[0],),
    })
    mechanism = EvidenceCommonsMechanism(spec=spec, institution=original.institution)
    observation = mechanism.observe(mechanism.initial_state(), "a1")
    assert ec_policies.visible_peer_contributor_count(observation) == 0
    assert conditional(peer_threshold="1", warmup_rounds=0).propose(
        observation, None,
    ).action == InspectEvidenceAction(evidence_id="e1")


@pytest.mark.parametrize("params", [
    {"peer_threshold": "-1/2"}, {"peer_threshold": "3/2"}, {"peer_threshold": "1/0"},
    {"peer_threshold": True}, {"peer_threshold": 0.5}, {"peer_threshold": "nan"},
    {"warmup_rounds": -1}, {"warmup_rounds": True}, {"warmup_rounds": "2.5"},
    {"warmup_rounds": 2.0}, {"share_evidence": "yes"}, {"peer_treshold": "1/2"},
])
def test_shared_contract_rejects_bad_params_before_policy_use(params):
    key = next(iter(params))
    with pytest.raises(ValueError, match=key):
        coerce_policy_params(NAME, params)
    with pytest.raises(ValidationError, match=key):
        PolicySpec(name=NAME, params=params)
    with pytest.raises(ValueError, match=key):
        ec_policies.build_ec_policy(NAME, params)


@pytest.mark.parametrize("value,exact", [(0, Fraction(0)), (1, Fraction(1)),
                                         ("2/4", Fraction(1, 2)), ("0.5", Fraction(1, 2))])
def test_exact_params_keep_serialized_specs_and_version_policy_behavior(value, exact):
    params = {"peer_threshold": value, "warmup_rounds": "3", "share_evidence": "true"}
    assert PolicySpec(name=NAME, params=params).model_dump(mode="json")["params"] == params
    parsed = coerce_policy_params(NAME, params)
    assert parsed == {"peer_threshold": exact, "warmup_rounds": 3, "share_evidence": True}
    policy = conditional(**params)
    expected_fraction = "1/2" if exact == Fraction(1, 2) else str(exact)
    assert policy.policy_id == (
        f"ec_conditional_contributor[peer_threshold={expected_fraction},warmup=3,share=True]@1"
    )
    assert PolicySpec(name=NAME).params == {}


def test_default_contract_is_explicit_and_legacy_identity_is_unchanged():
    assert conditional().policy_id == (
        "ec_conditional_contributor[peer_threshold=1/2,warmup=3,share=True]@1"
    )
    assert ec_policies.ECContributorPolicy().policy_id == "ec_contributor[share=True]@1"
