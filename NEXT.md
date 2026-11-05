# Next work

The immediate goal is a coherent offline laboratory workflow, with existing
scientific evidence and original artifacts preserved. [ROADMAP.md](ROADMAP.md)
defines the priorities, evidence boundaries and issue lifecycle;
[HANDOFF.md](HANDOFF.md) records actual verification and merge status.

## Finish the current workflow

| Order | Work | Tracking |
|---|---|---|
| In parallel | Discover and deliberately run existing experiments through the catalog | [#110](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/110) |
| In parallel | Inspect verified rounds, observations, graph interactions and released audits | [#111](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/111) |
| In parallel | Monitor completed, failed, unsealed and broken run artifacts | [#112](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/112) |
| In parallel | Establish the roadmap and validated manual issue seeder | [#113](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/113) |
| Integration | Exercise one documented question-to-inspection walkthrough from a clean checkout | [#115](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/115) |

Completion requires reviewed, verified behavior. A checked plan or attractive
console alone does not establish a scientific finding. Follow the
[lab walkthrough](docs/LAB_WALKTHROUGH.md) for the public command sequence.

## Then take a bounded next item

- **Engineering ([#116](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/116)):**
  explain compatible matched runs and branch continuations with aligned observable
  differences and explicit comparison assumptions.
- **Research ([#117](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/117)):**
  separately declare an audit cost/timing experiment with exact accounting and
  beneficial, harmful, null, late and unavailable controls.
- **Owner decision preparation ([#118](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/118)):**
  use the [prepared draft decision record](docs/research/PILOT_DECISION_RECORD.md)
  to review unresolved choices and finite-strategy alternatives. Document preparation
  does not choose a model, weights, budget or confirmatory design.

The acceptance criteria and dependencies live in
[scripts/issue_seeds.json](scripts/issue_seeds.json). Preview with
`python scripts/seed_issues.py --remote`; publication is a separate explicit action.
Closed seeds remain closed. Completed implementation history belongs in the
handoff and [milestone record](PLAN.md), so this page stays focused on next work.

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
distinguish kernel seed pairing from provider randomness. None of this blocks the
offline engineering queue above or turns mocked provider tests into live evidence.
