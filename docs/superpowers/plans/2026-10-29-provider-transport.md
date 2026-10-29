# Explicit Provider Transport Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement these tasks.

**Goal:** Add an explicitly configured provider transport with honest per-attempt
usage accounting, safe diagnostics and an offline-verifiable public API.

**Architecture:** Standard-library non-streaming Chat Completions feeds the existing
typed LLM policy. Additive manifest fields distinguish requested configuration,
reported models and complete versus partially measured usage.

**Tech Stack:** Python 3.12, urllib, exact Fraction strings, existing Pydantic/pytest.

**Spec:** `docs/superpowers/specs/2026-10-29-provider-transport-design.md`.

## Global Constraints

- No dependencies, live requests, provider/model selection or invented prices.
- Root owns `experiments/study.py`, `cli.py` and branching integration.
- Keep existing fake-provider behavior and shipped study hashes unchanged.
- Credential environment references only in StudySpecs; explicit execution opt-in.

## Review Focus

- 429 before success must not turn missing usage into a complete total.
- Refusals or malformed responses can still report consumed tokens.
- Reused policy instances must support continuation-only usage offsets.
- Redirects and reflected credentials must not expose authentication.
- Graph action schemas must preserve all existing N-IPD prompt bytes.

### Task 1: Configuration and transport

Files: new `agents/llm/configuration.py`, `agents/llm/openai_compatible.py`,
`tests/unit/test_openai_compatible_provider.py`; existing `providers.py`, `__init__.py`.

- [x] Write request, validation, response, retry and secret-boundary regressions.
- [x] Observe missing-API failures, then implement agreed constructors/factory and
      structured `ProviderAttempt` metadata on results and failures.
- [x] Verify literal wire payloads, reported model/usage, terminal failure modes,
      429 bounds and refusal/invalid-response accounting with mocked HTTP only.

### Task 2: Policy and manifest accounting

Files: `agents/llm/policy.py`, new `agents/llm/accounting.py`,
`experiments/manifests.py`, `tests/unit/test_provider_accounting.py`.

- [x] Write tests for multiple completion calls, parser retries, provider failures,
      missing dimensions, known partial sums and continuation offsets.
- [x] Implement `LLMPolicy.call_count`, `audit_metadata(since=0)`,
      `usage_totals(since=0)` and `llm_manifest_fields(policies, since=None)`.
- [x] Add defaulted manifest metadata fields and verify canonical serialization.
- [x] Preserve existing fake-provider and provider-failure replay assertions.
      Test doubles accept the root integration's explicit new keyword arguments.

### Task 3: Graph schema and integration documentation

Files: `agents/llm/rendering.py`, graph-schema unit regression,
`docs/adr/0010-configurable-provider-transport.md`, `docs/PROVIDER_USAGE.md`.

- [x] Test graph neighbourhood/pairwise schemas against literal action types.
- [x] Extend the renderer dispatch without changing legacy prompt bytes.
- [x] Document direct API, flat StudySpec inputs, opt-in integration, accounting,
      response subset, source protocol references and retry/timeout limits.

### Task 4: Final verification and handoff

- [x] Run focused tests, `ruff check src tests`, strict package mypy and full pytest.
- [x] Run shipped study validation and relevant offline acceptance gates.
- [x] Review diffs for secrets, scientific scope and unaffected shipped artifacts.
- [x] Commit only owned files; report SHA, exact red/green evidence and limitations.

## Verification record and rulings

- Initial transport/configuration/graph regression run: 70 failed for missing
  provider API or the graph schema falling through to Evidence Commons; then 70 passed.
- Accounting regressions exposed missing aggregation/continuation cursors and
  coercible token counts. Complete focused provider/fake/replay set passed afterward.
- Additional strict-JSON, nested secret scanning and direct-policy retry-default
  regressions: three red, then green; the real-engine secret-safe failure control passed.
- Independent review found mutable execution/provenance drift and escaped JSON
  decoding resource errors. Ten unit/metamorphic regressions were red, then green;
  the independent reviewer reran all ten and reported no remaining core blocker.
- Final focused provider/accounting/graph/failure-replay gate: 136 passed.
  Strict mypy checked 48 package files; repository ruff and `git diff --check`
  passed. Shipped study validation and all 11 offline acceptance scenarios passed;
  the Study 002 exact benchmark's canonical `--check` also passed.
- A full 937-case suite passed before the later hardening/review regressions and
  root's workflow integration. The current combined full-suite and exact-head CI
  gates belong to root; the focused results above cover the final core changes.
- Ruling: retain legacy fake/custom provider transcript shape when ProviderError
  has no structured attempts, while separately counting the failure as unknown
  usage. This preserves existing ledger/replay behavior and avoids inventing usage.
- Ruling: socket I/O timeout is not advertised as a total or DNS deadline. Only
  an explicit HTTP429 retry is supported; uncertain requests are never reposted.
- Root is implementing study/CLI/branch integration in the same worktree and
  owns those source paths and `tests/integration/test_provider_workflow.py`.
