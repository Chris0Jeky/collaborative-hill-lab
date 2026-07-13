# ADR-0007 — LLM adapter: typed actions, bounded retries, observable rationale only

Status: **accepted** (2026-07-13)

## Context

Models must be able to act without ever becoming authoritative over world state, and their
failures must be data, not corruption. No hidden chain-of-thought may be stored (locked
principle 10).

## Decision

- An LLM policy (`agents/llm/policy.py`) receives the rendered typed observation and must
  return strict JSON parsing to `ActionProposal` (typed action + concise public
  justification + optional message). Unknown keys, non-JSON, or schema violations trigger
  bounded re-prompting (`max_retries`, default 1) with the error appended; exhaustion
  yields an explicit `AbstainAction(reason="invalid_llm_output")`. **Invalid output is
  never silently repaired into the action the experimenter expected.**
- Mechanism-level illegality (valid schema, illegal move) is the engine's job:
  `ActionRejected` + the study-configured fallback (`fail` or safe abstention).
- Provider errors raise; the runner seals the run as `RunFailed` with a typed reason.
- What is stored: observations, typed proposals, justifications, rejections, results — in
  the hashed ledger; prompts + raw completions + token counts — in the UNHASHED
  `llm_transcript.jsonl` sidecar for audit. No chain-of-thought is requested or stored;
  the justification field is defined as a public one-sentence rationale.
- `policy_id` embeds provider model id, skin id, and prompt-template hash; manifests
  record sampling parameters. The only provider in the foundation is a deterministic
  `FakeProvider`; adding a real provider is a human-gated change (cost).

## Consequences

- Invalid-action rate is a first-class operational metric, comparable across models.
- Replay of LLM runs replays recorded actions (ADR-0001 determinism scope).
- Injection resistance is measurable: fixtures reach the model as clearly-delimited data;
  the engine is immune by construction, and the model's compliance behaviour is data.
