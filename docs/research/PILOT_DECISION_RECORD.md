# Pilot decision record — draft options, no execution decision

**Status: prepared for owner review; all scientific and spending choices below
remain unresolved.** This is a decision aid, not a preregistration, frozen study,
power calculation or authorization to contact a provider. Completing this
document's engineering task does not resolve the decisions in
[HANDOFF.md](../../HANDOFF.md#human-owned-decisions--unchanged).

The lab can validate scenarios, plan request bounds, execute explicitly permitted
providers and replay their recorded actions offline. Those capabilities have
been checked with fake or intercepted providers. The existing scientific
findings concern scripted policies in synthetic environments; there is no
measured live-model audit benefit to use as a pilot effect estimate.
Sources: [research charter](RESEARCH_CHARTER.md),
[provider boundary](../PROVIDER_USAGE.md),
[current evidence](../../README.md#what-the-experiments-establish).

## What the pilot needs to decide

The useful next live question should be small enough to explain when it fails.
A pilot would measure operational health and outcome variation under one declared
configuration before a later confirmatory design is chosen. It should preserve
failed and incomplete attempts as well as completed outcomes. A pilot finding
would not certify all institutions, models, narratives or strategies.

Three possible scopes are available for discussion; none is selected:

| Candidate scope | What it could inform | What it would leave unresolved |
|---|---|---|
| Basic Evidence Commons feasibility | Whether a selected model follows the action schema and sustains useful contribution under a small declared setup; measured repair/failure rates, usage and episode variation | An accountability effect, social-dilemma certification, general model capability |
| Study 001 institutional pilot | Variation and attrition across aggregate/attributable accountability × private/shared-ledger evidence for a separately declared population | Final weights, confirmatory hypotheses, sufficient sample size and external validity |
| Audit-response pilot | How a selected model reacts to positive, negative and unavailable public reports under the explicit `ec-audit@1` renderer | Real-world audit reliability, a guaranteed quality gain, the effect of charging for audits |

The first scope has the fewest interacting treatment choices. The second links
directly to the draft Study 001 question but needs an explicit incentive decision.
The third builds on the existing audit implementation but adds fallible-information
and response questions. Combining all three in the first pilot would make failures
harder to diagnose. This is a design tradeoff, not a selected study scope.
Sources: [Study 001](../../studies/001-evidence-commons/README.md),
[audit usage](../AUDIT_USAGE.md),
[audit-feedback design and results](../../experiments/audit-feedback/README.md).

## Decisions to record before any provider execution

| Decision | Current state | Information needed for a defensible choice |
|---|---|---|
| Pilot question and treatment contrast | **Unresolved** | Choose one scope above or state a different bounded question; name what remains fixed |
| Institutions and utility weights | **Unresolved** | Decide whether the current uncertified draft is an operational probe or whether a separate incentive design is required; retain the actual C1/C2/C3 results |
| Primary outcome and secondary diagnostics | **Unresolved** | Select the episode-level outcome; distinguish quality, accuracy, coverage, contribution, effort and attrition |
| Population, provider and exact requested model/version | **Unresolved** | Name the model composition, agent count, sampling settings and supported API contract; record the reported model separately |
| Prompt renderer, narrative skins and presentation controls | **Unresolved** | Choose `legacy@1` or the explicit EC audit renderer, declare skins and any prompt/order changes before running |
| Replication and pairing | **Unresolved** | Choose an independent design or justify a specific coupling; kernel seeds alone do not pair provider randomness |
| Pilot allocation | **Unresolved** | State episodes per condition and their operational purpose; any proposed count is a budget candidate, not a power claim |
| Request limits and monetary ceiling | **Unresolved** | Record attempt caps, output cap, retry policy, provider-specific prices and a separate spending control; preserve unknown usage as unknown |
| Stop, failure and exclusion rules | **Unresolved** | Specify what stops collection, how shortfall is recorded, and which attempted/failed/completed episodes enter each summary |
| Later confirmatory decisions | **Unresolved** | Use the pilot's measured variation and failure rates to choose a minimum relevant effect, sample size, estimands and exclusions before a separate freeze |

These rows prepare the existing owner decision list; they do not replace it.
No endpoint, model, price, sample size or utility default is supplied by this
record. An owner may reject a candidate or keep the next phase entirely offline.

## Incentive alternatives: preserve the finite scope

The current Study 001 placeholder settings fail collective stakes (C2).
The [incentive atlas](../../experiments/incentive-atlas/README.md) identifies the
common strict C1/C2 region `b >= 0`, `r >= 0`, `b + 7r > 39` for its **enumerated
contributor/freerider strategies**, with its other costs, penalties and settings
fixed. It does not establish the same inequalities for arbitrary LLM behavior.

| Existing atlas example `(b, r)` | Useful distinction | Limitation |
|---|---|---|
| `(40, 0)` | Larger common benefit with no attribution credit | Changes the benefit scale; supplies no measured behavioral response |
| `(33, 1)` | Keeps the atlas credit multiplier at one while crossing the strict C2 boundary | Lies close to the finite-strategy boundary; not a robustness guarantee |
| `(12, 4)` | Keeps the placeholder common benefit and increases attribution credit | Some contributors still have negative utility; C2 does not imply everyone benefits |
| `(0, 7)` | Demonstrates a different incentive pattern inside the finite admissible region | No attributable exit from all-contribution is profitable despite existential C1 holding elsewhere |

These are the atlas's existing examples, not recommended replacements for Study
001. Credit is created by the scoring rule rather than paid from an audited
resource budget. Increasing credit can increase utility without improving the
briefing. The strict boundary example `(32, 1)` gives `b + 7r = 39` and still fails
C2. A chosen new design needs its own declared files and actual certificate;
changing the current evidence or its recorded weights would erase the comparison.

## Measurement and analysis decisions

Use an episode as the sampling unit. Rounds and agents within an episode are
dependent observations; inherited branch history is also shared information.
Record accepted-correct and accepted-incorrect counts, filled slots and the
selected episode-level outcome so that an accuracy gain cannot hide lost coverage
or lower signed quality. Keep operational diagnostics beside outcomes: valid
completion, action repair/rejection, provider errors, request attempts, measured
tokens and costs when supplied. Sources:
[methodology](METHODOLOGY.md), [draft analysis plan](STATISTICAL_ANALYSIS_PLAN.md),
[audit findings](../../experiments/audit-feedback/RESULTS.md).

The original Study 001 inputs use `legacy-independent-v1`. Matching replicate
numbers across those conditions do not establish common random numbers.
`paired-policy-v2` can share specified kernel policy streams within a scenario
block, but the current LLM policy does not use that RNG to couple provider
sampling. Even a separately supplied provider seed requires a supported contract
and empirical validation. Choose the analysis from the declared, validated design;
do not add pairing after viewing outcomes. Source: the
[seed design and analysis boundary](STATISTICAL_ANALYSIS_PLAN.md#3-blocking-and-pairing-crn).

Repeated deterministic scripted controls check exact behavior; they do not add
independent outcome information. Conversely, equal observed stochastic outcomes
do not prove zero population variation. Preserve the actual stochastic episode
count and report the zero-observed-variance limitation. This pilot record makes
no effect-size, confidence-interval or power claim. The final sample-size
procedure requires an owner-selected minimum relevant effect and a variance
source appropriate to the chosen design.

## Operational limits to carry into a declaration

`chl study plan` can compute worst-case completion and HTTP-attempt counts without
credentials or requests. An attempt budget is not a monetary cap: input tokens
are not estimated, provider prices are not built in, and missing usage stays
`null`. Retry and format-repair attempts count toward the same admitted-request
limits. Concurrent invocations do not share one counter.

Deadlines are checked between requests, not an in-flight cancellation guarantee.
Abrupt termination can leave incomplete artifacts and incomplete accounting;
`chl monitor` reports unfinished valid prefixes as unsealed and malformed artifacts
as broken, without inferring liveness or final cost. An authorized live protocol
must state how provider-side spending
and any unconfirmed requests would be reconciled. These are implemented limits,
not hypothetical guarantees. Source:
[request planning, budgets and termination](../PROVIDER_USAGE.md#planning-and-request-budgets).

The preparation sequence, after the owner records the unresolved decisions, is:

1. Put the chosen pilot declaration and inputs in a separate versioned location;
   retain the original studies and readouts. Record what varies and what is fixed.
2. Validate its StudySpec offline, run applicable literal controls/certificates,
   and inspect the offline request plan. Record actual failures as well as passes.
3. Record a separate explicit execution decision with the chosen provider,
   spending boundary and stop rules. Preparing this record does not make that
   decision or trigger any request.
4. If execution is authorized later, keep the full attempted allocation and
   sealed/incomplete artifacts, inspect the outcomes, and produce a descriptive
   pilot readout. Resolve confirmatory design and freeze separately afterward.

No draft StudySpec is created by this document, so there is no new certificate
result or executable pilot configuration to mistake for an approved design.

## Decision and execution log

| Date | Record | Result |
|---|---|---|
| 2026-11-05 | Decision aid prepared from existing source records for issue #118 | All choices remain unresolved; no provider execution, new research result or freeze |

Future owner decisions should identify the chosen alternative, rationale,
rejected alternatives and relevant source commit. Execution records should link
the separately declared design, exact code/input identities, actual allocation,
failures and measured accounting. Keep those records separate from this document's
preparation status.
