"""One explicit policy parameter works identically for fake and live factories."""

import json
import random
from copy import deepcopy

import pytest
from test_audit_prompt_adapter import PLAIN_HASH, audit_data, observation, report
from test_prompt_legacy_compatibility import FIXTURE, GOOD

from collaborative_hill.agents.llm import (
    FakeProvider,
    LLMPolicy,
    build_openai_compatible_policy,
    validate_provider_params,
)
from collaborative_hill.agents.llm import configuration as provider_configuration
from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.experiments.scenario import NarrativeSkin, PolicySpec, ScenarioSpec
from collaborative_hill.experiments.scenario import compile_scenario as compile_spec
from collaborative_hill.experiments.study import build_policies

PARAMS = {"endpoint": "https://provider.invalid/chat", "model_id": "fixture-model",
          "max_tokens": 8, "temperature": "1/2"}


def scenario_data(*, world="ec", policy="llm_fake", renderer="ec-audit@1"):
    raw = deepcopy(next(case["scenario"] for case in FIXTURE["chains"] if case["name"] == world))
    raw["cognition"]["agents"][0]["policy"] = {
        "name": policy,
        "params": {**({"script": json.dumps([GOOD, GOOD])} if policy == "llm_fake" else PARAMS),
                   "prompt_renderer": renderer},
    }
    return raw


def compile_data(data):
    return compile_spec(ScenarioSpec.model_validate_json(json.dumps(data)),
                        NarrativeSkin(skin_id="plain"))


class WireResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return json.dumps({"model": "reported-fixture", "choices": [{
            "finish_reason": "stop", "message": {"role": "assistant", "content": GOOD},
        }]}).encode()


def forbid_credential_read(monkeypatch):
    original_get = provider_configuration.os.environ.get

    def checked_get(key, default=None):
        if key == "CHL_PROMPT_TEST_KEY":
            pytest.fail("configuration validation must precede credential access")
        return original_get(key, default)

    monkeypatch.setattr(provider_configuration.os.environ, "get", checked_get)


@pytest.mark.parametrize("name", ["llm_fake", "llm_openai_compatible"])
@pytest.mark.parametrize("renderer", [None, True, 1, "", "ec-audit@2", " ec-audit@1"])
def test_policy_spec_rejects_malformed_renderer_offline(name, renderer, monkeypatch):
    forbid_credential_read(monkeypatch)
    params = ({"script": "[]"} if name == "llm_fake" else
              {**PARAMS, "api_key_env": "CHL_PROMPT_TEST_KEY"})
    with pytest.raises(ValueError):
        PolicySpec(name=name, params={**params, "prompt_renderer": renderer})


@pytest.mark.parametrize("renderer", [None, True, 1, "", "ec-audit@2"])
def test_direct_compatible_factory_rejects_bad_selector_before_credentials(renderer, monkeypatch):
    forbid_credential_read(monkeypatch)
    with pytest.raises(ValueError, match="renderer"):
        build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), {
            **PARAMS, "api_key_env": "CHL_PROMPT_TEST_KEY", "prompt_renderer": renderer,
        })


@pytest.mark.parametrize("renderer", ["legacy@1", "ec-audit@1"])
def test_policy_selector_does_not_enter_transport_configuration(renderer):
    config = validate_provider_params({**PARAMS, "prompt_renderer": renderer})
    assert config == validate_provider_params(PARAMS)
    assert dict(config.sampling) == {"max_tokens": 8, "temperature": "1/2"}
    assert "prompt_renderer" not in config.__dict__


def test_fake_factory_forwards_explicit_mode_and_preserves_omitted_defaults():
    policies = build_policies(compile_data(scenario_data()))
    assert policies["a1"].prompt_renderer == "ec-audit@1"
    assert policies["a1"].prompt_template_hash == PLAIN_HASH
    assert policies["a2"].prompt_renderer == "legacy@1"
    assert policies["a2"].policy_id.endswith("]@1")


def test_compatible_factory_keeps_transport_metadata_and_uses_audited_prompt(monkeypatch):
    params = {**PARAMS, "prompt_renderer": "ec-audit@1"}
    policy = build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), params)
    legacy = build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), PARAMS)
    assert (policy.audit_metadata()["provider_metadata"]
            == legacy.audit_metadata()["provider_metadata"])
    assert policy.prompt_renderer == "ec-audit@1"
    assert policy.prompt_template_hash == PLAIN_HASH
    assert ",renderer=ec-audit@1," in policy.policy_id and policy.policy_id.endswith("]@2")
    params["prompt_renderer"] = "legacy@1"
    captured = []

    def open_request(request, **kwargs):
        captured.append(json.loads(request.data))
        return WireResponse()

    monkeypatch.setattr(policy.provider._opener, "open", open_request)
    policy.propose(observation((report(),)), random.Random(1))
    assert len(captured) == 1
    assert set(captured[0]) == {"model", "messages", "stream", "n", "max_tokens", "temperature"}
    assert audit_data(captured[0]["messages"][0]["content"])["envelope"]["reports"] == [report()]
    assert policy.prompt_renderer == "ec-audit@1"


@pytest.mark.parametrize("name", ["llm_fake", "llm_openai_compatible"])
def test_non_ec_scenario_rejects_opt_in_before_credentials(name, monkeypatch):
    forbid_credential_read(monkeypatch)
    data = scenario_data(world="nipd", policy=name)
    if name == "llm_openai_compatible":
        data["cognition"]["agents"][0]["policy"]["params"]["api_key_env"] = "CHL_PROMPT_TEST_KEY"
    with pytest.raises(ValueError, match="Evidence Commons"):
        compile_data(data)


@pytest.mark.parametrize("name", ["llm_fake", "llm_openai_compatible"])
@pytest.mark.parametrize("replacement", ["scripted", "legacy_llm"])
def test_copied_non_ec_scenario_cannot_bypass_effective_factory_guard(
    name, replacement, monkeypatch,
):
    data = scenario_data(world="nipd", policy=name, renderer="legacy@1")
    if name == "llm_openai_compatible":
        data["cognition"]["agents"][0]["policy"]["params"]["api_key_env"] = "CHL_PROMPT_TEST_KEY"
    resolved = compile_data(data)
    agent = resolved.spec.cognition.agents[0]
    changed = agent.model_copy(update={"policy": agent.policy.model_copy(update={
        "params": {**agent.policy.params, "prompt_renderer": "ec-audit@1"},
    })})
    copied = resolved.model_copy(update={"spec": resolved.spec.model_copy(update={
        "cognition": resolved.spec.cognition.model_copy(update={
            "agents": (changed, *resolved.spec.cognition.agents[1:]),
        }),
    })})
    forbid_credential_read(monkeypatch)
    with pytest.raises(ValueError, match="Evidence Commons"):
        build_policies(copied, allow_provider_requests=True)
    override = (build_nipd_policy("allc", "neighbourhood", {}) if replacement == "scripted" else
                LLMPolicy("a1", FakeProvider([GOOD]), resolved.skin))
    policies = build_policies(copied, overrides={"a1": override})
    assert policies["a1"] is override


def test_opt_in_changes_only_cognition_derived_hashes():
    legacy = compile_data(scenario_data(renderer="legacy@1"))
    audited = compile_data(scenario_data())
    assert legacy.scenario_hash != audited.scenario_hash
    assert legacy.mechanism_hash == audited.mechanism_hash
    assert legacy.narrative_hash == audited.narrative_hash
    assert legacy.evidence_corpus_hash == audited.evidence_corpus_hash


def test_compatible_factory_selection_still_requires_execution_opt_in():
    resolved = compile_data(scenario_data(policy="llm_openai_compatible"))
    with pytest.raises(ValueError, match="allow_provider_requests"):
        build_policies(resolved)


@pytest.mark.parametrize("kind", ["fake", "compatible"])
def test_effective_audit_aware_override_rejects_non_ec_before_any_call(kind, monkeypatch):
    resolved = compile_data(scenario_data(world="nipd", renderer="legacy@1"))
    if kind == "fake":
        override = LLMPolicy("a1", FakeProvider([GOOD]), resolved.skin,
                             prompt_renderer="ec-audit@1")
    else:
        override = build_openai_compatible_policy("a1", resolved.skin, {
            **PARAMS, "prompt_renderer": "ec-audit@1",
        })
        monkeypatch.setattr(override.provider._opener, "open",
                            lambda *args, **kwargs: pytest.fail("network"))
    with pytest.raises(ValueError, match="Evidence Commons"):
        build_policies(resolved, overrides={"a1": override}, allow_provider_requests=True)
    assert override.call_count == 0
    assert override.transcript == []
