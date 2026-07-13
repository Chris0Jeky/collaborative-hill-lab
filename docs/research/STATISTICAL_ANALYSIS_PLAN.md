# Statistical Analysis Plan — Study 001 (Evidence Commons 2×2)

> **STATUS: DRAFT.** This SAP is **not frozen**. It becomes binding only when the human
> freezes Study 001 via `chl study freeze` (writing `study.lock.json`, ADR-0006) with a
> committed preregistration (`PREREGISTRATION_TEMPLATE.md`). Until then every number here —
> N per cell, the final-window / effect-size thresholds, the exact estimator choices — is a
> proposal open to revision. Do not cite results against this SAP before the freeze.

Design under analysis: the **2×2** crossing of the two implemented institution axes
(`domain/institutions.py`):

- **A = accountability** ∈ {`aggregate`, `attributable`}
- **T = evidence_topology** ∈ {`private`, `shared_ledger`}

→ four conditions (cells). Each **episode** = one Evidence Commons `run_episode` with N=3–5
agents over the configured rounds (default 12), sealed to one `RunCompleted` summary. The
unit of analysis is the **episode** (METHODOLOGY §2); `n` = number of independent episodes.

---

## 1. Estimands

All estimands are defined on **episode-level scalars** computed by the metrics package over
the sealed ledger. The scientific hypothesis is Chris's core finding: **attributable
(targeted) accountability moves the population toward the Collaborative Hill** (accurate,
verified, cooperative briefings) relative to aggregate (diffuse) accountability, and the
effect may depend on evidence topology.

### 1.1 Primary outcome — briefing quality

**`briefing_quality = accepted_correct − accepted_incorrect`**, per episode, from
`metrics/epistemics.py` (`accepted_correct`, `accepted_incorrect` are counts of accepted
briefing slots whose winning claim is / is not the environment-true proposition). One integer
per episode, range `[−n_slots, +n_slots]`. This is the single pre-committed primary DV. It
directly encodes "did the commons converge on truth or on well-cited misinformation."

### 1.2 Estimands over the primary outcome (the confirmatory family)

- **E1 — accountability main effect:** difference in expected `briefing_quality` between
  `attributable` and `aggregate`, averaged over topology.
- **E2 — topology main effect:** difference between `shared_ledger` and `private`, averaged
  over accountability.
- **E3 — interaction A×T:** does the accountability effect differ by topology (the "targeted
  reciprocity needs the right information structure" claim).

These three constitute the **confirmatory family** for multiplicity control (§5).

### 1.3 Secondary (pre-listed, non-confirmatory)

- **Contribution rate:** per-episode share of agent-rounds spent on costly contribution
  actions (propose/verify/challenge/share/inspect) vs withhold/abstain, from
  `metrics/epistemics.py` `action_counts` and the ledger.
- **Verification rate:** `verify` actions and `verifications_supported` per episode.
- **`free_rider_advantage`** (`metrics/distribution.py`): mean utility of zero-effort agents
  minus mean utility of positive-effort agents (`None` when a group is empty — see §4.5).
- **Distributional:** `payoff_gini`, `effort_gini`; `collective_quality`; `false_claim_accepted`.

Secondary outcomes are reported with effect sizes and intervals but are **not** in the
FWER-controlled confirmatory family; they are supporting/exploratory.

---

## 2. Data structure

One row per episode:

```
study_hash, condition_id (A×T), replicate, seed_root,
briefing_quality, accepted_correct, accepted_incorrect, slots_filled,
contribution_rate, verify_supported, free_rider_advantage, payoff_gini,
n_agents, invalid_action_count, run_status, provider/model_id, prompt_template_hash,
input_tokens, output_tokens, cost_usd
```

Provenance columns (model, hashes, tokens) come from the run manifest
(`experiments/manifests.py`). **Agents are nested within episode**; agent-level actions are
**not** independent observations — R rounds × N agents is *not* a sample of size R·N (the
pseudo-replication trap, METHODOLOGY §2). Any agent- or round-level modelling must cluster on
episode (§4.2).

---

## 3. Blocking and pairing (CRN)

Study 001 uses **common random numbers**: replicate `r` shares
`seed_root = (study_seed, condition_id, r)` across all four cells, and policy streams are
agent-keyed and condition-independent (METHODOLOGY §3). Therefore **replicate `r` is a
matched block across the four conditions** — the same scenario randomness underlies cell
`(aggregate,private)`-r and cell `(attributable,private)`-r, etc.

Consequences for analysis:

- The primary contrasts are **paired/blocked on replicate**, which is where CRN's variance
  reduction becomes power.
- `replicate` (equivalently `scenario_block`) enters every model as a blocking factor.

---

## 4. Models and estimation

Pre-commit to the **episode-level model (4.1)** as primary. The round/agent-level model (4.2)
is a robustness/secondary lens, not the primary readout.

### 4.1 Primary — episode-level, blocked

`briefing_quality ~ A * T + C(replicate_block)`

fit as a linear model on the per-episode scalar with A and T effect-coded. Report E1, E2, E3
each as a point estimate with a **95% interval** (§4.4). Equivalently, because the design is
CRN-paired, compute **per-replicate paired differences** for the primary contrast E1
(mean over topology of `attributable − aggregate` within each replicate block) and summarise
the distribution of those paired differences — this is the most transparent expression of the
blocked design and is the pre-committed primary presentation for E1.

### 4.2 Secondary — round/agent-level, cluster-aware

If action-level dynamics are modelled directly (e.g. a per-agent-round cooperate/contribute
indicator), use a mixed model with a **random intercept for episode** (and for
agent-within-episode), or a GLM with **cluster-robust (sandwich) SEs clustered on episode**.
The episode random intercept / clustering is exactly what prevents pseudo-replication. This
is reported as a robustness check, never as the headline.

### 4.3 Nuisance terms

Seat/position and (for LLM) condition-execution order are **randomised** (METHODOLOGY §4) and
enter, if at all, as robustness covariates — tested, not primary. For scripted baselines they
are provable no-ops and are omitted.

### 4.4 Uncertainty intervals — bootstrap over episodes

Primary intervals are formed by **bootstrap resampling of whole episodes** (respecting the
replicate blocking: resample blocks, or resample within cell as pre-declared), **not** by
resampling rounds. Rationale: `briefing_quality` is a small-support integer that will not be
normal, and episodes — not rounds — are the independent units. Report the bootstrap 95% CI
for E1–E3; a t-based interval on the paired differences is reported alongside as a check.

### 4.5 Degenerate-variance guard (the legacy zero-width-CI defence)

**Deterministic scripted conditions produce identical replicates.** A scripted policy with no
stochastic component (`allc`, `alld`, deterministic TFT, `ec_contributor`, `ec_verifier`,
`ec_freerider`, `ec_misinformer`) yields a **byte-identical episode for every replicate** —
the RNG stream differs by `r` but is never consumed, so `final_event_hash` is constant across
`r`. That cell has **zero between-episode variance** and `n_effective = 1`, regardless of how
many replicates were run.

Mandatory handling:

1. **Detect.** Before any interval is computed, check each cell for zero between-episode
   variance in the outcome (equivalently: identical `final_event_hash` across replicates).
2. **Report, never fake.** For a zero-variance cell, report the point value and explicitly
   flag `n_effective = 1`; **do not** emit a normal/bootstrap CI (a bootstrap of identical
   values returns zero width — the legacy bug in a new costume). State that replication was
   degenerate and that the cell is deterministic.
3. **Interpretation.** A deterministic-scripted 2×2 is a **mechanism-geometry check** (does
   attributable credit change the sealed payoffs/briefing exactly as the mechanism certificate
   predicts?), not a statistical comparison. Statistical E1–E3 with intervals require a
   **stochastic** agent population (LLM agents, or scripted `random`/ε>0 policies) whose
   episodes genuinely vary across replicates.

This is the direct structural fix for the legacy `3_TFT` / `2_TFT+1_AllD` zero-width CIs.

### 4.6 Separation / bounded outcomes

If a cell's `briefing_quality` (or a binary derived outcome like `false_claim_accepted`)
is perfectly separated (all identical, or all 0 / all 1), do not force a logistic fit — fall
back to the episode-level linear model and report the degenerate cell per §4.5.

---

## 5. Multiplicity

- **Confirmatory family = {E1, E2, E3}** (3 contrasts). FWER controlled by **Holm** at
  α = .05. Report Holm-adjusted and unadjusted p-values, and — as the primary readout —
  the effect estimates with 95% intervals (§4.4).
- Secondary and exploratory outcomes (§1.3) are **not** in the family; they are reported
  descriptively with intervals and labelled non-confirmatory. No post-hoc contrast is
  promoted into the confirmatory family after seeing data.

---

## 6. Failed and invalid episodes

- **`RunFailed` episodes** (provider outage; unrecoverable invalid action under
  `invalid_action_policy="fail"`) are **excluded** from the primary estimand but **counted per
  cell**. Report the **inclusion rate per cell** and test **differential attrition** across
  A×T (a χ² / Fisher on failed-vs-completed counts by cell). Differential dropout is a
  confound and a reportable finding.
- **Invalid actions within a completed episode** (`ActionRejected`, and any
  `fallback`-abstentions) are summarised via `invalid_action_rate`
  (`metrics/operations.py`) per cell. The primary analysis includes such episodes as-run
  (intention-to-treat); a **sensitivity analysis** re-runs E1–E3 excluding episodes whose
  invalid-action rate exceeds a pre-declared threshold. Report both; if they disagree
  materially, that is a result, not something to reconcile silently.
- **Sensitivity table** (mandatory): E1–E3 reported (a) all completed episodes, (b) excluding
  high-invalid-rate episodes, (c) with any pre-declared exclusions applied — so the reader
  sees the estimate's dependence on the handling rule.

---

## 7. What stays exploratory

Not in the confirmatory family, reported only as exploratory with that label: round-level
dynamics and convergence timing; per-agent behavioural typing; provenance-graph structure;
`payoff_gini` / inequality effects; any contrast at N other than the pre-registered N;
any narrative-skin behavioural effect for LLM agents beyond the pre-listed robustness set;
any subgroup or post-hoc split. Exploratory findings may motivate a *new* preregistered study;
they are never reported as confirming Study 001.

---

## 8. Pre-registration linkage and freeze

This SAP is bound to Study 001 only when: (a) the preregistration (all 18 fields) is
committed; (b) the pilot has produced the between-episode SD used to set N/cell (METHODOLOGY
§5); (c) the human runs `chl study freeze`. After freeze, `study_hash` pins the design; any
scenario change is a new study version (`run_study` refuses drift). Deviations after freeze go
in the preregistration deviations log (field 18) with timestamp and rationale.

**Open HUMAN-DECISION items before freeze:** final N per cell (from pilot SD); the minimum
`briefing_quality` effect worth detecting; whether the confirmatory population is LLM,
stochastic-scripted, or both; N of agents (3, 4, or 5); the invalid-rate exclusion threshold
for §6; the number and identity of narrative skins in the robustness set.
</content>
