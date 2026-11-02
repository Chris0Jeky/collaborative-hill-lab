"""Literal pre-adapter outputs protect v1 prompts, identities and sealed chains."""

import json
import random
from pathlib import Path

import pytest

from collaborative_hill.agents.llm import (
    FakeProvider,
    LLMPolicy,
    OpenAICompatibleConfig,
    OpenAICompatibleProvider,
    ProviderError,
    llm_manifest_fields,
)
from collaborative_hill.agents.llm.rendering import prompt_template_hash, render_prompt
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.store import RunPaths
from collaborative_hill.experiments.scenario import NarrativeSkin, ScenarioSpec, compile_scenario
from collaborative_hill.experiments.study import build_policies

FIXTURE = json.loads((Path(__file__).resolve().parents[1]
                      / "fixtures/llm_prompt_v1_baseline.json").read_text(encoding="utf-8"))
GOOD = '{"action": {"type": "withhold"}, "justification": "fixture"}'


def compatible_provider():
    return OpenAICompatibleProvider(OpenAICompatibleConfig(
        "https://provider.invalid/chat", "fixture-model",
        {"max_tokens": 8, "temperature": "1/2"},
    ), api_key=None)


def prompt_case(name):
    return next(case for case in FIXTURE["prompts"] if case["name"] == name)


@pytest.mark.parametrize("case", FIXTURE["prompts"], ids=lambda case: case["name"])
def test_default_prompt_identity_and_provenance_match_prechange_literals(case):
    skin = NarrativeSkin.model_validate(case["skin"])
    assert render_prompt(case["observation"], skin) == case["prompt"]
    assert prompt_template_hash(skin) == case["template_hash"]
    fake = LLMPolicy("a1", FakeProvider([GOOD]), skin)
    compatible = LLMPolicy("a1", compatible_provider(), skin)
    assert fake.policy_id == case["fake_policy_id"]
    assert compatible.policy_id == case["compatible_policy_id"]
    assert llm_manifest_fields({"a1": fake}) == case["fake_metadata"]
    assert llm_manifest_fields({"a1": compatible}) == case["compatible_metadata"]


def test_default_retry_prompt_digests_and_usage_match_prechange_literals():
    fixture = FIXTURE["retry"]
    case = prompt_case(fixture["prompt_case"])
    policy = LLMPolicy("a1", FakeProvider(fixture["script"]),
                       NarrativeSkin.model_validate(case["skin"]))
    assert policy.propose(case["observation"], random.Random(4)).action.type == "withhold"
    assert policy.transcript == fixture["transcript"]
    assert llm_manifest_fields({"a1": policy}) == fixture["metadata"]


@pytest.mark.parametrize("case", FIXTURE["chains"], ids=lambda case: case["name"])
def test_default_fake_policy_ledgers_remain_byte_exact(case, tmp_path):
    resolved = compile_scenario(ScenarioSpec.model_validate_json(json.dumps(case["scenario"])),
                                NarrativeSkin.model_validate(case["skin"]))
    meta = {"scenario_hash": resolved.scenario_hash, "mechanism_hash": resolved.mechanism_hash,
            "narrative_hash": resolved.narrative_hash}
    assert meta == case["start_meta"]
    policies = build_policies(resolved)
    paths = RunPaths(tmp_path / case["name"]).create()
    result = run_episode(
        mechanism=resolved.build_mechanism(), policies=policies,
        config=RunConfig.model_validate_json(json.dumps(case["config"])),
        paths=paths, start_meta=meta,
    )
    assert result.model_dump(mode="json") == case["result"]
    assert paths.events.read_text(encoding="utf-8") == case["events_jsonl"]
    assert llm_manifest_fields(policies) == case["metadata"]


def test_legacy_fake_public_attribute_mutation_keeps_its_existing_behavior():
    case = prompt_case("ec_worded_inspected")
    captured = []

    def script(prompt, index):
        captured.append(prompt)
        return GOOD

    policy = LLMPolicy("a1", FakeProvider(script), NarrativeSkin(skin_id="plain"))
    policy.skin = NarrativeSkin.model_validate(case["skin"])
    policy.prompt_template_hash = "legacy-user-override"
    policy.policy_id = "custom-legacy-policy"
    policy.propose(case["observation"], random.Random(1))
    assert captured == [case["prompt"]]
    assert policy.policy_id == "custom-legacy-policy"
    assert policy.audit_metadata()["prompt_template_hash"] == "legacy-user-override"


@pytest.mark.parametrize("field,value", [
    ("max_retries", 1), ("sampling", {"max_tokens": 999}),
    ("skin", NarrativeSkin(skin_id="changed")), ("prompt_template_hash", "changed"),
])
def test_legacy_compatible_drift_is_rejected_at_proposal_not_assignment(field, value, monkeypatch):
    provider = compatible_provider()
    monkeypatch.setattr(provider._opener, "open", lambda *args, **kwargs: pytest.fail("network"))
    policy = LLMPolicy("a1", provider, NarrativeSkin(skin_id="plain"))
    setattr(policy, field, value)
    with pytest.raises(ProviderError, match="configuration"):
        policy.propose(prompt_case("ec_plain")["observation"], random.Random(1))
    assert policy.call_count == 0
    assert policy.transcript == []
