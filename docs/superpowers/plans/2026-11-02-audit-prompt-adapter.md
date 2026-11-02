# Audit Prompt Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose validated public EC audit findings through an explicit LLM prompt adapter while preserving every legacy default.

**Architecture:** A frozen construction-time prompt binding selects `legacy@1` or `ec-audit@1`. The new adapter validates public context and adds a data section; existing fake/compatible factories forward one policy-owned parameter without changing transport configuration.

**Tech Stack:** Python 3.12, committed dependency lock, Pydantic 2, pytest, Ruff, strict mypy.

**Spec:** `docs/adr/0019-opt-in-audit-aware-llm-prompts.md` (including reviewed legacy-mutability and data-section clarifications).

## Global Constraints

- Implementation base: `ab9e3ec`, isolated branch; do not edit the root checkout.
- `PYTHONPATH=src`; use `/workspace/scratch/08d5c480ea81/collaborative-hill-lab/.venv/bin/python`.
- No live provider/network requests, original scientific runs, result/design edits, freezes or final-weight changes.
- Existing v1 prompt bytes, template hashes, IDs, manifest fields and public mutation/drift behavior stay exact.
- `prompt_renderer` is exactly `legacy@1` (default) or `ec-audit@1`; no scalar coercion or automatic observation-based selection.
- New adapter consumes only public observation/skin, never truth, schedule, audit generation settings or seeds.

## Review Focus

- Fake providers must reject audit-mode skin/template drift even though legacy provider checks return early without metadata.
- A missing renderer parameter differs from an explicit null/unknown value; both direct and scenario/factory entry points validate it before side effects.
- Empty reports must remain distinct from absent channel and explicit unavailability; omitted candidates cannot be labeled definitely pending.
- Python/JSON container differences and malicious-looking IDs must not weaken scalar strictness or create unquoted audit-section payload.
- Non-EC copied scenarios and provider overrides must respect the effective policy, credential preflight and existing override bypass.

---

### Task 1: Capture pre-change compatibility evidence

**Files:** Create `tests/fixtures/llm_prompt_v1_baseline.json` and `tests/unit/test_prompt_legacy_compatibility.py`.

**Interfaces:** Consumes unchanged v1 `render_prompt`, `prompt_template_hash`, `LLMPolicy`, factories and `llm_manifest_fields`; produces literal prompts, IDs/hashes, transcript/metadata and event-chain fixtures for subsequent tasks.

- [ ] Capture EC/NIPD prompts with plain and nontrivial skins, fake/compatible policy identities, invalid-output retries and two sealed fake-only legacy chains before production edits. Record pre-change source commit/file digests.
- [ ] Add compatibility tests comparing real default outputs against the captured literals, plus existing mutation behavior (`prompt_template_hash`/skin assignments for fake, deferred `ProviderError` for compatible configuration drift).
- [ ] Run the new compatibility tests and focused existing LLM/provider suites; expected all pass on the unchanged source.
- [ ] Commit fixture evidence/tests before implementation.

### Task 2: Add the binding, public rendering and policy selection

**Files:** Create `src/collaborative_hill/agents/llm/prompt_adapters.py`, `tests/unit/test_audit_prompt_adapter.py`; modify `agents/llm/rendering.py` and `agents/llm/policy.py`.

**Interfaces:** `PromptRenderer = Literal["legacy@1", "ec-audit@1"]`; `validate_prompt_renderer(value: object) -> PromptRenderer`; `build_prompt_binding(skin, renderer) -> PromptBinding`. Frozen binding exposes `renderer`, `template_hash`, `template_hash_for(skin)` and `render(observation, skin)`. `LLMPolicy` adds keyword-only `prompt_renderer`.

- [ ] Write failing cases for the constructor selector, literal new hash/ID, stable identity across observations, exact audit-section cases, strict malformed/future/duplicate/out-of-candidate rejection, zero provider calls on failure and audit-mode mutation/drift refusal. New expected hash is independently derived from ADR's literal hash payload using stdlib SHA-256, not adapter helpers.
- [ ] Run and observe failures for missing constructor/API behavior before implementation.
- [ ] Implement minimal binding and validation, shared internal rendering body with unchanged v1 wrappers, selected policy ID/hash and pre-call drift checks. Keep legacy attribute assignment semantics and fake behavior unchanged.
- [ ] Run new cases, compatibility fixtures and existing LLM/provider tests; run focused Ruff and strict mypy. Expected green, then commit.

### Task 3: Wire explicit factory/scenario selection

**Files:** Modify `agents/llm/configuration.py`, `experiments/scenario.py`, `experiments/study.py`; create `tests/unit/test_audit_prompt_configuration.py`.

**Interfaces:** Existing compatible factory signature unchanged; `params["prompt_renderer"]` carries the validated policy-owned selector. Fake factory forwards the same value. Transport dataclass/metadata/sampling remain unchanged.

- [ ] Write failing direct/fake/live-scenario selector tests, unknown/null/bool/numeric cases, EC-only guards including copied models, scenario-versus-mechanism hash separation, unchanged transport output and override/credential preflight cases.
- [ ] Run and observe missing plumbing failures.
- [ ] Implement offline validation and forwarding at the effective policy boundary, preserving existing authorization and overrides.
- [ ] Run the configuration tests and focused existing workflow/budget/seed/branch validation tests; Ruff/mypy; commit on green.

### Task 4: Verify sealed fake workflow and final compatibility

**Files:** Create `tests/integration/test_audit_prompt_workflow.py`; add usage documentation in `docs/PROVIDER_USAGE.md` scoped to this adapter.

**Interfaces:** Real audited EC mechanism, fake providers, existing study manifest/transcript and offline replay/branch APIs. Intercept transport at its opener only when checking compatible request content; never use network.

- [ ] Test a small fake-only audited episode with captured prompts before/after publication; assert exact public findings, transcript digest, frozen template identity and manifest provenance. Confirm no fabricated usage.
- [ ] Test a continuation with a separately constructed same adapter, and offline replay that fails if any provider is called. Include a malformed-envelope/drift no-request boundary at the policy entry point.
- [ ] Document exact selection, observable-state meanings, provider opt-in unchanged and absence of model-quality evidence. Do not alter the original audit experiment readout.
- [ ] Run complete pytest suite, Ruff, strict mypy, acceptance and relevant historical `--check` gates on immutable commits; inspect all results and worktree cleanliness.
- [ ] Commit and send exact source/tree plus red/green and compatibility evidence for independent whole-branch review.
