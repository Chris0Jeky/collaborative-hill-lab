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
Current measured findings use synthetic scripted populations. No live provider pilot,
paid run or human-subject experiment supports them; see `docs/PROVIDER_USAGE.md`.

## Proving checks (run from the repo root; Windows `make` needs Git Bash)

Persistent GitHub Actions runs `make check test validate acceptance check-atlas
check-study002 check-responsive check-graph` on the exact PR head or main commit with the committed dependency
lock. Read its job steps and logs for the current commit; green results on an older
head are not evidence for a new one. Setup downloads dependencies, while the
science gates make no model-provider calls. CI currently covers Ubuntu/Python 3.12.

Current Study 001 passes C1, fails C2 and is **not social-dilemma certified**; C3
integrity passes. The responsive EC experiment is a separate unfrozen design with
its own finite-strategy diagnostics. Verification evidence and exact counts belong
in `HANDOFF.md` and `BUILD_LOG.md`. `make validate` covers the four shipped StudySpecs;
the standalone checks validate their own additional experiment inputs.

Use `.venv/bin/python` on POSIX or `.venv/Scripts/python.exe` on Windows for the
Python commands below.

| Changed area | Narrow check |
|---|---|
| Package or tests | `make check` (ruff, strict typing, unit/property); `make test` for the full suite |
| Kernel | `python -m pytest tests/property tests/unit/test_event_chain.py tests/metamorphic/test_replay_determinism.py tests/metamorphic/test_branch_prefix.py` |
| Graph mechanism | `python -m pytest tests/unit/test_graph_nipd.py tests/unit/test_graph_scenario.py tests/unit/test_graph_policies.py tests/metamorphic/test_graph_invariance.py tests/integration/test_graph_pipeline.py`; `make check-graph` |
| Responsive EC | `python -m pytest tests/unit/test_ec_conditional_contributor.py tests/metamorphic/test_ec_conditional_invariants.py`; `make check-responsive` |
| Provider transport/workflow | `python -m pytest tests/unit/test_openai_compatible_provider.py tests/unit/test_provider_accounting.py tests/integration/test_provider_workflow.py tests/metamorphic/test_replay_provider_failure.py` (mocked transport only) |
| Scenario, skin or study JSON | `make validate` and the affected standalone experiment check |
| Sealed artifacts and replay | `make acceptance`; `make replay-smoke` additionally needs a generated run under `artifacts/` |
| `.agent-harness/tier.json` | NOT covered by `make check` — no repo code reads it (the estate harness and session orientation do), so validate it with the vendored floor loader: `.venv/Scripts/python.exe -c "import os,sys;sys.path.insert(0,os.path.expanduser('~/.claude/hooks'));import dispatch;print(dispatch.load_tier('.'))"` |

## Hard rules specific to this repo (full invariant list: `AGENTS.md` §5)

- **Determinism is the product** (spec = the `engine/hashing.py` + `engine/seeds.py` docstrings):
  no floats and no wall-clock in hashed content (exact `Fraction` via `frac_str`); no global RNG —
  every draw from `rng_for(<seed path>)`, and no RNG state is ever persisted.
- An LLM is never authoritative for payoffs, world truth, evidence validity, permissions or metrics,
  and its output is never silently repaired — three paths: unparsable/schema-invalid output abstains
  (`invalid_llm_output`) after bounded retries; a provider error seals the run `RunFailed`; and only
  a schema-valid *illegal* action is `ActionRejected` + `invalid_action_policy` (`fail` default | `abstain`).
- Never fabricate tokens/costs (`None` = unmeasured), never store hidden chain-of-thought, never
  tune results toward the legacy paper, never present a simulation as a prediction about humans.
- Human-only: freezing a study (`--yes`), any paid LLM run, the `HANDOFF.md` decision list.
- **Synthetic data only** — real human-subject data needs `sensitive_data: true` in the tier file FIRST.
- ADR-locked (`docs/adr/0001…0012`; change = new ADR, not a refactor): own kernel + Concordia
  cognition-only, hash-linked ledger + CoW branches, five planes, mechanism/skin hash separation.
