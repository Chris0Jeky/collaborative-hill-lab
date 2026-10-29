# Responsive Evidence Commons — deterministic sensitivity results

This is an unfrozen scripted-policy experiment, not a live-model or human result.
The design and conditional predictions precede execution in [DESIGN.md](DESIGN.md).
The checked-in [RESULTS.json](RESULTS.json) retains every profile, seal commitment,
contrast and unilateral-deviation value; no cell is selected by its outcome.

The execution's file commitments and local source identity are recorded separately
in [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json). Hash-chain validation checks
retained ledger consistency; the source record documents the execution version.

**320 behavioral episodes and 160 controlled action replays**, each 12 rounds.
Across 160 attributable-minus-aggregate contrasts, quality increases in 2, decreases in 2, and is unchanged in 156.
Actions differ in 4 contrasts. These counts describe this finite grid;
they are not population frequency estimates or statistical significance tests.

## All-active profile: the full policy sensitivity

`C` means the active rule of that cell, not necessarily unconditional cooperation.
Quality is the engine's signed accepted-slot value. Contribution is the fraction
of all agent-round actions spent on inspection, sharing, proposing or verification.
All differences below are attributable minus aggregate.

| Corpus | Topology | Rule | Quality delta | Contribution delta | Total utility delta |
|---|---|---|---:|---:|---:|
| accurate | private | control | 0 | 0 | 0 |
| accurate | private | half-5 | 0 | 0 | 0 |
| accurate | private | all-5 | 24 | 5/12 | 14 |
| accurate | private | half-9 | 0 | 0 | 0 |
| accurate | private | all-9 | 0 | 0 | 0 |
| accurate | shared_ledger | control | 0 | 0 | 0 |
| accurate | shared_ledger | half-5 | 0 | 0 | 0 |
| accurate | shared_ledger | all-5 | 24 | 1/3 | 17 |
| accurate | shared_ledger | half-9 | 0 | 0 | 0 |
| accurate | shared_ledger | all-9 | 0 | 0 | 0 |
| misleading | private | control | 0 | 0 | 0 |
| misleading | private | half-5 | 0 | 0 | 0 |
| misleading | private | all-5 | -24 | 5/12 | -62 |
| misleading | private | half-9 | 0 | 0 | 0 |
| misleading | private | all-9 | 0 | 0 | 0 |
| misleading | shared_ledger | control | 0 | 0 | 0 |
| misleading | shared_ledger | half-5 | 0 | 0 | 0 |
| misleading | shared_ledger | all-5 | -24 | 1/3 | -59 |
| misleading | shared_ledger | half-9 | 0 | 0 | 0 |
| misleading | shared_ledger | all-9 | 0 | 0 | 0 |

## Incentives and task integrity are separate findings

9 of 40 finite-strategy cells satisfy both C1 (some strictly profitable active-to-free-rider deviation) and C2 (CCC total utility strictly exceeds FFF). This does not assert dominance, an equilibrium, or a social dilemma over untested strategies.

| Corpus | Topology | Accountability | Rule | C1 | C2 | CCC−FFF total utility |
|---|---|---|---|---|---|---:|
| accurate | private | aggregate | control | True | False | -1 |
| accurate | private | aggregate | half-5 | True | False | -1 |
| accurate | private | aggregate | all-5 | True | False | -15 |
| accurate | private | aggregate | half-9 | True | False | -1 |
| accurate | private | aggregate | all-9 | True | False | -1 |
| accurate | private | attributable | control | True | False | -1 |
| accurate | private | attributable | half-5 | True | False | -1 |
| accurate | private | attributable | all-5 | True | False | -1 |
| accurate | private | attributable | half-9 | True | False | -1 |
| accurate | private | attributable | all-9 | True | False | -1 |
| accurate | shared_ledger | aggregate | control | True | True | 2 |
| accurate | shared_ledger | aggregate | half-5 | True | True | 2 |
| accurate | shared_ledger | aggregate | all-5 | True | False | -15 |
| accurate | shared_ledger | aggregate | half-9 | True | True | 2 |
| accurate | shared_ledger | aggregate | all-9 | True | True | 2 |
| accurate | shared_ledger | attributable | control | True | True | 2 |
| accurate | shared_ledger | attributable | half-5 | True | True | 2 |
| accurate | shared_ledger | attributable | all-5 | True | True | 2 |
| accurate | shared_ledger | attributable | half-9 | True | True | 2 |
| accurate | shared_ledger | attributable | all-9 | True | True | 2 |
| misleading | private | aggregate | control | True | False | -77 |
| misleading | private | aggregate | half-5 | True | False | -77 |
| misleading | private | aggregate | all-5 | True | False | -15 |
| misleading | private | aggregate | half-9 | True | False | -77 |
| misleading | private | aggregate | all-9 | True | False | -77 |
| misleading | private | attributable | control | True | False | -77 |
| misleading | private | attributable | half-5 | True | False | -77 |
| misleading | private | attributable | all-5 | True | False | -77 |
| misleading | private | attributable | half-9 | True | False | -77 |
| misleading | private | attributable | all-9 | True | False | -77 |
| misleading | shared_ledger | aggregate | control | True | False | -74 |
| misleading | shared_ledger | aggregate | half-5 | True | False | -74 |
| misleading | shared_ledger | aggregate | all-5 | True | False | -15 |
| misleading | shared_ledger | aggregate | half-9 | True | False | -74 |
| misleading | shared_ledger | aggregate | all-9 | True | False | -74 |
| misleading | shared_ledger | attributable | control | True | False | -74 |
| misleading | shared_ledger | attributable | half-5 | True | False | -74 |
| misleading | shared_ledger | attributable | all-5 | True | False | -74 |
| misleading | shared_ledger | attributable | half-9 | True | False | -74 |
| misleading | shared_ledger | attributable | all-9 | True | False | -74 |

Every controlled same-action replay preserves the typed action schedule,
briefing, effort, collective quality and total utility. Individual credit
can redistribute. Adaptive policies may choose different actions when their
observations change; that behavioral difference is compatible with task integrity.

## Interpretation and limits

The rule responds to visible contribution, not to true evidence quality or
utility weights. Fresh false support can pass the provenance check. Attribution
can therefore facilitate harmful as well as useful activity. Anonymous
observations still certify distinct actors within a single verified claim;
a warmup can remove the identity bottleneck. This finite, synthetic design
does not select final Study 001 weights or establish that any institution
will improve cooperation in a broader population.

The paired seed protocol is explicitly declared, but these policies are
deterministic. One execution per design point supplies exact outcomes of
those algorithms, not independent samples for inferential confidence intervals.

## Reproduce

```bash
python experiments/responsive-commons/responsive_commons.py --out artifacts/responsive-new
python experiments/responsive-commons/responsive_commons.py --check
```

The first command requires a fresh output directory and retains inputs,
sealed ledgers, manifests and the readout there. The second regenerates
all 480 episodes in a temporary directory and checks byte-identical JSON
and Markdown against the committed readout. It makes no provider calls.

Study hash: `fea8cbfc08482b54ff8e1eaf07559d02bcf845fc67f666bd755ab82110cc75b4`. The study remains unfrozen.
