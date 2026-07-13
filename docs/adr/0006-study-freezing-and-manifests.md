# ADR-0006 — Human-gated study freezing; exhaustive run manifests

Status: **accepted** (2026-07-13)

## Context

Preregistration only binds if the frozen object is content-addressed and changes are
detectable; runs are only attributable if every input identity is recorded. Locked
principle 7 requires human approval before any freeze or paid study.

## Decision

- Lifecycle: draft → validated → frozen → running → sealed → analysed → published.
  `chl study validate` computes the study hash (`chl.study.v1` over design parameters +
  per-condition scenario hashes). `chl study freeze --yes` writes `study.lock.json`; the
  `--yes` flag is the explicit human step and is NEVER run by agents (Study 001 ships
  unfrozen by design). Running a study whose content diverges from its lock file is a hard
  error: a frozen study is immutable; changes create a new version (new hash).
- Smoke/exploratory runs of unfrozen studies are allowed; the manifest records
  `study_frozen: false`, so sealed science is distinguishable from exploration.
- `RunManifest` records: study id/hash/frozen flag, condition, replicate, scenario/
  mechanism/narrative/evidence hashes, institution config, code commit + dirty flag,
  python + platform, dependency lock hash, per-agent policy ids, provider model ids,
  prompt-template hashes, sampling params, seed root, checkpoint cadence, invalid-action
  policy, scorer (metric) versions, pricing-table version/date, token counts, cost,
  start/end timestamps, parent run + fork binding for branches, final status.
  **Unmeasured values are None — token counts and costs are never fabricated** (tested).

## Consequences

- Every reported number is traceable to (study hash, run set, metric version, code commit).
- Provider drift across time is visible in manifests without any extra machinery.
- A dirty worktree is recorded, not forbidden — but sealed publication-grade runs should
  come from clean commits (stated in METHODOLOGY.md).
