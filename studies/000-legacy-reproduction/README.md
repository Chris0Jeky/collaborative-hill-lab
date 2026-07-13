# Study 000 — Legacy reproduction and audit

**Status:** foundation study (scripted agents only, no LLM, no freeze required — it is an
audit, not a confirmatory experiment).
**Legacy source:** `Chris0Jeky/N-person-prisoners-dilemma-simulation` @ `f7f1cceb` (read-only
clone, accessed 2026-07-13); claims from the paper draft `Paper Resources/prisoners.tex`
(Tcaci & Huyck, *Navigating the N-Person Prisoner's Dilemma: From the Tragic Valley to the
Collaborative Hill*, work in progress).

## Research question

Does the legacy headline result — **pairwise voting sustains cooperation (Collaborative
Hill) while neighbourhood voting collapses (Tragic Valley)** — reproduce qualitatively in an
independent, deterministic, seeded reimplementation? And how much of the effect is the
*interaction structure* versus the *silently different TFT decision rules* the legacy code
used in each condition (see `docs/research/LEGACY_AUDIT.md`)?

## Game definitions (exact)

Parameters `T=5, R=3, P=1, S=0` (satisfy `T>R>P>S`, `2R>T+S`).

- **Pairwise**: each round, every agent plays an independent 2-player PD against each other
  agent (one move per opponent). Score = sum of the N−1 games.
- **Neighbourhood**: one collective vote per agent; with `k` = number of *other* cooperators:
  `U_C(k) = S + (R−S)·k/(N−1)`, `U_D(k) = P + (T−P)·k/(N−1)`.

N = 3 payoff oracle (hand-derived; enforced by `tests/unit/test_payoff_oracle.py`):

| profile | pairwise (per agent) | neighbourhood (per agent) |
|---|---|---|
| C,C,C | 6, 6, 6 | 3, 3, 3 |
| C,C,D | 3, 3, 10 | 3/2, 3/2, 5 |
| C,D,D | 0, 6, 6 | 0, 3, 3 |
| D,D,D | 2, 2, 2 | 1, 1, 1 |

## TFT variants (deconfounded — the legacy work conflated these)

| policy | rule | legacy source |
|---|---|---|
| `tft_pairwise` | per-opponent mirror, start C | paper's pairwise TFT (standalone scripts) |
| `tft_linked` | ONE move for all; defect if ANY opponent defected against me | legacy npdl "pairwise" TFT (agents.py:88-96) |
| `ptft[include_self]` | P(C) = last-round cooperators (incl. self)/N | figure-generating standalone code |
| `ptft[exclude_self]` | P(C) = other cooperators/(N−1) | paper-text reading (prisoners.tex §Strategies) |
| `tft_threshold[1/2]` | C iff other-coop ratio ≥ 1/2 | npdl "ecosystem-aware TFT" |

## Conditions and pre-stated analytical predictions

50 rounds, seed 20260713, 30 replicates (deterministic conditions produce identical
summaries across replicates — reported as a determinism check, not as fake variance).

| condition | prediction (stated BEFORE running) |
|---|---|
| pw-3tft | cooperation 1.0 every round; each score 300 |
| pw-2tft-alld | Hill via quarantine: TFT–TFT edge locks C,C; group vote rate (4/6) then 2/6; TFT scores 199, AllD 108 |
| pw-2tftlinked-alld | COLLAPSE despite pairwise structure: any-defect rule spreads punishment; all-D from round 2 |
| nb-3ptft-incself | all-C absorbing; cooperation 1.0 |
| nb-2ptft-alld-incself | Tragic Valley: geometric decay of P(C) (≈ (2/3)ʳ envelope), absorption at all-D |
| nb-2ptft-alld-excself | valley with faster decay (initial signal 1/2 vs 2/3) |
| nb-2tftthresh-alld | NO collapse: 1-of-2 others = exactly 1/2 ≥ threshold → sustained 2/3 group rate (knife-edge quorum) |
| pw-2tfte-alld | legacy claims ≈25% ("pair with the always defect agent largely defect"); qualitative band 0.10–0.40. NOTE: plain TFT with per-decision ε=0.1 falls into defection echoes on the TFT–TFT edge, so cooperation is LOW here — the Hill claim belongs to the AllC pairing below |
| nb-2ptfte-alld-incself | legacy claims ≈20%; qualitative band 0.05–0.35 |
| pw-2tfte-allc | legacy claims ≈75% ("pair with the collaborative agent largely collaborate"); qualitative: > 0.5 |
| nb-2ptfte-allc-incself | legacy claims ≈80%; qualitative: > 0.5 |

Prediction-encoding erratum (recorded, not hidden): the first run of this study encoded
pw-2tfte-alld as "mostly cooperative" — a misreading of prisoners.tex, whose 75%/25% figures
refer to the AllC/AllD pairings respectively. The prediction table above is the corrected
reading; the AllC pairings were added as conditions at the same time. Exploration
granularity is a further ambiguity: the draft does not say whether TFT-E flips one coin per
round or per opponent-decision; this implementation explores per decision.

The pw-2tftlinked and nb-2tftthresh rows are the deconfound: if structure alone drove the
result, linked-TFT pairwise should stay high and threshold-TFT neighbourhood should collapse.
Our analysis (and the legacy audit) predicts the opposite for both.

## Claims under test (from prisoners.tex)

1. "three TFT system continues to collaborate" (pairwise) — §Tragic Valley.
2. "two TFT agents … always collaborate with each other but … defect against the always
   defect agent" (pairwise quarantine) — §Tragic Valley.
3. "TFT agents with the always defect initially vote to collaborate, but then quickly move
   to always defect. They descend into the Tragic Valley." (neighbourhood) — §Tragic Valley.
4. TFT-E averages ≈75%/25% (pairwise) and ≈80%/20% (neighbourhood) — §figStaticAverage
   (qualitative only; legacy runs were unseeded and the cooperation *denominator* is not
   defined precisely in the draft).
5. Q-learning/EQL claims — **excluded** (RL agents are out of the foundation's scope;
   recorded as `blocked (out of scope)` in the replication report).

## Exclusions

- RL/Q-learning/EQL conditions (foundation is scripted-only by design).
- Exact-number reproduction of legacy CSVs/figures: the legacy pipeline was unseeded and the
  pairwise tracking defect contaminated its committed outputs; we reproduce *claims*, not
  artifacts. See `tests/unit/test_legacy_defect_regression.py` for the defect fixture.

## Analysis plan

Per condition: replicate-level `mean_cooperation` and `final_window_cooperation`
(episode = unit of analysis), percentile bootstrap CIs over replicates for stochastic
conditions, exact determinism check for deterministic ones, decay-curve inspection for
valley conditions. Output: `docs/research/REPLICATION_REPORT.md` via `generate_report.py`,
classifying every claim as reproduced / qualitatively reproduced / not reproduced /
ambiguous / blocked by defect / blocked (out of scope).

## How to run

    chl run "studies/000-legacy-reproduction" --artifacts artifacts
    python "studies/000-legacy-reproduction/generate_report.py"
