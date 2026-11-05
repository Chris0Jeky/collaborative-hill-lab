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

**Delivery record, 2026-11-05:** monitor PR #114, core PR #119 and pilot decision-record
PR #120 are merged. HTML comparison #116 is implemented, independently reviewed
and verified; [PR #121](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/121)
retains its publication checks and merge status. The corrected native Windows
export path passed the complete platform gates. Checked items below record the
stated work and tested revisions; see `HANDOFF.md` for the verification table.

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

- [x] Pin the omitted-experiment and stale-path behaviors with focused tests.
- [x] Implement discovery and explicit recipes/entry points, preserving source/output rules.
- [x] Run targeted tests, lint/types and record the exact commands and limitations.
- [x] Review the task independently and incorporate fixes.

## Task 2: Verified round inspector

Owner: inspector lane. Files: `reporting/lab.py`, focused new reporting modules and
`tests/integration/test_lab_console.py` / inspector-specific tests.
Consumes: verified events and resolved scenarios from `load_run`.
Produces: deterministic public/observed round data and a self-contained explorer.

- [x] Test literal round state, branch context, hostile strings and safe export destinations.
- [x] Implement state projection and accessible navigation using existing ledger contracts.
- [x] Run focused regressions and package lint/types; review six-fixture Chrome predecessor views.
- [x] Perform independent source review and identify ancestry/export corrections.
- [x] Implement and independently review the native export correction.
- [x] Verify the corrected export path in complete Ubuntu/Windows CI and review Chrome views.

## Task 3: Run monitoring snapshot

Owner: integration lane. Files: `reporting/monitor.py`, CLI command and
`tests/integration/test_run_monitor.py`.
Interface: `monitor_runs(root: Path) -> dict[str, Any]`; output contains schema version,
per-run observations and state counts; CLI JSON is stable and contains no wall clock.

- [x] Test a real completed fixture, valid failure, running prefix, partial final line,
  malformed complete line, manifest-only reservation, tampering and empty roots.
- [x] Verify valid prefix hashes without treating unsealed artifacts as scientific evidence;
  use full `load_run` validation for sealed manifests.
- [x] Add human text and JSON CLI output, exit 1 on broken/failed records and 2 on bad input.
- [x] Test source-byte preservation, deterministic output and absence of provider activity.
- [x] Complete independent review and both platform gates; merge PR #114.

## Task 4: Identity, roadmap and issue lifecycle

Owner: roadmap lane. Files: README/NEXT and focused docs, seed manifest, seeder script,
offline tests, explicit `workflow_dispatch` workflow if appropriate.
Produces: validated machine-readable seed plan with stable deduplication markers.

- [x] Establish a short identity, evidence ladder and ordered roadmap from inspected source.
- [x] Test manifest validation, open/closed dedupe, pagination and failure reporting.
- [x] Implement preview-first issue seeding with a deliberately invoked publish mode.
- [x] Review workflow permissions, issue semantics and documentation against actual interfaces.

## Task 5: Integration and publication

Owner: integration lane. Files: handoff/build log/agent command map and any integration fixes.

- [x] Integrate the catalog/inspector/monitor/seeder slices and source-preservation checks.
- [x] Run the complete predecessor offline gate (2,258 tests) and inspect actual Chrome views.
- [x] Open the core and pilot draft PRs and attach their verification/review evidence.
- [x] Publish the bounded issue queue and pin all eight existing issue numbers.
- [x] Inspect complete Ubuntu/Windows logs and browser evidence for the tested heads in HANDOFF.
- [x] Merge the reviewed core and pilot records; record their merge commits and issue delivery.

## Follow-up delivery: comparison and pilot decision aid

- [x] Implement `chl compare --out` while preserving default descriptive JSON (#116).
- [x] Align recorded observations/actions; expose compatibility, missing records and shared history.
- [x] Add sealed-fixture and Chrome checks and reuse the shared guarded export writer.
- [x] Publish the comparison implementation in PR #121.
- [x] Complete comparison implementation review and exact-head platform/browser gates.
- [x] Prepare reviewed comparison delivery docs; link PR #121 for final publication and merge status.
- [x] Prepare the source-backed pilot decision aid, correcting pairing and incomplete-artifact wording (#118).
- [x] Complete pilot document review and PR #120 CI/merge; owner choices remain unresolved.

The next research implementation starts with the separate design and exact
cost/timing contract for #117. No live pilot, cost/timing result or scientific
default is selected by these delivery checkboxes.
