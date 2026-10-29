# ADR-0010 — Explicit provider transport and measured request accounting

Status: accepted for the engineering implementation, 2026-10-29.
Extends ADR-0007 and the continuation accounting boundary in ADR-0009.

## Context

The typed LLM policy existed behind a deterministic fake provider. Successful
responses could carry token counts, but study manifests did not aggregate them;
an unsuccessful request had no accounting record. A real transport needs an
explicit execution boundary, honest missing-usage semantics and diagnostics that
cannot copy credentials or remote error bodies into sealed artifacts.

## Decision

Implement a standard-library, non-streaming OpenAI-compatible Chat Completions
provider. Endpoint, requested model and a positive completion-token cap are
explicit configuration. Optional temperature/top-p values are exact strings in
scientific configuration; only the HTTP body converts them to wire numbers.
Provenance records both those values and the serialized wire-number strings.
Credentials are private constructor arguments or named environment-variable
references, never literal PolicySpec parameters or public provider metadata.

The client requires HTTPS, except for explicitly enabled loopback HTTP. It does
not follow redirects. It bounds the response to 1 MiB and uses a configurable
socket I/O timeout. That timeout is not a server cancellation or a total
wall-clock deadline, including DNS resolution.

There is one POST by default. Only HTTP 429 is eligible for explicitly enabled
transport retries, with at most three retries and a bounded configured delay.
Server Retry-After values do not extend that delay. Timeouts, network errors,
5xx responses, refusals and malformed completions are terminal provider errors.
Action-format repair is a separate policy setting; this provider defaults to
zero repairs, while the fake provider retains its existing default of one.
No retry is claimed to be billing-idempotent or free.

The supported result is one assistant text choice with finish_reason=stop.
Refusals, filtering, token-limit truncation and tool-call results are explicit
failures. Error messages are stable classifications; raw exception messages,
HTTP bodies/headers and refusal text are not persisted. Only visible completion
text is retained, never separate reasoning fields. A literal occurrence of the
configured credential in the request prompt, public configuration or decoded
response is rejected before persistence. This does not authenticate a remote
server or promise detection of arbitrarily encoded secrets.

Each request receives a safe attempt record, including HTTP 429 and failed
requests. The policy records all completion calls, including format repairs.
Input and output token totals are known independently, and only when every
attempted request reports that dimension. Measured partial sums and coverage
counts remain explicitly labeled. Refusal or malformed responses may still
report usage; that measured usage is retained. Missing counts remain null and
cost/pricing data remain null: the client has no price table.

Additive manifest fields record provider configuration, actually reported models,
usage coverage and whether usage describes an episode or a continuation.
Continuation callers snapshot policy call cursors before execution and slice
transcripts separately; parent usage and pricing must not be copied into the
child's measurements. Existing fake policy identities and historical ledgers
remain compatible. A real provider's policy identity also commits to its public
transport/sampling configuration, rather than identifying it by model label alone.

## Execution authorization and integration

Direct construction is an explicit Python API; it sends no request until
complete/propose is called. The study registry recognizes
`llm_openai_compatible`, validates flat non-secret parameters offline, and requires
an explicit execution opt-in for network policies. CLI execution uses
`--allow-provider-requests`; validation and recorded-action replay stay offline.
An opt-in is an execution safeguard, not a scientific freeze or a budget approval.
Provider/model/version selection, live-pilot budget and stopping rules remain
human-owned decisions. No live call is part of this implementation's tests.

## Consequences and limits

The protocol subset is intentionally small: no provider SDK, streaming, Responses
API, tool calls, arbitrary headers or Azure-specific query authentication. A
compatible server may support a different model-specific parameter subset;
rejection is recorded rather than repaired by changing the declared settings.
Provider seeds and temperature do not establish deterministic replay or paired
provider randomness. Replay continues to reproduce recorded typed actions.

See [provider usage](../PROVIDER_USAGE.md) for the public API, parameter bounds,
accounting examples and the official protocol references consulted.
