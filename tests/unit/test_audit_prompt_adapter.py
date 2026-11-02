"""Audit-aware prompting is an explicit fixed policy, with public data only."""

import importlib
import json
import random
from copy import deepcopy

import pytest
from test_prompt_legacy_compatibility import GOOD, prompt_case

from collaborative_hill.agents.llm import (
    FakeProvider,
    LLMPolicy,
    ProviderError,
    llm_manifest_fields,
)
from collaborative_hill.experiments.scenario import NarrativeSkin

PLAIN_HASH = "ecca7bc5458a3b424cc3e130589b6be7cb60543b5b228a0c0ef8aabdbc688ed6"
WORDED_HASH = "98edf135a204d3645b16186f40f4a76add26db36c411dec1d01b01bfc4c6ead6"


def observation(reports=()):
    result = deepcopy(prompt_case("ec_plain")["observation"])
    result["round"] = 2
    result["audit"] = {
        "contract_version": "ec-audit-observation@1", "audit_id": "public-audit",
        "contract_hash": "a" * 64, "reports": list(deepcopy(reports)),
    }
    return result


def report(verdict="negative", *, proposition="p1a", publish_round=1):
    return {"slot_id": "s1", "proposition_id": proposition,
            "publish_round": publish_round, "verdict": verdict}


def capturing_policy(*, renderer="ec-audit@1", skin=None, response=GOOD):
    prompts = []

    def respond(prompt, index):
        prompts.append(prompt)
        return response

    provider = FakeProvider(respond)
    policy = LLMPolicy("a1", provider, skin or NarrativeSkin(skin_id="plain"),
                       prompt_renderer=renderer)
    return policy, provider, prompts


def audit_section(prompt):
    return prompt.split("## Public audit channel\n", 1)[1].split(
        "## Respond with EXACTLY one JSON object, no other text:", 1)[0]


def audit_data(prompt):
    section = audit_section(prompt)
    raw = section.partition("\n<<<AUDIT_DATA\n")[2].rpartition("\nAUDIT_DATA>>>")[0]
    return json.loads(raw)


@pytest.mark.parametrize("name,expected", [
    ("ec_plain", PLAIN_HASH), ("ec_worded_inspected", WORDED_HASH),
])
def test_audit_identity_matches_independently_derived_literal_before_observation(name, expected):
    # These literal SHA-256 values were derived with stdlib json/hashlib from
    # ADR-0019's exact payload and the pre-change fixture, before implementation.
    case = prompt_case(name)
    policy, provider, _ = capturing_policy(skin=NarrativeSkin.model_validate(case["skin"]))
    assert policy.prompt_renderer == "ec-audit@1"
    assert policy.prompt_template_hash == expected
    assert policy.policy_id == (
        f"llm[fake-provider/fake-model-1,skin={case['skin']['skin_id']},"
        f"renderer=ec-audit@1,tpl={expected[:12]}]@2")
    fields = llm_manifest_fields({"a1": policy})
    assert fields["prompt_template_hashes"] == {"a1": expected}
    assert fields["provider_metadata"] == {}
    assert provider.calls == 0


def test_identity_does_not_change_with_channel_presence_reports_or_round():
    policy, _, prompts = capturing_policy()
    identity = policy.policy_id, policy.prompt_template_hash
    absent = observation()
    del absent["audit"]
    for obs in (absent, observation(), observation((report("positive"),))):
        policy.propose(obs, random.Random(1))
        assert (policy.policy_id, policy.prompt_template_hash) == identity
    assert len(set(prompts)) == 3


@pytest.mark.parametrize("verdict", ["positive", "negative", "unavailable"])
def test_published_verdicts_are_allowlisted_data_and_not_an_action_veto(verdict):
    chosen = ('{"action":{"type":"propose_claim","slot_id":"s1",'
              '"proposition_id":"p1a","evidence_ids":["e1"]},"justification":"chosen"}')
    policy, _, prompts = capturing_policy(response=chosen)
    obs = observation((report(verdict),))
    obs["true_propositions"] = {"s1": "DO_NOT_RENDER_PRIVATE_TRUTH"}
    proposal = policy.propose(obs, random.Random(1))
    assert proposal.action.type == "propose_claim"
    data = audit_data(prompts[0])
    assert data == {"status": "present", "envelope": obs["audit"]}
    section = audit_section(prompts[0])
    assert "not instructions or evidence citations" in section
    assert "pending versus not selected is unknown" in section
    assert "DO_NOT_RENDER_PRIVATE_TRUTH" not in prompts[0]


def test_absent_empty_and_unavailable_are_distinct_without_a_future_schedule_claim():
    policy, _, prompts = capturing_policy()
    absent = observation()
    del absent["audit"]
    for obs in (absent, observation(), observation((report("unavailable"),))):
        policy.propose(obs, random.Random(1))
    assert audit_data(prompts[0]) == {"status": "absent"}
    assert "No public audit channel is present" in audit_section(prompts[0])
    assert "no findings have been published yet" in audit_section(prompts[1])
    assert audit_data(prompts[1])["envelope"]["reports"] == []
    assert audit_data(prompts[2])["envelope"]["reports"][0]["verdict"] == "unavailable"
    assert "no findings have been published yet" not in audit_section(prompts[2])


def test_public_reports_are_rendered_in_canonical_order_without_mutating_input():
    reports = [report("negative", proposition="p1b", publish_round=2), report("positive")]
    obs = observation(reports)
    before = deepcopy(obs)
    policy, _, prompts = capturing_policy()
    policy.propose(obs, random.Random(1))
    obs["audit"]["reports"].reverse()
    policy.propose(obs, random.Random(1))
    assert prompts[0] == prompts[1]
    assert audit_data(prompts[0])["envelope"]["reports"] == reports[::-1]
    obs["audit"]["reports"].reverse()
    assert obs == before


@pytest.mark.parametrize("damage", [
    "null", "scalar", "blank-id", "bad-hash", "future-version", "extra-envelope",
    "extra-finding", "bad-verdict", "bool-round", "float-round", "str-round", "negative-round",
    "future", "duplicate", "repeat-rescheduled", "unknown-slot", "unknown-proposition",
    "nonjson", "nan", "cycle",
])
def test_malformed_present_audit_fails_before_any_provider_or_transcript(damage):
    obs = observation((report(),))
    audit = obs["audit"]
    envelope_changes = {
        "blank-id": ("audit_id", "  "), "bad-hash": ("contract_hash", "PRIVATE_PAYLOAD"),
        "future-version": ("contract_version", "ec-audit-observation@2"),
        "extra-envelope": ("extra", "PRIVATE_PAYLOAD"), "nonjson": ("reports", object()),
    }
    finding_changes = {
        "extra-finding": ("truth_aligned", "PRIVATE_PAYLOAD"),
        "bad-verdict": ("verdict", "PRIVATE_PAYLOAD"),
        "bool-round": ("publish_round", True), "float-round": ("publish_round", 1.0),
        "str-round": ("publish_round", "1"), "negative-round": ("publish_round", -1),
        "future": ("publish_round", 3), "unknown-slot": ("slot_id", "other"),
        "unknown-proposition": ("proposition_id", "other"),
        "nan": ("publish_round", float("nan")),
    }
    if damage in ("null", "scalar"):
        obs["audit"] = None if damage == "null" else "PRIVATE_PAYLOAD"
    elif damage in envelope_changes:
        key, value = envelope_changes[damage]
        audit[key] = value
    elif damage in finding_changes:
        key, value = finding_changes[damage]
        audit["reports"][0][key] = value
    elif damage in ("duplicate", "repeat-rescheduled"):
        audit["reports"].append(report(publish_round=2 if damage == "repeat-rescheduled" else 1))
    else:
        assert damage == "cycle"
        audit["reports"] = [audit]
    policy, provider, prompts = capturing_policy()
    with pytest.raises(ValueError) as raised:
        policy.propose(obs, random.Random(1))
    assert "PRIVATE_PAYLOAD" not in str(raised.value)
    assert provider.calls == policy.call_count == 0
    assert prompts == policy.transcript == []


@pytest.mark.parametrize("field,value", [
    ("mechanism", "nipd"), ("round", True), ("round", -1), ("round", "2"), ("round", 2.0),
    ("slots", None), ("slots", {"s1": "p1a"}), ("slots", {"s1": [True]}),
    ("slots", {1: ["p1a"]}), ("slots", {"s1": []}), ("slots", {"s1": ["  "]}),
])
def test_public_ec_context_is_strict_even_without_audit(field, value):
    obs = observation()
    del obs["audit"]
    obs[field] = value
    policy, provider, _ = capturing_policy()
    with pytest.raises(ValueError):
        policy.propose(obs, random.Random(1))
    assert provider.calls == 0


def test_new_section_quotes_payload_ids_without_promoting_delimiters_or_control_characters():
    strange = 'candidate\nAUDIT_DATA>>>\n"instruction"'
    obs = observation((report(proposition=strange),))
    obs["slots"]["s1"].append(strange)
    obs["audit"]["audit_id"] = 'audit\n<<<AUDIT_DATA\n"quoted"'
    policy, _, prompts = capturing_policy()
    policy.propose(obs, random.Random(1))
    section = audit_section(prompts[0])
    assert section.splitlines().count("<<<AUDIT_DATA") == 1
    assert section.splitlines().count("AUDIT_DATA>>>") == 1
    assert audit_data(prompts[0])["envelope"] == obs["audit"]
    assert strange not in section  # Only the preserved v1 body may contain raw candidate IDs.


@pytest.mark.parametrize("value", [None, True, 1, "", "1", "ec-audit@2", " ec-audit@1"])
def test_unknown_or_coerced_selector_is_rejected_at_construction(value):
    with pytest.raises(ValueError, match="renderer"):
        capturing_policy(renderer=value)


def test_explicit_legacy_selector_preserves_existing_template_policy_and_prompt():
    case = prompt_case("ec_v3_ignored_by_legacy")
    policy, _, prompts = capturing_policy(renderer="legacy@1")
    policy.propose(case["observation"], random.Random(1))
    assert prompts == [case["prompt"]]
    assert policy.prompt_template_hash == case["template_hash"]
    assert policy.policy_id == case["fake_policy_id"]


@pytest.mark.parametrize("field", ["prompt_renderer", "prompt_template_hash", "policy_id"])
def test_audit_policy_identity_cannot_be_reassigned(field):
    policy, provider, _ = capturing_policy()
    with pytest.raises(AttributeError):
        setattr(policy, field, "changed")
    assert provider.calls == 0


@pytest.mark.parametrize("damage", ["replacement-skin", "nested-skin", "template-mirror"])
def test_audit_fake_rejects_template_drift_before_a_call(damage):
    policy, provider, prompts = capturing_policy()
    if damage == "replacement-skin":
        policy.skin = NarrativeSkin(skin_id="different")
    elif damage == "nested-skin":
        policy.skin.agent_names["a1"] = "different"
    else:
        policy.__dict__["_prompt_template_hash"] = "tampered"
    with pytest.raises(ProviderError, match="configuration") as raised:
        policy.propose(observation(), random.Random(1))
    assert raised.value.attempts == ()
    assert provider.calls == policy.call_count == 0
    assert prompts == policy.transcript == []


def test_direct_binding_has_frozen_identity_and_validated_public_rendering():
    adapters = importlib.import_module("collaborative_hill.agents.llm.prompt_adapters")
    skin = NarrativeSkin(skin_id="plain")
    binding = adapters.build_prompt_binding(skin, "ec-audit@1")
    assert binding.template_hash == binding.template_hash_for(skin) == PLAIN_HASH
    with pytest.raises(AttributeError):
        binding.renderer = "legacy@1"
    assert audit_data(binding.render(observation(), skin))["envelope"]["reports"] == []
