# HANDOFF — exact current state (updated 2026-07-17)

Written by the founding engineer session (Claude Fable 5) and updated by the Codex runtime
refresh. Everything below was verified by running it; anything not verified is labelled.

**Picking up in a fresh session:** read this file, then `docs/FOUNDATION_REVIEW.md`, then
`AGENTS.md` §5 (invariants). Verify the repo with the command block below (~5 min; the
venv at `.venv/` already exists — only run `make setup` if it is missing). The foundation
history is on `origin/main` through `65a387f`; the 2026-07-17 Codex refresh is on
`chore/codex-runtime-refresh`, starting with `7954abb`. All 16 founding tasks completed;
there is no half-finished product work in the tree.

## Codex runtime refresh (2026-07-17)

- `.codex/hooks.json` now invokes the installed floor v1.4.1 with `--runtime codex`; a
  simulated force-push was denied and a benign `git status` was allowed.
- `.codex/config.toml` explicitly enables hooks and disables multi-agent fan-out at T1.
  Approval and sandbox defaults remain user-owned and are not committed.
- `AGENTS.md`, `CLAUDE.md`, and `.claude/tier.json` now agree on the live floor, M0 state,
  exact-head verification rule, and Codex trust boundary.
- Human-action file: none (`.claude/tier.json` declares `human_todo=null`). One runtime UI
  action remains: in the next Codex session, review and trust the changed hook hash via
  `/hooks`; until then the project hook may be skipped.
- Verified on this branch: `make check`, `make test` (125 passed), and `make validate`.
  NOT verified in this refresh: the long generated-study/report/replay/acceptance sequence;
  its last clean-state evidence remains the founding-session record below.

## What exists and is verified working

- **Kernel** (`src/collaborative_hill/engine/`): canonical hashing (floats forbidden),
  stateless hierarchical seeds, hash-linked JSONL event ledger, checkpoints, runner,
  replay verification, copy-on-write branching. `mypy --strict`: clean (39 files).
  `ruff`: clean.
- **Mechanisms**: N-IPD (engine v1; pairwise per-opponent + neighbourhood linear PGG,
  exact fractions) and Evidence Commons (engine v2; one-verification/one-challenge per
  (agent, claim) — v2 closed a support-inflation/challenge-spam exploit found in the
  adversarial pass; engine versions are inside the mechanism hash).
- **Agents**: deconfounded TFT family (tft_pairwise, tft_linked, ptft include/exclude-self,
  tft_threshold, allc, alld, random), EC personas (contributor, freerider, verifier,
  misinformer), replay policy, LLM adapter (strict typed parsing, bounded retries, safe
  abstention, unhashed transcript sidecar) + deterministic FakeProvider. No real provider
  exists (deliberate — human-gated cost decision).
- **Studies**:
  - 000 legacy reproduction: 11 conditions × 30 replicates run; report generated
    (`docs/research/REPLICATION_REPORT.md`): 5 exact + 6 qualitative reproductions.
    Deconfound result: linked-TFT collapses inside pairwise; threshold-TFT sustains inside
    neighbourhood — structure alone does not carry the legacy effect.
  - 001 Evidence Commons: DRAFT (NOT frozen — deliberately); 2×2 + misinformer arm;
    scripted fixture runs; mechanism certificate (dilemma certified by enumeration in all
    4 institutions; intervention integrity certified); two skins hash-verified
    mechanism-identical; measured cost worksheet without prices.
- **Tests**: `make test` = **125 passed** (91 unit + 24 property + 9 metamorphic + 10
  integration; ~7 s). Zero xfails — no known source defects at handoff. `make check`
  additionally runs ruff (clean) and `mypy --strict` (clean, 39 files).
- **Acceptance A–K**: `scripts/acceptance.py` — 11/11 pass (final run from a clean
  generated state at commit `9ad1212`).
- **Docs**: ADR-0001…0007 (accepted), FOUNDATION_REVIEW, research suite under
  `docs/research/` (charter, legacy audit, related work, novelty matrix, methodology,
  SAP, claims+limitations, threat model, prereg template, replication report).

## Commands to verify this repository (all previously run successfully)

    make doctor && make check && make test
    make validate
    make study-000            # ~330 episodes, regenerates REPLICATION_REPORT.md
    make study-001-smoke
    make replay-smoke
    .venv/Scripts/python.exe scripts/acceptance.py

## Known failures / caveats (none hidden)

- No CI exists (T1 sandbox — promote to T2 before adding; see `.claude/tier.json`).
- `artifacts/` is gitignored and regenerable, never canon. The trees on disk at handoff
  (`DRAFT-5dcde1a9b6c9` = study 000, `DRAFT-a3bffdfcf171` = study 001) were produced by
  the final clean-state pass under EC engine v2; `make study-000` / `make study-001-smoke`
  reproduce them (deterministic).
- `git status` CRLF warnings on Windows are cosmetic; event files are written with
  explicit `\n` so ledger bytes are platform-stable.
- Legacy repo clone lives in the session scratchpad (temp) — re-clone
  `Chris0Jeky/N-person-prisoners-dilemma-simulation` @ `f7f1cceb` if needed again.
- The `.claude/settings.local.json` bypassPermissions file is owner-managed (gitignored).
- Codex project hooks are hash-trusted. After `.codex/hooks.json` changes, use `/hooks` to
  review and trust the new definition before assuming the deny floor is active.

## Open scientific questions

1. Which framing of the deconfound is right for publication: "structure AND strategy
   jointly required" vs "the legacy claim needs narrowing"? (Study 000 report has data.)
2. pTFT denominator (include/exclude-self) and TFT-E exploration granularity are
   underspecified in the legacy draft — which convention should the lineage canonize?
3. Evidence Commons v0 verification cannot be lied about (engine-adjudicated). When
   deception lands (NEXT.md E3), what is the honest-verifier baseline to compare against?
4. Do the ECParams placeholder weights create the *intended* effect sizes for LLM
   populations, or are they too coarse? (Pilot question.)

## Open engineering questions

1. Real provider adapter: which SDK, how to pin model versions, where token counts come
   from (NEXT.md E1).
2. Condition-order randomisation for LLM runs is designed (METHODOLOGY.md) but not
   implemented in run_study (no-op for deterministic scripted runs; needed before pilot).
3. Message-passing (`communication: "messages"`) is schema-only — no mechanism consumes
   messages yet.
4. Study-hash artifact directories use `DRAFT-<hash12>` for unfrozen studies — revisit
   naming when the first frozen study lands.

## HUMAN-OWNED decisions (do not decide these silently — locked)

1. Study 001 final hypotheses and wording.
2. Primary outcomes (proposal: briefing quality + contribution rate).
3. Utility weights (ECParams defaults are placeholders that provably yield a dilemma).
4. Full study sample size (after pilot) and minimum effect of interest.
5. Model providers/versions; single- vs mixed-model populations.
6. Acceptable cost ceiling + stopping rules.
7. Whether Study 001 is publication-ready; venue.
8. Whether any legacy result counts as "replicated" (see REPLICATION_REPORT verdicts).
9. Novelty claims (NOVELTY_MATRIX has the honest assessment + open verification items).
10. The repository is now public and the foundation is on `origin/main`; any future
    publication, release, or paid-run decision remains human-owned.

## Next five tasks (detail in NEXT.md)

1. Human: fill + freeze Study 001 preregistration (R1 ⛔).
2. Real provider adapter with honest token capture (E1).
3. 5-episode/cell pilot + variance/cost report (R2).
4. Deterministic analysis pipeline for the 2×2 (E2).
5. Deception-capable verification design (E3).

## Read-first for the next model

1. `CLAUDE.md` (locked decisions, never-do list) — 2 minutes.
2. `docs/FOUNDATION_REVIEW.md` (why everything is the way it is) — 5 minutes.
3. `AGENTS.md` §5 invariants + §7 how-to-add — 5 minutes.
4. `src/collaborative_hill/engine/runner.py` (the lifecycle, top docstring).
5. `studies/000-legacy-reproduction/README.md` + `docs/research/REPLICATION_REPORT.md`
   (what the science says so far).
6. `docs/research/LEGACY_AUDIT.md` before ever trusting a legacy number.
