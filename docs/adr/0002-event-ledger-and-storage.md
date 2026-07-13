# ADR-0002 — Hash-linked JSONL event ledger; transparent file artifacts; copy-on-write branches

Status: **accepted** (2026-07-13)

## Context

Every run must be versioned, content-addressed, event-sourced, replayable, and attributable.
Two hazards found in review: (a) wall-clock/nondeterministic values leaking into hashes;
(b) the "branch prefix byte-identical" requirement conflicting with a per-run run_id inside
the hashed envelope.

## Decision

- Envelope: `{schema_version, study_id, run_id, seq, logical_time, actor, event_type,
  payload, parent_hash, event_hash, meta}`. `event_hash` = SHA-256 of the canonical JSON of
  the envelope MINUS `event_hash` and `meta`. `meta` is the only unhashed field (wall clock,
  durations, tokens). Floats are rejected in hashed content (`engine/hashing.py`); payoffs
  are exact fraction strings.
- Storage: `artifacts/<study_hash>/<condition>/<run_id>/` with `manifest.json`,
  `events.jsonl` (one canonical-JSON line per event), `checkpoints/ckpt-<seq>.json`,
  `metrics/`, `report.md`, `scenario.resolved.json` (self-contained replay). JSONL over a
  database: transparency beats premature scale; compression is a later, additive change.
- Branching: a child COPIES the parent's ledger lines `0..fork_seq` byte-for-byte
  (copy-on-write). Shared prefix events retain the PARENT's run_id — honest provenance:
  those events ARE the parent's history. The chain does not require run_id constancy; the
  child's first new event links from the parent hash at the fork, and `branch.json` +
  manifest record `parent_run`, `fork_seq`, and `parent_event_hash_at_fork`. Fork points
  are checkpoint boundaries only (small and correct over general and magical).
- Integrity is tamper-EVIDENT, not tamper-proof: anyone can rewrite a local file and rehash
  the chain end-to-end. The guarantees are (1) accidental corruption/edit detection and
  (2) binding of every event to study/scenario/code identity via the manifest. Stronger
  guarantees (signing, third-party anchoring) are out of scope at T1.

## Consequences

- Replay verification recomputes hashes over the hashed view; timestamps can differ freely.
- Branches are cryptographically bound to parents; prefix identity is structural, tested
  byte-for-byte.
- Large studies produce many small files — acceptable; DuckDB/Parquet derivations exist for
  analysis-scale reads.
