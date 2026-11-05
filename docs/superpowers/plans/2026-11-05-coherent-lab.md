# Coherent Lab Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or
> superpowers:executing-plans for task implementation and independent review.

**Goal:** Make existing simulation work discoverable, inspectable and connected to an
active development queue without altering scientific evidence.

**Architecture:** Add read-only views around the existing run/validation contracts and
a curated experiment index. Reuse the single-file HTML console and GitHub Actions;
preserve source and evidence boundaries.

**Tech Stack:** Python 3.12, Typer, Pydantic, standard library, standalone HTML/JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-05-coherent-lab-design.md`.

## Global Constraints

- Preserve all original study/scenario/result bytes, scientific weights and policy identities.
- No live-provider execution, paid calls, study freezing, licensing or hook-trust changes.
- Keep the deterministic kernel and mechanism semantics unchanged; existing ledgers replay.
- Use existing Python 3.12, Typer and standard-library infrastructure; no new dependencies.
- Publish through connector branches and draft PRs, review and validate exact heads before merge.

## Review Focus

- Existing evidence paths and symlink aliases must not be overwritten by view exports.
- Truncated final writes must remain distinct from a corrupt complete event record.
- Sibling branches and duplicate default IDs must not become independent replicate summaries.
- Ledger text must not execute as HTML or script in a self-contained inspector.
- Closed/duplicate issue seeds must not create repeated work or erase existing discussion.

## Task 1: Experiment discovery and entry points

Owner: catalog lane. Files: new catalog module and tests, CLI catalog registration,
`scripts/lab.py` where a small coherent demonstration can reuse existing inputs.
Produces: text/JSON catalog with stable IDs and validated paths/commands.

- [ ] Pin the omitted-experiment and stale-path behaviors with focused tests.
- [ ] Implement discovery and explicit recipes/entry points, preserving source/output rules.
- [ ] Run targeted tests, lint/types and record the exact commands and limitations.
- [ ] Review the task independently and incorporate fixes.

## Task 2: Verified round inspector

Owner: inspector lane. Files: `reporting/lab.py`, focused new reporting modules and
`tests/integration/test_lab_console.py` / inspector-specific tests.
Consumes: verified events and resolved scenarios from `load_run`.
Produces: deterministic public/observed round data and a self-contained explorer.

- [ ] Test literal round state, branch context, hostile strings and safe export destinations.
- [ ] Implement state projection and accessible navigation using existing ledger contracts.
- [ ] Check rendered output and run focused regressions plus package lint/types.
- [ ] Review the task independently and incorporate fixes.

## Task 3: Run monitoring snapshot

Owner: integration lane. Files: `reporting/monitor.py`, CLI command and
`tests/integration/test_run_monitor.py`.
Interface: `monitor_runs(root: Path) -> dict[str, Any]`; output contains schema version,
per-run observations and state counts; CLI JSON is stable and contains no wall clock.

- [ ] Test a real completed fixture, valid failure, running prefix, partial final line,
  malformed complete line, manifest-only reservation, tampering and empty roots.
- [ ] Verify valid prefix hashes without treating unsealed artifacts as scientific evidence;
  use full `load_run` validation for sealed manifests.
- [ ] Add human text and JSON CLI output, exit 1 on broken/failed records and 2 on bad input.
- [ ] Test source-byte preservation, deterministic output and absence of provider activity.

## Task 4: Identity, roadmap and issue lifecycle

Owner: roadmap lane. Files: README/NEXT and focused docs, seed manifest, seeder script,
offline tests, explicit `workflow_dispatch` workflow if appropriate.
Produces: validated machine-readable seed plan with stable deduplication markers.

- [ ] Establish a short identity, evidence ladder and ordered roadmap from inspected source.
- [ ] Test manifest validation, open/closed dedupe, pagination and failure reporting.
- [ ] Implement preview-first issue seeding with a deliberately invoked publish mode.
- [ ] Review workflow permissions, issue semantics and documentation against actual interfaces.

## Task 5: Integration and publication

Owner: integration lane. Files: handoff/build log/agent command map and any integration fixes.

- [ ] Integrate isolated local commits; test source identities and preserved original files.
- [ ] Run the complete offline gate and inspect an actual generated console.
- [ ] Open draft PRs through the connector; attach exact verification and review evidence.
- [ ] Inspect both platform CI logs and merge only verified, reviewed current heads.
- [ ] Seed remaining issues, reconcile statuses and record final merged state and next work.
