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
from typing import Any

from pydantic import ValidationError

from collaborative_hill.agents.llm.providers import CompletionProvider
from collaborative_hill.agents.llm.rendering import prompt_template_hash, render_prompt
from collaborative_hill.domain.actions import ActionProposal
from collaborative_hill.engine.hashing import sha256_hex
from collaborative_hill.experiments.scenario import NarrativeSkin


class LLMPolicy:
    def __init__(self, agent_id: str, provider: CompletionProvider, skin: NarrativeSkin,
                 max_retries: int = 1, sampling: dict[str, Any] | None = None) -> None:
        self.agent_id = agent_id
        self.provider = provider
        self.skin = skin
        self.max_retries = max_retries
        self.sampling = sampling or {}
        self.prompt_template_hash = prompt_template_hash(skin)
        self.policy_id = (f"llm[{provider.model_id},skin={skin.skin_id},"
                          f"tpl={self.prompt_template_hash[:12]}]@1")
        # Unhashed audit trail; the study runner writes it to llm_transcript.jsonl.
        self.transcript: list[dict[str, Any]] = []

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        del rng  # sampling randomness belongs to the provider, not the kernel streams
        prompt = render_prompt(observation, self.skin)
        attempt_prompt = prompt
        last_error = ""
        for attempt in range(self.max_retries + 1):
            result = self.provider.complete(attempt_prompt)
            proposal, error = self._parse(result.text)
            self.transcript.append({
                "agent_id": self.agent_id,
                "round": observation.get("round"),
                "attempt": attempt,
                "prompt_sha256": sha256_hex(attempt_prompt),
                "raw_text": result.text,
                "model_id": result.model_id,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "outcome": "parsed" if error is None else f"invalid: {error}",
            })
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
