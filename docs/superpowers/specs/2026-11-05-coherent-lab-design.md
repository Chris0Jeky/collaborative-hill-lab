# A coherent, inspectable cooperation laboratory

## Intent

Connect the existing simulations into a laboratory that people and agents can discover,
run deliberately, inspect and extend. The project's research question remains: which
interaction structures, information structures and institutional mechanisms sustain
accurate, useful cooperation under mixed incentives? Current findings concern synthetic
scripted populations. LLM research is the longer-term target, not a result already measured.

The owner requested broad implementation, review, issue updates and safe merges, with
explicit permission to use subagents. The repository was inspected through the GitHub
connector. At the start of this work there were no open issues or pull requests. The
uploaded archive's 418 file blobs and complete Git tree match main
`b8e072041f97314c6d4e8c00cbdd3dea8f208435` / tree
`17823dff30a1b3f039809168e1e829a3bd117be2`.

## Findings and approach

The newer experiments have engine implementations, source records, reproduction scripts
and CI gates. The integration gap is chiefly discovery and inspection: separate commands,
no queryable catalog, a small default demo, and a sealed-run console that summarizes
actions without a round-by-round state view. The roadmap also has no active issue queue.

Three approaches were considered: add another simulation family; build a new hosted
application; or connect the existing evidence workflow. This implementation chooses the
third. It makes the substantial existing work accessible, preserves deterministic
execution, and avoids adding service operations or a frontend build dependency. A new
scientific mechanism should follow a specific research question and declared controls.

## Deliverables

1. **Experiment catalog.** Provide stable identifiers, research questions, evidence status,
   source and readout paths, verification recipes and runnable entry points. Expose text
   and machine-readable JSON. Distinguish studies, exact analytical experiments and
   archived legacy material. Validate the catalog against shipped files and entry points.
   Commands must preserve each experiment's fresh-output and source-provenance rules.
2. **Visual run inspector.** Extend the self-contained lab HTML with deterministic
   per-round views of accepted actions, observed/public state, released audits and graph
   interactions where available. Preserve branch boundaries and integrity labels. The
   inspector must never synthesize hidden knowledge or treat a missing observation as
   an empty world. All ledger-derived text must remain inert in HTML/JavaScript.
3. **Operational inventory.** Add `chl monitor TARGET [--json]` as a read-only snapshot.
   Separate verified completed/failed runs, unsealed artifacts, and broken artifacts.
   Expose event progress and manifest status without claiming that an unsealed process
   is alive. A partial last record is uncommitted; a malformed complete record is broken.
   Only the sealed validation path earns the verified label. Never modify a ledger,
   resolve a provider, or infer complete usage from incomplete records.
4. **Direction and issue seeds.** Update the entry documentation and prioritized roadmap.
   Keep a small versioned issue-seed manifest with stable IDs, rationale, scope, acceptance
   and dependencies. Supply a read-only planning/validation mode and an explicitly
   invoked publishing path that deduplicates both open and closed issues. Do not reopen
   closed work or overwrite discussion. Seed concrete next work during this session.

## Constraints

- Preserve all original study/scenario/result bytes, scientific weights and policy identities.
- No live-provider execution, paid calls, study freezing, licensing or hook-trust changes.
- Keep the deterministic kernel and mechanism semantics unchanged; existing ledgers replay.
- Runtime observations never gain hidden truth, future audit reports or private information.
- Derived inspection data is explicitly a view, not new evidence or independent samples.
- All exported files use UTF-8 with explicit LF newlines and protect source artifacts.
- Use existing Python 3.12, Typer and standard-library infrastructure; no new dependencies.
- Publish through GitHub connector branches and draft PRs. Review and inspect exact-head
  Ubuntu/Windows CI before merging. Reconcile current main before every branch publication.

## Verification and risks

Regression tests must exercise output overwrites, missing/partial/corrupt artifacts,
branch identity, HTML escaping and reproducible view generation. Catalog tests must
detect stale paths and omitted experiment directories. Seeder tests must cover pagination,
closed issue dedupe, malformed plans and publication failures without claiming success.
Run package lint/types/full tests, all study validations, acceptance and the existing
research reproduction gates. Record the actual environment, counts and limits in the
handoff and PR evidence; a green earlier commit is not verification of a later change.

The main risk is making polished presentation look scientifically stronger than the
evidence. Each interface therefore distinguishes a declared design, executed synthetic
finding, verification rerun, incomplete run and owner decision.
