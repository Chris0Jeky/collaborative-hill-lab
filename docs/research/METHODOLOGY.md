# Methodology — Collaborative Hill Lab

Status: **living methodology backbone.** Binds to the implemented system as of the
engine/domain/experiments layers (`engine/runner.py`, `engine/seeds.py`,
`domain/world/evidence_commons.py`, `domain/world/graph_nipd.py`,
`experiments/study.py`, `metrics/*`). Study-specific
numbers (N per cell, effect sizes, K windows) are declared per study in a preregistration
(`PREREGISTRATION_TEMPLATE.md`) and analysed under a study SAP
(`STATISTICAL_ANALYSIS_PLAN.md`); this file is the method that all studies inherit.

This document consolidates and supersedes `_discovery/methodology-stats.md`. It separates
implemented engine checks from procedures a future live study must declare. The optional
provider transport has offline engineering tests; no live pilot, automatic condition-order
randomizer or dollar-budget controller is implied by its availability.

---

## 0. What we are measuring, and what we are not

The lab studies **properties of populations of LLM (and scripted) agents under configured
interaction, information, and institutional mechanisms** — including when changes improve
accurate cooperation, leave it unchanged or make it worse. The
first environment is **Evidence Commons** (`domain/world/evidence_commons.py`); the
canonical micro-mechanism is the **N-person Prisoner's Dilemma** (`domain/world/nipd.py`)
used for legacy reproduction and calibration. The separately versioned graph world uses
explicit local neighborhoods; it does not reinterpret old complete-population records.

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
   Evidence Commons incentives are enumerated in the mechanism certificate (`studies/001`):
   C1 passes but C2 fails, so the configured social dilemma is not certified. Hand-derived
   literals are the oracle — expectations in tests and analyses are
   written from the derivation, never read back from the code under test.
2. **Scripted / deterministic baselines.** Scripted policies (`agents/scripted/*`:
   `allc`, `alld`, `random`, `tft_*`, `ptft`, `ec_contributor`, `ec_freerider`,
   `ec_verifier`, `ec_misinformer`, `ec_conditional_contributor`, and the graph-local
   reciprocators) run the same mechanism with fully specified strategies.
   These calibrate the environment (does the dilemma bite? does attributable credit change
   the payoff geometry as the certificate predicts?) and produce the null/positive-control
   curves against which LLM populations are read.
3. **LLM experiments.** Only after 1–2 are sealed do LLM populations (`agents/llm/*`) run
   the identical scenarios. A `FakeProvider` (scripted, deterministic completion provider)
   exercises parsing, retries, abstention and transcript recording. Mocked HTTP fixtures
   additionally check the configurable transport, usage accounting and workflow boundary
   without sending requests. A live pilot remains separate work under its declared design.

Scripted populations provide explicit controls, not guaranteed upper or lower performance
bounds. A contributor can spread fresh misinformation. The responsive EC experiment
therefore fixes both accurate and misleading corpora and retains positive, negative and
null accountability contrasts. Its conditional policy reads contribution history rather
than truth or utility weights; monetary-incentive diagnostics and behavior are separate.

### Current finite controls

The [responsive EC design](../../experiments/responsive-commons/DESIGN.md) enumerates
320 deterministic episodes at N=3 and 12 rounds: two accountability levels, two evidence
topologies, two corpora, five threshold/warmup rules and eight labeled active/freerider
profiles. The [full readout](../../experiments/responsive-commons/RESULTS.md) has 2 positive,
2 negative and 156 zero quality contrasts. For each strategy pair, C1 is existence of a
strictly profitable unilateral active-to-freerider switch among twelve labeled deviations;
C2 is strictly greater total utility at CCC than FFF. Neither condition establishes
dominance, equilibrium or a general social dilemma. All 160 separate fixed-action replays
test C3 by holding typed actions and the world/topology fixed while changing accountability.
Their agreement on briefing, effort, quality and total utility does not require adaptive
policies to choose the same actions under different observations.

The [graph design](../../experiments/graph-topology/README.md) fixes N=5, one AllD,
eight rounds and mean edge payoff. Its 18 conditions cross complete/ring/star adjacency,
AllD's labeled seat and targeted/linked/quorum reciprocity. All 18
[recorded cooperation curves](../../experiments/graph-topology/RESULTS.md) match the
pre-execution predictions; every original sealed run replays. Placement and policy are
explicit factors. Pairwise rates count directed edge votes; neighbourhood rates count
one vote per positive-degree agent. A star's first-round difference can therefore reflect
vote weighting before any reciprocal response. Comparisons across policy modes also change
the action/observation rule. The Study 002 complete-population count-state pTFT benchmark
cannot be transferred to sparse graphs; [ADR-0011](../adr/0011-versioned-graph-nipd.md)
gives an exact local-history counterexample.

These are unfrozen exploratory controls. Deterministic enumeration supplies exact values
for the declared grid, not repeated samples or inferential confidence intervals. Local
pre-execution predictions, execution source commitments and original ledger evidence are
recorded separately; a later byte-identical regeneration is a check, not another sample.

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
`mean ± 1.96·σ/√20` with population `σ` (ddof=0). Repeating a fixed deterministic
trajectory gives `σ = 0` and a **zero-width** interval, without adding evidence through
"20 runs for statistical significance." The lab treats this as the canonical
anti-pattern: repeating a known deterministic trajectory adds no independent outcome
information. This differs from a stochastic sample whose observed values happen to be
equal: zero empirical variance does not prove a degenerate population or reduce those
independent episodes to one. The SAP's degenerate-variance guard (§4.5) reports when its
sample-based interval cannot be estimated rather than claiming population certainty.
Study 002's ideal-process benchmark illustrates this distinction explicitly.

---

## 3. Paired scenario seeds across conditions (common random numbers)

The lab supports **common random numbers (CRN) for kernel policy streams** through explicit
`paired-policy-v2` studies (ADR-0008). The checked-in Study 000 and original Study 001 use
`legacy-independent-v1`; they do not have cross-condition CRN. Missing protocol metadata
always means legacy independent, never inferred pairing from equal replicate numbers.

### How the seed scheme implements CRN

Kernel randomness derives from explicit paths via `engine/seeds.py`; there is no global RNG
state. The SHA-256 derivation primitive remains unchanged. `study_seed_roots` allocates paths
under the study's recorded protocol:

| Protocol | Policy root | Mechanism root (`seed_root`) |
|---|---|---|
| `legacy-independent-v1` | `(seed, condition, r)` | `(seed, condition, r)` |
| `paired-policy-v2` | `(seed, "paired-policy-v2", "block", scenario_block, "replicate", r)` | `(seed, "paired-policy-v2", "condition", condition, "replicate", r)` |

The runner appends `("agent", agent_id, "round", t)` for policy randomness and
`("mechanism", "round", t)` for world randomness. Every v2 condition must explicitly name
its `scenario_block`; both the protocol and the block mapping enter the study hash.
Manifests and the new protocol's `RunStarted` payload record both roots and the block.
Legacy study hashes, streams, and sealed ledger payloads remain unchanged.

Within a v2 block and replicate, the same agent/round gets the same initial PRNG stream
across conditions. Matching sequences of RNG calls yield matching draws. Different
observations or within-round draw consumption can still produce different actions. EC
observations already differ by accountability/topology, so institution-only comparisons do
not guarantee identical observations or behaviour. Mechanism randomness stays
condition-specific. Adding a consumer in a separate agent/round/purpose path cannot shift
the existing streams.

`LLMPolicy` currently discards its supplied kernel RNG; provider sampling is separate and
is **not coupled** by v2. Recorded-action replay is not evidence of provider CRN. Before a
paired LLM analysis, the provider controls and the actual coupling must be established.

### Consequence for analysis

Paired contrasts require a declared block design and verified coupling for the randomness
actually consumed. Record `(scenario_block, replicate)` as the block key within a study.
CRN may reduce or increase contrast variance depending on outcome covariance; measure the
paired variance in the pilot. Never retrofit paired inference to legacy runs solely because
their replicate numbers match. See SAP §3 for the intended future paired Study 001 design.

---

## 4. Condition-order and position randomisation (and when it is a no-op)

For a future **LLM study**, execution order and positional layout are nuisance variables
to address in its design:

- **Condition execution order** should be randomized or balanced so provider drift (§6)
  cannot align with a single condition (e.g. "attributable happened to run in the morning").
- **Seat / position and prompt option order** should be randomized or balanced across conditions,
  because LLMs exhibit primacy bias (over-selecting first-listed options/agents).

The current `run_study` executes conditions and replicates in their declared order; it
does not implement a randomized scheduler or automatically balance prompt options. A live
design needs to specify and record that schedule before drawing conclusions about drift.

Reordering independent **deterministic scripted condition executions** does not change
their outcomes when code, inputs, seed protocol, run identity and start metadata are held
fixed. World transitions do not read wall-clock time. This does not make agent placement
or list order inert: graph position changes local interactions, and EC resolution/ties use
declared identities and claim order. Deterministic relabeling tests have their own explicit
scope; stochastic seed paths also depend on agent IDs. Replay checks reproduce recorded
actions under the same engine contract, without making a provider call.

---

## 5. Pilot → power → confirm

Every confirmatory study follows a three-phase procedure:

1. **Pilot** (small, e.g. 5–10 episodes/cell) to estimate the **between-episode standard
   deviation** of the primary outcome and to shake out operational failures (parse rates,
   refusal rates, cost per episode). **Pilot p-values are never read** and pilot episodes are
   discarded from the confirmatory corpus.
2. **Power.** From the pilot SD (using the **paired** SD when verified CRN is the design),
   compute N/cell to detect the pre-declared minimum effect of interest at the target power
   (e.g. 80–90%) and Holm-adjusted α. For a paired design, use the measured variance of
   the paired contrast, rather than assuming a reduction from the between-cell marginal.
3. **Confirm.** Freeze N (the stopping rule, §14), run the confirmatory batch, analyse per
   the frozen SAP.

This prevents both the legacy underpowered scenarios (`runs: 3`/`5`) and optional-stopping
p-hacking.

---

## 6. Provider drift logging via manifests

LLM sampling is separate from the kernel RNG, and a requested model alias can resolve to a
different served version. The lab records available execution provenance in the **run manifest**
(`experiments/manifests.py`, written per run by `study.py`):

- `providers` (requested model per agent), `prompt_template_hashes`, declared `sampling`,
  transport/endpoint settings in `provider_metadata`, observed `reported_models`, and
  `scorer_versions`. Exact sampling strings and serialized wire-number strings remain distinct.
- `code_commit`, `worktree_dirty`, `python_version`, `platform`,
  `dependency_lock_sha256`, `study_hash`, `study_frozen`, per-condition `scenario_hash` /
  `mechanism_hash` / `narrative_hash` / `evidence_corpus_hash`.
- `provider_usage` records completion calls, request attempts, known per-dimension token
  sums and measurement coverage. An input/output total is known only when every attempted
  request reports that dimension. Unknown 429/timeout usage is retained; measured refusal
  and action-repair usage is included. Costs and prices remain unknown because the transport
  supplies no price table. A continuation records only calls and transcript rows after its
  own starting cursors and clears inherited usage/pricing metadata.

The [provider contract](../PROVIDER_USAGE.md) defines explicit endpoint/model/token-cap
configuration, environment-variable credential references, redacted errors and bounded
retries. Its timeout covers socket I/O, not a total request or DNS deadline. Transport
retries (`rate_limit_retries`) are opt-in and limited to HTTP 429. Separately, the policy's
`max_retries` can request additional completions to repair invalid action JSON inside a
valid text response; these calls also count toward usage. Validation and recorded-action
replay remain offline. Effective network policies
in a study or branch require execution opt-in; every selected credential/configuration is
preflighted before the first call or output reservation. These are engineering controls,
not evidence of live reliability, model determinism, billing accuracy or paired randomness.

For a future live study, the drift protocol is to pin `model_id` with a dated/versioned
alias where the provider exposes one;
**block-collect each condition contemporaneously** (interleave, do not batch a whole
condition then the next); and schedule **anchor re-runs** of a fixed scenario at intervals to
detect behavioural drift between provider updates. A cross-time comparison whose manifests
show a changed served model version is flagged, not silently pooled. The factorial
analyzer checks recorded transport settings within each declared block and rejects
different known reported-model sets for the same agent, including versions observed in
failed runs. Missing/empty sets remain unknown and do not remove pre-response failures
from attrition. Metadata consistency cannot authenticate a provider's implementation.

---

## 7. Narrative-skin robustness

Mechanics live **exclusively** in typed structures; a `NarrativeSkin`
(`experiments/scenario.py`) has **no numeric or rule-bearing fields** (only names, prose,
wording), so it cannot change legal actions, payoffs, visibility, institution, or metrics.
`mechanism_hash` is computed from `mechanism_view` (world+information+interaction+institution
+agent roster) and is provably **untouched by the skin** (`narrative_hash` is separate).

- **For scripted agents**, metamorphic tests assert that swapping skins leaves
  `mechanism_hash` and world behavior unchanged. Full event-chain equality additionally
  holds run identity fixed and omits narrative-bearing start metadata; ordinary study
  runs can record different narrative hashes. This checks presentation separation, not
  an empirical LLM robustness finding.
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

For a sampled stochastic comparison, the primary readout is an **estimated effect with
an uncertainty interval** (the draft SAP uses 95% bootstrap-over-episode intervals; §4.4),
with the design and assumptions stated. p-values are secondary. A finite deterministic
enumeration instead reports exact differences for its declared cells; it does not invent
sampling uncertainty. If the design or observed data cannot support an interval, report
that limitation explicitly. The legacy
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
Per-episode tokens and any independently measured costs belong in the manifest. The current
transport records token coverage but cannot infer dollars, cancel remote generation or
enforce a total study spend from a completion-token cap. A live pilot needs an operational
budget/stopping procedure in addition to the request settings.

If a ceiling or abort threshold binds before the confirmatory N is reached, follow the
**predeclared stopping or adaptation rule and its analysis**, if one exists. Preserve the
completed and failed episodes, record the unattempted allocation by cell, and log the
stopping reason and any departure from the declared plan. Report incomplete collection and
the resulting power or comparability limitations. Without a predeclared adaptation, the
original hypotheses, cells and target N remain the reference; do not revise them after
seeing results to make the shortened run appear confirmatory. Any revision outside the
predeclared adaptation belongs to a separately declared follow-up, including a changed
sample size, hypothesis or minimum effect; it cannot retroactively confirm the original
study. Other abort conditions (e.g. a provider deprecation mid-study) likewise remain
predeclared and recorded when triggered.

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
| CRN / paired seeds | Explicit `paired-policy-v2`; `engine/seeds.study_seed_roots`; shared `(scenario_block, replicate)` policy root; legacy/default streams remain independent (ADR-0008) |
| No global RNG | `engine/seeds.py` (every stream derived from an explicit path) |
| Provenance / drift log | `RunManifest`, provider attempt accounting and within-block configuration/reported-model checks |
| Offline verification / explicit provider execution | configuration-only validation; run/branch opt-in and credential preflight; recorded-action replay |
| Finite responsive controls | `experiments/responsive-commons/`: declared full grid, separate C1/C2 diagnostics and fixed-action C3 replays |
| Local graph semantics | `nipd_graph`, canonical adjacency, local observation tests and explicit payoff/vote denominators |
| Freeze before confirm | `study.freeze_study` → `study.lock.json`; `run_study` rejects post-freeze drift |
| Skin is presentation-only | `scenario.NarrativeSkin` (no rule-bearing fields); `mechanism_hash` excludes it |
| Programmatic scoring only | `metrics/*` over sealed ledgers; `runner` never imports metrics |
| No silent repair | `runner` `ActionRejected` + typed fallback; `LLMPolicy` abstain-on-invalid (ADR-0007) |
| Costs never fabricated | unknown totals remain `None`; measured partial sums labeled; child usage excludes the parent prefix |
