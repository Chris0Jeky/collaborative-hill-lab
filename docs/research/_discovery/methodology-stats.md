# Methodology & Statistics Discovery — Collaborative Hill Lab

**Role:** Experimental methodology and statistics reviewer
**Date:** 2026-07-13
**Legacy clone (READ-ONLY):** `.../scratchpad/legacy-npd`
**Scope:** Audit legacy experimental methods; design a research-grade statistical backbone for an LLM-agent lab; deliver preregistration template, statistical analysis plan (SAP) for a 2×2 design, and LLM-specific validity threats.

Confidence legend: **[V]** verified against code/math/paper text first-hand; **[I]** inferred/interpretation; **[R]** recommendation (forward-looking, not a legacy claim).

---

## 1. LEGACY METHODS AUDIT

### 1.0 Two parallel, inconsistent experiment stacks [V]

The legacy repo runs experiments through **two independent pipelines with different, incompatible statistics discipline**. Any "reproduction" study must pick one deliberately.

| | **Headline "research" stack** | **Older `npdl` stack** |
|---|---|---|
| Entry point | `3-Person_Tragic_vs_Reciprocity/run_research_experiments.py` | `main.py`, `npdl/simulation/runner.py` |
| Engine | `npd_simulator/experiments/runners/experiment_runner.py` | `npdl/core/environment.py` + `true_pairwise*` |
| Replicates | `num_runs=20`, `num_rounds=200` (`run_research_experiments.py:30-33`) | `num_runs` default **10** (`runner.py:454`, `main.py:273`) |
| **Seeding** | **NONE** (grep for `seed`/`np.random.seed` in `npd_simulator/` returns empty) | `random.seed(run_number)` + `np.random.seed(run_number)` (`runner.py:512-513`) |
| Stats | mean/std + 95% CI via normal approx; **no hypothesis tests** | ANOVA `f_oneway` + Welch t-tests (`analysis.py:656,687`), **uncorrected** |
| Effect claim | raw sign of mean difference | p-value with `*/**/***` stars |

The paper (`Paper Resources/prisoners.tex`) does **not** match either exactly on replicate count.

### 1.1 Headline stack details (`research_experiments.py`) [V]

- **Replicates & aggregation:** For each config, 20 runs × 200 rounds. `_save_aggregated_csv` (lines 268-302) computes, per round, `means = np.mean(data, axis=0)`, `stds = np.std(data, axis=0)` across the 20 runs, then `ci_margin = 1.96 * stds / sqrt(n)` with `n=20` (lines 277-281). Unit of aggregation is the **run** (correct choice) but:
  - **Normal approx, not t:** uses fixed `z=1.96` for n=20; a t-interval (`t_{.975,19}=2.093`) is ~7% wider. Minor but systematic under-coverage. **[V]**
  - **`np.std` is population std (ddof=0):** biases the CI **too narrow** at small n. **[V]** (`np.std` default `ddof=0`, line 275.)
- **No hypothesis tests at all.** "Tragic valley" / "reciprocity hill" are declared by the **raw sign** of a mean difference: `"shows_tragic_valley": pw_coop > nb_coop` (lines 366-368), with **no CI on the difference and no test** (lines 359-369, 454-469). Any positive/negative difference of any magnitude flips the boolean. **[V]**
- **Unseeded → non-reproducible AND degenerate for deterministic configs.** Because `npd_simulator` never seeds, two problems:
  1. Re-running yields different numbers → results are not reproducible. **[V]**
  2. Several headline configs are **fully deterministic** — `3_TFT` and `2_TFT__plus__1_AllD` use `exploration_rate: 0.0` (lines 39-53) and deterministic TFT/AllD/AllC agents. With deterministic dynamics, **all 20 runs are identical**, so `std=0`, the CI has **zero width**, and the "20 runs for statistical significance" (comment, `run_research_experiments.py:31`) is illusory — it is one run copied 20×. The only stochastic configs are those with TFT-E (`exploration_rate 0.1`), `Random`, or Q-learning `epsilon`. **[V/I]**
- **Metric inconsistency across configs.** `_extract_cooperation_by_round` (lines 238-266) extracts cooperation from **only TFT/pTFT-typed agents** when present (lines 247-256), else falls back to the round's all-agent `cooperation_rate` (line 258/260). So "cooperation" means different denominators for different configs — not comparable across the 2×2-style contrasts. **[V]**
- **Zero-padding bias.** If a run's history is shorter than `num_rounds`, missing rounds are padded with `0.0` (lines 263-265), silently pulling means down and inflating variance. **[V]**
- **Ad hoc convergence detection.** `_find_convergence` flags convergence when a sliding 10-round window has `std < 0.05` (lines 410-421); arbitrary threshold, no justification, used in reported analysis. **[V]**
- **Multiple comparisons unmanaged.** The Q-learning sweep enumerates `2QL × 5 others × {QL,EQL}` plus all `1QL` pairs (`i,j` double loop, lines 129-141) → ~30+ configs, each labeled success/degraded/stable by a ±0.1 improvement threshold (lines 474-479). No correction, no family definition. **[V]**

### 1.2 Older `npdl` stack details [V]

- **Seeding is present and is a paired/CRN design.** `runner.py:512-513` sets `seed = run_number` for both `random` and `numpy`, **reset identically for every scenario**. This means scenario A run 3 and scenario B run 3 share the same seed → common random numbers across conditions (variance-reduction, good for paired comparison). But: seeds are the small ints 0..n-1 only, and numpy vs Python `random` streams are not independent-substream-safe. **[V/I]**
- **Statistical tests exist but are explicitly uncorrected.** `analysis.py` runs one-way ANOVA (`stats.f_oneway`, line 656) then **always** runs pairwise Welch t-tests regardless of ANOVA (`if p_anova < alpha or True:`, line 676) with the in-code comment: *"Using simple t-tests without correction for multiple comparisons here. For rigorous analysis, consider corrections like Bonferroni or Tukey's HSD."* (lines 672-674). So the code knows the gap and ships it anyway. **[V]**
- **Unit of analysis is correct (per-run), but the estimator is noisy.** `final_cooperation_rate` is computed **from the single last round only** (`final_round = run_df[run == max]`, then `mean(move=="cooperate")`; lines 605-611) — an N-agent (=3) proportion from one round. Extremely high-variance point estimate; a last-K-round average would be far more stable. `average_final_score` similarly per-run (lines 620-631). **[V]**
- **Very low replicate counts in shipped scenarios.** `scenarios/true_pairwise_scenarios.json` sets `"runs": 3` or `"runs": 5` per scenario (verified lines 19,33,55,70,...). n=3 t-tests are effectively uninterpretable. **[V]**

### 1.3 Paper methods (`prisoners.tex`) [V]

- **Inconsistent replicate counts across figures, never justified:** "Fifty iterations are performed" for static-policy pairwise (line ~250), "the results reflect an average of 100 runs" (line 314), "average of 500 runs" for EQL (line 457). Different N per figure suggests per-figure tuning rather than a fixed protocol. **[V]**
- **No error bars, no CIs, no statistical tests reported anywhere.** Grep for `t-test|anova|p<|CI|interval|variance|significan` finds only one informal use: "demonstrate a clear and significant improvement" (line 433) — rhetorical, not statistical. **[V]**
- **Claims stated as averages of curves** (cooperation ratio "80% and 20%", lines 285, 328) with no dispersion. **[V]**

### 1.4 Consolidated legacy weaknesses (the ones the new lab must not inherit)

1. **Non-reproducibility** — headline pipeline unseeded; no run manifest binds results to code/config version. **[V]**
2. **Pseudo-replication / degenerate variance** — deterministic configs replicated 20× report a CI as if independent; only source of variance is agent stochasticity, not scenario sampling. **[V]**
3. **No inferential statistics in the headline path**; effect existence decided by sign of a difference. **[V]**
4. **Uncorrected multiple comparisons** in the path that does test (30+ configs). **[V]**
5. **Noisy single-round outcome estimator** (`final_cooperation_rate` from one round). **[V]**
6. **Inconsistent outcome definition** (TFT-only vs all-agent cooperation). **[V]**
7. **Silent data mangling** (zero-padding to `num_rounds`). **[V]**
8. **Garden of forking paths** — many configs, post-hoc labels ("tragic valley observed"), no exploratory/confirmatory split, no preregistration. **[V/I]**
9. **Underpowered shipped scenarios** (n=3–5). **[V]**
10. **Rounds are autocorrelated within a run** — any analysis that pools rounds as independent samples (the paper's curve averaging implicitly, and any per-round test) violates independence. The headline aggregation avoids this by collapsing to per-run summaries first; the paper's prose does not. **[V/I]**

---

## 2. NEW-LAB METHODOLOGY BACKBONE (LLM agents)

For each item: **what**, **why**, **failure mode prevented**. All **[R]**.

1. **Unit of analysis = the episode (one full game/session), never the turn.**
   - *Why:* turns within an episode are autocorrelated (an agent's move at t depends on its own and others' history). n = number of independent episodes, not turns×episodes.
   - *Prevents:* pseudo-replication — the legacy paper's curve-averaging and any "1000 turns → n=1000" claim. Inflated significance from treating a single episode as thousands of samples.

2. **Paired scenario seeds across conditions (common random numbers).**
   - *Why:* fix a `scenario_seed` that determines environment content (which evidence items exist, event order, group composition) and reuse the *same* seed set across all cells of the design; vary only the treatment. Differences are then within-scenario, dramatically reducing variance. This is the one genuinely good instinct in the legacy `npdl` runner (seed=run_number shared across scenarios) — keep it, formalize it.
   - *Prevents:* between-condition differences being swamped by which-scenario-you-drew noise; enables paired/mixed-model analysis with far higher power.

3. **Full seed provenance and reproducibility manifest.**
   - *Why:* record `{scenario_seed, agent_sample_seed, provider, model_id + version/date, temperature, top_p, prompt_template_hash, code_git_sha, config_hash}` per episode. LLM sampling is a second RNG you don't control at the client — log everything you *can* pin and everything you *can't*.
   - *Prevents:* the legacy non-reproducibility; silent provider/model drift invalidating cross-time comparisons.

4. **Condition-order and position randomization.**
   - *Why:* randomize which agent slot/seat each policy occupies, the order conditions are executed, and the order options/agents appear in prompts. Balance or randomize.
   - *Prevents:* position/primacy bias (LLMs favor first-listed options) and temporal provider drift confounding a condition that happened to run "in the morning."

5. **Pilot → power → confirm procedure.**
   - *Why:* run a small pilot (e.g., 5–10 episodes/cell) to estimate the between-episode SD of the primary outcome, compute the N needed for a pre-specified minimum effect size at 80–90% power, *then* run the confirmatory batch at that N. Do not read the pilot's p-values.
   - *Prevents:* both underpowered studies (legacy n=3–5) and optional-stopping p-hacking.

6. **Report effect sizes with uncertainty intervals, not just p.**
   - *Why:* primary readout = estimated treatment effect (e.g., difference in mean episode cooperation, or standardized effect / risk ratio) with a 95% interval, ideally bootstrap or model-based (cluster-aware). p-values secondary.
   - *Prevents:* the legacy "sign of the difference = effect" and "significant" hand-waving; makes practical magnitude legible.

7. **Multiple-comparison discipline tied to a pre-declared family.**
   - *Why:* declare the confirmatory family (usually 1–3 primary contrasts) and control FWER (Holm) or FDR (Benjamini–Hochberg) within it; everything else is exploratory and labeled as such.
   - *Prevents:* the legacy uncorrected 30-config sweep and forking-paths inflation.

8. **Exploratory vs confirmatory separation (preregistration).**
   - *Why:* freeze hypotheses, outcomes, and the analysis before the confirmatory data are seen. Exploratory findings are allowed and valuable but reported in a separate section and never claimed as confirmed.
   - *Prevents:* post-hoc "tragic valley observed" narratives; HARKing.

9. **Narrative-skin robustness checks.**
   - *Why:* the same game mechanics dressed in different surface narratives (e.g., "evidence commons" vs "shared wiki" vs neutral tokens). Run the primary contrast across ≥2–3 skins.
   - *Prevents:* mistaking a prompt-story artifact for a mechanism effect; the effect must survive re-skinning to be real.

10. **Provider/model drift logging + periodic anchor re-runs.**
    - *Why:* pin `model_id` and log the served version/date; re-run a fixed "anchor" scenario at intervals to detect silent behavioral drift between provider updates.
    - *Prevents:* comparing conditions collected weeks apart under a silently-updated model; time-confounded conclusions.

11. **Pre-declared exclusion rules for invalid episodes.**
    - *Why:* define upfront what counts as invalid (malformed/unparseable action, refusal, context-overflow truncation, API error, timeout) and how it's handled (retry-then-exclude, or intention-to-treat coding). Report inclusion rate per cell.
    - *Prevents:* per-cell differential attrition silently biasing results; ad hoc dropping.

12. **Stopping rules fixed in advance.**
    - *Why:* the confirmatory N (from step 5) is the stop; no "run more until significant." If sequential analysis is wanted, use a pre-registered group-sequential/alpha-spending design.
    - *Prevents:* optional-stopping false positives.

13. **Cost ceiling per study.**
    - *Why:* LLM episodes cost tokens/$; declare a max spend and max episodes so power decisions are made under an explicit budget (may force a larger minimum detectable effect). Log token+$ per episode.
    - *Prevents:* silently truncating a study when the bill arrives → underpowered, biased-by-when-you-stopped data.

14. **Negative-result preservation.**
    - *Why:* register outcomes and report them regardless of direction; keep all run artifacts (including failed/null cells) in the ledger.
    - *Prevents:* publication/selection bias inside the lab's own corpus; the legacy habit of surfacing only the configs that "show" the effect.

---

## 3. PREREGISTRATION TEMPLATE (field list)

Draft fields with 1–2 sentence guidance each. **[R]**

1. **Title & version** — Short name + semantic version + date; bump on any change after data collection starts.
2. **Hypothesis (H1…Hk)** — One directional, falsifiable sentence each (e.g., "Pairwise accountability yields higher mean episode cooperation than aggregate accountability"). Mark each as confirmatory or exploratory.
3. **Mechanism / theory of change** — The causal story you expect (why the IV should move the DV). Grounds interpretation and the robustness checks.
4. **Independent variables & levels** — Each factor, its levels, and how it is operationalized in the scenario spec (e.g., accountability ∈ {pairwise, aggregate}; evidence-topology ∈ {star, ring}). Note crossed vs nested.
5. **Primary outcome(s)** — The single (or ≤2) pre-committed DV and its exact computation at the episode level (e.g., mean cooperation over the last K rounds of the episode). One number per episode.
6. **Secondary/exploratory outcomes** — Additional DVs, explicitly non-confirmatory (e.g., time-to-convergence, misinformation rate, payoff inequality).
7. **Population / model selection** — Which model(s), provider(s), version pin, temperature/top_p, and the agent-policy population; sampling frame for scenarios (how scenario seeds are drawn).
8. **Pilot plan** — Size and purpose of the pilot; explicitly state that pilot data are used only to estimate variance/feasibility, not to test hypotheses, and whether pilot episodes are discarded.
9. **Sample-size decision procedure** — The minimum effect size of interest, target power and α, the variance estimate source, and the resulting N per cell; the formula/simulation used.
10. **Randomization** — What is randomized (seat/position, condition order, prompt option order, scenario→cell assignment), the RNG seed policy, and the CRN pairing across conditions.
11. **Exclusion / data-handling rules** — Definition of an invalid episode, retry policy, inclusion-rate reporting, and how invalid *actions within* a valid episode are coded.
12. **Analysis plan** — The exact model/estimand for each primary hypothesis (see §4), the test statistic, the software, and how uncertainty intervals are formed (bootstrap/model-based, cluster-aware).
13. **Multiple-comparison handling** — The declared confirmatory family and the correction method (Holm/BH) and target error rate.
14. **Robustness / sensitivity checks** — Pre-listed: narrative-skin replication, alternative outcome window, alternative model, prompt-paraphrase set, seed re-draw.
15. **Stopping rule** — When data collection stops (fixed N or pre-registered sequential design). No open-ended "until significant."
16. **Cost ceiling** — Max episodes and max $ / tokens; what happens if the ceiling binds before N is reached (down-scope hypotheses, do not silently truncate).
17. **Claim boundary** — One sentence on the scope of any positive result (which models/skins/topologies it does and does not license generalizing to). Guards against anthropomorphic overclaiming.
18. **Deviations log** — A committed-to place to record any departure from this prereg, with timestamp and rationale.

---

## 4. STATISTICAL ANALYSIS PLAN — 2×2 (accountability × evidence-topology), 3–5 LLM agents/episode

Design: factors **A = accountability** {pairwise, aggregate}, **T = evidence-topology** {e.g., star, ring}; crossed → 4 cells. Each **episode** = one game with 3–5 agents over R rounds. **[R]**

### 4.1 Estimands
- **E1 (primary, main effect of A):** difference in expected episode-level mean cooperation between pairwise and aggregate accountability, averaged over topology.
- **E2 (main effect of T):** analogous for topology.
- **E3 (interaction A×T):** does the accountability effect depend on topology (the "targeted reciprocity needs the right structure" claim).
- All estimands defined on the **episode-mean cooperation over the last K rounds** (pre-registered K), one scalar per episode.

### 4.2 Data structure
- Rows = episodes. Columns: `A, T, scenario_seed, agent_seed, model_id/version, seat_permutation, outcome, invalid_action_count, tokens, cost`.
- Agents are **nested within episode**; agent-level actions are *not* independent → do not treat 4 agents × 200 rounds as 800 samples.

### 4.3 Models (in increasing sophistication; pre-commit to one primary)
1. **Primary — episode-level linear model on the scalar outcome:**
   `outcome ~ A * T` (OLS with A, T effect-coded). With CRN-paired scenario seeds, add the paired scenario as a blocking factor: `outcome ~ A * T + C(scenario_block)`, or use paired differences per scenario for the primary contrast. Report each effect with a 95% CI (t-based or bootstrap).
2. **If modeling round-level or agent-level actions directly — mixed / cluster-robust:**
   Binary cooperate/defect per agent-round via a GLMM: `cooperate ~ A * T + (1 | episode) + (1 | agent_within_episode)` (logistic), or, if convergence is fragile, a GLM with **cluster-robust (sandwich) SEs clustered on episode**. The random intercept / clustering on episode is what prevents the pseudo-replication that the legacy paper risked.
3. **Seat/position** entered as a nuisance covariate or absorbed by randomization; test as a robustness check, not a primary term.

### 4.4 Uncertainty & multiple comparisons
- Primary family = {E1, E2, E3} → 3 tests → Holm correction (FWER). Report corrected and uncorrected.
- Prefer **bootstrap over episodes** (resample whole episodes, not rounds) for CIs on E1–E3 — respects the clustering and is robust to non-normal episode-mean distributions (cooperation proportions bunch near 0/1).

### 4.5 Handling invalid actions / failures
- **Invalid action within a valid episode:** pre-registered coding — either (a) treat as defection (conservative, if the mechanism is "did they contribute"), or (b) impute-and-flag, or (c) exclude the agent-round. State which; report sensitivity to the choice.
- **Invalid episode** (API error, refusal cascade, truncation): excluded per §2.11 rules; **report inclusion rate per cell** and test for differential attrition across A×T (a χ² on inclusion counts). Differential dropout is itself a finding and a confound.
- **Degenerate-variance guard:** if a cell's outcome has zero between-episode variance (all identical), do **not** report a normal CI (the legacy zero-width-CI bug); flag it — it usually means the condition is deterministic and n is effectively 1 for that cell.
- **Separation in logistic models** (cooperation = 0 or 1 in a cell): use penalized/Firth logistic or fall back to the episode-level linear model.

### 4.6 Power
- From pilot between-episode SD of the episode-mean outcome, compute N/cell for the smallest E1/E3 worth detecting at 80–90% power, α=.05 (Holm-adjusted). Because CRN pairing reduces variance, power the **paired** contrast. Pre-register the resulting N.

---

## 5. LLM-SPECIFIC VALIDITY THREATS & MITIGATIONS

All **[R]**; these are the threats that classical ABM (the legacy RL/static work) never faced and that the new lab must build in from day one.

1. **Prompt sensitivity / paraphrase fragility.** Small wording changes flip behavior.
   - *Mitigation:* pre-register a canonical prompt (hash it into the manifest); include a paraphrase-set robustness check (§3.14) — the primary effect must survive ≥2–3 paraphrases. Never tune prompts against confirmatory data.

2. **Position / primacy bias.** LLMs over-select the first-listed option/agent/action.
   - *Mitigation:* randomize option and agent-listing order per turn; balance seat assignment across conditions; include position as a robustness covariate (§4.3).

3. **Provider nondeterminism at temperature 0.** Batching, MoE routing, and non-associative float reductions make even temp-0 non-deterministic across calls.
   - *Mitigation:* do **not** assume temp-0 = deterministic; treat every episode as a stochastic draw and set n from variance, not from a false determinism assumption. Log per-call fingerprints where the API exposes them.

4. **Tokenizer / model-version drift.** A silent provider update changes the model mid-study.
   - *Mitigation:* pin `model_id` with an explicit dated/versioned alias where possible; log served version; schedule anchor re-runs (§2.10); block-collect each condition contemporaneously so drift can't align with a single condition.

5. **Contamination / training-data leakage.** The model *knows* the Prisoner's Dilemma, Axelrod, TFT, and "tragedy of the commons" — it may role-play the textbook answer rather than reason.
   - *Mitigation:* de-jargon the surface narrative (neutral skins, §2.9); include a "knows-the-literature" probe; compare against a scrambled-incentive control where the game-theoretic label no longer predicts the optimal move — if behavior tracks the label not the payoffs, it's recall, not reasoning.

6. **Anthropomorphic overclaiming.** Reading "reciprocity," "trust," or "intent" into token statistics.
   - *Mitigation:* pre-register a **claim boundary** (§3.17); report behavior (action distributions, payoffs) as the primary object; keep any mentalistic language in a clearly-labeled interpretation section; require the effect to be mechanism-linked (survives skin changes) before any cognitive framing.

7. **Cross-episode memory / state bleed.** Shared context windows, caching, or conversation reuse can leak information between "independent" episodes.
   - *Mitigation:* fresh context per episode; verify no server-side conversation reuse; treat cache hits as a logged covariate.

8. **Self-anchoring / degenerate populations.** All agents from one model can collapse to identical behavior (correlated errors), understating true variance.
   - *Mitigation:* report between-episode variance explicitly; consider mixed-model populations; flag zero-variance cells (§4.5) rather than reporting a false-tight CI.

---

## Appendix — Key legacy file:line references (verified)

- `run_research_experiments.py:30-33` — `num_runs=20, num_rounds=200`, comment "for statistical significance".
- `npd_simulator/experiments/research_experiments.py:274-281` — CI = mean ± 1.96·(pop-std)/√20; `np.std` ddof=0.
- `...research_experiments.py:247-266` — TFT-only cooperation extraction + fallback (metric inconsistency) + zero-padding to `num_rounds`.
- `...research_experiments.py:359-369, 454-469` — "tragic valley / reciprocity hill" from raw sign of mean diff, no test.
- `...research_experiments.py:410-421` — ad hoc convergence (window std<0.05).
- `npd_simulator/.../experiment_runner.py` — no seeding anywhere (grep empty).
- `npdl/simulation/runner.py:510-513` — `random.seed(run_number)`, `np.random.seed(run_number)`, shared across scenarios (CRN).
- `npdl/simulation/runner.py:454`, `main.py:273` — `num_runs` default 10.
- `npdl/analysis/analysis.py:656,676,687-689` — ANOVA + always-on uncorrected Welch t-tests; comment lines 672-674 acknowledge missing correction.
- `npdl/analysis/analysis.py:602-611` — `final_cooperation_rate` from single last round (high-variance estimator); unit = per-run (correct).
- `scenarios/true_pairwise_scenarios.json:19,33,55,70,...` — `"runs": 3`/`5` (underpowered).
- `Paper Resources/prisoners.tex:~250,314,457` — "Fifty iterations", "average of 100 runs", "average of 500 runs" (inconsistent); line 433 "clear and significant" (informal, no test); no CIs/error bars/tests anywhere.
