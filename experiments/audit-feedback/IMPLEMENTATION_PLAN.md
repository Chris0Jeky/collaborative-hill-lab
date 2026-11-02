# Audit feedback implementation plan

> **For agentic workers:** Use superpowers:executing-plans for this assigned
> implementation lane. Root coordinates the separate model/kernel work and fresh
> independent review. Do not publish or merge from this lane.

**Goal:** Implement the declared negative-veto policy and reproduce the exact
76-run audit-feedback design without altering historical policy or study behavior.

**Architecture:** A new policy wraps the unchanged skeptical rule and consumes the
shared strict public audit schema. A separate experiment keeps its literal action
oracle and closed forms independent of policy/engine execution. The root lane
integrates the versioned audit engine, publication hook and persistent CI gate.

**Tech Stack:** Python 3.12, exact Fraction arithmetic, Pydantic, pytest, Ruff and
strict mypy with the repository's pinned environment.

**Spec:** [DESIGN.md](DESIGN.md), committed before audit-enabled execution.

## Global constraints

- Original design commits: `4ef3d57` and pre-execution clarification `d2974a0`.
- Root publishes the design before any audit-enabled episode.
- Use `PYTHONPATH=src` and the shared environment's Python from this worktree.
- No old policy functions, historical evidence, StudySpecs or human decisions change.
- No live providers, paid execution, freezes, final-weight choices or GitHub writes.
- Original research execution requires clean committed/published source and a fresh root.
- Any prediction miss remains in the retained readout; probabilities are exact strings.

## Review focus

- Malformed audit envelopes fail even when the base action is inspection or a no-op.
- Unavailable, absent and unrelated reports are exact old-policy action bridges.
- Opaque contract hashes and configured probability settings cannot select policy actions.
- Same-action C3 includes forced verification after negative audits, avoiding a vacuous gate.
- Complete unavailability has undefined conditional audit accuracy; use joint mass checks.

## Task 1: separately registered policy

Files: new `src/collaborative_hill/agents/scripted/ec_audit.py`, additive changes
to `ec_policies.py`, `params.py`, `experiments/study.py`, and new
`tests/unit/test_ec_audit_contributor.py`.

Consumes: `domain.audit.AuditEnvelope`, `ECSkepticalContributorPolicy`, ordinary
EC observation dictionaries and the public audit envelope. Produces:
`ECAuditVetoContributorPolicy(min_sources=2, peer_threshold="1/2",
warmup_rounds=3, share_evidence=True)`, with pure `propose(observation,rng)`.

- [x] Write literal pure-observation tests through the old factory, including all
  review-focus boundaries and registered parameter validation.
- [x] Run tests and retain the expected missing-factory/contract failures.
- [x] Implement validation-before-selection, negative Propose/Verify veto and exact
  non-veto forwarding. Parse the shared envelope through strict JSON validation.
- [x] Run pure policy, legacy policy/parameter, lint/type checks and the full suite
  permitted by the current integration state; report any blocked integration gate.
- [x] Commit policy source and tests separately from research source.

## Task 2: independent literal and probability oracles

Files: `experiments/audit-feedback/audit_closed_form.py` and
`tests/unit/test_audit_feedback.py`.

Consumes: only declared `(T,R,V,tau)` and exact `(e,a,u)` values. Produces literal
A/B/C/D schedules/task outcomes, exact cell masses, expectation formulas and
retained undefined denominators. It must not call the production policy or engine
to obtain expected answers.

- [x] Write tests with DESIGN's literal traces, negative/null/unavailable metric
  rows, joint mass and conditional-accuracy denominator cases.
- [x] Observe the expected absent-oracle failures, then implement the formulas.
- [x] Check all 720 laws against a separate finite enumeration of literal worlds.

## Task 3: integrated reproduction and evidence checks

Files: `experiments/audit-feedback/audit_feedback.py` and experiment tests.

Consumes: the reviewed v3 engine/compiler/kernel integration, registered policy,
shared models and independent oracle. Produces a fresh 76-run tree, 60 C3 bindings,
publication/leak/replay checks, original provenance and exact JSON/Markdown readouts.

- [x] Integrate root's reviewed kernel/compiler commits without editing its lane.
- [x] Add failing tests for fresh-output/clean-source guards, cell completeness,
  report timing, prediction retention and invalid/corrupt evidence rejection.
- [x] Implement endpoint execution through the real generator; never inject findings
  or choose seeds by outcomes. Use 52 behavioral and 24 literal schedule runs.
- [ ] Check complete task/publication invariants and replay every run; implement
  `--check` as temporary regeneration plus byte-identical readout comparison.
- [ ] Complete relevant lint/type, package and integration tests; send the complete
  clean source commit to root for publication before original `--out` execution.

## Task 4: original execution and readout

- [ ] After public source confirmation, run the original design once into a fresh
  artifact root. Keep every cell, prediction status, seal and actual source identity.
- [ ] Commit the retained readouts and original provenance separately from source.
- [ ] Run the complete `--check` gate and applicable historical reproduction gates.
- [ ] Provide source/run/check evidence to root and independent reviewers. Root owns
  archival/public mapping, final documentation, Makefile/CI publication and merge.

Development log: `artifacts/audit-feedback-development/progress.md` (ignored local
working record, not research evidence). That record tracks command outputs and
integration decisions; commits preserve the deliverable history.
