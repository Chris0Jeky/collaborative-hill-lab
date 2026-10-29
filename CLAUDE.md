# CLAUDE.md — Collaborative Hill Lab

T1 sandbox · push/merge free · authority `.agent-harness/tier.json` (its notes carry the promotion
criteria; return sessions are not one) · persistent exact-commit CI · dual-runtime (Codex reads `AGENTS.md`; Claude does not load it, so read its §5 invariants before
product changes). Start inline; a read-only review subagent is always allowed (global law 2g). No deny
floor is guaranteed on this host: act as if nothing catches an irreversible command. Global laws are auto-injected. State, open questions, the 10 decisions: `HANDOFF.md`.

## What this is
A deterministic, fully offline laboratory for one thesis: which interaction, information and
institutional structures move agent populations out of the **Tragic Valley** (free-riding,
misinformation, coordination failure) onto the **Collaborative Hill** (accurate, sustained
cooperation). Tcaci & Huyck's N-person IPD comparison motivates the question; Study 000/002
show that both structure and reciprocity policy matter, so the legacy pattern is not a
structure-only effect. The longer-term target is LLM agents reasoning over evidence.
First environment **Evidence Commons**. M0 is built; no real provider, no paid run, no human data.

## Proving checks (run from the repo root; Windows `make` needs Git Bash)

Persistent GitHub Actions runs `make check test validate acceptance check-atlas
check-study002` on the exact PR head or main commit with the committed dependency
lock. Read its job steps and logs for the current commit; green results on an older
head are not evidence for a new one. Setup downloads dependencies, while the
science gates make no model-provider calls. CI currently covers Ubuntu/Python 3.12.

The measured counts below are a historical July checkpoint, not the current suite
inventory. Its old C1-only certificate wording is superseded: current Study 001
passes C1, fails C2 and is **not social-dilemma certified**; C3 integrity passes.
Current verification evidence and research limitations live in `HANDOFF.md` and
`BUILD_LOG.md`. `make validate` now covers four StudySpecs across three studies.

| changed | narrowest command that exercises it | measured 2026-07-27 |
|---|---|---|
| anything | `make check` (ruff + `mypy --strict` + unit/property); unsure → `make test`, the whole suite | check clean, 39 files, 106 passed ~5s; suite 125 passed (82 unit + 24 property + 9 metamorphic + 10 integration) in 7s |
| kernel (`engine/`) | `.venv/Scripts/python.exe -m pytest tests/property tests/unit/test_event_chain.py tests/metamorphic/test_replay_determinism.py tests/metamorphic/test_branch_prefix.py` | 36 passed, 2s |
| mechanism (`domain/world/`) | `.venv/Scripts/python.exe -m pytest tests/unit/test_nipd_transitions.py tests/unit/test_ec_transitions.py tests/unit/test_payoff_oracle.py tests/unit/test_hidden_truth_leak.py` | 37 passed, 0.5s |
| LLM adapter (`agents/llm/`) | `.venv/Scripts/python.exe -m pytest tests/unit/test_invalid_llm_output.py tests/unit/test_provider_failure.py tests/unit/test_capability_enforcement.py tests/unit/test_cost_honesty.py` | 16 passed, 0.5s |
| scenario / skin / study JSON | `make validate`; `cd studies/001-evidence-commons && ../../.venv/Scripts/python.exe certificate.py` | both valid; C1 dilemma True, C3 violations 0; certificate rewritten byte-identically |
| ledger, reports, anything sealed | `.venv/Scripts/python.exe scripts/acceptance.py` (self-contained: its runs live in a temp dir it deletes). Replay needs its own input — a fresh clone's `artifacts/` holds only `.gitkeep` — so `make study-000 study-001-smoke` first, then `.venv/Scripts/python.exe scripts/replay_smoke.py` | 11/11 A–K in 4.4s; generation ~60s; 2 sealed runs replayed |
| `.agent-harness/tier.json` | NOT covered by `make check` — no repo code reads it (the estate harness and session orientation do), so validate it with the vendored floor loader: `.venv/Scripts/python.exe -c "import os,sys;sys.path.insert(0,os.path.expanduser('~/.claude/hooks'));import dispatch;print(dispatch.load_tier('.'))"` | tier 1, 4 flags False; rejects bad JSON and an out-of-range tier |

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
- ADR-locked (`docs/adr/0001…0009`; change = new ADR, not a refactor): own kernel + Concordia
  cognition-only, hash-linked ledger + CoW branches, five planes, mechanism/skin hash separation.
