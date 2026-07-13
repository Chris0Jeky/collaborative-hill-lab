"""Completion providers. Only a deterministic fake exists in the foundation.

A real provider (Anthropic/OpenAI/...) is a later, human-approved addition:
it must fill model_id exactly as reported by the API, pass through real token
counts or leave them None, and never fabricate cost data (locked principle).
"""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


class ProviderError(RuntimeError):
    """Raised when a provider cannot return a completion (outage, refusal...)."""


class ProviderResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    model_id: str
    input_tokens: int | None = None
    output_tokens: int | None = None


@runtime_checkable
class CompletionProvider(Protocol):
    model_id: str

    def complete(self, prompt: str) -> ProviderResult: ...


class FakeProvider:
    """Deterministic scripted provider for tests and fixtures.

    ``script`` is either a list of responses consumed in order, or a callable
    (prompt, call_index) -> response text. ``fail_at`` simulates an outage on
    the given 0-based call index. Token counts stay None — the fake measures
    nothing, so manifests must show nothing (tested)."""

    def __init__(self, script: list[str] | Callable[[str, int], str],
                 model_id: str = "fake-provider/fake-model-1",
                 fail_at: int | None = None) -> None:
        self._script = script
        self.model_id = model_id
        self._fail_at = fail_at
        self.calls = 0

    def complete(self, prompt: str) -> ProviderResult:
        index = self.calls
        self.calls += 1
        if self._fail_at is not None and index >= self._fail_at:
            raise ProviderError(f"simulated provider outage at call {index}")
        if callable(self._script):
            text = self._script(prompt, index)
        else:
            if index >= len(self._script):
                raise ProviderError(f"fake script exhausted at call {index}")
            text = self._script[index]
        return ProviderResult(text=text, model_id=self.model_id)
