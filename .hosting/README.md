# Collaborative Hill hosting reference

Reference-only preparation, 2026-09-10. `manifest.json` is inert agent-intake metadata. No mechanism, ledger, dataset, paid provider, study state, name, domain or deployment trigger changes here. Existing workflows, if any, still apply after a future merge.

Keep the laboratory local or batch-run. A selected research report or synthetic demonstration can be published as static files without hosting the simulation engine. CH1 defines an explicit artifact allowlist with provenance, scope and limitations. Never upload the repository or an entire raw-run directory as a website.

CH2 preserves deterministic mechanisms, exact/hash-sensitive representations, sealed-ledger custody, replay and hidden-truth separation. No convenience hosting adapter may introduce global randomness, alter experiment semantics or silently repair invalid agent output. CH3 keeps paid providers, human-subject data and study freezing behind their existing independent owner gates. Publication is not permission to run a new experiment.

Follow `CLAUDE.md`, `AGENTS.md`, the current handoff and existing research decisions. No new harness or executable prompt system is added. Use synthetic fixtures only. Syntax: `python -m json.tool .hosting/manifest.json`. The existing local proving gate is `make check`; reports/ledgers need the current acceptance and replay checks as applicable. The repository guide reports no CI, so do not substitute an imaginary green workflow for those local results.

JSON validation is not scientific, rendering or hosted acceptance. Record actual commands, fixture identities and outputs in the appropriate ledger. Preserve a previous reviewed report/build before publication and keep private operational receipts, credentials and unregistered naming candidates out of this public repository.
