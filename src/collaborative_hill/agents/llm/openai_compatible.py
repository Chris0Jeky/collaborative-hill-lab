"""Explicit, bounded non-streaming Chat Completions transport (ADR-0010).

No SDK, implicit endpoint/model, streaming, automatic ambiguous-request retries,
raw error-body persistence or price estimation. Construction does not make a call.
"""

import json
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any, NoReturn

from collaborative_hill.agents.llm.configuration import OpenAICompatibleConfig
from collaborative_hill.agents.llm.providers import ProviderAttempt, ProviderError, ProviderResult

_MAX_RESPONSE_BYTES = 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        return None


def _token_count(usage: dict[str, Any], key: str) -> tuple[int | None, bool]:
    value = usage.get(key)
    if value is None:
        return None, True
    if type(value) is int and value >= 0:
        return value, True
    return None, False


def _reject_constant(value: str) -> NoReturn:
    raise ValueError("nonstandard JSON numeric constant")


class OpenAICompatibleProvider:
    """A provider whose endpoint, model and bounded sampling are explicit.

    ``api_key`` is private process memory only. Passing None explicitly supports
    an unauthenticated compatible endpoint. The timeout is a socket I/O timeout;
    it neither cancels remote generation nor guarantees a wall-clock deadline.
    """

    def __init__(self, config: OpenAICompatibleConfig, *, api_key: str | None) -> None:
        if api_key is not None and (not isinstance(api_key, str) or not api_key
                                    or any(ord(c) <= 32 or ord(c) >= 127 for c in api_key)):
            raise ValueError("provider credential must be a nonempty printable bearer token")
        self._config = config
        self._api_key = api_key
        if api_key is not None and self._contains_secret(self.audit_metadata()):
            raise ValueError("provider credentials must not appear in public configuration")
        self._opener = urllib.request.build_opener(_NoRedirect())

    @property
    def config(self) -> OpenAICompatibleConfig:
        return self._config

    @property
    def model_id(self) -> str:
        return self.config.model_id

    @property
    def sampling(self) -> Mapping[str, str | int]:
        return self.config.sampling

    @property
    def default_action_retries(self) -> int:
        return self.config.max_retries

    def audit_metadata(self) -> dict[str, Any]:
        return {
            "transport": "openai-compatible-chat@1", "endpoint": self.config.endpoint,
            "requested_model_id": self.model_id, "sampling": dict(self.config.sampling),
            "wire_sampling": {key: json.dumps(value) if isinstance(value, float) else value
                              for key, value in self.config.wire_sampling().items()},
            "timeout_seconds": self.config.timeout_seconds,
            "rate_limit_retries": self.config.rate_limit_retries,
            "retry_delay_seconds": self.config.retry_delay_seconds,
            "max_response_bytes": _MAX_RESPONSE_BYTES,
            "authenticated": self._api_key is not None,
        }

    def _contains_secret(self, value: Any) -> bool:
        if self._api_key is None:
            return False
        pending = [value]
        while pending:
            item = pending.pop()
            if isinstance(item, str) and self._api_key in item:
                return True
            if isinstance(item, dict):
                pending.extend(item.keys())
                pending.extend(item.values())
            elif isinstance(item, list | tuple):
                pending.extend(item)
        return False

    def complete(self, prompt: str) -> ProviderResult:
        if not isinstance(prompt, str) or self._contains_secret(prompt):
            raise ProviderError("provider prompt contains invalid or sensitive input", attempts=())
        payload = {"model": self.model_id, "messages": [{"role": "user", "content": prompt}],
                   "stream": False, "n": 1, **self.config.wire_sampling()}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key is not None:
            headers["Authorization"] = "Bearer " + self._api_key
        body = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode("utf-8")
        attempts: list[ProviderAttempt] = []
        for index in range(self.config.rate_limit_retries + 1):
            request = urllib.request.Request(self.config.endpoint, body, headers, method="POST")
            try:
                with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                    raw = response.read(_MAX_RESPONSE_BYTES + 1)
                    status = response.status
            except urllib.error.HTTPError as exc:
                status = exc.code
                exc.close()
                attempts.append(ProviderAttempt(outcome="http_error", http_status=status))
                if status == 429 and index < self.config.rate_limit_retries:
                    time.sleep(self.config.retry_delay_seconds)
                    continue
                raise ProviderError(f"provider HTTP error ({status})", attempts=tuple(attempts)) \
                    from None
            except Exception as exc:
                reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
                kind = "timeout" if isinstance(reason, TimeoutError) else "transport_error"
                attempts.append(ProviderAttempt(outcome=kind))
                raise ProviderError(f"provider {kind}", attempts=tuple(attempts)) from None
            if len(raw) > _MAX_RESPONSE_BYTES:
                attempts.append(ProviderAttempt(outcome="response_too_large", http_status=status))
                raise ProviderError("provider response exceeds size limit",
                                    attempts=tuple(attempts))
            try:
                result = self._decode(raw, status)
            except ProviderError as exc:
                raise ProviderError(str(exc), attempts=tuple(attempts) + (exc.attempts or ())) \
                    from None
            return result.model_copy(update={"attempts": tuple(attempts) + (result.attempts or ())})
        raise AssertionError("bounded provider loop must return or raise")

    def _decode(self, raw: bytes, status: int) -> ProviderResult:
        try:
            data = json.loads(raw, parse_constant=_reject_constant)
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, UnicodeError, RecursionError):
            raise ProviderError("provider invalid response", attempts=(
                ProviderAttempt(outcome="invalid_response", http_status=status),
            )) from None

        model_id = data.get("model")
        model_valid = (isinstance(model_id, str) and bool(model_id.strip())
                       and not any(ord(c) < 32 for c in model_id))
        usage = data.get("usage")
        usage_valid = usage is None or isinstance(usage, dict)
        counts = usage if isinstance(usage, dict) else {}
        input_tokens, input_valid = _token_count(counts, "prompt_tokens")
        output_tokens, output_valid = _token_count(counts, "completion_tokens")
        attempt = ProviderAttempt(
            outcome="completed", http_status=status,
            model_id=model_id if model_valid and not self._contains_secret(model_id) else None,
            input_tokens=input_tokens, output_tokens=output_tokens,
        )

        def fail(outcome: str) -> NoReturn:
            raise ProviderError(f"provider {outcome}", attempts=(
                attempt.model_copy(update={"outcome": outcome}),
            ))

        if self._contains_secret(data):
            fail("sensitive_response")
        if (not isinstance(model_id, str) or not model_valid or not usage_valid
                or not input_valid or not output_valid):
            fail("invalid_response")
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            fail("invalid_response")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            fail("invalid_response")
        if message.get("refusal") is not None or choice.get("finish_reason") == "content_filter":
            fail("refusal")
        if choice.get("finish_reason") == "length":
            fail("incomplete_completion")
        if choice.get("finish_reason") != "stop" or message.get("tool_calls"):
            fail("unsupported_completion")
        content = message.get("content")
        if not isinstance(content, str):
            fail("invalid_response")
        return ProviderResult(text=content, model_id=model_id, input_tokens=input_tokens,
                              output_tokens=output_tokens, attempts=(attempt,))
