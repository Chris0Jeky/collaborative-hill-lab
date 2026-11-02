"""Atomic audit publication changes public observations, not the EC task."""

from copy import deepcopy

import pytest
from _fixtures import ec_hand_example, ec_provenance_world
from test_audit_models import settings_data

from collaborative_hill.domain.actions import (
    InspectEvidenceAction,
    ProposeClaimAction,
    VerifyClaimAction,
    WithholdAction,
)
from collaborative_hill.domain.audit import AuditFinding, AuditMechanismConfig
from collaborative_hill.domain.institutions import AuditInstitutionConfig, InstitutionConfig
from collaborative_hill.domain.world.audited_evidence_commons import AuditedEvidenceCommonsMechanism
from collaborative_hill.engine.seeds import rng_for


def audit_settings(*, accuracy="1", unavailable="0"):
    data = settings_data(accuracy=accuracy, unavailable=unavailable)
    data["contract"]["schedule"] = (
        {"slot_id": "s1", "proposition_id": "p1a", "publish_round": 0},
        {"slot_id": "s1", "proposition_id": "p1b", "publish_round": 2},
        {"slot_id": "s2", "proposition_id": "p2a", "publish_round": 2},
        {"slot_id": "s2", "proposition_id": "p2b", "publish_round": 4},
    )
    return AuditMechanismConfig.model_validate(data)


def audited_mechanism(config=None, spec=None):
    return AuditedEvidenceCommonsMechanism(
        spec=spec or ec_provenance_world(rounds=6),
        institution=AuditInstitutionConfig(accountability="attributable",
                                          audit=config or audit_settings()),
    )


def keyed_rng(key):
    return rng_for(103, "mechanism", "round-opening", *key)


def no_rng(key):
    pytest.fail(f"invalid/already-prepared state must not request randomness: {key}")


def literal_reports():
    return [
        {"slot_id": "s1", "proposition_id": "p1a", "publish_round": 0, "verdict": "positive"},
        {"slot_id": "s1", "proposition_id": "p1b", "publish_round": 2, "verdict": "negative"},
        {"slot_id": "s2", "proposition_id": "p2a", "publish_round": 2, "verdict": "positive"},
        {"slot_id": "s2", "proposition_id": "p2b", "publish_round": 4, "verdict": "negative"},
    ]


def test_round_zero_publication_is_complete_public_and_detached():
    mechanism = audited_mechanism()
    state = mechanism.initial_state()
    before = deepcopy(state)
    assert state["audit_reports"] == []
    prepared, events = mechanism.prepare_round(state, keyed_rng)
    assert state == before
    assert prepared["audit_reports"] == literal_reports()[:1]
    assert len(events) == 1
    assert events[0] == {
        "event_type": "AuditPublished", "actor": "engine",
        "payload": {"contract_version": "ec-audit-observation@1", "audit_id": "toy-audit",
                    "contract_hash": audit_settings().contract.contract_hash(),
                    "report": literal_reports()[0]},
    }
    obs_a = mechanism.observe(prepared, "a1")
    obs_b = mechanism.observe(prepared, "a2")
    assert obs_a["observation_schema_version"] == 3
    assert obs_a["audit"] == obs_b["audit"]
    assert obs_a["audit"]["reports"] == literal_reports()[:1]
    obs_a["audit"]["reports"][0]["verdict"] = "negative"
    assert obs_b["audit"]["reports"] == prepared["audit_reports"] == literal_reports()[:1]
    events[0]["payload"]["report"]["verdict"] = "negative"
    assert prepared["audit_reports"] == literal_reports()[:1]


def test_complete_due_batch_is_atomic_and_preparation_is_idempotent():
    mechanism = audited_mechanism()
    state = mechanism.initial_state()
    state.update(round=2, audit_reports=literal_reports()[:1])
    before = deepcopy(state)
    prepared, events = mechanism.prepare_round(state, keyed_rng)
    assert state == before
    assert prepared["audit_reports"] == literal_reports()[:3]
    assert [event["payload"]["report"] for event in events] == literal_reports()[1:3]
    repeated, extra = mechanism.prepare_round(prepared, no_rng)
    assert repeated == prepared and extra == []


@pytest.mark.parametrize("reports", [
    [], literal_reports()[1:3], literal_reports()[:2],
    [literal_reports()[0], literal_reports()[2]], literal_reports(),
    [literal_reports()[0], literal_reports()[0]],
])
def test_prepare_rejects_missing_past_partial_current_future_and_duplicate_batches(reports):
    mechanism = audited_mechanism()
    state = mechanism.initial_state()
    state.update(round=2, audit_reports=deepcopy(reports))
    before = deepcopy(state)
    with pytest.raises(ValueError, match="audit|published"):
        mechanism.prepare_round(state, no_rng)
    assert state == before


@pytest.mark.parametrize("reports", [None, {}, [None], [{"truth_aligned": True}]])
def test_public_state_shape_is_validated_before_publication(reports):
    mechanism = audited_mechanism()
    state = mechanism.initial_state()
    state["audit_reports"] = reports
    with pytest.raises(ValueError):
        mechanism.prepare_round(state, no_rng)


def test_observe_requires_complete_current_prefix_not_an_unprepared_checkpoint():
    mechanism = audited_mechanism()
    state = mechanism.initial_state()
    with pytest.raises(ValueError, match="published"):
        mechanism.observe(state, "a1")
    state.update(round=2, audit_reports=literal_reports()[:1])
    with pytest.raises(ValueError, match="published"):
        mechanism.observe(state, "a1")


def test_unavailable_is_published_and_no_future_target_is_sampled():
    mechanism = audited_mechanism(audit_settings(unavailable="1"))
    keys = []

    def recorded_rng(key):
        keys.append(key)
        return keyed_rng(key)

    state, events = mechanism.prepare_round(mechanism.initial_state(), recorded_rng)
    assert len(events) == 1
    assert events[0]["payload"]["report"]["verdict"] == "unavailable"
    assert {key[3:5] for key in keys} == {("s1", "p1a")}
    assert all(report["publish_round"] == 0 for report in state["audit_reports"])
    assert {key[-1] for key in keys} == {"availability", "verdict"}


def test_truth_flip_is_observation_identical_before_release_then_only_changes_audit():
    config_data = audit_settings().model_dump(mode="python")
    config_data["contract"]["schedule"][0]["publish_round"] = 2
    config = AuditMechanismConfig.model_validate(config_data)
    world = ec_provenance_world(rounds=6)
    truth = {"s1": "p1b", "s2": "p2b"}
    flipped = world.model_copy(update={
        "true_propositions": truth,
        "evidence": tuple(item.model_copy(update={
            "truth_aligned": (item.proposition_id == truth[item.slot_id])
                             == (item.stance == "supports"),
        }) for item in world.evidence),
    })
    mechanisms = [audited_mechanism(config, spec) for spec in (world, flipped)]
    states = [mechanism.initial_state() for mechanism in mechanisms]
    for rnd in range(3):
        observations = []
        for index, mechanism in enumerate(mechanisms):
            states[index], _ = mechanism.prepare_round(states[index], keyed_rng)
            observations.append(mechanism.observe(states[index], "a1"))
            actions = {agent: WithholdAction() for agent in mechanism.agent_ids()}
            states[index], _ = mechanism.resolve(states[index], actions, rng_for(103, rnd))
        if rnd < 2:
            assert observations[0] == observations[1]
        else:
            assert observations[0]["audit"] != observations[1]["audit"]
            assert {k: v for k, v in observations[0].items() if k != "audit"} == {
                k: v for k, v in observations[1].items() if k != "audit"}


def test_fixed_actions_keep_literal_legacy_rewards_even_when_audit_verdict_is_wrong():
    base = ec_hand_example(InstitutionConfig(accountability="attributable"), rounds=3)
    data = settings_data(accuracy="0", unavailable="0")
    data["contract"]["schedule"] = (
        {"slot_id": "s1", "proposition_id": "p1a", "publish_round": 1},
        {"slot_id": "s1", "proposition_id": "p1b", "publish_round": 2},
    )
    config = AuditMechanismConfig.model_validate(data)
    audited = AuditedEvidenceCommonsMechanism(spec=base.spec, institution=AuditInstitutionConfig(
        accountability="attributable", audit=config))
    states = [base.initial_state(), audited.initial_state()]
    schedules = [
        {"a1": InspectEvidenceAction(evidence_id="e1"),
         "a2": InspectEvidenceAction(evidence_id="e1"), "a3": WithholdAction()},
        {"a1": ProposeClaimAction(slot_id="s1", proposition_id="p1a", evidence_ids=("e1",)),
         "a2": WithholdAction(), "a3": WithholdAction()},
        {"a1": WithholdAction(), "a2": VerifyClaimAction(claim_id="c1"), "a3": WithholdAction()},
    ]
    for rnd, actions in enumerate(schedules):
        states[1], _ = audited.prepare_round(states[1], keyed_rng)
        for index, mechanism in enumerate((base, audited)):
            assert all(mechanism.validate_action(states[index], agent, action) is None
                       for agent, action in actions.items())
            states[index], _ = mechanism.resolve(states[index], actions, rng_for(103, rnd))
        assert states[0] == {key: value for key, value in states[1].items()
                             if key != "audit_reports"}
    rewards = audited.final_rewards(states[1])
    assert rewards == base.final_rewards(states[0])
    assert rewards["collective_quality"] == 12
    assert rewards["individual_credit"] == {"a1": "3", "a2": "2", "a3": "0"}
    assert rewards["effort"] == {"a1": 2, "a2": 3, "a3": 0}
    assert rewards["utility"] == {"a1": "5", "a2": "3", "a3": "4"}
    assert [AuditFinding.model_validate(row).verdict for row in states[1]["audit_reports"]] == (
        ["negative", "positive"])
