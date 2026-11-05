# Roadmap — a coherent, inspectable cooperation laboratory

Collaborative Hill Lab tests how interaction rules, information and institutions
affect accurate, useful cooperation under mixed incentives. Its foundation is a
deterministic synthetic laboratory: declared scenarios, explicit policy behavior,
sealed event records and reproducible comparisons. LLM populations are a research
target; current scientific findings come from scripted agents.

The current development goal is **one usable offline workflow: discover a
question → plan a run → execute into fresh output → monitor artifacts → inspect
rounds → verify the result against its source record**. This makes the accumulated
experiments useful to contributors and gives new research a reliable starting
point. The workflow and optional HTML comparison are implemented, reviewed and
verified. The next research design concerns audit cost and timing; owner pilot
choices remain separate.

## Keep four kinds of progress distinct

| Kind | What it establishes | Where to look |
|---|---|---|
| Executed synthetic evidence | Results for a declared finite design, policies and assumptions, including harmful and null outcomes | [Evidence table](README.md#what-the-experiments-establish), experiment readouts and original source records |
| Exploratory research | A question or draft design that still needs predictions, controls and execution | The research queue below and the [research charter](docs/research/RESEARCH_CHARTER.md) |
| Engineering readiness | A capability has passed relevant implementation and integrity checks | Tests, CI and [HANDOFF.md](HANDOFF.md); a green provider test is not a measured model result |
| Owner scientific decisions | Chosen weights, outcomes, models, budget, stopping rules and any confirmatory freeze | [Prepared pilot decision aid](docs/research/PILOT_DECISION_RECORD.md), [Study 001 draft](studies/001-evidence-commons/README.md) and [statistical plan](docs/research/STATISTICAL_ANALYSIS_PLAN.md); choices remain unresolved |

A verification rerun checks reproduction; it does not enlarge the original sample.
A visual inspector explains an existing record; it does not add evidence. A branch
inherits history, so its shared prefix is not an independent replicate.

## Available workflow and delivery records

| Work | Delivered behavior | Delivery status |
|---|---|---|
| Experiment catalog ([#110](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/110)) | Stable IDs, evidence status, source/readout paths and explicit run/check/reference boundaries; inspectable plans | Reviewed, verified and merged in PR #119 |
| Round inspector ([#111](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/111)) | Recorded actions, available observations, released audits, graph interactions and branch context | Reviewed, verified and merged in PR #119 |
| Run monitor ([#112](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/112)) | Completed, failed, unsealed and broken artifact states without a liveness claim | Reviewed, verified and merged in PR #114 |
| Direction and issue lifecycle ([#113](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/113)) | Validated bounded queue, preview-first publication and open/closed issue deduplication | Reviewed, verified and merged in PR #119 |
| Reproduction walkthrough ([#115](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/115)) | Real graph discovery, fresh execution, monitoring, inspection, replay and safe rerun refusal | Reviewed, verified and merged in PR #119 |
| HTML comparison ([#116](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/116)) | Aligned observations/actions, exact utilities, compatibility metadata and inherited/shared history | Implemented, independently reviewed and verified; delivery record in PR #121 |

The [lab walkthrough](docs/LAB_WALKTHROUGH.md) is the user-facing integration check.
Core [PR #119](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/119) and monitor
[PR #114](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/114) are merged.
[PR #121](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/121) records the
comparison's publication, exact-head checks and merge status.
[HANDOFF.md](HANDOFF.md) identifies the reviewed and tested revisions. The
comparison remains descriptive: shared history and two episodes do not establish
independent replication or a causal effect.

## Next: audit cost/timing research and owner pilot decisions

1. **Audit cost and latency experiment ([#117](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/117)).**
   This is the next research item. Declare a separate synthetic question about
   the resource cost and timing of audits. Prerecord predictions and exact charging
   semantics, retain the existing free-audit reference, and include harmful, null,
   late and unavailable controls.
   Report accuracy, coverage, signed quality and cost separately. Existing
   mechanism versions, study weights and original evidence stay fixed; any new
   behavior needs its own explicit contract.
2. **Owner pilot decisions.**
   The [prepared decision aid](docs/research/PILOT_DECISION_RECORD.md), merged in
   [PR #120](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/120), presents
   source-backed alternatives and leaves unresolved choices visible:
   institutions, weights, outcomes, provider/model, skins, cost ceiling and stopping
   rules. Study 001's current weights fail C2; the incentive atlas offers
   finite-strategy candidates without choosing a default. Owner review can proceed
   offline alongside research design. Selecting scientific defaults, authorizing a
   live pilot and freezing a confirmatory study remain separate owner decisions.

These are bounded seeds, not an instruction to execute every proposed experiment
automatically. A live pilot measures variance, invalid-output rates and actual
usage/cost before confirmatory sample-size and hypothesis decisions. The
[provider boundary](docs/PROVIDER_USAGE.md) still applies.

## What waits for a specific need

New deception/reputation mechanisms, a Concordia adapter, policy-override
serialization, a hosted service, database storage and ledger compression need a
specific experiment or measured operational problem before becoming active work.
The project does not need another general agent framework to make its current
evidence discoverable. Historical milestones remain in [PLAN.md](PLAN.md).

## Curated issue seeding

[scripts/issue_seeds.json](scripts/issue_seeds.json) is the versioned queue. Keep at
most eight seeds, each with a stable ID, rationale, bounded scope, acceptance
criteria, verification, dependencies and existing source paths. The planning
status (`active`, `next`, `owner-decision`) is an editorial priority, not an
automatic claim about GitHub issue state or scientific completion.

```bash
# Offline validation and a fully rendered, unreconciled preview:
python scripts/seed_issues.py --check
python scripts/seed_issues.py

# Read all open and closed issues and print the reconciled plan:
python scripts/seed_issues.py --remote

# Explicit publication, using GITHUB_TOKEN or GH_TOKEN with issue-write access:
python scripts/seed_issues.py --publish
```

For an offline review of a previously collected complete issue array, use
`--issues-file path/to/issues.json`. A snapshot cannot be used for publication:
publishing always reads GitHub again before any creation. The default offline
preview says `unreconciled`, not `create`, because it has no current issue history.

The **Seed roadmap issues** GitHub workflow runs only by manual dispatch. Its
default is a read-only preview; the explicit `publish` checkbox enables a separate
issue-write job after preview succeeds. Workflow runs are serialized to avoid
two seeding runs racing each other. There is no schedule or automatic idea
generation.

Each issue body contains `<!-- chl-roadmap:<id> -->`. The seeder checks every page
with `state=all`, ignores pull requests, and matches both that marker and any
pinned issue number. Existing open issues are left alone; existing closed issues
are reported as `existing-closed` and never reopened or recreated. Missing pinned
issues or ambiguous matches stop the plan before writes. Do not reuse a closed
seed ID for a new task: write a new, justified seed and link the prior decision.

Publication creates only missing issues. It never replaces descriptions, adds
comments or changes existing discussion. A failed POST is reported as
`unconfirmed`, later creations are `not-attempted`, and the command exits nonzero.
After a failed request, inspect GitHub before retrying: a connection failure can
hide a successful server-side creation. A later deliberate invocation reconciles
the marker again. Concurrent manual edits or an external seeder still require
normal review; GitHub issue creation has no transaction spanning the whole queue.

When work closes, preserve its stable marker and record the issue number in the
manifest. Retire finished entries when making room for a newly reviewed priority.
The offline test suite validates the shipped manifest and source links, so
changing the semantic queue cannot silently pass as a documentation-only edit.
