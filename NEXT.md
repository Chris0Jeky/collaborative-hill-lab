# Next work

The next development task is the separately declared audit cost/timing experiment
(#117). The offline workflow and HTML comparison are implemented, reviewed and
verified. [HANDOFF.md](HANDOFF.md) records tested revisions and delivery records;
[ROADMAP.md](ROADMAP.md) defines the evidence boundaries and issue lifecycle.
The [lab walkthrough](docs/LAB_WALKTHROUGH.md) covers the available interfaces,
and [PR #121](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/121) retains
the comparison's publication record.

## Next research: declare audit cost and timing (#117)

For [#117](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/117), first
write a separate design with a bounded question, predicted contrasts and exact
charging semantics. State who pays, when the charge occurs, and how timing,
unavailability and failed requests affect the declared budget. Keep the existing
free-audit reference and original evidence intact.

Before execution, specify beneficial, harmful, null, late and unavailable
controls; derive literal accounting and outcome expectations. Any new mechanism
behavior needs an explicit versioned contract and integrity checks. Report
accuracy, coverage, signed quality and resource cost separately. This is the next
research task; no cost/timing result has been produced by the current UI work.

## Owner review remains open

Use the [prepared pilot decision record](docs/research/PILOT_DECISION_RECORD.md)
from merged [PR #120](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/120) to discuss
the question, incentive alternatives, outcomes, population/model, pairing,
allocation, spending ceiling and stop rules. Every choice remains unresolved.

The acceptance criteria and dependencies live in
[scripts/issue_seeds.json](scripts/issue_seeds.json). Preview with
`python scripts/seed_issues.py --remote`; publication is a separate explicit action.
Closed seeds remain closed. Implementation history belongs in the handoff and
[milestone record](PLAN.md).

## Scientific decisions before live or confirmatory work

Study 001 is still an unfrozen draft whose placeholder weights fail collective
stakes (C2). The [incentive atlas](experiments/incentive-atlas/README.md) identifies
admissible regions for its enumerated strategies without choosing a default.
An owner-declared pilot must choose institutions/weights, outcomes, model/version,
skins, cost ceiling and stopping rules. A candidate pilot episode count is a
budget choice, not an established power requirement.

After a declared pilot measures episode variance, invalid-output rate and actual
usage/cost, the owner can finalize minimum effects, sample size, hypotheses,
exclusions and the statistical analysis plan. A confirmatory freeze and execution
follow those recorded decisions. Preserve negative and incomplete results, and
distinguish kernel seed pairing from provider randomness. The offline research
design can proceed while these choices remain open. Mocked provider tests remain
engineering evidence.
