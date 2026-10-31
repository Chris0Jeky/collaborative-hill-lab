"""Cumulative HTTP request-attempt admission, an operational control (ADR-0015).

The unit is one outbound HTTP request attempt: first POSTs, HTTP 429 retries and
action-repair completions all count. An attempt is charged when it is ADMITTED,
before it is sent, so a timeout, transport error or response without usage can
never be undercounted. This is neither a token nor a currency budget, and no
default limit exists: an unset limit means "unlimited", not "safe".

Scopes (all counters live on one shared object; nothing resets on a retry):
  episode       attempts since ``begin("episode")``; resets only at a new episode
  run           attempts for the object's whole life (one ``chl run`` invocation)
  continuation  ``begin("continuation")`` marks a branch start WITHOUT resetting
                any counter, so reusing the object keeps charging the same limits

The deadline uses ``time.monotonic`` (or the injected clock) and is checked only
BETWEEN requests: before and after a 429 retry delay, and at each admission. It is not
an in-flight bound: a request admitted just before the deadline can still run for
up to the transport's socket timeout (and longer if DNS or the server stalls).
"""

import time
from collections.abc import Callable
from typing import Any, Literal


class RequestBudgetExhausted(RuntimeError):
    """A request was refused before it was sent; ``reason`` is a stable code.

    The transport re-raises this as a plain ``ProviderError`` carrying the same
    message: the runner seals ``policy error for X: ProviderError: <message>`` and
    replay decodes exactly that prefix, so the sealed text carries the stable code.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"provider request budget exhausted: {reason}")
        self.reason = reason


def _limit(value: int | None, name: str) -> int | None:
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError(f"{name} must be a nonnegative integer or None")
    return value


class RequestBudget:
    def __init__(self, *, max_episode_attempts: int | None = None,
                 max_run_attempts: int | None = None, deadline_seconds: int | None = None,
                 cancelled: Callable[[], bool] | None = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.max_episode_attempts = _limit(max_episode_attempts, "max_episode_attempts")
        self.max_run_attempts = _limit(max_run_attempts, "max_run_attempts")
        self.deadline_seconds = _limit(deadline_seconds, "deadline_seconds")
        self._cancelled = cancelled
        self._clock = clock
        # The deadline counts from construction: construct it just before executing.
        self._deadline = (clock() + self.deadline_seconds
                          if self.deadline_seconds is not None else None)
        self._episode = self._run = 0
        self._scope: Literal["episode", "continuation"] = "episode"
        self._before = {"episode": 0, "run": 0}
        self._stop: str | None = None

    @property
    def admitted(self) -> dict[str, int]:
        return {"episode": self._episode, "run": self._run}

    def begin(self, scope: Literal["episode", "continuation"]) -> None:
        """Mark a new episode (resets the episode counter) or a continuation (does not)."""
        self._scope = scope
        self._before = self.admitted
        self._stop = None  # a stop describes one manifest; refusals are re-evaluated per request
        if scope == "episode":
            self._episode = 0
            self._before["episode"] = 0

    def check(self, *, after_seconds: int = 0) -> None:
        """Raise if a request would be refused, ``after_seconds`` from now, without charging."""
        reason = self._refusal(after_seconds)
        if reason is not None:
            self._stop = reason
            raise RequestBudgetExhausted(reason)

    def admit(self) -> None:
        """Charge one attempt immediately before sending, or raise."""
        self.check()
        self._episode += 1
        self._run += 1

    def _refusal(self, after_seconds: int) -> str | None:
        if self._cancelled is not None and self._cancelled():
            return "cancelled"
        if self._deadline is not None and self._clock() + after_seconds >= self._deadline:
            return "deadline_exceeded"
        if self.max_run_attempts is not None and self._run >= self.max_run_attempts:
            return "request_attempt_limit_run"
        if (self.max_episode_attempts is not None
                and self._episode >= self.max_episode_attempts):
            return "request_attempt_limit_episode"
        return None

    def snapshot(self) -> dict[str, Any]:
        """Manifest record: settings, charged attempts and the stable stop reason."""
        return {
            "unit": "http_request_attempts",
            "limits": {"episode": self.max_episode_attempts, "run": self.max_run_attempts,
                       "deadline_seconds": self.deadline_seconds},
            "deadline_check": "between_requests_monotonic",
            "scope": self._scope,
            "admitted_before": dict(self._before),
            "admitted": self.admitted,
            "stop_reason": self._stop,
        }
