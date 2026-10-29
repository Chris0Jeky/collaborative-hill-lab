"""Provider protocol and deterministic fixture; unavailable usage remains unknown."""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class ProviderAttempt(BaseModel):
    """Safe metadata for one HTTP request, including unsuccessful requests."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: str
    http_status: int | None = None
    model_id: str | None = None
    input_tokens: int | None = Field(default=None, strict=True, ge=0)
    output_tokens: int | None = Field(default=None, strict=True, ge=0)


class ProviderError(RuntimeError):
    """Raised when a provider cannot return a completion (outage, refusal...)."""

    def __init__(self, message: str, *,
                 attempts: tuple[ProviderAttempt, ...] | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts


class ProviderResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    model_id: str
    input_tokens: int | None = Field(default=None, strict=True, ge=0)
    output_tokens: int | None = Field(default=None, strict=True, ge=0)
    attempts: tuple[ProviderAttempt, ...] | None = None


@runtime_checkable
class CompletionProvider(Protocol):
    @property
    def model_id(self) -> str: ...

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
