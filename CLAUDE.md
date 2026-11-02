# CLAUDE.md — Collaborative Hill Lab

T1 sandbox · push/merge free · authority `.agent-harness/tier.json` (its notes carry the promotion
criteria; return sessions are not one) · persistent exact-commit CI · dual-runtime (Codex reads `AGENTS.md`; Claude does not load it, so read its §5 invariants before
product changes). Start inline; a read-only review subagent is always allowed (global law 2g). No deny
floor is guaranteed on this host: act as if nothing catches an irreversible command. Global laws are auto-injected. State, open questions, the 10 decisions: `HANDOFF.md`.

## What this is

A deterministic laboratory with offline verification and optional provider execution: which interaction, information and
institutional structures move agent populations out of the **Tragic Valley** (free-riding,
misinformation, coordination failure) onto the **Collaborative Hill** (accurate, sustained
cooperation). Tcaci & Huyck's N-person IPD comparison motivates the question; Study 000/002
show that both structure and reciprocity policy matter, so the legacy pattern is not a
structure-only effect. The longer-term target is LLM agents reasoning over evidence.
First environment **Evidence Commons**. The lab includes observation-responsive EC
scripts, explicitly versioned local graph N-IPD and a configurable provider transport.
Separate EC component ablations and declared noisy-corpus models retain exact
predictions and controls. The standalone audit contract remains unchanged;
ADR-0018 implements issue #103's six ADR-0017 gates through opt-in EC v3,
scheduled public findings, replay/branch support and a separate scripted veto policy.
The declared audit-feedback experiment and independent original-artifact audit are
complete in [PR #107](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/107);
the complete local gate passed. Use that PR for final hosted checks and merge status.
The legacy LLM renderer omits audit findings. ADR-0019 and
[PR #109](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/109) implement an
explicit `ec-audit@1` renderer with fixed policy/template identity and strict public
projection. Legacy prompt bytes and hashes are preserved; fake-provider and
intercepted HTTP checks cover its integration. The PR records final verification
and merge evidence.
Current measured findings use synthetic scripted populations. No live provider pilot,
paid run or human-subject experiment supports them; see `docs/PROVIDER_USAGE.md`.

Audit modules: `domain/audit.py` defines strict schemas, opt-in settings, exact
synthetic generation and public projection;
`domain/world/audited_evidence_commons.py` publishes complete due batches before
observations through the optional runner `prepare_round` seam. State contains only
released findings, and task legality, acceptance and reward rules are inherited.
`agents/scripted/ec_audit.py` supplies `ec_audit_veto_contributor@1`;
`experiments/audit-feedback/` retains the design, literal oracle, original results,
source mapping and artifact audit. Paths above are under `src/collaborative_hill/`
except the experiment directory. Usage and scientific limits: `docs/AUDIT_USAGE.md`.

## Proving checks (run from the repo root; Windows `make` needs Git Bash)

Persistent GitHub Actions runs `make check test validate acceptance check-atlas
check-study002 check-responsive check-quality-safeguards check-graph check-sparse-ptft
check-noisy-corpus check-ec-rule-ablation check-audit-feedback` on the exact PR head or main commit with the committed dependency
lock. Read its job steps and logs for the current commit; green results on an older
head are not evidence for a new one. Setup downloads dependencies, while the
science gates make no model-provider calls. CI covers Ubuntu and Windows on Python 3.12; every text write fixes its newline because evidence commits to bytes.

Current Study 001 passes C1, fails C2 and is **not social-dilemma certified**; C3
integrity passes. The responsive EC experiment is a separate unfrozen design with
its own finite-strategy diagnostics. Verification evidence and exact counts belong
in `HANDOFF.md` and `BUILD_LOG.md`. `make validate` covers the four shipped StudySpecs;
the standalone checks validate their own additional experiment inputs.
The audit-feedback gate checks lint/types, regenerates sealed episodes and branch
fixtures, replays them and compares retained readouts. It uses temporary outputs;
the original evidence is retained separately and is not replaced by verification.

Use `.venv/bin/python` on POSIX or `.venv/Scripts/python.exe` on Windows for the
Python commands below.

Start with `make quick` (diff-selected checks) and `make lab` (film strips of real runs in
the terminal and `artifacts/lab/console.html`); the table below is the manual equivalent.
`make mutants` samples token mutants in science-critical modules: a survivor is a test gap or
an equivalent change, so triage it. Whole-episode invariants are fuzzed in
`tests/property/test_engine_fuzz.py`.

| Changed area | Narrow check |
|---|---|
| Package or tests | `make check` (ruff, strict typing, unit/property); `make test` for the full suite |
| Kernel | `python -m pytest tests/property tests/unit/test_event_chain.py tests/metamorphic/test_replay_determinism.py tests/metamorphic/test_branch_prefix.py` |
| Graph mechanism | `python -m pytest tests/unit/test_graph_nipd.py tests/unit/test_graph_scenario.py tests/unit/test_graph_policies.py tests/metamorphic/test_graph_invariance.py tests/integration/test_graph_pipeline.py`; `make check-graph` |
| Responsive EC | `python -m pytest tests/unit/test_ec_conditional_contributor.py tests/metamorphic/test_ec_conditional_invariants.py`; `make check-responsive` |
| Skeptical EC rule | `python -m pytest tests/unit/test_ec_skeptical_contributor.py`; `make check-quality-safeguards` |
| EC component ablation | `python -m pytest tests/unit/test_ec_ablation_contributor.py tests/unit/test_ec_rule_ablation.py`; `make check-ec-rule-ablation` |
| Noisy corpus / audit contract | `make check-noisy-corpus` |
| Audit runtime / scenario | `python -m pytest tests/unit/test_audit_models.py tests/unit/test_audit_scenario.py tests/unit/test_audited_ec.py tests/metamorphic/test_audit_runtime.py tests/metamorphic/test_audit_legacy_compatibility.py` |
| Audit policy / feedback experiment | `python -m pytest tests/unit/test_ec_audit_contributor.py tests/unit/test_audit_feedback.py tests/unit/test_audit_feedback_execution.py`; `make check-audit-feedback` |
| Audit LLM prompts | `python -m pytest tests/unit/test_prompt_legacy_compatibility.py tests/unit/test_audit_prompt_adapter.py tests/unit/test_audit_prompt_configuration.py tests/integration/test_audit_prompt_workflow.py` (fake/intercepted providers only) |
| Sparse exact pTFT | `make check-sparse-ptft` |
| Provider transport/workflow | `python -m pytest tests/unit/test_openai_compatible_provider.py tests/unit/test_provider_accounting.py tests/integration/test_provider_workflow.py tests/metamorphic/test_replay_provider_failure.py` (mocked transport only) |
| Provider budgets / failure analysis | `python -m pytest tests/integration/test_provider_budget.py` (mocked requests only) |
| Lab branch summaries | `python -m pytest tests/integration/test_lab_console.py` |
| Recorded seed metadata | `python -m pytest tests/unit/test_seed_protocol.py tests/integration/test_recorded_seed_validation.py tests/integration/test_seed_protocol.py tests/property/test_seed_properties.py` |
| Scenario, skin or study JSON | `make validate` and the affected standalone experiment check |
| Sealed artifacts and replay | `make acceptance`; `make replay-smoke` additionally needs a generated run under `artifacts/` |
| `.agent-harness/tier.json` | NOT covered by `make check` — no repo code reads it (the estate harness and session orientation do), so validate it with the vendored floor loader: `.venv/Scripts/python.exe -c "import os,sys;sys.path.insert(0,os.path.expanduser('~/.claude/hooks'));import dispatch;print(dispatch.load_tier('.'))"` |

## Hard rules specific to this repo (full invariant list: `AGENTS.md` §5)

- **Determinism is the product** (spec = the `engine/hashing.py` + `engine/seeds.py` docstrings):
  no floats and no wall-clock in hashed content (exact `Fraction` via `frac_str`); no global RNG —
  every draw from `rng_for(<seed path>)`, and no RNG state is ever persisted.
- Recorded seed metadata is validated in both the manifest and sealed start before
  string conversion or replay/branch output. Preserve valid integer/string aliases,
  empty mechanism-root prefixes and legacy/paired behavior; never repair source artifacts.
- An LLM is never authoritative for payoffs, world truth, evidence validity, permissions or metrics,
  and its output is never silently repaired — three paths: unparsable/schema-invalid output abstains
  (`invalid_llm_output`) after bounded retries; a provider error seals the run `RunFailed`; and only
  a schema-valid *illegal* action is `ActionRejected` + `invalid_action_policy` (`fail` default | `abstain`).
- Never fabricate tokens/costs (`None` = unmeasured), never store hidden chain-of-thought, never
  tune results toward the legacy paper, never present a simulation as a prediction about humans.
- Human-only: freezing a study (`--yes`), any paid LLM run, the `HANDOFF.md` decision list.
- **Synthetic data only** — real human-subject data needs `sensitive_data: true` in the tier file FIRST.
- ADR-locked (`docs/adr/0001…0017`; change = new ADR, not a refactor): own kernel + Concordia
  cognition-only, hash-linked ledger + CoW branches, five planes, mechanism/skin hash separation.
