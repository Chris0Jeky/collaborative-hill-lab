# Sealed analysis input validation

`chl analyze` is the draft Study 001 accountability × evidence-topology readout.
Its unit is the episode. It reads sealed artifacts and does not rerun, edit, or
freeze a study. The estimands and inference limits remain those in
[STATISTICAL_ANALYSIS_PLAN.md](STATISTICAL_ANALYSIS_PLAN.md) and
[ADR-0008](../adr/0008-versioned-policy-pairing.md).

## Comparison populations

A valid event ledger establishes what was recorded. It does not by itself
establish that four runs form a comparable factorial design. The analysis checks
all eligible sealed attempts, including failed attempts, before selecting the
completed episodes used for outcome estimation.

Every input must have the same recorded study identity, study hash, study seed,
and seed protocol. Within a comparison population, inputs must agree on:

- The world, evidence, interaction, and cognition planes, including agent IDs,
  policy parameters, budgets, round counts, and payoff settings.
- The institution plane after removing only `accountability` and
  `evidence_topology`, the two declared interventions.
- The narrative hash and the recorded policy assignments, providers, prompt
  template hashes, sampling settings, and invalid-action policy.

Scenario IDs and descriptions can differ across factorial cells. Each
condition within a block must still have one recorded scenario hash; changing
that scenario between replicates is not silently pooled.

For `legacy-independent-v1`, all four cells belong to one comparison
population. For `paired-policy-v2`, comparisons are checked within each explicit
`scenario_block`. Different declared blocks may carry different baseline
configurations. Paired inference still requires a complete quartet for every
`(scenario_block, replicate)` and the existing policy-randomness checks. An
incomplete block is not silently reinterpreted as an independent design.

These checks reject confounding; they do not certify a runtime implementation
from a policy label or prove that recorded provider metadata describes an
independently verified model call. The provider-pairing limitation in ADR-0008
continues to apply. No provider coupling is inferred from kernel seeds.

## Copies, retries, and exclusions

An experimental unit is identified by condition, scenario block (when present),
and replicate within the validated study. An exact repeat of the analysis row
is a duplicate artifact, not another independent episode. Duplicates remain
visible in the exclusions and do not increase sample or attempted-episode
counts.

Conflicting sealed artifacts for the same unit cause analysis to fail. In
particular, a failed attempt followed by a successful retry cannot be selected
according to directory sort order. A retry policy and its treatment in an
analysis require an explicit design; this readout supplies neither implicitly.

Invalid or unsealed artifacts, branches, exploratory conditions, and misplaced
condition directories retain their exclusion categories. They do not define
the validated study's identity or comparison population. Eligible failed
episodes remain in the failure counts, and a study with no completed episodes
still reports the seed protocol recorded in its failed runs.

Attrition counts describe discovered artifacts. A completely absent run
directory cannot be counted from the input alone; the analysis does not infer
an unrecorded planned sample size or invent missing outcomes.

## Compatibility and verification

The valid scripted fixture retains the same schema version and byte-identical
canonical output in `tests/integration/golden/analysis_001.json`. Previously
accepted confounded populations and conflicting repeated attempts now fail
with a `ValueError`. For inputs consisting entirely of failed runs, the
top-level seed protocol and declared resampling unit now retain the recorded
design instead of defaulting to missing/independent metadata.

No study JSON, study hash, seed allocation, metric definition, contrast weight,
bootstrap estimator, Student-t formula, or Holm correction changes. Regression
fixtures exercise real offline sealed runs. The numerical tests include a
literal centered-bootstrap tail-probability oracle in addition to the existing
bootstrap-index, contrast-sign, percentile, Holm, and Student-t checks.

Focused checks:

```bash
python -m pytest tests/integration/test_analysis.py tests/unit/test_analysis_stats.py
```

Repository gates remain `make check`, `make test`, `make validate`, and the
sealed-artifact acceptance script. This validation work does not freeze the
SAP or select any of its human-owned scientific choices.
