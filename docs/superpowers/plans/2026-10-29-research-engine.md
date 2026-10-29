# Research engine advancement implementation plan

> For agentic workers: use subagent-driven development or executing-plans to carry out independently reviewable tasks. The owner authorized implementation, draft PRs, and verified merges in this session.

**Goal:** make the offline laboratory safer to extend and use, and execute the documented N-IPD sensitivity follow-up.

**Architecture:** retain the deterministic kernel, exact payoff representation, versioned seed protocols and sealed-ledger analysis. Add validation at input and analysis boundaries, persistent verification, and a study-local experiment using existing mechanisms.

**Tech stack:** Python 3.12, Pydantic, pytest/Hypothesis, Ruff, strict mypy, GitHub Actions.

**Spec:** GitHub issues #64–#68 and the explicitly post hoc extension #72; Study 002's README records its predictions before execution. Existing architecture and scientific invariants remain in AGENTS.md and ADRs 0001–0009.

## Global constraints

- Study 000/001 input bytes, hashes and freeze states remain unchanged.
- No global RNG, floats in hashed data, real provider calls, paid runs or human data.
- Separate deterministic checks from independent stochastic episodes; do not treat agents or rounds as independent replicates.
- Publish through draft PRs; review diffs and exact-head CI before merging.
- Preserve failed/negative results and state unverified boundaries plainly.

## Review focus

- Invalid or platform-ambiguous condition names must fail before filesystem writes.
- A symlink beneath an artifact root must not redirect study output elsewhere.
- Typos and invalid policy probabilities must fail instead of silently becoming defaults.
- Failed attempts and conflicting retries must not escape population or unit checks.
- Study reports must verify expected inputs, seals and analytical predictions without reusing measured values as their oracle.

## Task 1 — persistent offline verification (#64)

Files: `.github/workflows/ci.yml`, `Makefile`, `scripts/check_atlas.py`.

- [x] Add minimal-permission CI pinned to official action commits and the exact tested head.
- [x] Exercise existing quality/full-suite/study/acceptance gates and standalone atlas generation.
- [x] Verify clean workspace and scratch cleanup locally.
- [x] Review published exact-head Actions results and merge the ready PR.

## Task 2 — analysis input integrity (#65)

Files: `reporting/analysis.py`, analysis tests and validation documentation.

- [x] Reproduce confounds, conflicting retries, misplaced identities and failed-only protocol loss with sealed artifacts.
- [x] Compare non-treatment settings within declared populations and reject conflicting experimental units.
- [x] Keep valid golden output and numerical formulas stable; add an independent bootstrap-tail oracle.
- [x] Review the complete diff, validate in CI and merge.

## Task 3 — Study 002 sensitivity experiment (#66)

Files: `studies/002-nipd-sensitivity/`, new unit/integration tests.

- [x] Record analytical predictions before executing the experiment.
- [x] Implement canonical generation, distinct deterministic/stochastic components and sealed-data reporting.
- [x] Execute all declared episodes; check deterministic oracles and replay representatives.
- [x] Independently review mathematics, integrity guards and interpretation; publish validated results.

## Task 4 — study output safety (#67)

Files: `experiments/study.py`, `engine/runner.py`, input safety integration tests.

- [x] Write regressions for unsafe names, case collisions, empty designs, invalid counts and output symlinks.
- [x] Observe failures, then validate portable components and strict execution counts without rewriting valid data.
- [x] Check all planned output paths before execution and again before reservation; retain explicit root symlink support.
- [x] Verify old hashes, normal runs, reservation cleanup, full suite and exact-head CI.

## Task 5 — scripted policy contract (#68)

Files: scripted parameter contract, `PolicySpec`, CLI overrides and regression tests.

- [x] Demonstrate ignored parameters and invalid exploration/threshold values.
- [x] Share one built-in contract while preserving unknown policy serialization and valid original spec bytes.
- [x] Verify rational parameters, endpoints, CLI failures, hashes and existing studies.
- [x] Review, validate and merge.

## Task 6 — post hoc exact pTFT benchmark (#72)

Files: `study002_markov.py`, `generate_exact_benchmark.py`, exact benchmark JSON/Markdown/SVG, mathematical and report tests.

- [x] Derive exact transition matrices, moments, cross-time covariance and full/window variance.
- [x] Verify with literal and independently enumerated labelled-agent/history oracles.
- [x] Bind the post hoc report to the unchanged 221-episode readout; distinguish F40 and F49.
- [x] Reproduce and fix inherited rounding/style drift; verify read-only byte regeneration.
- [x] Add Make targets, all four StudySpec validations and the exact benchmark CI gate.
- [x] Inspect exact-head CI and merge PR #79.

## Integration and handoff

- [x] Bring current status, commands and open research directions into README, NEXT, PLAN, HANDOFF and BUILD_LOG.
- [x] Recheck the integrated tree and all shipped study identities.
- [x] Record real remaining decisions as issues with acceptance criteria; report merged work and limitations.
