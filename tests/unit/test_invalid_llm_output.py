"""Invalid LLM output is never silently repaired (ADR-0007): after bounded
retries the policy abstains with reason ``invalid_llm_output``; a schema-valid
but mechanism-illegal action becomes ActionRejected plus the configured
fallback. Retry counts are exactly honoured."""

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.domain.actions import AbstainAction
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.engine.events import EventType
from collaborative_hill.experiments.scenario import NarrativeSkin

from _fixtures import AGENTS, ec_hand_example, run_episode_tmp

SKIN = NarrativeSkin(skin_id="plain")


def _propose_once(script, *, max_retries=1):
    provider = FakeProvider(script)
    policy = LLMPolicy("a1", provider, SKIN, max_retries=max_retries)
    import random
    proposal = policy.propose({"round": 0, "mechanism": "evidence_commons",
                               "self_id": "a1", "slots": {}, "evidence": [], "claims": [],
                               "my_budgets": {"inspect": 6, "verify": 3},
                               "my_effort_spent": 0}, random.Random(0))
    return proposal, provider


def test_non_json_garbage_abstains_with_reason():
    proposal, provider = _propose_once(["garbage", "still not json"], max_retries=1)
    assert isinstance(proposal.action, AbstainAction)
    assert proposal.action.reason == "invalid_llm_output"
    assert provider.calls == 2  # initial attempt + 1 retry


def test_valid_json_wrong_schema_abstains():
    # unknown top-level keys
    proposal, _ = _propose_once(['{"foo": 1}', '{"bar": 2}'], max_retries=1)
    assert isinstance(proposal.action, AbstainAction)
    assert proposal.action.reason == "invalid_llm_output"


def test_valid_json_bad_action_type_abstains():
    # schema violation: unknown action discriminator
    proposal, _ = _propose_once(
        ['{"action":{"type":"teleport"}}', '{"action":{"type":"teleport"}}'], max_retries=1)
    assert isinstance(proposal.action, AbstainAction)
    assert proposal.action.reason == "invalid_llm_output"


def test_retry_count_honoured():
    _p, provider = _propose_once(["x"] * 5, max_retries=2)
    assert provider.calls == 3  # initial + 2 retries
    _p2, provider2 = _propose_once(["x"] * 5, max_retries=0)
    assert provider2.calls == 1  # no retries


def test_abstain_action_proposed_recorded_in_ledger_ec_run(tmp_path):
    # In EC, abstain is legal -> garbage-driven runs complete and every
    # ActionProposed records the abstain/invalid_llm_output typed action.
    mech = ec_hand_example(InstitutionConfig(), rounds=2)
    policies = {a: LLMPolicy(a, FakeProvider(["garbage"] * 40), SKIN, max_retries=1)
                for a in AGENTS}
    result, events, _paths = run_episode_tmp(
        mech, policies, tmp_path, invalid_action_policy="fail", run_id="ec_garbage")
    assert result.status == "completed"
    proposed = [e for e in events if e.event_type == EventType.ACTION_PROPOSED]
    assert proposed
    for ev in proposed:
        action = ev.payload["proposal"]["action"]
        assert action["type"] == "abstain"
        assert action["reason"] == "invalid_llm_output"
    # 3 agents x 2 rounds x 2 attempts (1 retry) = 12 provider calls total
    assert sum(p.provider.calls for p in policies.values()) == 12


def test_illegal_action_fallback_abstain_vs_fail(tmp_path):
    # schema-valid action, but inspecting a nonexistent item is illegal.
    script = ['{"action":{"type":"inspect_evidence","evidence_id":"NOPE"}}'] * 40

    # policy=abstain -> ActionRejected then an accepted fallback abstain; run completes
    mech_a = ec_hand_example(InstitutionConfig(), rounds=2)
    pol_a = {a: LLMPolicy(a, FakeProvider(list(script)), SKIN) for a in AGENTS}
    res_a, ev_a, _p = run_episode_tmp(
        mech_a, pol_a, tmp_path, invalid_action_policy="abstain", run_id="ill_abstain")
    assert res_a.status == "completed"
    rejected = [e for e in ev_a if e.event_type == EventType.ACTION_REJECTED]
    assert rejected and "not visible" in rejected[0].payload["reason"]
    fallbacks = [e for e in ev_a if e.event_type == EventType.ACTION_ACCEPTED
                 and e.payload.get("fallback")]
    assert fallbacks
    assert fallbacks[0].payload["action"]["type"] == "abstain"

    # policy=fail -> first illegal action seals RunFailed
    mech_f = ec_hand_example(InstitutionConfig(), rounds=2)
    pol_f = {a: LLMPolicy(a, FakeProvider(list(script)), SKIN) for a in AGENTS}
    res_f, ev_f, _p2 = run_episode_tmp(
        mech_f, pol_f, tmp_path, invalid_action_policy="fail", run_id="ill_fail")
    assert res_f.status == "failed"
    assert ev_f[-1].event_type == EventType.RUN_FAILED
