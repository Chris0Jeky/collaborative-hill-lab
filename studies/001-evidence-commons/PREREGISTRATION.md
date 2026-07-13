# Preregistration — Study 001: Evidence Commons

**STATUS: DRAFT — HUMAN APPROVAL REQUIRED. NOT FROZEN.**
Nothing here is final until the human researcher completes every `HUMAN DECISION` field and
runs `chl study freeze "studies/001-evidence-commons" --yes`. Freezing was deliberately NOT
performed by the founding agent (locked principle #7).

## 1. Hypotheses (PROPOSED)

- **H1 (accountability):** LLM-agent populations under *attributable peer review* produce
  higher briefing quality and higher contribution rates than under *aggregate
  accountability*, holding evidence topology fixed.
  Theoretical mechanism: attribution restores the targeted-reciprocity channel that the
  legacy N-IPD work showed carries cooperation (Study 000: per-opponent TFT sustains, linked
  or probabilistic aggregate reciprocity collapses); credit that follows the contributor
  makes contribution individually rational (mechanism certificate C1/C3).
- **H2 (evidence topology):** a *shared provenance ledger* increases verification rate and
  reduces provenance-broken accepted claims versus *private/fragmented* evidence, holding
  accountability fixed.
  Mechanism: under private topology, citations are unverifiable until shared (extra cost),
  so verification is undersupplied.
- **H3 (interaction, exploratory):** accountability and topology interact — attribution
  matters more when provenance is public.

## 2. Independent variables

2x2 factorial, between-episode:
- accountability ∈ {aggregate, attributable}
- evidence_topology ∈ {private, shared_ledger}
Optional intervention arm (exploratory, not part of the confirmatory family):
`attr-priv-misinfo` (one misinformation-holding agent replaces a contributor).

## 3. Primary outcomes (PROPOSED — final selection is a HUMAN DECISION)

1. **Briefing quality** per episode: `accepted_correct − accepted_incorrect` (epistemics v1).
2. **Contribution rate** per episode: contribution actions (inspect/share/propose/verify/
   challenge) ÷ total agent-rounds (cooperation family).

Everything else (free-rider advantage, provenance-broken acceptances, verification rate,
false-claim propagation, payoff Gini, invalid-action rate) is SECONDARY.

## 4. Population and model selection — HUMAN DECISION

Provider(s), exact model version(s), temperature, single- vs mixed-model populations.
Manifests record exact model ids; provider drift is bounded by anchor runs (METHODOLOGY.md).

## 5. Pilot

Before any full run: 5 episodes per cell at the chosen model, to estimate episode-level
outcome variance, invalid-action rate, and token consumption. Pilot data are exploratory
and excluded from confirmatory analysis.

## 6. Sample-size decision procedure

From pilot variance: choose replicates per cell for 80% power to detect the minimum effect
of interest (HUMAN DECISION: define it, e.g. 1.0 briefing-quality points) with Holm-adjusted
α=0.05 over the confirmatory family. The episode is the unit of analysis.

## 7. Randomisation

Paired scenario seeds: replicate r shares `seed_root=(study_seed, condition, r)` structure
across conditions; condition execution order randomised per replicate block; agent-name and
skin assignment balanced.

## 8. Exclusions and failure handling (predeclared)

- Episodes with `RunFailed` (provider outage): excluded from primary analysis; counts
  reported; sensitivity analysis including them as worst-case.
- Invalid actions: recorded as `ActionRejected` + safe abstention (never silently repaired);
  the invalid-action rate is itself an operational outcome. Episodes with >25% invalid
  actions for any agent are flagged and sensitivity-analysed.
- No exclusions based on outcome values.

## 9. Analysis

Per STATISTICAL_ANALYSIS_PLAN.md: episode-level outcomes; paired contrasts over shared
replicate seeds; bootstrap-over-episodes CIs; Holm over the confirmatory family {H1 main
effect, H2 main effect}; H3 exploratory. Effect sizes with intervals, distributions plotted;
no single leaderboard score.

## 10. Robustness

- Two narrative skins (official-briefing, newsroom-desk) — confirmatory conclusions must
  hold in sign under both skins or be reported as skin-sensitive.
- Prompt-injection fixture (e08) present in all cells; injection-compliance is monitored
  as an operational outcome.
- Scripted-baseline anchors: the 2x2 with scripted personas (this repo, replicates=3) runs
  alongside as a mechanism sanity anchor.

## 11. Stopping rule and cost ceiling — HUMAN DECISION

Abort thresholds (spend, invalid-action rate, provider failure rate) and the total budget
must be set before freeze. See COST_WORKSHEET.md (no prices are assumed there).

## 12. Claim boundary

Results are claims about *LLM-agent populations under configured mechanisms*, specific to
the tested models and prompts. They are NOT predictions about human communities, public
policy, or other models. Negative results will be preserved and reported.

## 13. Deviations log

Any post-freeze change requires a new study version (the freeze hash changes) and an entry
here explaining what changed and why.

---
Human decisions outstanding before freeze: final H1/H2 wording, primary-outcome selection,
minimum effect of interest, model/provider list, replicate count (post-pilot), cost ceiling,
stopping rule, utility-weight confirmation (ECParams defaults are placeholders).
