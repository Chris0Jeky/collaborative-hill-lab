# Explicit provider transport and measured usage

Issue #77 is an authorized engineering implementation, not authorization for a
live provider run. The adapter remains optional and all validation is offline.

## Agreed approach

Use the standard library for a narrow non-streaming OpenAI-compatible Chat
Completions client. An SDK would add a dependency and implicit retry behavior;
a general HTTP abstraction would broaden the protocol without helping the current
typed-action seam. The accepted implementation uses an explicit endpoint, model,
bounded token cap, sampling parameters, timeout and retry configuration.

`OpenAICompatibleConfig` contains non-secret configuration. Its public constructor
accepts a sampling mapping; `validate_provider_params(params)` accepts the flat
primitive-valued PolicySpec form. The factory
`build_openai_compatible_policy(agent_id, skin, params)` resolves only the named
`api_key_env`. Constructing and validating configuration never sends a request.
`OpenAICompatibleProvider(config, api_key=...)` implements the existing
`complete(prompt)` protocol. The root integration separately requires explicit
`allow_provider_requests=True` / `--allow-provider-requests` for execution.

Only one text choice is supported. Streaming, tools, hidden reasoning fields and
prices are outside this implementation. The provider records the API's reported
model separately from the requested model and preserves missing usage as null.

## Request and failure boundary

HTTPS is required unless an explicit flag permits HTTP on a literal loopback
host. Credentials never belong in URLs, configuration files or provenance.
Redirects are refused. Responses are bounded to 1 MiB. Timeout is an I/O timeout,
not a promise to cancel server work or bound DNS/whole-request wall time.

Transport defaults to one POST. Only HTTP 429 can be retried, and only with an
explicit bounded retry count. Timeouts, network failures, 5xx, refusal and malformed
responses are not retried. Action-format repair retries are separately configured
and default to zero for this provider. Neither kind of retry is billing-idempotent.

Provider errors have stable, sanitized messages and structured attempt metadata.
Raw error bodies, headers, refusal text and exception messages do not enter
artifacts. A response echoing the configured credential fails before persistence.
No hidden reasoning field is requested or stored.

## Accounting and compatibility

`LLMPolicy.call_count`, `audit_metadata(since=0)` and `usage_totals(since=0)` retain
all completion calls, including invalid outputs and failures. A total is known
only when every attempted request in that slice reports that token dimension.
Known partial sums and measured-attempt counts remain separately labeled. A
429-then-success sequence therefore has unknown totals if the 429 usage is absent.

`llm_manifest_fields(policies, since=None)` supplies existing manifest metadata,
additive provider configuration/reported-model/usage coverage fields and totals.
Branches snapshot call offsets and transcript lengths before continuation, then
write only that continuation's usage and transcript. Original fake behavior,
scripted identities and shipped study inputs remain compatible. Root owns study,
CLI and branching wiring; this lane owns the provider, policy and manifest schema.

The graph N-IPD renderer reuses the current N-IPD action schemas without changing
legacy prompt bytes. ADR0010 and provider documentation record usage and limits.

## Verification

Mock the HTTP boundary, keeping request building, HTTP redirect handling,
decoding, parsing, accounting and ledger sealing real. Cover success, absent and
partial usage, malformed data, refusal, network and timeout failures, 429 retry
bounds, credential reflection, immutable configuration and branch offsets. Run
the existing fake-provider/replay tests, full suite, lint and strict types before
commit. No real model/provider request is part of any gate.
