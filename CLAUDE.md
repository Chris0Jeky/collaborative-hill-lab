# CLAUDE.md — Collaborative Hill Lab

T1 sandbox · push/merge free · authority `.agent-harness/tier.json` · no CI · dual-runtime (Codex
reads `AGENTS.md`; fan-out off, work inline). Global laws are auto-injected — not repeated here.
State, open questions and the 10 human-owned decisions: `HANDOFF.md`. T1 stays until something
consumes this repo's output (first LLM pilot, paper, benchmark, 2nd contributor); sessions don't.

## What this is
A deterministic, fully offline laboratory for one thesis: which interaction, information and
institutional structures move agent populations out of the **Tragic Valley** (free-riding,
misinformation, coordination failure) onto the **Collaborative Hill** (accurate, sustained
cooperation). It carries Tcaci & Huyck's N-person IPD result — targeted pairwise accountability
breeds reciprocity, diffuse punishment collapses it — to LLM agents reasoning over evidence. First
environment **Evidence Commons**. M0 is built; no real provider, no paid run, no human data.

## Proving checks (run from the repo root; `make` needs Git Bash; no CI — this is the gate)

| changed | narrowest command that exercises it | measured 2026-07-27 |
|---|---|---|
| anything | `make check` (ruff + `mypy --strict` + unit/property) | clean, 39 files, 106 passed, ~5s |
| kernel (`engine/`) | `.venv/Scripts/python.exe -m pytest tests/property tests/unit/test_event_chain.py tests/metamorphic/test_replay_determinism.py tests/metamorphic/test_branch_prefix.py` | 36 passed, 2s |
| mechanism (`domain/world/`) | `.venv/Scripts/python.exe -m pytest tests/unit/test_nipd_transitions.py tests/unit/test_ec_transitions.py tests/unit/test_payoff_oracle.py tests/unit/test_hidden_truth_leak.py` | 37 passed, 0.5s |
| LLM adapter (`agents/llm/`) | `.venv/Scripts/python.exe -m pytest tests/unit/test_invalid_llm_output.py tests/unit/test_provider_failure.py tests/unit/test_capability_enforcement.py tests/unit/test_cost_honesty.py` | 16 passed, 0.5s |
| scenario / skin / study JSON | `make validate`; `cd studies/001-evidence-commons && ../../.venv/Scripts/python.exe certificate.py` | both valid; C1 dilemma True, C3 violations 0; certificate rewritten byte-identically |
| ledger, reports, anything sealed | `.venv/Scripts/python.exe scripts/acceptance.py`; `.venv/Scripts/python.exe scripts/replay_smoke.py` | 11/11 A–K in 4.6s; 2 sealed runs replayed |
| unsure | `make test` — the whole suite is 8 seconds | 125 passed (82 unit + 24 property + 9 metamorphic + 10 integration) |

## Hard rules specific to this repo (full invariant list: `AGENTS.md` §5)
- **Determinism is the product** (spec = the `engine/hashing.py` + `engine/seeds.py` docstrings):
  no floats and no wall-clock in hashed content (exact `Fraction` via `frac_str`); no global RNG —
  every draw from `rng_for(<seed path>)`, and no RNG state is ever persisted.
- An LLM is never authoritative for payoffs, world truth, evidence validity, permissions or
  metrics; invalid model output becomes `ActionRejected` + abstention, never a silent repair.
- Never fabricate tokens/costs (`None` = unmeasured), never store hidden chain-of-thought, never
  tune results toward the legacy paper, never present a simulation as a prediction about humans.
- Human-only: freezing a study (`--yes`), any paid LLM run, the `HANDOFF.md` decision list.
- **Synthetic data only** — if real human-subject data is ever headed here, flip
  `sensitive_data: true` in `.agent-harness/tier.json` BEFORE it lands.
- ADR-locked (`docs/adr/0001…0007`; change = new ADR, not a refactor): own kernel + Concordia
  cognition-only, hash-linked ledger + CoW branches, five planes, mechanism/skin hash separation.
