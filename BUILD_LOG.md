# BUILD_LOG — decisions made and commands actually run

Chronological, foundation session 2026-07-13 (Claude Fable 5, ultracode). Only entries
that were actually executed/verified are listed.

## Discovery

- Cloned legacy repo read-only to scratchpad (`git clone` + `core.longpaths=true` for
  Windows MAX_PATH). HEAD `f7f1cceb`.
- First-hand reads: `prisoners.tex` (claims source; draft), `npdl/core/utils.py`
  (payoffs; duplicate `get_pairwise_payoffs`), `CORRECTED_RESULTS_SUMMARY.md` (defect
  admission).
- Six parallel discovery agents (Opus 4.8) → `docs/research/_discovery/*.md`. One agent
  returned a junk structured summary but a good report file (kept; noted).

## Key decisions (full rationale in ADRs)

- Option C kernel; Concordia cognition-only behind adapter (ADR-0001).
- Floats forbidden in hashed content; exact `Fraction` strings (hashing.py).
- Stateless per-(agent,round) seed streams; no persisted RNG state (ADR-0005) — chosen
  over Philox after realizing per-round derivation removes the need for fast-forward.
- Branch = copy-on-write byte prefix; shared events keep parent run_id (ADR-0002).
- Propositions are a finite typed space; NL only in skins (ADR-0003/0004).
- EC verification = engine-adjudicated provenance-checking, NOT truth oracle; documented
  as v0 limitation (CLAIMS_AND_LIMITATIONS).
- ApproveClaim deferred to v1 (in type union, not legal in v0).
- Self-knowledge flags (`verified_by_me` etc.) added to EC observations so scripted
  personas stay stateless (branch-rebuild safe).

## Commands run and verified (chronological highlights)

- `python -m venv .venv` + `pip install -e ".[dev,analysis]"` → all extras import on
  Python 3.14.3/Windows.
- Inline smoke: pairwise 2TFT+AllD 10 rounds → scores 39/39/28 (= hand-derived theory);
  replay + fresh-rerun chain equality both True.
- EC smoke: briefing 2/2 correct; free-rider advantage +1.5; ledger canary scan clean.
- `chl run "studies/000-legacy-reproduction"` — 270 then (after erratum, see below) 330
  episodes, all completed; `generate_report.py` → REPLICATION_REPORT.md, 11/11 reproduced.
- **Erratum (recorded honestly):** first prediction encoding misread prisoners.tex —
  its 75%/25% TFT-E figures refer to the AllC/AllD pairings. Fixed the reading, added the
  two missing AllC conditions, reran. No mechanism change; README of Study 000 documents it.
- `studies/001-evidence-commons/generate_study.py` → 5 conditions; skin-pair mechanism-hash
  equality asserted at generation. `chl run` fixture: 15/15 episodes completed.
- `certificate.py` → dilemma certified in all 4 institutions (C1/C2); intervention
  integrity C3: 0 violations across 16 profile pairs.
- Prompt-size measurement for COST_WORKSHEET: 36 prompts/episode, mean 2,524 chars.
- `make doctor` / `make validate` / `make replay-smoke` (replays of both studies' sealed
  runs verified chain-identical).
- Test suites (unit/property/metamorphic/integration) written by three supervised agents +
  reconciled; final pytest results in HANDOFF.md.

## Final verification (end of founding session)

From a clean generated state, in sequence, all exit 0:
`make clean-generated` → `make doctor` (10/10) → `make check` (ruff + mypy --strict +
unit/property) → `make test` (**125 passed**: 91 unit + 24 property + 9 metamorphic +
10 integration — 1 metamorphic file contributes 4 parametrizations) → `make validate` →
`make study-000` (330 episodes; REPLICATION_REPORT regenerated, **11/11 REPRODUCED**,
5 exact) → `make study-001-smoke` (certificate: C1 dilemma everywhere TRUE, C3 violations
0) → `make replay-smoke` (both studies chain-verified) → `make report` →
`scripts/acceptance.py` (**11/11 A–K pass**). Adversarial pass found and fixed: EC
verify/challenge duplication exploits (engine v2), engine-version-in-hash gap,
`_find_repo_root` wrong-repo provenance, ornamental interfaces duplication (deleted).

## Process notes

- One mid-flight commit accidentally included agent work-in-progress test files
  (harmless at T1; final state supersedes it).
- All work local; nothing pushed (task constraint), no remote/legacy-repo modification.
