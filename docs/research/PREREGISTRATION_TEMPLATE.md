# Preregistration Template — Collaborative Hill Lab

> **STATUS: DRAFT TEMPLATE.** Copy this to `studies/<id>/PREREGISTRATION.md`, fill every field,
> commit it, and only then freeze the study (`chl study freeze` → `study.lock.json`, a
> **human-confirmed** step, ADR-0006). Freezing pins `study_hash`; any later scenario change is
> a new study version, not an edit (`run_study` refuses post-freeze drift). Fields marked
> **[HUMAN-DECISION]** must be set by the human before freeze — an agent may draft a proposal
> but must not decide them. Ground every operational choice in the implemented system
> (`domain/institutions.py`, `domain/world/evidence_commons.py`, `metrics/*`,
> `experiments/study.py`) and in `METHODOLOGY.md` / `STATISTICAL_ANALYSIS_PLAN.md`.

Study id: `___`  ·  Version: `___`  ·  Date: `___`  ·  Author(s): `___`

---

**1. Hypothesis.** State each hypothesis as one directional, falsifiable sentence, marked
confirmatory or exploratory (e.g. "H1 [confirmatory]: attributable accountability yields higher
episode `briefing_quality` than aggregate accountability"). List H1…Hk; the confirmatory ones
define the multiplicity family (field 11). **[HUMAN-DECISION]** which hypotheses are confirmatory.

**2. Theoretical mechanism.** The causal story: *why* the IV should move the DV (e.g. targeted
pairwise accountability makes contribution individually reciprocated, aggregate credit dilutes
it — the Hill-vs-Valley account). This grounds interpretation and dictates the robustness checks
(field 12); an effect with no mechanism is exploratory only.

**3. Independent variables & levels.** Each factor, its levels, and its exact operationalisation
in the scenario/institution spec (Study 001: `accountability ∈ {aggregate, attributable}` ×
`evidence_topology ∈ {private, shared_ledger}` from `InstitutionConfig`; crossed → 4 cells).
Note crossed vs nested and which planes change. Only implemented axes are valid IVs.

**4. Primary outcome(s) (max 2).** The pre-committed DV(s) and their exact episode-level
computation from a metric (Study 001 primary: `briefing_quality = accepted_correct −
accepted_incorrect` from `metrics/epistemics.py`, one integer per episode). One number per
episode; the unit of analysis is the episode, never the turn. **[HUMAN-DECISION]** the primary
outcome and, if two, their ordering.

**5. Secondary / exploratory outcomes.** Additional DVs, explicitly non-confirmatory (e.g.
contribution rate, verification rate, `free_rider_advantage`, `payoff_gini`,
`false_claim_accepted`). Reported with intervals but outside the FWER family.

**6. Population & model selection.** Which agents: scripted policy set, or model(s) +
provider(s) + version pin + `sampling` (temperature/top_p) + agent-policy composition; and the
scenario sampling frame (how replicate seeds are drawn, `seed_root=(study_seed, condition, r)`).
State N of agents (3–5) and whether the confirmatory population is LLM, stochastic-scripted, or
both — deterministic scripted cells have `n_effective=1` (SAP §4.5). **[HUMAN-DECISION]** the
model(s)/version pin, agent-N, and population type.

**7. Pilot.** Size and purpose of the pilot (e.g. 5–10 episodes/cell) used **only** to estimate
the between-episode SD of the primary outcome and to check operational health (parse/refusal
rates, cost/episode). State that pilot p-values are not read and pilot episodes are discarded
from the confirmatory corpus. **[HUMAN-DECISION]** pilot size.

**8. Sample-size decision procedure.** The minimum effect size of interest on the primary
outcome, target power (e.g. 80–90%), α (Holm-adjusted), the variance source (the pilot **paired**
SD, since the design is CRN-paired), and the formula/simulation yielding N per cell. Record the
resulting N here before confirmatory collection. **[HUMAN-DECISION]** minimum effect, power, α, N.

**9. Randomisation.** What is randomised and how: replicate→cell pairing via shared seeds (CRN),
seat/position, prompt option order, and condition **execution order** for LLM runs; note that for
deterministic scripted runs this is a provable no-op (METHODOLOGY §4). State the seed policy
(`derive_seed`, no global RNG). **[HUMAN-DECISION]** the seat/order randomisation scheme for LLM.

**10. Exclusions / data-handling.** Definition of an invalid **episode** (`RunFailed`: provider
outage, or unrecoverable invalid action under `invalid_action_policy="fail"`) and predeclared
exclusions (refusal cascade, truncation, budget). State that excluded episodes are counted per
cell, inclusion rate is reported, and differential attrition across cells is tested (SAP §6).
**[HUMAN-DECISION]** the predeclared exclusion set and any invalid-rate exclusion threshold.

**11. Analysis.** The exact estimand/model for each confirmatory hypothesis (Study 001 primary:
`briefing_quality ~ A*T + C(replicate_block)`, or per-replicate paired differences for E1),
the estimator, software, and how intervals are formed (**bootstrap over episodes**, cluster/
block-aware). Declare the confirmatory family and the multiplicity correction here (Study 001:
Holm over {E1 accountability, E2 topology, E3 interaction}). Include the degenerate-variance
guard (never emit a CI for a zero-variance cell). Points to the study SAP.

**12. Robustness / sensitivity (incl. skins).** Pre-list the robustness set: **narrative-skin
replication** (the primary effect must survive ≥2–3 skins for LLM agents — skins are proven
mechanism-invariant for scripted agents only), alternative outcome definition, alternative
model, prompt paraphrase, seed re-draw, and the with/without-invalid sensitivity analysis.
**[HUMAN-DECISION]** the number and identity of skins and alternative models in the set.

**13. Stopping rule.** When collection stops: the fixed confirmatory N from field 8, or a
pre-registered group-sequential/alpha-spending design. No open-ended "run until significant."
State it explicitly. **[HUMAN-DECISION]** fixed-N vs sequential and its parameters.

**14. Cost ceiling.** Maximum episodes and maximum $/tokens for the study, and what happens if
the ceiling binds before N (down-scope hypotheses / drop a cell / raise the minimum detectable
effect — never silently truncate, METHODOLOGY §14). Per-episode cost is logged in the manifest
when measured. **[HUMAN-DECISION]** the max spend and max episode count.

**15. Claim boundary.** One sentence scoping any positive result: which model(s), environment,
N, institution cell(s), and scale it does and does not license generalising to — and the
standing exclusions (no human-behaviour, no policy, no provider-general or absolute-alignment
claims; see `CLAIMS_AND_LIMITATIONS.md`). Guards anthropomorphic overclaiming.

**16. Provider drift handling.** How model drift is controlled: version pin + logging of the
served model/version in the manifest, **contemporaneous block-collection** of all cells (so
drift can't align with one condition), and scheduled anchor re-runs. State the action if a
served-version change is detected mid-study (flag, do not pool; log in deviations).
**[HUMAN-DECISION]** the anchor-scenario and re-run cadence.

**17. Invalid-action coding.** How invalid actions **within** a completed episode are coded for
the outcome: the `invalid_action_policy` used (`fail` vs `abstain`) and whether within-episode
rejects/abstentions are counted as abstention, imputed, or excluded — with the with/without
sensitivity analysis (SAP §6). Invalid actions are never silently repaired (ADR-0007).
**[HUMAN-DECISION]** the coding rule and `invalid_action_policy`.

**18. Deviations log.** A committed location (this file's Deviations section) recording every
departure from this prereg after freeze, each with timestamp and rationale. An empty log at
freeze time is expected; entries are append-only.

---

### Deviations (append-only, post-freeze)

| Date | Field | Change | Rationale |
|------|-------|--------|-----------|
|      |       |        |           |
</content>
