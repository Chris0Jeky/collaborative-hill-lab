"""Usage is complete only when every attempted request reports that dimension."""

import json
import random

import pytest
from pydantic import ValidationError

from collaborative_hill.agents import llm
from collaborative_hill.engine.hashing import canonical_json
from collaborative_hill.experiments.manifests import RunManifest
from collaborative_hill.experiments.scenario import NarrativeSkin
from collaborative_hill.metrics.operations import operational_metrics

GOOD = '{"action":{"type":"abstain"}}'
SKIN = NarrativeSkin(skin_id="plain")
OBSERVATION = {"mechanism": "nipd", "mode": "neighbourhood", "self_id": "a1", "round": 0}


class SequenceProvider:
    model_id = "requested-model"

    def __init__(self, results):
        self.results = iter(results)

    def complete(self, prompt):
        value = next(self.results)
        if isinstance(value, Exception):
            raise value
        return value


def _result(input_tokens=None, output_tokens=None, *, text=GOOD, model="reported-v1",
            attempts=None):
    return llm.ProviderResult(text=text, model_id=model, input_tokens=input_tokens,
                              output_tokens=output_tokens, attempts=attempts)


def _policy(*results, retries=0):
    return llm.LLMPolicy("a1", SequenceProvider(results), SKIN, max_retries=retries)


def _propose(policy):
    return policy.propose(dict(OBSERVATION), random.Random(0))


def _fields(policies, **kwargs):
    assert hasattr(llm, "llm_manifest_fields"), "manifest usage aggregation is missing"
    return llm.llm_manifest_fields(policies, **kwargs)


def test_format_retries_are_real_completions_with_usage():
    policy = _policy(_result(7, 2, text="not JSON"), _result(11, 3, model="reported-v2"),
                     retries=1)
    assert _propose(policy).action.type == "abstain"
    fields = _fields({"a1": policy})
    assert fields["input_tokens"] == 18
    assert fields["output_tokens"] == 5
    assert fields["cost_usd"] is None
    assert fields["reported_models"] == {"a1": ["reported-v1", "reported-v2"]}
    assert fields["providers"] == {"a1": "requested-model"}
    assert fields["provider_usage"]["a1"] == {
        "completion_calls": 2, "request_attempts": 2,
        "input_tokens": 18, "output_tokens": 5,
        "known_input_tokens": 18, "known_output_tokens": 5,
        "input_measured_attempts": 2, "output_measured_attempts": 2,
    }
    assert policy.call_count == 2


def test_partial_dimensions_keep_unknown_total_and_labeled_known_sum():
    a = _policy(_result(10, 4), _result(None, 6))
    b = _policy(_result(3, None))
    _propose(a)
    _propose(a)
    _propose(b)
    fields = _fields({"a1": a, "a2": b})
    assert fields["input_tokens"] is None
    assert fields["output_tokens"] is None
    assert a.usage_totals()["known_input_tokens"] == 10
    assert a.usage_totals()["input_measured_attempts"] == 1
    assert a.usage_totals()["output_tokens"] == 10
    assert b.usage_totals()["input_tokens"] == 3
    assert b.usage_totals()["output_tokens"] is None


def test_provider_failure_during_format_retry_prevents_false_complete_totals():
    policy = _policy(_result(10, 2, text="invalid"), llm.ProviderError("fixture outage"),
                     retries=1)
    with pytest.raises(llm.ProviderError, match="fixture outage"):
        _propose(policy)
    fields = _fields({"a1": policy})
    assert fields["input_tokens"] is None
    assert fields["output_tokens"] is None
    assert fields["provider_usage"]["a1"]["known_input_tokens"] == 10
    assert fields["provider_usage"]["a1"]["request_attempts"] == 2
    # Legacy providers retain their transcript format; accounting still sees failure.
    assert len(policy.transcript) == 1


def test_structured_refusal_records_measured_consumption_without_raw_refusal():
    attempt = llm.ProviderAttempt(outcome="refusal", http_status=200, model_id="reported-v1",
                                  input_tokens=12, output_tokens=2)
    policy = _policy(llm.ProviderError("provider refusal", attempts=(attempt,)))
    with pytest.raises(llm.ProviderError):
        _propose(policy)
    fields = _fields({"a1": policy})
    assert (fields["input_tokens"], fields["output_tokens"]) == (12, 2)
    assert policy.transcript[0]["outcome"] == "provider_error"
    assert policy.transcript[0]["raw_text"] is None
    assert policy.transcript[0]["provider_attempts"][0]["outcome"] == "refusal"


def test_http_attempts_are_not_confused_with_action_repair_attempts():
    attempts = (llm.ProviderAttempt(outcome="http_error", http_status=429),
                llm.ProviderAttempt(outcome="completed", http_status=200, model_id="reported-v1",
                                    input_tokens=12, output_tokens=2))
    policy = _policy(_result(12, 2, attempts=attempts))
    _propose(policy)
    fields = _fields({"a1": policy})
    assert fields["input_tokens"] is None
    usage = fields["provider_usage"]["a1"]
    assert usage["completion_calls"] == 1
    assert usage["request_attempts"] == 2
    assert usage["known_input_tokens"] == 12
    assert usage["input_measured_attempts"] == 1


def test_continuation_offset_excludes_parent_usage_and_reported_models():
    policy = _policy(_result(100, 30, model="parent-version"),
                     _result(7, 2, model="child-version"))
    _propose(policy)
    assert hasattr(policy, "call_count"), "continuation usage cursor is missing"
    offset = policy.call_count
    _propose(policy)
    fields = _fields({"a1": policy}, since={"a1": offset})
    assert (fields["input_tokens"], fields["output_tokens"]) == (7, 2)
    assert fields["reported_models"] == {"a1": ["child-version"]}
    assert fields["provider_usage_scope"] == "continuation"
    assert fields["provider_usage"]["a1"]["completion_calls"] == 1
    assert policy.usage_totals()["input_tokens"] == 107
    assert policy.audit_metadata(since=offset)["reported_models"] == ["child-version"]


def test_uncalled_agents_do_not_make_an_otherwise_measured_total_unknown():
    called = _policy(_result(0, 2))
    uncalled = _policy()
    _propose(called)
    fields = _fields({"a1": called, "a2": uncalled})
    assert (fields["input_tokens"], fields["output_tokens"]) == (0, 2)
    assert fields["provider_usage"]["a2"]["request_attempts"] == 0
    assert _fields({"a1": uncalled})["input_tokens"] is None
    assert _fields({})["input_tokens"] is None
    assert _fields({})["provider_usage_scope"] is None


@pytest.mark.parametrize("offset", [-1, 1, True, "0"])
def test_invalid_accounting_offsets_are_rejected(offset):
    policy = _policy()
    assert hasattr(policy, "usage_totals"), "usage accounting is missing"
    with pytest.raises(ValueError):
        policy.usage_totals(since=offset)


@pytest.mark.parametrize("count", [-1, True, 1.2, "2"])
def test_provider_result_cannot_fabricate_integer_token_counts(count):
    with pytest.raises(ValidationError):
        _result(count, 2)


def test_real_provider_sampling_and_identity_cannot_be_misdeclared():
    config = llm.OpenAICompatibleConfig("https://provider.invalid/chat", "same-label",
                                        {"max_tokens": 8, "temperature": "1/3"})
    provider = llm.OpenAICompatibleProvider(config, api_key=None)
    policy = llm.LLMPolicy("a1", provider, SKIN, max_retries=0)
    assert policy.sampling == {"max_tokens": 8, "temperature": "1/3"}
    with pytest.raises(ValueError):
        llm.LLMPolicy("a1", provider, SKIN, sampling={"max_tokens": 100})
    alternative = llm.OpenAICompatibleProvider(llm.OpenAICompatibleConfig(
        "https://another-provider.invalid/chat", "same-label", config.sampling,
    ), api_key=None)
    other = llm.LLMPolicy("a1", alternative, SKIN, max_retries=0)
    assert policy.policy_id != other.policy_id
    fields = _fields({"a1": policy})
    assert fields["provider_metadata"]["a1"]["endpoint"] == config.endpoint
    assert fields["sampling"]["a1"] == {"max_tokens": 8, "temperature": "1/3"}
    assert "api_key_env" not in json.dumps(fields)
    canonical_json(fields)  # No wire floats leak into scientific metadata.


def test_fake_policy_identity_and_unmeasured_usage_remain_compatible():
    policy = llm.LLMPolicy("a1", llm.FakeProvider([GOOD]), SKIN)
    expected_id = (f"llm[fake-provider/fake-model-1,skin=plain,"
                   f"tpl={policy.prompt_template_hash[:12]}]@1")
    assert policy.policy_id == expected_id
    _propose(policy)
    fields = _fields({"a1": policy})
    assert fields["provider_metadata"] == {}
    assert fields["sampling"] == {}
    assert fields["input_tokens"] is None and fields["output_tokens"] is None
    assert "provider_attempts" not in policy.transcript[0]


def test_manifest_accepts_usage_fields_and_operational_metrics_preserve_them():
    policy = _policy(_result(9, 2))
    _propose(policy)
    manifest = RunManifest(
        study_id="fixture", condition_id="cell", run_id="run", replicate=0,
        scenario_hash="s", mechanism_hash="m", narrative_hash="n", evidence_corpus_hash="e",
        institution={}, **_fields({"a1": policy}),
    )
    data = manifest.model_dump(mode="json")
    assert data["reported_models"] == {"a1": ["reported-v1"]}
    assert data["provider_usage_scope"] == "episode"
    ops = operational_metrics([], data)
    assert (ops["input_tokens"], ops["output_tokens"], ops["cost_usd"]) == (9, 2, None)


@pytest.mark.parametrize("text", [
    pytest.param('{"action":{"type":"abstain"},"extra":' + "1" * 5000 + "}",
                 id="integer-decoding-limit"),
    pytest.param("[" * 10000 + "0" + "]" * 10000, id="nesting-decoding-limit"),
])
def test_action_decoding_limits_preserve_invalid_output_and_measured_usage(text):
    policy = _policy(_result(12, 5, text=text))
    proposal = _propose(policy)
    assert proposal.action.type == "abstain"
    assert proposal.action.reason == "invalid_llm_output"
    assert len(policy.transcript) == 1
    assert policy.transcript[0]["raw_text"] == text
    assert policy.transcript[0]["outcome"].startswith("invalid:")
    assert policy.usage_totals()["input_tokens"] == 12
    assert len(proposal.justification) < 250
