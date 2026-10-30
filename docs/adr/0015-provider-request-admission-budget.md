# ADR-0015 — Cumulative provider request-attempt admission and offline planning

Status: accepted for the engineering implementation, 2026-10-30.
Extends ADR-0010. ADR-0013 and ADR-0014 are reserved by other work.

## Context

ADR-0010 bounded each request (token cap, socket timeout, at most three 429
retries, at most three action repairs) but nothing bounded an episode or a run.
A completion token cap is not an episode budget; a socket timeout is not a
deadline. Retries and repairs multiply: a three-round agent with `max_retries=2`
and `rate_limit_retries=1` may legitimately send up to 18 HTTP requests.

## Decision

**Unit and timing.** The budget counts HTTP request attempts. An attempt is
charged when it is admitted, before it is sent, so timeouts, transport errors,
429s and responses without usage are all counted and none can be undercounted.
First POSTs, 429 retries and action-repair completions all draw on the same
counters. There is no token or currency allowance: the lab has no price table and
an estimate must not be mistaken for billing.

**Scopes.** One `RequestBudget` object carries an episode counter and a run
counter. `begin("episode")` resets only the episode counter; nothing resets on a
retry, a repair or a 429. `begin("continuation")` (used by `branch_run`) resets
nothing, so passing the object already used for the parent keeps one cumulative
limit, and a fresh object gives an independent limit. `chl run` builds one object
per invocation, so "run" means that invocation across conditions and replicates.

**Deadline and cancellation.** `deadline_seconds` is measured on a monotonic
clock from the object's construction and is checked between requests: before each
admission and before sleeping for a 429 retry whose delay would pass it. A Python
caller may also pass a `cancelled()` callable, checked at the same points. It is
NOT an in-flight bound. A request admitted just before the deadline may still run
for the socket timeout or longer; the existing timeout is not relabelled. A
cancellable in-flight mechanism would need a worker thread or process whose
abandoned request may still be generated and billed remotely, so it is left to a
later decision with the owner.

**Failure path.** An exhausted budget raises inside the transport as an ordinary
`ProviderError` (message `provider request budget exhausted: <code>`), so the
existing path applies: the runner seals `RunFailed`, replay reproduces the failure
from the sealed text offline, and no silent abstain occurs. The stable codes are
`request_attempt_limit_episode`, `request_attempt_limit_run`, `deadline_exceeded`
and `cancelled`. After a run-level stop, each later network episode is still
created and sealed `RunFailed` with zero requests and the same code (scripted
episodes still run), so every planned run has a recorded outcome.

**Hash decision.** Budget configuration is operational and enters no scenario,
mechanism, narrative or study hash, no PolicySpec parameter, no policy identity
and no RunStarted payload. It is an admission policy over how a study is executed
(like `--allow-provider-requests`), not a property of the world or the agent.
Consequently scenarios without a budget are byte-for-byte unchanged, a generous
budget leaves a completing run's ledger identical to an unbudgeted run (tested),
and only a budget-stopped run differs, in its `RunFailed` reason. The record lives
in the manifest `request_budget` field (limits, `admitted_before`, `admitted`,
scope, stop code), null when no budget was configured. Unmeasured token
and cost totals stay null; partial sums keep their existing coverage fields.

**Planning.** `chl study plan` (and `plan_study`) reads only study files and
prints worst-case logical completions, action-repair completions, 429 retry
attempts and HTTP attempts per agent, condition, episode and selection. It builds
no policy, reads no credential variable and sends nothing. It also shows
`requested_output_token_ceiling` (attempts times the requested completion cap),
labelled as requested, not measured; input tokens and prices are not estimated.

## Consequences and limits

No default limit exists and none is chosen: omitting the flags keeps ADR-0010
behaviour (unlimited). Endpoint/model, a cost ceiling, a stopping rule and any paid
pilot remain owner decisions. The counters live in one process; two concurrent
`chl run` invocations do not share a budget. The deadline starts at construction,
and the CLI builds the budget first, so offline preparation counts against it. Only the network
transport consumes the budget: the fake provider sends nothing, so budgets do not
apply to it. See [provider usage](../PROVIDER_USAGE.md).
