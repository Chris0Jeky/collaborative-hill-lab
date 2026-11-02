"""Literal hand-observation oracles for the separately versioned audit veto.

No episode or audit generator is invoked here. The public dictionaries contain
the complete ordinary EC observation shape plus the declared audit envelope.
"""

import copy
import json
from pathlib import Path

import pytest

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
from collaborative_hill.experiments.scenario import (
    NarrativeSkin,
    PolicySpec,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import build_policies

NAME = "ec_audit_veto_contributor"
PARAMS = {"min_sources": 2, "peer_threshold": "0", "warmup_rounds": 0,
          "share_evidence": True}
EXPECTED_ID = "ec_audit_veto_contributor[min_sources=2,peer_threshold=0,warmup=0,share=True]@1"


def report(verdict="negative", *, slot="s1", proposition="p", published=3):
    return {"slot_id": slot, "proposition_id": proposition,
            "publish_round": published, "verdict": verdict}


def envelope(*reports):
    return {"contract_version": "ec-audit-observation@1", "audit_id": "audit-1",
            "contract_hash": "a" * 64, "reports": list(reports)}


def claim():
    return {"claim_id": "c1", "slot_id": "s1", "proposition_id": "p",
            "evidence_ids": ["e1", "e2", "e3"], "net_support": 0,
            "n_verifications": 0, "n_challenges": 0, "proposed_by_me": False,
            "verified_by_me": False, "challenged_by_me": False}


def observation(mode="propose"):
    evidence = [
        {"evidence_id": f"e{i}", "source_id": f"src-{i}", "slot_id": "s1",
         "public": True,
         "facts": {"evidence_id": f"e{i}", "source_id": f"src-{i}", "version": 1,
                   "slot_id": "s1", "proposition_id": "p", "stance": "supports",
                   "freshness": "fresh"}}
        for i in (1, 2, 3)
    ]
    value = {
        "mechanism": "evidence_commons", "round": 3, "n_agents": 3, "self_id": "a1",
        "accountability": "aggregate", "evidence_topology": "shared_ledger",
        "slots": {"s1": ["p", "q"]}, "my_budgets": {"inspect": 0, "verify": 2},
        "my_effort_spent": 3, "my_credit": None, "evidence": evidence, "claims": [],
    }
    if mode == "inspect":
        del evidence[0]["facts"]
        value["my_budgets"]["inspect"] = 1
        value["my_effort_spent"] = 2
    elif mode == "share":
        value["evidence_topology"] = "private"
        evidence[0]["public"] = False
    elif mode in ("verify", "challenge"):
        value["claims"] = [claim()]
        if mode == "challenge":
            evidence[2]["facts"]["stance"] = "contradicts"
    elif mode == "empty":
        value["evidence"] = []
        value["my_effort_spent"] = 0
    return value


def policy(**overrides):
    return build_ec_policy(NAME, {**PARAMS, **overrides})


@pytest.mark.parametrize(("mode", "expected"), [
    ("propose", ProposeClaimAction(slot_id="s1", proposition_id="p",
                                  evidence_ids=("e1", "e2", "e3"))),
    ("verify", VerifyClaimAction(claim_id="c1")),
])
@pytest.mark.parametrize("audit", [None, envelope(), envelope(report("positive")),
                                  envelope(report("unavailable")),
                                  envelope(report(proposition="q"))])
def test_absent_pending_nonnegative_and_unrelated_reports_leave_the_selected_action(
    mode, expected, audit,
):
    obs = observation(mode)
    if audit is not None:
        obs["audit"] = copy.deepcopy(audit)
    assert policy().propose(obs, object()).action == expected


@pytest.mark.parametrize("mode", ["propose", "verify"])
def test_matching_published_negative_vetoes_proposal_or_verification(mode):
    obs = observation(mode)
    obs["audit"] = envelope(report())
    assert policy().propose(obs, object()).action == WithholdAction()


def test_negative_report_is_scoped_to_its_slot_and_proposition():
    obs = observation()
    obs["slots"]["s2"] = ["p", "q"]
    obs["audit"] = envelope(report(slot="s2"))
    assert policy().propose(obs, None).action == ProposeClaimAction(
        slot_id="s1", proposition_id="p", evidence_ids=("e1", "e2", "e3"))


def test_veto_does_not_rerank_to_another_candidate():
    obs = observation()
    obs["slots"]["s2"] = ["p", "q"]
    for number, source in ((4, "src-4"), (5, "src-5")):
        obs["evidence"].append({
            "evidence_id": f"e{number}", "source_id": source, "slot_id": "s2",
            "public": True,
            "facts": {"evidence_id": f"e{number}", "source_id": source, "version": 1,
                      "slot_id": "s2", "proposition_id": "p", "stance": "supports",
                      "freshness": "fresh"},
        })
    obs["audit"] = envelope(report(), report("positive", slot="s2"))
    assert policy().propose(obs, None).action == WithholdAction()


@pytest.mark.parametrize(("mode", "expected"), [
    ("inspect", InspectEvidenceAction(evidence_id="e1")),
    ("share", ShareEvidenceAction(evidence_id="e1")),
    ("challenge", ChallengeClaimAction(claim_id="c1", evidence_ids=("e3",))),
    ("empty", WithholdAction()),
    ("quorum", WithholdAction()),
])
def test_negative_audit_preserves_inspection_sharing_challenge_and_existing_noops(mode, expected):
    obs = observation(mode)
    obs["audit"] = envelope(report())
    actor = policy(peer_threshold="1") if mode == "quorum" else policy()
    assert actor.propose(obs, object()).action == expected


def test_warmup_and_quorum_remain_the_existing_rule():
    obs = observation()
    obs["audit"] = envelope(report("positive"))
    actor = policy(peer_threshold="1", warmup_rounds=4)
    assert actor.propose(obs, None).action == ProposeClaimAction(
        slot_id="s1", proposition_id="p", evidence_ids=("e1", "e2", "e3"))
    obs["round"] = 4
    assert actor.propose(obs, None).action == WithholdAction()


@pytest.mark.parametrize("limitation", ["missing", "stale", "one_source", "rival"])
def test_positive_audit_does_not_supply_evidence_or_bypass_the_screen(limitation):
    obs = observation()
    obs["audit"] = envelope(report("positive"))
    if limitation == "missing":
        obs["evidence"] = []
    elif limitation == "stale":
        for item in obs["evidence"]:
            item["facts"]["freshness"] = "stale"
    elif limitation == "one_source":
        for item in obs["evidence"]:
            item["facts"]["source_id"] = "src-1"
    else:
        obs["evidence"][2]["facts"]["proposition_id"] = "q"
    assert policy().propose(obs, None).action == WithholdAction()


def test_positive_audit_does_not_verify_an_unread_citation():
    obs = observation("verify")
    obs["audit"] = envelope(report("positive"))
    obs["claims"][0]["evidence_ids"] = ["e4"]
    obs["evidence"].append({"evidence_id": "e4", "source_id": "src-4",
                            "slot_id": "s1", "public": True})
    assert policy().propose(obs, None).action == WithholdAction()


@pytest.mark.parametrize("mode", ["propose", "verify", "inspect", "share", "challenge",
                                  "empty", "quorum"])
@pytest.mark.parametrize("invalid", ["version", "future"])
def test_invalid_envelope_is_rejected_before_every_possible_base_action(mode, invalid):
    obs = observation(mode)
    obs["audit"] = envelope(report())
    if invalid == "version":
        obs["audit"]["contract_version"] = "future-contract"
    else:
        obs["audit"]["reports"][0]["publish_round"] = 4
    actor = policy(peer_threshold="1") if mode == "quorum" else policy()
    with pytest.raises(ValueError, match="audit"):
        actor.propose(obs, None)


@pytest.mark.parametrize("audit", [
    None, [], "negative", {},
    {**envelope(), "audit_id": "  "},
    {**envelope(), "audit_id": 7},
    {**envelope(), "contract_hash": "short"},
    {**envelope(), "reports": {}},
    {**envelope(), "reports": None},
    {**envelope(), "truth_aligned": True},
    envelope({**report(), "verdict": "unknown"}),
    envelope({**report(), "publish_round": True}),
    envelope({**report(), "publish_round": 3.0}),
    envelope({**report(), "publish_round": "3"}),
    envelope({**report(), "publish_round": -1}),
    envelope({**report(), "truth_aligned": True}),
    envelope(report(proposition="not-a-candidate")),
    envelope(report(slot="absent-slot")),
    envelope(report(), report()),
    envelope(report(), report("positive", published=2)),
])
def test_present_malformed_audit_is_never_treated_as_absent(audit):
    obs = observation()
    obs["audit"] = copy.deepcopy(audit)
    actor = policy()
    with pytest.raises(ValueError, match="audit"):
        actor.propose(obs, None)


@pytest.mark.parametrize("round_value", [None, True, "3", 3.0, -1])
def test_audit_time_comparison_requires_an_actual_nonnegative_integer(round_value):
    obs = observation()
    obs["round"] = round_value
    obs["audit"] = envelope(report())
    actor = policy()
    with pytest.raises(ValueError, match="audit"):
        actor.propose(obs, None)


def test_audit_projection_is_not_modified_and_rebuilt_policy_needs_no_history():
    obs = observation()
    obs["audit"] = envelope(report())
    original = copy.deepcopy(obs)
    actor = policy()
    assert actor.propose(obs, object()).action == WithholdAction()
    assert policy().propose(obs, object()).action == WithholdAction()
    assert obs == original
    obs["audit"] = envelope(report("positive"))
    expected = ProposeClaimAction(slot_id="s1", proposition_id="p",
                                  evidence_ids=("e1", "e2", "e3"))
    assert actor.propose(obs, object()).action == expected
    assert policy().propose(obs, object()).action == expected


@pytest.mark.parametrize("verdict", ["positive", "negative", "unavailable"])
def test_opaque_contract_hash_does_not_choose_policy_actions(verdict):
    obs = observation()
    obs["audit"] = envelope(report(verdict))
    expected = (WithholdAction() if verdict == "negative" else ProposeClaimAction(
        slot_id="s1", proposition_id="p", evidence_ids=("e1", "e2", "e3")))
    for digest in ("a" * 64, "b" * 64, "0" * 64):
        obs["audit"]["contract_hash"] = digest
        assert policy().propose(obs, None).action == expected


@pytest.mark.parametrize("params", [
    {"min_sources": 0}, {"min_sources": True}, {"min_sources": "1.5"},
    {"peer_threshold": "-1/2"}, {"peer_threshold": "3/2"}, {"peer_threshold": True},
    {"warmup_rounds": -1}, {"warmup_rounds": True},
    {"share_evidence": "yes"}, {"share_evidence": 1},
    {"min_source": 2}, {"audit_accuracy": "1"},
])
def test_policy_spec_and_parameter_contract_reject_invalid_settings(params):
    with pytest.raises(ValueError):
        coerce_policy_params(NAME, params)
    with pytest.raises(ValueError):
        PolicySpec(name=NAME, params=params)


def test_policy_factory_normalizes_cli_settings_and_has_a_distinct_identity():
    actor = policy()
    assert actor.policy_id == EXPECTED_ID
    configured = build_ec_policy(NAME, {"min_sources": "2", "peer_threshold": "1/2",
                                       "warmup_rounds": "3", "share_evidence": "false"})
    assert configured.policy_id == (
        "ec_audit_veto_contributor[min_sources=2,peer_threshold=1/2,warmup=3,share=False]@1")
    with pytest.raises(ValueError, match="min_sources"):
        type(actor)(min_sources=0)


def test_study_builder_constructs_the_registered_policy_without_running_an_episode():
    path = (Path(__file__).resolve().parents[2]
            / "studies/001-evidence-commons/scenarios/attr-ledger.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    for agent in data["cognition"]["agents"]:
        agent["policy"] = {"name": NAME, "params": PARAMS}
    scenario = compile_scenario(ScenarioSpec.model_validate(data), NarrativeSkin(skin_id="plain"))
    actors = build_policies(scenario)
    assert set(actors) == {"a1", "a2", "a3"}
    assert all(actor.policy_id == EXPECTED_ID for actor in actors.values())
    obs = observation()
    obs["audit"] = envelope(report())
    assert all(actor.propose(obs, None).action == WithholdAction() for actor in actors.values())
