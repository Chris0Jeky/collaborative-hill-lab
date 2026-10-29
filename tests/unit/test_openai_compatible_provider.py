"""Offline wire-contract checks for an explicitly configured completion provider."""

import io
import json
import socket
import urllib.error
import urllib.request
import urllib.response
from email.message import Message

import pytest

from collaborative_hill.agents import llm

GOOD = '{"action":{"type":"abstain"}}'
SECRET = "unit-test-private-key-DO-NOT-PERSIST"
ENDPOINT = "https://provider.invalid/v1/chat/completions"


def _response(**updates):
    body = {
        "id": "chatcmpl-test", "object": "chat.completion", "created": 0,
        "model": "reported-model-version",
        "choices": [{"index": 0, "message": {
            "role": "assistant", "content": GOOD, "refusal": None,
        }, "finish_reason": "stop", "logprobs": None}],
        "usage": {"prompt_tokens": 17, "completion_tokens": 3, "total_tokens": 20},
    }
    body.update(updates)
    return body


@pytest.fixture
def wire(monkeypatch):
    replies, requests, sleeps = [], [], []

    def no_network(*args, **kwargs):
        pytest.fail("a provider test attempted an actual network connection")

    def open_request(handler, request):
        requests.append(request)
        assert replies, "unexpected extra POST"
        item = replies.pop(0)
        if isinstance(item, Exception):
            raise item
        status, body, headers = item
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        message = Message()
        for key, value in headers.items():
            message[key] = value
        response = urllib.response.addinfourl(io.BytesIO(raw), message,
                                             request.full_url, status)
        response.msg = "fixture status"
        return response

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(urllib.request.HTTPSHandler, "https_open", open_request)
    monkeypatch.setattr(urllib.request.HTTPHandler, "http_open", open_request)
    monkeypatch.setattr("time.sleep", sleeps.append)
    return replies, requests, sleeps


def _config(**updates):
    assert hasattr(llm, "OpenAICompatibleConfig"), "public explicit provider config is missing"
    values = {"endpoint": ENDPOINT, "model_id": "requested-model",
              "sampling": {"max_completion_tokens": 64, "temperature": "1/2"}}
    values.update(updates)
    return llm.OpenAICompatibleConfig(**values)


def _provider(**updates):
    assert hasattr(llm, "OpenAICompatibleProvider"), "public provider transport is missing"
    return llm.OpenAICompatibleProvider(_config(**updates), api_key=SECRET)


def test_explicit_request_and_reported_usage(wire):
    replies, requests, _ = wire
    replies.append((200, _response(), {}))
    provider = _provider(timeout_seconds=7)
    assert requests == []  # Construction is offline.

    result = provider.complete("visible observation only")

    assert result.text == GOOD
    assert result.model_id == "reported-model-version"
    assert (result.input_tokens, result.output_tokens) == (17, 3)
    assert provider.model_id == "requested-model"
    assert len(requests) == 1
    request = requests[0]
    assert request.full_url == ENDPOINT
    assert request.get_method() == "POST"
    assert request.timeout == 7
    assert request.get_header("Authorization") == f"Bearer {SECRET}"
    assert json.loads(request.data) == {
        "model": "requested-model", "messages": [
            {"role": "user", "content": "visible observation only"},
        ], "stream": False, "n": 1, "max_completion_tokens": 64, "temperature": 0.5,
    }
    assert len(result.attempts) == 1
    assert result.attempts[0].input_tokens == 17
    assert SECRET not in repr(provider)
    assert SECRET not in json.dumps(provider.audit_metadata())


@pytest.mark.parametrize("usage,expected", [
    (None, (None, None)), ({}, (None, None)),
    ({"prompt_tokens": 0}, (0, None)),
    ({"completion_tokens": 2}, (None, 2)),
])
def test_unavailable_or_partial_usage_is_not_invented(wire, usage, expected):
    wire[0].append((200, _response(usage=usage), {}))
    result = _provider().complete("prompt")
    assert (result.input_tokens, result.output_tokens) == expected


@pytest.mark.parametrize("status", [400, 401, 403, 408, 500, 502, 503])
def test_http_errors_are_sanitized_and_not_retried(wire, status):
    wire[0].append((status, {"error": {"message": f"secret {SECRET}"}}, {}))
    provider = _provider(rate_limit_retries=3)
    with pytest.raises(llm.ProviderError) as raised:
        provider.complete("private prompt")
    assert str(status) in str(raised.value)
    assert SECRET not in str(raised.value)
    assert "private prompt" not in str(raised.value)
    assert len(wire[1]) == 1
    assert wire[2] == []
    assert raised.value.attempts[0].http_status == status


@pytest.mark.parametrize("failure", [
    TimeoutError(SECRET), urllib.error.URLError(TimeoutError(SECRET)),
    urllib.error.URLError(SECRET), OSError(SECRET), RuntimeError(SECRET),
])
def test_ambiguous_transport_failure_never_reposts(wire, failure):
    wire[0].append(failure)
    with pytest.raises(llm.ProviderError) as raised:
        _provider(rate_limit_retries=3).complete("prompt")
    assert SECRET not in str(raised.value)
    assert SECRET not in repr(raised.value)
    assert len(wire[1]) == 1
    assert len(raised.value.attempts) == 1
    assert raised.value.attempts[0].input_tokens is None
    assert wire[2] == []


def test_redirect_cannot_forward_authorization(wire):
    wire[0].append((302, b"", {"Location": "https://elsewhere.invalid/collect"}))
    with pytest.raises(llm.ProviderError):
        _provider().complete("prompt")
    assert [request.full_url for request in wire[1]] == [ENDPOINT]


def test_429_is_not_retried_by_default(wire):
    wire[0].append((429, {}, {"Retry-After": "999999"}))
    with pytest.raises(llm.ProviderError):
        _provider().complete("prompt")
    assert len(wire[1]) == 1
    assert wire[2] == []


def test_opted_in_429_retry_keeps_unknown_attempt_usage(wire):
    wire[0].extend([(429, {}, {"Retry-After": "999999"}), (200, _response(), {})])
    result = _provider(rate_limit_retries=1, retry_delay_seconds=2).complete("prompt")
    assert len(wire[1]) == 2
    assert wire[2] == [2]
    assert [attempt.http_status for attempt in result.attempts] == [429, 200]
    assert [attempt.input_tokens for attempt in result.attempts] == [None, 17]


def test_429_retries_stop_at_the_configured_bound(wire):
    wire[0].extend([(429, {}, {})] * 4)
    with pytest.raises(llm.ProviderError) as raised:
        _provider(rate_limit_retries=2).complete("prompt")
    assert len(wire[1]) == 3
    assert len(raised.value.attempts) == 3
    assert wire[2] == [1, 1]


@pytest.mark.parametrize("body", [
    b"not JSON", b"\xff", b"[]", b"NaN", {},
    _response(model=None), _response(choices=[]),
    _response(choices=[{"message": {"content": GOOD}, "finish_reason": "stop"}]),
    _response(usage={"prompt_tokens": -1, "completion_tokens": 3}),
    _response(usage={"prompt_tokens": True, "completion_tokens": 3}),
    _response(usage={"prompt_tokens": "17", "completion_tokens": 3}),
])
def test_malformed_response_fails_without_reposting(wire, body):
    wire[0].append((200, body, {}))
    with pytest.raises(llm.ProviderError):
        _provider(rate_limit_retries=3).complete("prompt")
    assert len(wire[1]) == 1


@pytest.mark.parametrize("finish_reason,refusal", [
    ("stop", "refusal with private details"), ("content_filter", None),
    ("length", None), ("tool_calls", None),
])
def test_noncompletion_outcomes_keep_real_usage(wire, finish_reason, refusal):
    body = _response()
    body["choices"][0]["finish_reason"] = finish_reason
    body["choices"][0]["message"]["refusal"] = refusal
    wire[0].append((200, body, {}))
    with pytest.raises(llm.ProviderError) as raised:
        _provider().complete("prompt")
    assert "private details" not in str(raised.value)
    attempt, = raised.value.attempts
    assert (attempt.input_tokens, attempt.output_tokens) == (17, 3)
    assert attempt.model_id == "reported-model-version"


@pytest.mark.parametrize("field", ["model", "content"])
def test_reflected_credentials_never_escape_the_provider(wire, field):
    body = _response()
    if field == "model":
        body["model"] = SECRET
    else:
        body["choices"][0]["message"]["content"] = f"{GOOD} {SECRET}"
    wire[0].append((200, body, {}))
    with pytest.raises(llm.ProviderError) as raised:
        _provider().complete("prompt")
    assert SECRET not in str(raised.value)
    assert SECRET not in repr(raised.value)
    assert SECRET not in json.dumps([a.model_dump() for a in raised.value.attempts])


def test_response_size_is_bounded(wire):
    wire[0].append((200, b"x" * (1024 * 1024 + 1), {}))
    with pytest.raises(llm.ProviderError):
        _provider().complete("prompt")
    assert len(wire[1]) == 1


@pytest.mark.parametrize("changes", [
    {"endpoint": "https://user:password@provider.invalid/chat"},
    {"endpoint": f"{ENDPOINT}?api_key={SECRET}"},
    {"endpoint": f"{ENDPOINT}#private"},
    {"endpoint": "http://provider.invalid/chat"},
    {"endpoint": "http://127.0.0.1/chat"},
    {"endpoint": "https://provider.invalid/\nchat"},
    {"model_id": ""}, {"model_id": "bad\nmodel"},
    {"sampling": {}}, {"sampling": {"max_tokens": 0}},
    {"sampling": {"max_tokens": True}},
    {"sampling": {"max_tokens": 1, "max_completion_tokens": 1}},
    {"sampling": {"max_tokens": 1, "temperature": 0.5}},
    {"sampling": {"max_tokens": 1, "temperature": "3"}},
    {"sampling": {"max_tokens": 1, "top_p": "-1/10"}},
    {"sampling": {"max_tokens": 1, "seed": True}},
    {"sampling": {"max_tokens": 1, "unknown": "x"}},
    {"timeout_seconds": 0}, {"timeout_seconds": 301}, {"timeout_seconds": True},
    {"rate_limit_retries": 4}, {"rate_limit_retries": -1},
    {"retry_delay_seconds": 61}, {"max_retries": -1}, {"max_retries": 4},
    {"api_key_env": "not-an-env-name"},
])
def test_invalid_configuration_is_rejected_offline(wire, changes):
    with pytest.raises(ValueError) as raised:
        _config(**changes)
    assert SECRET not in str(raised.value)
    assert wire[1] == []


def test_sampling_configuration_cannot_drift_after_construction(wire):
    sampling = {"max_tokens": 8, "top_p": "3/4"}
    config = _config(sampling=sampling)
    sampling["max_tokens"] = 900
    with pytest.raises(TypeError):
        config.sampling["max_tokens"] = 900
    wire[0].append((200, _response(), {}))
    llm.OpenAICompatibleProvider(config, api_key=None).complete("prompt")
    assert json.loads(wire[1][0].data)["max_tokens"] == 8
    assert wire[1][0].get_header("Authorization") is None


def test_explicit_loopback_http_is_usable(wire):
    wire[0].append((200, _response(), {}))
    provider = _provider(endpoint="http://127.0.0.1:1234/v1/chat/completions",
                         allow_insecure_localhost=True)
    assert provider.complete("prompt").text == GOOD


def test_factory_accepts_only_flat_nonsecret_configuration(wire, monkeypatch):
    assert hasattr(llm, "validate_provider_params"), "flat provider validation is missing"
    assert hasattr(llm, "build_openai_compatible_policy"), "provider policy factory is missing"
    from collaborative_hill.experiments.scenario import NarrativeSkin

    params = {"endpoint": ENDPOINT, "model_id": "requested-model", "max_tokens": 64,
              "temperature": "1/2", "api_key_env": "CHL_UNIT_TEST_KEY"}
    monkeypatch.delenv("CHL_UNIT_TEST_KEY", raising=False)
    llm.validate_provider_params(params)  # Validation never reads credentials.
    with pytest.raises(ValueError):
        llm.build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), params)
    monkeypatch.setenv("CHL_UNIT_TEST_KEY", SECRET)
    policy = llm.build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), params)
    assert policy.max_retries == 0
    assert policy.sampling == {"max_tokens": 64, "temperature": "1/2"}
    for key, value in (("api_key", SECRET), ("sampling", {}), ("typo", 1)):
        with pytest.raises(ValueError):
            llm.validate_provider_params({**params, key: value})
    assert wire[1] == []


def test_direct_policy_defaults_do_not_add_billable_format_repairs(wire):
    import random

    from collaborative_hill.experiments.scenario import NarrativeSkin

    body = _response()
    body["choices"][0]["message"]["content"] = "not an action"
    wire[0].append((200, body, {}))
    policy = llm.LLMPolicy("a1", _provider(), NarrativeSkin(skin_id="plain"))
    assert policy.max_retries == 0
    proposal = policy.propose({"self_id": "a1", "round": 0, "mechanism": "nipd",
                               "mode": "neighbourhood"}, random.Random(0))
    assert proposal.action.reason == "invalid_llm_output"
    assert len(wire[1]) == 1


def test_nonstandard_json_numbers_are_a_sanitized_protocol_failure(wire):
    wire[0].append((200, _response(unknown_extra=float("nan")), {}))
    with pytest.raises(llm.ProviderError):
        _provider().complete("prompt")


def test_nested_credential_reflection_cannot_escape_as_an_untyped_error(wire):
    nested = SECRET
    for _ in range(600):
        nested = [nested]
    wire[0].append((200, _response(unknown_extra=nested), {}))
    with pytest.raises(llm.ProviderError) as raised:
        _provider().complete("prompt")
    assert SECRET not in str(raised.value)
    assert SECRET not in repr(raised.value.attempts)


def test_sensitive_response_seals_failure_without_persisting_the_credential(wire, tmp_path):
    from _fixtures import AGENTS, ec_hand_example, run_episode_tmp

    from collaborative_hill.domain.institutions import InstitutionConfig
    from collaborative_hill.experiments.scenario import NarrativeSkin

    body = _response(model=SECRET)
    wire[0].append((200, body, {}))
    policies = {agent: llm.LLMPolicy(agent, _provider() if agent == "a1" else
                                    llm.FakeProvider([GOOD]), NarrativeSkin(skin_id="plain"))
                for agent in AGENTS}
    result, _, paths = run_episode_tmp(ec_hand_example(InstitutionConfig(), rounds=1),
                                       policies, tmp_path)
    assert result.status == "failed"
    assert "ProviderError" in result.failure_reason
    assert SECRET not in paths.events.read_text()
    assert SECRET not in json.dumps(policies["a1"].transcript)
    fields = llm.llm_manifest_fields(policies)
    assert SECRET not in json.dumps(fields)
    assert (fields["input_tokens"], fields["output_tokens"]) == (17, 3)


def test_provider_execution_configuration_is_read_only(wire):
    provider = _provider()
    with pytest.raises(AttributeError):
        provider.model_id = "changed-model"
    with pytest.raises(AttributeError):
        provider.config = _config(endpoint="https://elsewhere.invalid/chat")
    with pytest.raises(TypeError):
        provider.sampling["max_completion_tokens"] = 999
    assert wire[1] == []


@pytest.mark.parametrize("field", ["max_retries", "sampling", "skin"])
def test_real_policy_rejects_execution_configuration_drift(wire, field):
    import random

    from collaborative_hill.experiments.scenario import NarrativeSkin

    policy = llm.LLMPolicy("a1", _provider(), NarrativeSkin(skin_id="plain"))
    values = {"max_retries": 1, "sampling": {"max_tokens": 999},
              "skin": NarrativeSkin(skin_id="changed-skin")}
    setattr(policy, field, values[field])
    wire[0].append((200, _response(), {}))
    with pytest.raises(llm.ProviderError, match="configuration"):
        policy.propose({"self_id": "a1", "round": 0, "mechanism": "nipd",
                        "mode": "neighbourhood"}, random.Random(0))
    assert wire[1] == []
    assert policy.call_count == 0
