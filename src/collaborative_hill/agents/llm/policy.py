"""LLM-backed policy: strict typed-action parsing, bounded retries, safe abstention.

Invalid model output is NEVER silently repaired into a hoped-for action
(ADR-0007). The escalation ladder is:

  attempt 0..max_retries: parse strict JSON -> ActionProposal. A parse or
      schema failure re-prompts once per retry with the error appended.
  exhausted: return AbstainAction(reason="invalid_llm_output") — visible in
      the hashed ledger — while the raw attempts land in the run's unhashed
      transcript sidecar (llm_transcript.jsonl) for audit.

Provider errors propagate; the runner seals the run as RunFailed (typed
failure), satisfying the provider-failure acceptance test. Mechanism-level
illegality (valid schema, illegal action) is the runner/mechanism's job:
it produces ActionRejected + the configured fallback there, not here.
"""

import json
import random
from collections.abc import Mapping
from copy import deepcopy
from types import MappingProxyType
from typing import Any

from pydantic import ValidationError

from collaborative_hill.agents.llm.accounting import summarize_attempts
from collaborative_hill.agents.llm.providers import (
    CompletionProvider,
    ProviderAttempt,
    ProviderError,
)
from collaborative_hill.agents.llm.rendering import prompt_template_hash, render_prompt
from collaborative_hill.domain.actions import ActionProposal
from collaborative_hill.engine.hashing import canonical_json, sha256_hex
from collaborative_hill.experiments.scenario import NarrativeSkin


class LLMPolicy:
    def __init__(self, agent_id: str, provider: CompletionProvider, skin: NarrativeSkin,
                 max_retries: int | None = None, sampling: dict[str, Any] | None = None) -> None:
        self.agent_id = agent_id
        self.provider = provider
        self.skin = skin
        if max_retries is None:
            max_retries = getattr(provider, "default_action_retries", 1)
        if type(max_retries) is not int or max_retries < 0:
            raise ValueError("max_retries must be a nonnegative integer")
        self.max_retries = max_retries
        provider_audit = getattr(provider, "audit_metadata", None)
        self._provider_metadata = deepcopy(provider_audit()) if callable(provider_audit) else {}
        self.sampling: Mapping[str, Any] = dict(sampling or {})
        if self._provider_metadata:
            effective_sampling = self._provider_metadata["sampling"]
            if sampling is not None and sampling != effective_sampling:
                raise ValueError("policy sampling must match the configured provider request")
            self.sampling = MappingProxyType(dict(effective_sampling))
            self._provider_metadata["action_retries"] = max_retries
        self.prompt_template_hash = prompt_template_hash(skin)
        self.policy_id = (f"llm[{provider.model_id},skin={skin.skin_id},"
                          f"tpl={self.prompt_template_hash[:12]}]@1")
        if self._provider_metadata:
            identity = sha256_hex(canonical_json(self._provider_metadata))[:16]
            self.policy_id = self.policy_id.replace("]@1", f",provider={identity}]@1")
        # Unhashed audit trail; the study runner writes it to llm_transcript.jsonl.
        self.transcript: list[dict[str, Any]] = []
        self._calls: list[tuple[ProviderAttempt, ...]] = []

    @property
    def call_count(self) -> int:
        """A cursor for auditing only a subsequent continuation of this policy."""
        return len(self._calls)

    def _attempts_since(self, since: int) -> list[ProviderAttempt]:
        if type(since) is not int or not 0 <= since <= self.call_count:
            raise ValueError("usage cursor must be an existing nonnegative completion-call offset")
        return [attempt for call in self._calls[since:] for attempt in call]

    def usage_totals(self, *, since: int = 0) -> dict[str, int | None]:
        attempts = self._attempts_since(since)
        return {"completion_calls": self.call_count - since,
                **summarize_attempts(attempts)}

    def audit_metadata(self, *, since: int = 0) -> dict[str, Any]:
        attempts = self._attempts_since(since)
        return {"provider": self.provider.model_id,
                "prompt_template_hash": self.prompt_template_hash,
                "sampling": dict(self.sampling),
                "provider_metadata": deepcopy(self._provider_metadata),
                "reported_models": sorted({attempt.model_id for attempt in attempts
                                           if attempt.model_id is not None})}

    def _check_provider_configuration(self) -> None:
        """Refuse provenance drift before making a real provider request."""
        if not self._provider_metadata:
            return
        try:
            current = self.provider.audit_metadata()  # type: ignore[attr-defined]
            current["action_retries"] = self.max_retries
            unchanged = (
                canonical_json(current) == canonical_json(self._provider_metadata)
                and canonical_json(dict(self.sampling)) ==
                canonical_json(self._provider_metadata["sampling"])
                and prompt_template_hash(self.skin) == self.prompt_template_hash
            )
        except Exception:
            unchanged = False
        if not unchanged:
            raise ProviderError("provider configuration changed; construct a new policy",
                                attempts=())

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        del rng  # sampling randomness belongs to the provider, not the kernel streams
        self._check_provider_configuration()
        prompt = render_prompt(observation, self.skin)
        attempt_prompt = prompt
        last_error = ""
        for attempt in range(self.max_retries + 1):
            base = {"agent_id": self.agent_id, "round": observation.get("round"),
                    "attempt": attempt, "prompt_sha256": sha256_hex(attempt_prompt)}
            try:
                result = self.provider.complete(attempt_prompt)
            except Exception as exc:
                reported = exc.attempts if isinstance(exc, ProviderError) else None
                failures = reported if reported is not None else (
                    ProviderAttempt(outcome="provider_error"),
                )
                self._calls.append(failures)
                # Preserve old fake/custom transcript shape while recording a
                # real transport's failed requests and any measured refusal usage.
                if reported is not None:
                    usage = summarize_attempts(failures)
                    self.transcript.append({
                        **base, "raw_text": None,
                        "model_id": failures[-1].model_id if failures else None,
                        "input_tokens": usage["input_tokens"],
                        "output_tokens": usage["output_tokens"], "outcome": "provider_error",
                        "provider_attempts": [item.model_dump(mode="json") for item in failures],
                    })
                raise
            self._calls.append(result.attempts if result.attempts is not None else (
                ProviderAttempt(outcome="completed", model_id=result.model_id,
                                input_tokens=result.input_tokens,
                                output_tokens=result.output_tokens),
            ))
            proposal, error = self._parse(result.text)
            entry = {
                **base,
                "raw_text": result.text,
                "model_id": result.model_id,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "outcome": "parsed" if error is None else f"invalid: {error}",
            }
            if result.attempts is not None:
                entry["provider_attempts"] = [item.model_dump(mode="json")
                                              for item in result.attempts]
            self.transcript.append(entry)
            if proposal is not None:
                return proposal
            last_error = error or "unknown parse error"
            attempt_prompt = (
                prompt
                + "\n## Your previous reply was invalid: "
                + last_error
                + "\nReply with EXACTLY one valid JSON object."
            )
        from collaborative_hill.domain.actions import AbstainAction

        return ActionProposal(
            action=AbstainAction(reason="invalid_llm_output"),
            justification=(f"output invalid after {self.max_retries + 1} attempts: "
                           f"{last_error[:200]}"),
        )

    @staticmethod
    def _parse(text: str) -> tuple[ActionProposal | None, str | None]:
        try:
            data = json.loads(text.strip())
        except json.JSONDecodeError as exc:
            return None, f"not JSON: {exc}"
        except (ValueError, RecursionError):
            return None, "not JSON: decoder limits exceeded"
        if not isinstance(data, dict):
            return None, "top level must be a JSON object"
        allowed = {"action", "justification", "message_to", "message"}
        unknown = set(data) - allowed
        if unknown:
            return None, f"unknown keys: {sorted(unknown)}"
        try:
            return ActionProposal.model_validate(data), None
        except ValidationError as exc:
            return None, f"schema violation: {exc.errors()[:3]}"
