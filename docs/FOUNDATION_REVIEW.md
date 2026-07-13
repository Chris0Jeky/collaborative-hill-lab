# Foundation Review — Collaborative Hill Lab

Synthesis of the six-lens Phase 0 discovery (full reports in `docs/research/_discovery/`),
reconciled by the founding engineer against first-hand reads of `prisoners.tex`,
`npdl/core/utils.py`, and `CORRECTED_RESULTS_SUMMARY.md`. Written 2026-07-13, before the
foundation implementation was finalized; the "as built" notes were completed after.

## 1. What can be safely reused from the legacy repo

- **Payoff definitions** (R=3,S=0,T=5,P=1; pairwise sum-of-2-player-games; neighbourhood
  linear `S+(R−S)k/(N−1)` / `P+(T−P)k/(N−1)`) — consistent across paper text and
  `npdl/core/utils.py`; reimplemented here in exact rational arithmetic and verified
  against hand-derived N=3 tables.
- **The qualitative scientific claim set** (Collaborative Hill vs Tragic Valley) — as
  claims under test, not as ground truth.
- **Two clean pure functions** (`get_pairwise_payoffs`, `calculate_payoffs`) as an external
  cross-check oracle only. Nothing else: no RNG-coupled code, no engines, no outputs.

## 2. What had to be reimplemented (and why)

Everything else. Decisive findings:

- **The defect:** the pairwise-cooperation 0% bug is a reporting-schema mismatch in
  `npd_simulator/experiments/research_experiments.py:238-266` (round-indexed extractor
  reading pair-indexed history, silently defaulting to 0.0). It was never fixed in place;
  the paper's figures came from separate, *unseeded* standalone scripts. Committed CSVs are
  contaminated; artifacts are not traceable to code versions.
- **The confound:** "TFT" is three different decision rules across legacy engines —
  per-opponent TFT (pairwise figures), probabilistic pTFT (neighbourhood figures, with an
  include-self /N denominator that contradicts the paper text's /(N−1)), and a threshold
  quorum TFT (npdl "ecosystem" TFT). npdl's own "pairwise" mode is linked-aggregate
  (defect-if-any), which produces the OPPOSITE of the paper's pairwise claim — and a
  committed test enshrines that behaviour.
- **Methodology:** the headline experiment stack is unseeded, computes z-based CIs with
  population SD at n=20, has zero-width CIs on deterministic configs, no hypothesis tests,
  and zero-pads missing rounds. Four parallel engines disagree on payoff details (a
  quadratic cooperation bonus on by default in npdl; a self-inclusive cooperator count in
  one runner producing impossible payoffs).

## 3. What is scientifically uncertain (carried forward)

- Which exact code produced each paper figure (MED-HIGH confidence it was the standalone
  scripts) and what the 66%/75%/80% cooperation denominators were.
- Whether the legacy TFT-E explored per round or per decision (draft is silent);
  this repo explores per decision and documents the gap (Study 000 erratum note).
- Whether the canonical N-person reciprocator "should" be pTFT or threshold TFT — Study 000
  shows the Tragic Valley claim is strategy-dependent (threshold TFT does NOT collapse).
  This narrows, not overturns, the legacy story: HUMAN decision on how to frame it.
- RL/Q-learning claims: untested here (out of foundation scope).

## 4. Architecture options considered

- **A. Extend legacy NPDL** — rejected: global RNG, float payoffs, four divergent engines,
  no typed schemas/ledger; the audit shows the risk is not hypothetical.
- **B. Build on Concordia v2.4.0** — rejected as substrate: the Game Master adjudicates
  world state via LLM free-text; nondeterministic, unhashable, scored variables in
  generative hands. No documented ledger/replay/branching.
- **C. Own deterministic kernel + optional adapters** — CHOSEN (ADR-0001).

## 5. Recommended (and built) architecture

Five-plane typed scenarios compiled to content-hashed, mechanism/skin-separated resolved
scenarios (ADR-0003/0004); hash-linked JSONL event ledger with unhashed meta and
copy-on-write branching (ADR-0002); stateless hierarchical randomness giving paired runs
by construction (ADR-0005); human-gated study freezing with exhaustive manifests
(ADR-0006); LLM adapter with typed actions, bounded retries, observable rationale only
(ADR-0007). Two mechanisms: N-IPD (both interaction structures, exact fractions, the full
deconfounded TFT family) and Evidence Commons v0 (slots/propositions/evidence, provenance-
checking verification, net-support acceptance, 2×2 institutions, integer credit units).

Review fixes adopted from the adversarial architecture lens: determinism-scope statement
(replay ≠ model reproducibility), branch/run_id resolution via copy-on-write with honest
mixed run_ids, per-round derived streams instead of persisted RNG state (making Philox
unnecessary), float prohibition in all hashed content, domain-separation tags on every
hash. Rejected from the review: import-linter (a unit test greps the import direction
instead — cheaper), Philox/numpy in the kernel (no persisted RNG state to fast-forward).

## 6. Major failure modes this design guards (and their tests)

| failure mode | guard | test |
|---|---|---|
| model becomes world-truth authority | typed actions; engine-only resolution | capability + invalid-action tests |
| hidden truth leaks to agents | observation projection; truth fields only in world plane | leak canary scans of full ledgers |
| narrative changes mechanics | skin schema structurally inert; separate hashes | skin-isolation metamorphic test |
| unreproducible runs | seeds + ledger + manifests; replay verification | replay/rerun chain-equality tests |
| silent action repair | ActionRejected + explicit abstain fallback | invalid-LLM-output tests |
| pseudo-replication | episode as unit of analysis | METHODOLOGY.md + report design |
| defect-class recurrence (legacy 0% bug) | schema-safe metrics | legacy-defect regression fixture |
| fabricated cost/tokens | None-unless-measured manifests | cost-honesty test |

## 7. Decisions that remain human-owned

Study 001 final hypotheses/primary outcomes/utility weights/sample size/model providers/
cost ceiling; whether any legacy result counts as "replicated"; novelty claims; publication
readiness; repository publicity. Enumerated in HANDOFF.md and marked in PREREGISTRATION.md.
