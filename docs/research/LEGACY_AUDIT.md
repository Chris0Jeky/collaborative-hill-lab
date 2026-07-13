# Legacy Audit — N-Person Prisoner's Dilemma Simulation

**Status:** Foundation-phase discovery consolidation. **Date:** 2026-07-13.
Consolidates `_discovery/legacy-code-audit.md`, `_discovery/mechanism-math-review.md`, and
`_discovery/methodology-stats.md`. Confidence tags: **HIGH** (read the code and the artifact
first-hand), **MED** (strong inference), **LOW** (plausible, unverified).

---

## 1. What was audited, and how

**Legacy repository:** `github.com/Chris0Jeky/N-person-prisoners-dilemma-simulation`, cloned
read-only at commit **`f7f1cceb`** ("Create single_run_3tfte_only.py", branch `main`).
**Access date:** 2026-07-13.

**Scientific-claims source (reconciled).** The paper of record for the scientific claims is the
LaTeX draft **`Paper Resources/prisoners.tex`** — Tcaci & Huyck, *Navigating the N-Person
Prisoner's Dilemma: From the Tragic Valley to the Collaborative Hill*. It is an explicit
**work-in-progress** with visible `undone` markers, inconsistent per-figure replicate counts, and
no reported error bars or statistical tests. A separate PDF in the same folder — *Cooperation in
N-Person Iterated Prisoner's Dilemma: Pairwise vs Group Interaction Structures – A Li* — is a
**literature review**, not the results paper; where the discovery mechanism review calls "the
paper" a formula-free literature review, it is describing that *A Li* lit-review PDF, **not**
`prisoners.tex`. This reconciliation (lead engineer's verification) governs: treat `prisoners.tex`
as the claim source and the *A Li* PDF as motivation/terminology only.

**Method.** Every finding below was verified against source and committed artifacts first-hand;
legacy prose and summary docs were treated as suspect until confirmed. Payoff algebra was
re-derived by hand and independently re-enumerated numerically. The legacy repo's own scripts were
*not* executed end-to-end (no venv build); findings rest on reading source plus independent
re-derivation. Q-learning dynamics and large-N / network-topology effects were read but not
re-simulated.

**Ground-truth parameters (hand-derived, used as literals in the new lab's oracle — never derived
from legacy code):** N=3, T=5, R=3, P=1, S=0. Pairwise per-round payoffs (sum of two 2-player
games): all-C → 6 each; two C + one D → each C gets 3, the D gets 10; one C + two D → the C gets 0,
each D gets 6; all-D → 2 each. Neighbourhood linear public-goods payoffs with k = *other*
cooperators: `U_C(k)=3k/2`, `U_D(k)=1+2k`; all-C → 3 each; two C + one D → C gets 3/2, D gets 5;
one C + two D → C gets 0, D gets 3; all-D → 1 each. D strictly dominates in both modes; all-C
Pareto-dominates all-D.

---

## 2. Claim-by-claim audit table

Reproduction status vocabulary: **reproduced** (numeric match re-derived), **qualitatively
reproduced** (direction/mechanism confirmed, no numeric match yet), **not reproduced**, **ambiguous**
(under-specified), **blocked by defect** (the committed artifact is contaminated). At this stage most
claims are *qualitatively reproduced (pending Study 000 run)* or *blocked* — **no numeric reproduction
is claimed.**

| # | Claim | Where stated | Code path | Existing output | Theoretical expectation | Test coverage | Reproduction status | Suspected issue | Conf. |
|---|---|---|---|---|---|---|---|---|---|
| a | Pairwise 3×TFT sustains cooperation (Collaborative Hill) | `prisoners.tex` (static pairwise figure, ~l.250); `COMPREHENSIVE_NPD_DOCUMENTATION.md:104` | standalone per-opponent TFT (`final_experimentations/v9/final_agents.py:33-45`; `code_for_website/.../single_run_3tfte_standalone.py`) | website/`pictures/` figures (self-contained script); **contaminated** `test_results/pairwise_*_summary.csv` (all 0.0) | 3 mutual per-opponent TFTs never trigger retaliation ⇒ every edge stays `(C,C)` ⇒ 100% cooperation | none asserts it; `test_neighborhood_vs_pairwise.py` asserts the *opposite* for the npdl engine | **qualitatively reproduced** (standalone) / **blocked by defect** (npd_simulator CSV) | per-opponent vs defect-if-any TFT confound; unseeded standalone | HIGH |
| b | Pairwise 2×TFT + 1×AllD → defector quarantined, TFTs keep cooperating | `prisoners.tex` (2TFT+AllD stress); `COMPREHENSIVE_NPD_DOCUMENTATION.md:106` | standalone per-opponent TFT | figures only (per-agent coop rate ≈ 0.50 in re-sim; scores ≈ 4/round) | TFT–TFT edge is absorbing `(C,C)`=R each; TFT–AllD edge locks to `(D,D)`=P after one sucker round ⇒ each TFT earns R+P=4/round, AllD earns 2P=2 | none | **qualitatively reproduced** (independent 200-round re-sim, math review §3.2) | reported "~66%" vs re-derived per-agent 50% is a denominator mismatch; figures use TFT-E exploration | MED-HIGH |
| c | Neighbourhood 2×pTFT + 1×AllD → tragic-valley collapse | `prisoners.tex` (group/neighbourhood figures, coop "20%", ~l.328); `CORRECTED_RESULTS_SUMMARY.md:24-28` | standalone pTFT (`final_agents.py:54-66`; `static_figure_generator.py:58-66`) | figures; re-sim per-agent coop ≈ 0.015 | pTFT cooperates w.p. = prior-round group coop ratio; with one AllD the ratio contracts `q_r=(2/3)q_{r-1}→0` ⇒ universal defection | none | **qualitatively reproduced** (re-sim + closed-form, math review §3.3) | denominator convention (incl-self /N vs excl-self /(N-1)) changes the contraction ratio and fixed point | HIGH |
| d | Neighbourhood 3×TFT sustains (high cooperation) | `prisoners.tex` group figures; `test_results/neighbourhood_*_summary.csv` (=1.0) | npd_simulator neighbourhood path | CSV = 1.0 all rounds | pTFT with all cooperating stays at ratio 1 — a trivial fixed point | none | **reproduced (trivially)** | a fixed point that says nothing about the valley; contrast requires a defector to bite | HIGH |
| e | Pairwise TFT-E (ε-exploration) → ≈ 75/25 cooperation split | `prisoners.tex` EQL/exploration figures (avg of 500 runs, ~l.457); README | standalone TFT-E (`config.py` TFT-E exploration 0.1) | figures only | per-opponent TFT with 10% exploration relaxes the pure 100/0 edges toward a mixed rate | none | **ambiguous / qualitatively plausible** | unseeded; the "≈75/25" is a curve average with no dispersion reported | MED |
| f | Neighbourhood TFT-E → ≈ 80/20 cooperation split | `prisoners.tex` (coop "80% and 20%", l.285/328) | standalone pTFT + exploration | figures only | exploration floors the geometric decay above 0, settling near a low mixed rate | none | **ambiguous / qualitatively plausible** | same unseeded-average issue; the 80/20 headline has no error bars | MED |
| g | QL pairwise ≈ 80% / neighbourhood ≈ 20% cooperation | `prisoners.tex` EQL figures; `ql_comparison_analysis.md` | v9 `LegacyQLearner`/`Legacy3Round` (`cooperation_measurement.py`) | results dir not committed | per-opponent Q-tables can converge to CC vs TFT; diffuse Q cannot target | `test_pairwise.py:224` only checks Q-tables non-empty | **blocked — out of foundation scope** | RL out of scope; unseeded; no committed output to check | LOW |
| h | The published-figure pipeline reproduces the headline numbers | `prisoners.tex`; `CORRECTED_RESULTS_SUMMARY.md` | `npd_simulator/experiments/research_experiments.py` (research path) | **contaminated** `test_results/pairwise_tft_cooperation_all_experiments_summary.csv` (0.0 for all 20 rounds) | should report the per-round cooperation the standalone figures show | no regression test guards the extractor | **blocked by defect** (npd_simulator path); the *real* figures came from the standalone scripts, not this path | the `_extract_cooperation_by_round` schema-mismatch defect (§3) | HIGH |

---

## 3. The defect anatomy

**Location.** `3-Person_Tragic_vs_Reciprocity/npd_simulator/experiments/research_experiments.py`,
`_extract_cooperation_by_round()` at **lines 238–266** (the padding tail at 263–265).

**Mechanism.** The pairwise engine `PairwiseGame`
(`npd_simulator/core/game/pairwise_game.py:114–133`) records history as **pair-indexed** dicts —
keys `agent1_id, agent2_id, action1, action2, payoff1, payoff2, round, episode`. There is **no
`agents` key and no `cooperation_rate` key** on a pairwise record. The extractor, however, reads a
round-indexed schema:

```python
for round_data in sorted_history:
    if "agents" in round_data:                                   # never true for pairwise
        ... tft_coops from agent_data["action"] ...
    else:
        cooperation_rates.append(round_data.get("cooperation_rate", 0))   # key absent → 0
```

For pairwise history the `"agents"` branch is never taken, the `"cooperation_rate"` key is absent,
and `.get(..., 0)` returns **0 for every record** — including round 1, where TFT always cooperates.
Lines 263–265 then pad any short history to `num_rounds` with more `0.0`. The result is an
identically-zero pairwise cooperation curve. Because round 1 is also zero, this is provably a
**reporting/tracking bug, not a behavioural one**: the agents do cooperate; the reader looks at the
wrong schema and defaults to zero. (HIGH — read the code and the CSV.)

A contributing design flaw: `experiment_runner.run_pairwise_experiment` plays each pair to
completion sequentially (`experiment_runner.py:195–262`), so there is no common global round axis to
align pairwise against neighbourhood even with a correct reader.

**Contamination.** The committed `test_results/pairwise_tft_cooperation_all_experiments_summary.csv`
reports `3_TFT_mean = 0.0` for all 20 rounds (the neighbourhood twin reports 1.0). Any per-run CSV or
figure generated off this research path via `visualize_research_results.py` inherits the zeros. The
neighbourhood CSVs are not hit by *this* bug but come from a different code path with its own
semantics. (HIGH.)

**Non-fix.** The defect was **never fixed in place**. `CORRECTED_RESULTS_SUMMARY.md` only *describes*
the expected corrected picture and lists the fix as a TODO. A parallel
`static_style_runner.run_pairwise_experiment_enhanced` (`static_style_runner.py:132–200`) builds a
proper synchronized round loop that would report cooperation correctly, but it is a **different
runner** and there is no evidence it regenerated the committed `test_results`. The de-facto "fix" was
to **abandon this path** and generate the paper figures with the standalone
`final_experimentations`/`code_for_website` scripts, which track per-agent cooperation directly. That
standalone tracking is correct, but it is a *different experiment* (different TFT semantics, unseeded)
— so the "corrected results" are trustworthy as a new run, not as a bug-for-bug repair of the
`npd_simulator` numbers. (HIGH / MED.)

---

## 4. The TFT-semantics confound (co-equal to the defect)

"TFT" is **not one strategy** across the legacy codebase. Three pairwise and two neighbourhood
definitions coexist:

- **Per-opponent pairwise TFT** (standalone `final_agents.py:33-45`;
  `single_run_3tfte_standalone.py`): keeps `opponent_last_moves[opponent_id]` and retaliates
  *only* against the specific opponent who defected. This is genuine targeted reciprocity and is the
  strategy behind the published Collaborative-Hill figures.
- **Defect-if-any pairwise TFT** (`npdl/core/agents.py:88-96`): emits **one move per round applied to
  all opponents** and defects against everyone if **any** opponent defected last round
  (`if any(move == "defect" ...): return "defect"`). This is a grim-ish collective trigger, *not*
  targeted reciprocity. Under 2 TFT + 1 AllD it makes both TFTs defect against *each other*, breaking
  the very `(C,C)` relationship the Hill result depends on — it reproduces the **wrong** result for
  the central claim. A committed test (`test_neighborhood_vs_pairwise.py:67-70`) actively enshrines
  this behaviour (`assert final_moves_p[i] == "defect"`).
- **True per-opponent engine** (`npdl/core/true_pairwise.py`, `OpponentSpecificMemory`): a separate,
  correct per-opponent implementation, but it is **not wired into `main.py`**.
- **Neighbourhood probabilistic pTFT** (`final_agents.py:54-66`): cooperate w.p. = prior-round group
  cooperation ratio — the paper's group-average generalization, which `prisoners.tex`/`A Li` predict
  a priori will collapse.
- **Neighbourhood 0.5-threshold "ecosystem-aware TFT"** (`npdl/core/agents.py:99-115`): cooperate iff
  coop-proportion ≥ 0.5 — the paper's *quorum/threshold* idea, **relabelled** "TFT". The name
  "ecosystem-aware TFT" is a legacy-code coinage, not from either paper document.

**Consequence.** The headline Hill-vs-Valley gap partly conflates *interaction structure* (pairwise vs
neighbourhood) with *decision rule* (deterministic per-opponent reciprocity vs probabilistic
group-average). Which engine you run changes the answer. A clean study must hold the strategy fixed
across conditions or treat the strategy itself as an explicit, named variable. (HIGH.)

---

## 5. Payoff-variant inconsistencies

- **Duplicate definition.** `npdl/core/utils.py` defines `get_pairwise_payoffs` **twice** (lines 138
  and 152); the second shadows the first. Numerically identical, so no live bug, but dead code and a
  maintenance hazard. (HIGH, low severity.)
- **Self-exclusion disagreement in the "final" runner.** `single_run_3tfte_standalone.py` and
  `cooperation_measurement.py` correctly exclude self when counting other cooperators; but
  `final_simulation.py:10-14` with call site `:58` passes the **total** cooperator count, not the
  others' count — for 3-of-3 cooperating this yields `0 + 3·(3/2) = 4.5 > R`, an impossible payoff.
  So two "final" runners disagree on the neighbourhood denominator; which one fed a given figure
  matters. (MED — flag for reproduction.)
- **Undocumented quadratic global bonus.** `npdl/core/environment.py:192-198` adds a quadratic global
  cooperation bonus to cooperators only (`global_bonus = global_coop_rate**2 * 2`, max +2), **on by
  default**. This is not in the linear model of either paper document and silently inflates cooperator
  payoffs — any npdl neighbourhood run left at defaults is *not* the paper's game. (HIGH.)
- **Scale mismatch, unnormalized.** Pairwise sums N−1 games (all-C total = (N−1)·R = 6 at N=3) while
  neighbourhood normalizes to one game's scale (all-C = 3). Within `npdl`, the pairwise path *learns*
  from the average payoff but *scores* the total — reward and fitness signals on different scales
  within one file. Cross-mode comparisons are not apples-to-apples without dividing pairwise by (N−1).
  (HIGH — asserted by legacy tests `test_neighborhood_vs_pairwise.py:305-320`.)
- **Cooperation-ratio denominator, three ways.** The scalar driving pTFT is computed as `/N` incl.
  self (`static_figure_generator.py:180`, `npd_game.py:89`) in some paths and `/(N-1)` excl. self
  (`environment.py:348`, `agents.py:111-112`) in others. For 2 TFT + 1 AllD this is the difference
  between a `2/3` and `1/2` signal — materially different collapse dynamics and fixed points. The
  single most under-specified quantity in the legacy code. (HIGH.)
- **Code-only payoff variants.** `utils.py:40-135` implements `exponential_*` (exponent 2) and
  `threshold_*` (0.3/0.7 at threshold 0.5) payoff shapes with arbitrary magic constants and no paper
  grounding. Not "the paper's payoff function." (HIGH.)

---

## 6. Seeding and methodology weaknesses

- **Unseeded headline stack.** The `npd_simulator` research path — the one that generated the
  committed (contaminated) CSVs and the standalone paper scripts — has **no seeding anywhere** (`grep
  seed` returns nothing in `single_run_3tfte_standalone.py`, `final_simulation.py`,
  `cooperation_measurement.py`). Results are reproducible only *in distribution*, never bit-for-bit.
  Only `npdl/main.py:334-335` seeds (`random.seed(run_number)`), and it is not the path that made the
  figures. All randomness draws from a single process-global RNG shared by network construction,
  exploration, and tie-breaks — no per-agent or per-component stream isolation. (HIGH.)
- **Zero-width confidence intervals from deterministic configs.** The research runner uses
  `num_runs=20, num_rounds=200` "for statistical significance", but the headline `3_TFT` and
  `2_TFT + 1_AllD` configs are **fully deterministic** (`exploration_rate: 0.0`), so all 20 runs are
  identical → `std=0`, CI width 0. "20 runs" is one run copied 20×; the only genuine variance sources
  are TFT-E, Random, or Q-learning configs. (V.)
- **Normal-approx (z) instead of t, population std.** CIs use fixed `z=1.96` for n=20 (a t-interval is
  ~7% wider) and `np.std` with `ddof=0` (population std), both biasing intervals **too narrow**.
  (V — `research_experiments.py:274-281`.)
- **No hypothesis tests in the headline path.** "Tragic valley"/"reciprocity hill" are declared by the
  **raw sign** of a mean difference (`shows_tragic_valley: pw_coop > nb_coop`), with no CI on the
  difference and no test — any nonzero difference flips the boolean. The `npdl` analysis path *does*
  run ANOVA + Welch t-tests but **always uncorrected** (`if p_anova < alpha or True:`), with an in-code
  comment acknowledging the missing Bonferroni/Tukey correction. (V.)
- **Padding bias.** Runs shorter than `num_rounds` are padded with `0.0` (lines 263–265), silently
  pulling means down and inflating variance. (V.)
- **Noisy single-round estimator.** `npdl` computes `final_cooperation_rate` from the **single last
  round** — an N=3 proportion from one round — a high-variance point estimate where a last-K-round
  average would be far more stable. (V.)
- **Uncorrected multiple comparisons / forking paths.** The QL sweep enumerates 30+ configs, each
  labelled success/degraded/stable by a ±0.1 threshold, with no correction, no pre-declared family,
  and post-hoc "tragic valley observed" labelling. Shipped scenarios are underpowered (n=3–5). The
  paper reports inconsistent per-figure replicate counts (50 / 100 / 500 runs) with no error bars, CIs,
  or tests anywhere. (V.)

---

## 7. What Study 000 in this repo does about each

The new lab reimplements everything from scratch (Option C — see
`_discovery/architecture-stress.md` §7); legacy is retained only as an external **oracle** and as
behavioural fixtures, never imported into the kernel. Study 000 deconfounds structure from strategy
and hardens every weakness above:

- **Defect (§3).** Replaced by a typed, fail-loud metrics layer over a single canonical round schema
  with integer/`Fraction`-exact quantities; there is no silent `.get(..., 0)` fallback and no
  cross-schema round axis. A regression asserts round-1 cooperation is never zeroed for a cooperating
  policy. The contaminated `test_results/*` CSVs are discarded, never used as fixtures.
- **TFT confound (§4).** Study 000 gives the strategies **distinct names** and holds them explicitly:
  per-opponent pairwise TFT, probabilistic neighbourhood pTFT, and the 0.5-threshold quorum strategy
  are separate policies, never all called "TFT". A metamorphic oracle asserts that 2 TFT + 1 AllD keeps
  the TFT–TFT edge at `(C,C)` forever (rate 1.0) while TFT–AllD locks to 0 after round 1 — guarding
  against the defect-if-any regression. The Hill-vs-Valley contrast is thereby attributable to
  interaction structure, with strategy as an explicit second variable.
- **Payoff variants (§5).** A single payoff oracle is the sole source of truth, checked against the
  §1 hand-derived golden tables (never against the code under test); the duplicate function, the
  self-exclusion bug, the quadratic global bonus, and the code-only exponential/threshold shapes are
  simply not carried over. The cooperation-ratio denominator (excl-self /(N-1) in `world/nipd.py`) and
  the score/reward normalization are each a single documented, asserted convention.
- **Seeding & methodology (§6).** Seeds are derived by *identity* (not draw order) with
  length-unambiguous labelling, per-stream and recorded in a run manifest; runs are hash-chained and
  replay bit-for-bit. Deterministic configs are flagged (no false zero-width CI); the unit of analysis
  is the episode, not the round; CRN-paired scenario seeds enable powered paired contrasts; effect
  sizes with intervals replace sign-of-difference; a pre-declared confirmatory family with a
  correction replaces the uncorrected sweep; exploratory and confirmatory analyses are split. These
  rails live in the study lifecycle and are covered in `_discovery/methodology-stats.md` §§2–4.

**Honest status.** Study 000 is scaffolding for a *run*, not a run. The claims in §2 remain
*qualitatively reproduced (pending Study 000 run)* or *blocked/out-of-scope*; **no numeric
reproduction of the legacy headline percentages is claimed at this stage.**
