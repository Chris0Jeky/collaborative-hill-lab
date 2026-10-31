# Configurable provider transport

The lab includes an explicit non-streaming OpenAI-compatible Chat Completions
transport. Its tests use mocked HTTP responses only. Adding this transport does
not choose a model, approve a paid run, supply prices or freeze a study.

## Public Python API

Construction and validation are offline. The first `complete()` or `propose()`
call sends a request; use it only within an authorized run and declared budget.

```python
import os

from collaborative_hill.agents.llm import (
    LLMPolicy,
    OpenAICompatibleConfig,
    OpenAICompatibleProvider,
    llm_manifest_fields,
)
from collaborative_hill.experiments.scenario import NarrativeSkin

config = OpenAICompatibleConfig(
    endpoint=os.environ["CHL_ENDPOINT"],  # complete .../chat/completions URL
    model_id=os.environ["CHL_MODEL_ID"],  # an explicitly selected model/version
    sampling={"max_completion_tokens": 256, "temperature": "1/2"},
    timeout_seconds=30,
    rate_limit_retries=0,
    max_retries=0,
)
provider = OpenAICompatibleProvider(config, api_key=os.environ["CHL_API_KEY"])
policy = LLMPolicy("a1", provider, NarrativeSkin(skin_id="plain"))

# The runner supplies the allowed observation and kernel RNG to policy.propose.
# Before and after execution, this produces manifest-compatible metadata:
manifest_updates = llm_manifest_fields({"a1": policy})
```

The numeric settings above illustrate the API; they are not study defaults or
a proposed experimental sampling choice. Pass `api_key=None` explicitly for an
endpoint that does not require authentication. The provider never searches for
an endpoint, model or credential on its own. `config.sampling` is an immutable
copy. Supplying a contradictory `LLMPolicy(..., sampling=...)` is an error.
Provider execution settings are read-only. If a real policy's sampling, retry
count or skin is changed after its provenance is captured, it refuses the next
request; construct a fresh policy for a new configuration.

The transport implements `CompletionProvider.complete(prompt) -> ProviderResult`.
`provider.model_id` is the requested identifier; `result.model_id` is the model
reported by the response. `result.input_tokens` and `result.output_tokens` refer
to the returned completion. Its `attempts` tuple additionally includes any HTTP
429 attempts. Use the policy/helper totals for complete-call accounting.

## Study configuration and execution boundary

Use flat PolicySpec parameters so inputs remain canonical and hashable:

```json
{
  "name": "llm_openai_compatible",
  "params": {
    "endpoint": "https://your-provider.example/v1/chat/completions",
    "model_id": "your-explicit-model-version",
    "max_completion_tokens": 256,
    "temperature": "1/2",
    "api_key_env": "CHL_API_KEY",
    "timeout_seconds": 30,
    "max_retries": 0,
    "rate_limit_retries": 0
  }
}
```

`validate_provider_params(params)` returns the typed configuration without
reading credentials or sending requests.
`build_openai_compatible_policy(agent_id, skin, params)` resolves only the named
environment variable and constructs the policy; it still sends no request.
The study/CLI integration requires explicit network execution opt-in:

```sh
chl study validate path/to/your/study
chl run path/to/your/study --artifacts artifacts/your-fresh-run --allow-provider-requests
```

The first command is offline. The second requires separately authorized endpoint,
model/version, budget and stopping rules. Without the opt-in, the run refuses a
selected network policy before reserving output. Recorded-action replay does not
call the original provider. Branches require opt-in for effective network policies;
explicit scripted replacements can keep a counterfactual continuation offline.

Never place the credential itself in JSON, the endpoint URL, a skin or a prompt.
Literal `api_key`, arbitrary authorization headers and nested `sampling` parameters
are rejected. The declared environment-variable name can remain in the scenario;
the resolved value is excluded from manifests and transcripts.

## Planning and request budgets

Both are offline-first and opt-in; neither selects a model or approves a paid run.
No default limit exists: leaving the flags out means *unlimited* (the behaviour
above), not a safe budget. Design record: ADR-0015.

```sh
chl study plan path/to/your/study [--condition ID] [--replicates N] \
    [--max-episode-request-attempts N] [--max-run-request-attempts N]
```

`plan` reads only the study files (no policy built, no credential variable read,
no request) and prints JSON maxima. For each LLM agent per episode it separates
`max_logical_completions` (rounds x (1 + `max_retries`)),
`max_action_repair_completions`, `max_rate_limit_retry_attempts` (HTTP 429) and
`max_http_request_attempts` (logical completions x (1 + `rate_limit_retries`)).
It repeats these per condition and for the whole selection, and says whether the
worst case exceeds each limit you passed. `requested_output_token_ceiling` is
attempts times the requested completion cap: a request, not a measurement; input
tokens and prices are not estimated. These are maxima for episodes that run to
completion, not predictions.

```sh
chl run path/to/your/study --allow-provider-requests \
    --max-episode-request-attempts 20 --max-run-request-attempts 200 --deadline-seconds 1800
```

(The numbers are placeholders, not recommendations.) The unit is the **HTTP
request attempt**, charged when admitted and before it is sent, so timeouts,
transport errors, 429s and responses without usage all count; repairs and 429
retries draw on the same counters. Scopes:

| Scope | Counts | Resets |
|---|---|---|
| episode | attempts of one episode (all its agents) | at each new episode only |
| run | attempts of this whole `chl run` invocation | never |
| continuation | `branch_run(..., request_budget=b)` marks the fork | never; reuse `b` for one cumulative limit |

A retry, repair or continuation never resets a counter. In Python, build
`RequestBudget(max_episode_attempts=, max_run_attempts=, deadline_seconds=,
cancelled=)`, pass it to `run_study(request_budget=...)` or
`branch_run(request_budget=...)` (a network override must be built with the same
object: `build_openai_compatible_policy(..., budget=b)`). It applies only to the
network transport; the fake provider sends nothing.

**Deadline and cancellation are between-request checks, not an in-flight bound.**
`deadline_seconds` runs on a monotonic clock from the budget's construction and is
checked before each admission and before a 429 delay that would pass it. A request
admitted just before the deadline may still run for `timeout_seconds` or longer
(DNS and a stalled server are not covered), and its response is kept and measured.
`timeout_seconds` remains a socket I/O timeout. A truly cancellable in-flight
bound is not implemented.

An exhausted budget follows the existing failure path (no silent abstain): the
run is sealed `RunFailed` with `policy error for <agent>: ProviderError: provider
request budget exhausted: <code>`, and replay reproduces it offline. Stable codes:
`request_attempt_limit_episode`, `request_attempt_limit_run`, `deadline_exceeded`,
`cancelled`. After a run-level stop each later network episode is still sealed
`RunFailed` with zero requests; scripted episodes run normally. The manifest gains
`request_budget` (null when no budget was configured; omitted from a continuation manifest without one): `limits`, `scope`,
`admitted_before`, `admitted`, `stop_reason` and
`deadline_check="between_requests_monotonic"`. `admitted` is a count of attempts,
not tokens or money; token/cost totals stay null when unmeasured. The budget is
operational: it enters no scenario, mechanism or study hash, no PolicySpec and no
ledger event, so unbudgeted scenarios and completing budgeted runs are
byte-identical. Counters are per process; concurrent invocations do not share one.

## Supported parameters

| Parameter | Contract |
|---|---|
| `endpoint` | Explicit absolute HTTPS URL for the complete endpoint; no userinfo, query, fragment, control characters or backslashes. No URL is appended automatically. |
| `model_id` | Explicit nonempty printable requested model identifier. The response's reported identifier is recorded separately. |
| `max_completion_tokens` or `max_tokens` | Exactly one positive integer is required. Choose the field supported by the selected model/compatible endpoint. |
| `temperature` | Optional exact rational/decimal string in `[0, 2]`. |
| `top_p` | Optional exact rational/decimal string in `[0, 1]`. |
| `seed` | Optional signed 64-bit integer, passed explicitly to the provider; unrelated to kernel seed paths. |
| `api_key_env` | Optional environment-variable name. Missing/empty referenced credentials fail construction. Omission means unauthenticated access. |
| `timeout_seconds` | Integer 1–300; default 30. Socket I/O timeout, not a total deadline. |
| `rate_limit_retries` | Integer 0–3; default 0. Applies only to HTTP 429. |
| `retry_delay_seconds` | Integer 0–60; default 1. Fixed bounded delay for each enabled 429 retry. |
| `max_retries` | Integer 0–3 in provider configuration; default 0. Additional action-format repair completions. |
| `allow_insecure_localhost` | Boolean, default false. Enables HTTP only for literal `localhost`, `127.0.0.1` or `::1`. |

Unknown parameters and coercible substitutes such as boolean token counts are
rejected. No defaults are added to the stored PolicySpec. Rational values are
normalized only in the runtime configuration. Wire JSON uses floating-point
ratios, and provenance includes their actual serialized strings; no floats enter
scientific configuration or metadata. Omitted sampling values mean the server's
defaults were not specified, not that the client measured an effective value.

## Failure and retry behavior

Every request uses one user message, `n=1`, and `stream=false`. A successful result
contains one assistant text choice whose finish reason is `stop`. The provider
does not execute tools, follow redirects or retain separate reasoning fields.
Refusal, content filtering, token-limit truncation, tool-call responses, malformed
JSON/schema, unsafe response content and responses over 1 MiB raise `ProviderError`.
The runner seals such failures as `RunFailed`. Invalid action JSON inside a valid
text completion follows the existing parse/retry/abstain path instead.
That path also treats JSON integer-size or nesting-limit errors as invalid model
output, preserving the transcript and measured usage without changing Python's
process-wide decoding limits.

Timeouts, connection failures, 5xx errors and parse/refusal failures are never
reposted automatically. A timed-out POST may already have generated output and
incurred cost; the client cannot determine or undo that. Explicit 429 retries
also do not promise free requests or provider idempotency. Fixed retry delays
remain bounded even if a response contains an extreme `Retry-After` value.
The token cap constrains requested completion size; it is not a dollar ceiling
or a total episode token budget.

Error diagnostics contain a stable category and, for HTTP failures, the status
code. Remote error bodies, headers, refusal text and underlying exception text
are not copied into artifacts. Known literal credential reflection is rejected,
including reflection in a reported model identifier. This is a bounded check,
not an assurance against a malicious server encoding a secret into other data.

## Usage and provenance

The manifest records requested model, prompt-template identity, declared sampling,
transport/endpoint configuration and the set of actually reported model IDs.
`provider_usage` reports each agent's completion calls, HTTP request attempts,
per-dimension totals, known partial sums and measured-attempt counts.

The factorial analyzer requires recorded transport configuration to agree within
each comparison block. It also refuses different nonempty reported-model sets
for the same agent, including versions observed on failed attempts. Missing or
empty reported-model sets remain unknown; they do not establish a model match or
cause a pre-response failure to disappear from attrition. Available provider
metadata is carried into episode analysis rows. Legacy scripted rows are unchanged.

For example, measured input counts `10, null, 7` produce `input_tokens=null`,
`known_input_tokens=17`, and `input_measured_attempts=2` out of 3 attempts. A
separately complete output dimension can still have a known total. A 429 followed
by success stays incomplete when the 429's usage is absent. A refusal that reports
usage contributes those measured counts. Uncalled agents add no attempted request;
an episode with no measurements still has null totals. Costs and pricing fields
remain null, even when token usage is complete.

`LLMPolicy.call_count` is a cursor for reused policy objects. For a continuation:

```python
offsets = {agent: p.call_count for agent, p in policies.items() if isinstance(p, LLMPolicy)}
transcript_offsets = {
    agent: len(p.transcript) for agent, p in policies.items() if isinstance(p, LLMPolicy)
}
# Execute the continuation with these policy objects.
child_updates = llm_manifest_fields(policies, since=offsets)
child_transcripts = {
    agent: p.transcript[transcript_offsets[agent]:]
    for agent, p in policies.items() if isinstance(p, LLMPolicy)
}
```

The child fields are labeled `provider_usage_scope="continuation"` and must
replace inherited provider/usage metadata. They do not claim to measure the
parent prefix. The legacy fake-provider transcript shape and policy identity
remain compatible; the accounting layer still notices its failed calls.

## Protocol sources and validation scope

Official references consulted on 2026-10-29:

- [Create Chat Completion](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create): request fields and token/sampling parameter semantics. OpenAI deprecates `max_tokens` in favor of `max_completion_tokens`; compatible endpoints may differ.
- [Chat response types](https://developers.openai.com/api/reference/resources/chat): reported model, message/refusal, finish reason and optional usage fields.
- [API authentication](https://developers.openai.com/api/reference/overview#authentication): bearer credentials and environment/key-management handling.

Compatibility is tested against mocked responses for this documented subset.
No live endpoint/model behavior, billing, provider determinism or paired provider
randomness has been verified. A later pilot must measure those operational facts
under its declared design; this implementation supplies no confirmatory findings.
