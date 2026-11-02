# EC rule component ablation implementation plan

> For agentic workers: execute the authorized plan with the executing-plans
> workflow; the design and literal predictions precede any experiment execution.

**Goal:** Isolate all four skeptical-rule components with a reproducible bounded
factorial, without changing old policy behavior or evidence bytes.

**Architecture:** A separately versioned scripted policy uses the existing
observation and engine. A standalone generator runs six contexts, paired truths,
all 16 variants and fixed-action controls, retaining exact contrasts and seals.

**Tech stack:** Existing Python 3.12, Pydantic, pytest, exact Fraction arithmetic.

**Spec:** [DESIGN.md](DESIGN.md), [ADR-0016](../../docs/adr/0016-ec-rule-component-ablation.md).

## Global constraints

No provider calls, freeze, final weights or human-owned decisions. Preserve all
existing policy IDs and quality-safeguards files. No new dependencies. Portable
LF writes. Parent handles CI/Makefile/publication and shared handoff documents.

## Review focus

- Citation gating must be independent of screening, and look for supporting
  citations for the correct proposition and slot.
- Sharing off must hide contradictions without disabling supporting sharing.
- Challenge timing, self-exclusion and later verification must match v1.
- Source records must bind the actual variants and generated scenario identity.
- Every factorial pairing must hold non-treatment inputs fixed and retain nulls.

## Task 1: independently switched policy

- [x] Add literal probe/endpoint/boundary tests in
  `tests/unit/test_ec_ablation_contributor.py`; observe the initial import failure.
- [x] Implement `ECAblationContributorPolicy` in
  `src/collaborative_hill/agents/scripted/ec_ablation.py` and additive registry
  hooks in `params.py`, `ec_policies.py`, and `experiments/study.py`.
- [x] Run the new tests and existing conditional/skeptical tests, ruff and mypy.
- [x] Commit the working policy and tests.

Task 1 verification: initial test failed on the missing registry name; after
implementation the ablation/conditional/skeptical suites passed 193 tests. Ruff
passed and strict mypy checked 54 source files. One observation-boundary test was
corrected to assert that a mismatched citation is not verified: changing an
item's proposition can legitimately make a different proposal eligible before
verification. This does not change a declared experiment prediction.

## Task 2: declared experiment, controlled contrasts and hostile inspection

- [x] Implement `ec_rule_ablation.py`: `cells`, `scenario`, `execute`, `collect`,
  `render_report`, `source_provenance`, `--out`, `--check`.
- [x] Test exact cell counts/factorial arithmetic, hand-derived T1-T3 and outcome
  literals, endpoint shadows, truth observations and fail-closed run inspection in
  `tests/unit/test_ec_rule_ablation.py`.
- [x] Run narrow tests and lint; commit before recording the experiment.

Task 2 verification: the initial experiment import failed because the generator
did not exist. The new experiment/policy, legacy conditional/skeptical and
portable-write tests then passed 208 tests; ruff and strict source mypy passed.
The runner validates exact saved inputs, schedules, manifest identity and every
replayed event chain. Tests include wrong input/manifests and prediction misses.
Ruling: keep contrast arithmetic, prediction literals and Markdown rendering in
`ablation_readout.py` to keep the execution/audit module focused; the runner
imports it, and its digest is included in execution provenance.

## Task 3: execution and immutable readout

- [ ] Run `--out` into a fresh ignored artifact directory from clean source.
- [ ] Copy the generated results/provenance into this experiment directory,
  reporting every predeclared prediction miss without changing predictions.
- [ ] Run `--check`, the unchanged quality-safeguards `--check`, relevant test
  suites and full available repository checks; commit the readout.
- [ ] Send parent exact commits, evidence, gate command and known limits.
