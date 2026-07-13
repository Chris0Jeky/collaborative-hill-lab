# Methodology — Collaborative Hill Lab

Status: **living methodology backbone.** Binds to the implemented system as of the
engine/domain/experiments layers (`engine/runner.py`, `engine/seeds.py`,
`domain/world/evidence_commons.py`, `experiments/study.py`, `metrics/*`). Study-specific
numbers (N per cell, effect sizes, K windows) are declared per study in a preregistration
(`PREREGISTRATION_TEMPLATE.md`) and analysed under a study SAP
(`STATISTICAL_ANALYSIS_PLAN.md`); this file is the method that all studies inherit.

This document consolidates and supersedes `_discovery/methodology-stats.md`. Where the
discovery draft was prescriptive ("the lab must…"), the mechanisms it asked for are now
implemented; this file cites the code construct that realises each one.

---

## 0. What we are measuring, and what we are not

The lab studies **properties of populations of LLM (and scripted) agents under configured
interaction, information, and institutional mechanisms** — specifically whether targeted
pairwise accountability breeds accurate cooperation (the Collaborative Hill) where diffuse
aggregate accountability breeds free-riding and misinformation (the Tragic Valley). The
first environment is **Evidence Commons** (`domain/world/evidence_commons.py`); the
canonical micro-mechanism is the **N-person Prisoner's Dilemma** (`domain/world/nipd.py`)
used for legacy reproduction and calibration.

We make **model-comparison and mechanism-comparison** claims ("under model M, mechanism A
produces higher briefing quality than mechanism B, on this environment, at this scale"). We
do **not** make **absolute-trustworthiness** claims ("model M is aligned / honest") nor
**human-behaviour** claims. See `CLAIMS_AND_LIMITATIONS.md` for the full boundary; every
study's preregistration restates its own claim boundary (field 15).

---

## 1. Ordering: analytical and scripted baselines precede LLM experiments

No LLM result is interpretable without a same-environment baseline whose behaviour is known
in closed form. The build/run order is fixed:

1. **Analytical ground truth.** The payoff structure is hand-derived and independently
   re-derived (N=3, T=5, R=3, P=1, S=0; pairwise and neighbourhood payoff tables), and the
   Evidence Commons dilemma is proved by enumeration in the mechanism certificate
   (`studies/001`). These literals are the oracle — expectations in tests and analyses are
   written from the derivation, never read back from the code under test.
2. **Scripted / deterministic baselines.** Scripted policies (`agents/scripted/*`:
   `allc`, `alld`, `random`, `tft_*`, `ptft`, `ec_contributor`, `ec_freerider`,
   `ec_verifier`, `ec_misinformer`) run the same mechanism with fully specified strategies.
   These calibrate the environment (does the dilemma bite? does attributable credit change
   the payoff geometry as the certificate predicts?) and produce the null/positive-control
   curves against which LLM populations are read.
3. **LLM experiments.** Only after 1–2 are sealed do LLM populations (`agents/llm/*`) run
   the identical scenarios. A `FakeProvider` (scripted, deterministic completion provider)
   exercises the entire LLM code path — parsing, retries, abstention, transcript sidecar —
   without a network call, so the harness itself is validated before any real provider spend.

Rationale: a scripted `ec_freerider` population is the mechanistic definition of the Valley;
an `ec_contributor`/`ec_verifier` mix is the Hill. If the LLM population lands between them,
the baselines give the reading a scale. Without them, an LLM cooperation number is a
free-floating datum.

---

## 2. Unit of analysis = the episode. Never the turn.

**The unit of analysis is one full episode** — one `run_episode` call producing one sealed
ledger and one `RunCompleted` summary. Outcomes are computed **per episode** (one scalar per
episode) and the sample size `n` is **the number of independent episodes**, never
turns × episodes, never agents × rounds.

### Why this is non-negotiable — the pseudo-replication failure mode

Turns within an episode are **autocorrelated**: an agent's move at round *t* depends on its
own and others' histories up to *t*. Treating the ~R rounds of an episode (or R × N
agent-rounds) as independent samples is **pseudo-replication** — it manufactures precision
that does not exist and inflates every significance statement. The cooperation metric
(`metrics/cooperation.py`) is deliberately built to enforce this: it collapses each episode
to per-round rates first and reports `mean_cooperation` / `final_window_cooperation` as
**one number per episode**; downstream analysis then treats each episode as one row.

### The cautionary example (the legacy zero-width-CI story)

The legacy headline pipeline (`run_research_experiments.py`) ran deterministic configs
(`3_TFT`, `2_TFT+1_AllD` with `exploration_rate: 0.0`) 20× and computed a 95% CI as
`mean ± 1.96·σ/√20` with population `σ` (ddof=0). Because the dynamics were deterministic,
**all 20 runs were byte-identical**: `σ = 0`, the CI had **zero width**, and "20 runs for
statistical significance" was one run copied 20 times. The lab treats this as the canonical
anti-pattern: replicate count is not sample size, and a zero-variance cell is `n_effective =
1`, not `n = 20`. The SAP's degenerate-variance guard (below, and §4.5 of the SAP) exists
specifically to detect and *report* this rather than emit a false-tight interval.

---

## 3. Paired scenario seeds across conditions (common random numbers)

The lab implements **common random numbers (CRN)** so that between-condition contrasts are
*within-scenario* differences, dramatically reducing variance and enabling paired analysis.

### How the seed scheme implements CRN

All randomness derives from a hierarchical path via `engine/seeds.py`
(`derive_seed` = SHA-256 over a version-tagged, unit-separated path; **no global RNG state
exists anywhere**). For a study run (`experiments/study.py`):

- `seed_root = (study_seed, condition_id, replicate)` — see `RunConfig.seed_root` and the
  manifest's `seed_root` field.
- Each policy draws from an **agent-keyed** stream:
  `rng_for(*seed_root, "agent", agent_id, "round", t)` (`runner.py` propose loop).
- The mechanism draws from `rng_for(*seed_root, "mechanism", "round", t)`.

The CRN property falls out of two facts: (a) the same `replicate` index `r` is reused across
**every** condition, and (b) policy streams are keyed by **agent id and round, not by
condition**. Therefore two conditions that differ **only in the institution** (e.g.
`aggregate` vs `attributable`, holding scenario and replicate fixed) receive **identical
policy randomness** for the same agent at the same round. Any behavioural difference between
them is attributable to the institution, not to which random draws happened. This is the one
genuinely good instinct in the legacy `npdl` runner (`seed = run_number`, shared across
scenarios), now formalised, collision-resistant (SHA-256, reserved separator), and
substream-safe (adding a new random consumer cannot shift an existing stream).

### Consequence for analysis

Because conditions are paired at the replicate level, the primary contrasts are **paired
contrasts over shared replicate seeds** (SAP §4). Paired analysis is what turns CRN's
variance reduction into power.

---

## 4. Condition-order and position randomisation (and when it is a no-op)

For **LLM runs**, execution order and positional layout are nuisance variables that can
confound results:

- **Condition execution order** is randomised so provider drift (§6) cannot align with a
  single condition (e.g. "attributable happened to run in the morning").
- **Seat / position and prompt option order** are randomised or balanced across conditions,
  because LLMs exhibit primacy bias (over-selecting first-listed options/agents).

For **deterministic scripted runs this randomisation is a provable no-op**: a scripted
episode's sealed ledger is a pure function of `(mechanism, policies, seed_root)`. It does not
read wall-clock time (that lives only in unhashed event `meta`), does not depend on the order
conditions execute, and — for policies with no stochastic component — does not even depend on
the drawn RNG values. Two runs of the same scripted condition produce byte-identical
`final_event_hash`. We still record order in the manifest for uniformity, but for scripted
baselines it carries no inferential weight. (This is also why replay is exact: `agents/replay.py`
reproduces recorded actions, and the hash chain verifies it.)

---

## 5. Pilot → power → confirm

Every confirmatory study follows a three-phase procedure:

1. **Pilot** (small, e.g. 5–10 episodes/cell) to estimate the **between-episode standard
   deviation** of the primary outcome and to shake out operational failures (parse rates,
   refusal rates, cost per episode). **Pilot p-values are never read** and pilot episodes are
   discarded from the confirmatory corpus.
2. **Power.** From the pilot SD (using the **paired** SD, since CRN pairing is the design),
   compute N/cell to detect the pre-declared minimum effect of interest at the target power
   (e.g. 80–90%) and Holm-adjusted α. Because CRN reduces the paired variance, power the
   paired contrast, not the between-cell marginal.
3. **Confirm.** Freeze N (the stopping rule, §12), run the confirmatory batch, analyse per
   the frozen SAP.

This prevents both the legacy underpowered scenarios (`runs: 3`/`5`) and optional-stopping
p-hacking.

---

## 6. Provider drift logging via manifests

LLM sampling is a second RNG we do not control at the client, and providers silently update
models. The lab pins and logs everything pinnable in the **run manifest**
(`experiments/manifests.py`, written per run by `study.py`):

- `providers` (model_id per agent), `prompt_template_hashes`, `sampling`
  (temperature/top_p/etc.), `scorer_versions`.
- `code_commit`, `worktree_dirty`, `python_version`, `platform`,
  `dependency_lock_sha256`, `study_hash`, `study_frozen`, per-condition `scenario_hash` /
  `mechanism_hash` / `narrative_hash` / `evidence_corpus_hash`.
- Cost/token fields (`input_tokens`, `output_tokens`, `cost_usd`, `pricing_table_version`)
  are recorded **only when measured** — a `None` means unmeasured and is **never
  fabricated**.

Drift protocol: pin `model_id` with a dated/versioned alias where the provider exposes one;
**block-collect each condition contemporaneously** (interleave, do not batch a whole
condition then the next); and schedule **anchor re-runs** of a fixed scenario at intervals to
detect behavioural drift between provider updates. A cross-time comparison whose manifests
show a changed served model version is flagged, not silently pooled.

---

## 7. Narrative-skin robustness

Mechanics live **exclusively** in typed structures; a `NarrativeSkin`
(`experiments/scenario.py`) has **no numeric or rule-bearing fields** (only names, prose,
wording), so it cannot change legal actions, payoffs, visibility, institution, or metrics.
`mechanism_hash` is computed from `mechanism_view` (world+information+interaction+institution
+agent roster) and is provably **untouched by the skin** (`narrative_hash` is separate).

- **For scripted agents**, metamorphic tests assert that swapping skins leaves
  `mechanism_hash` and the **entire event chain** byte-identical. This proves the skin is a
  pure presentation layer — a necessary invariant, not a robustness *finding*.
- **For LLM agents**, the skin is the surface the model actually reads, so behaviour *may*
  change with wording. This is the real robustness axis: **a mechanism effect must survive
  re-skinning across ≥2–3 skins** to be reported as a mechanism effect rather than a
  prompt-story artifact. Until LLM skin-invariance is measured, we state only that skins are
  verified **mechanism-invariant with scripted agents** (see `CLAIMS_AND_LIMITATIONS.md`).

---

## 8. Exploratory vs confirmatory separation

Each study freezes its hypotheses, primary outcome(s), and analysis **before** confirmatory
data are seen (the preregistration is committed and the study is frozen via
`chl study freeze`, which writes `study.lock.json`; freezing is a **human-confirmed** step,
never automatic — ADR-0006). After freeze, changing any scenario changes `study_hash` and is
a *new study version*, not an edit (`run_study` refuses to run a frozen study whose content
hash drifted). Exploratory findings are permitted and valued but are reported in a clearly
separated section and **never described as confirmed**. This blocks HARKing and post-hoc
"tragic valley observed" narratives.

---

## 9. Effect sizes and uncertainty intervals over point p-values

The primary readout of any contrast is an **estimated effect with a 95% uncertainty
interval** (bootstrap-over-episodes preferred; see SAP §4.4), not a bare p-value. p-values
are secondary and always reported alongside the effect and its interval. The legacy
"effect = sign of a mean difference" (a boolean that flips on any nonzero difference of any
magnitude, with no interval) is explicitly disallowed.

## 10. Multiple-comparison handling

A study declares a **confirmatory family** of a small number of pre-committed contrasts
(Study 001: the three contrasts — accountability main effect, topology main effect,
interaction). FWER is controlled with **Holm** over that family. Both corrected and
uncorrected values are reported. Everything outside the declared family is **exploratory** and
labelled as such; the legacy uncorrected 30-config sweep is the anti-pattern.

## 11. Scoring discipline: no LLM judge as sole scorer

Primary outcomes are computed by **programmatic metrics over the sealed, typed ledger**
(`metrics/*`), which read only environment-validated action records — never agent-controlled
free text. **v0 has no LLM scoring at all**: verification is engine-adjudicated
provenance-checking (`_adjudicate_verification`), acceptance is the mechanical net-support
rule (`final_briefing`), and correctness is a comparison to environment truth
(`true_propositions`) done by the scorer, not by any model. **Rule:** an LLM judge may never
be the *sole* scorer of a confirmatory outcome. If an LLM judge is ever introduced (a future
slice), the judged text is delimited as untrusted, the judge sees no agent-supplied
"grade me" channel, and it is validated against human coding before use.

## 12. Human-coding codebook requirement

Any outcome that requires human judgement (e.g. categorising a justification, rating a
narrative) must be governed by a **written codebook**: category definitions, decision rules,
worked examples, and an inter-rater reliability procedure (≥2 coders on a shared subsample,
report agreement, adjudicate disagreements). No confirmatory human-coded outcome ships from a
single coder's ad-hoc judgement. (v0 has no human-coded outcomes; this governs the first one.)

---

## 13. Predeclared exclusions and failure handling

Failure taxonomy, mapped to the engine's typed events:

- **Invalid action within a valid episode.** The mechanism's `validate_action` rejects an
  illegal action → `ActionRejected` event. Under `invalid_action_policy="abstain"` the runner
  substitutes an explicit `AbstainAction` (recorded, `fallback: true`); under `"fail"` the run
  seals as `RunFailed`. Invalid actions are **never silently repaired** (ADR-0007). Each
  study predeclares how within-episode invalid actions are coded for its outcome (e.g.
  count-as-abstention vs sensitivity-analysed both ways) and reports the `invalid_action_rate`
  (`metrics/operations.py`) per cell.
- **Failed episode (`RunFailed`).** A provider outage or an unrecoverable invalid action seals
  the run as failed with a typed reason. Failed episodes are **excluded** from the primary
  outcome but **counted and reported per cell**, and the analysis tests for **differential
  attrition** across conditions (a failure rate that differs by cell is itself a confound and
  a finding — SAP §4.5). Inclusion rate per cell is always reported.
- **Predeclared exclusions** (refusal cascades, context truncation, budget exhaustion) are
  defined in the preregistration (fields 10, 16) before data collection.

## 14. Cost ceilings and abort conditions

Each study declares a **maximum spend and maximum episode count** (preregistration field 14).
Per-episode token/cost is logged in the manifest when measured. If the ceiling binds before
the confirmatory N is reached, the response is to **down-scope the hypotheses** (raise the
minimum detectable effect, drop a cell), never to silently truncate — silent truncation
biases results by *when you stopped*. Abort conditions (e.g. per-cell failure rate above a
threshold, a provider deprecation mid-study) are predeclared and, when triggered, logged in
the deviations record.

## 15. Model-comparison vs absolute-trustworthiness

Results license statements of the form "**under model M and these mechanisms, on this
environment, at this scale**, mechanism A yields outcome distribution X vs mechanism B's Y."
They do **not** license "model M is honest/aligned/trustworthy," nor generalisation to
providers or models not run. One model's behaviour is one model's behaviour; provider-general
conclusions require multiple models and are out of scope for any single-model study.

## 16. No human-behaviour claims

Agents are LLMs and scripts, not people. The lab makes **no claims about human cooperation,
human institutions, or policy** from agent behaviour. Mentalistic vocabulary ("reciprocity,"
"trust," "intent") is confined to a clearly-labelled interpretation section and only after
the effect is shown mechanism-linked (survives re-skinning). The primary object of every
report is **behaviour**: action distributions, briefing quality, payoffs, and their
uncertainty.

## 17. Negative-result preservation

Outcomes are registered and reported **regardless of direction**. All run artifacts — sealed
ledgers, manifests, and failed/null cells — are retained in the study's artifact tree. The
lab does not surface only the cells that "show" the effect; a null or reversed result on a
preregistered contrast is a first-class result of the study.

---

## Appendix — method → implementing construct

| Method rule | Implemented by |
|---|---|
| Episode as unit | `runner.run_episode` (one sealed ledger); `metrics/cooperation.py` collapses to one scalar/episode |
| CRN / paired seeds | `engine/seeds.derive_seed`; `seed_root=(study_seed, condition, replicate)`; agent-keyed streams in `runner.py` |
| No global RNG | `engine/seeds.py` (every stream derived from an explicit path) |
| Provenance / drift log | `experiments/manifests.RunManifest`, written by `run_study` |
| Freeze before confirm | `study.freeze_study` → `study.lock.json`; `run_study` rejects post-freeze drift |
| Skin is presentation-only | `scenario.NarrativeSkin` (no rule-bearing fields); `mechanism_hash` excludes it |
| Programmatic scoring only | `metrics/*` over sealed ledgers; `runner` never imports metrics |
| No silent repair | `runner` `ActionRejected` + typed fallback; `LLMPolicy` abstain-on-invalid (ADR-0007) |
| Costs never fabricated | manifest token/cost fields `None` when unmeasured |
</content>
</invoke>
