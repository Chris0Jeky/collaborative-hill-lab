# Inspect run health without changing evidence

`chl monitor` gives people and agents a read-only snapshot of an artifact directory:

```bash
chl monitor artifacts
chl monitor artifacts --json
chl monitor artifacts/DRAFT-<hash>/<condition>/<run-id> --json
```

With an unactivated environment, use `.venv/bin/python -m collaborative_hill.cli`
on POSIX or `.venv/Scripts/python.exe -m collaborative_hill.cli` on Windows in
place of `chl`. No provider or policy is constructed, no replay is executed, and
no source file is written. Repeat the command to obtain another snapshot.

## Read the states correctly

| State | Meaning | Next action |
|---|---|---|
| `completed` | The completed seal, event chain, scenario and branch bindings pass the existing sealed-run validator. | Use `chl lab` for behavior or `chl replay` for deterministic re-execution. |
| `failed` | A valid sealed run records failure. This is an observed failure, not automatically corrupted evidence. | Read `failure_reason`; preserve the run when changing the design or retrying. |
| `unsealed` | Artifacts exist but do not yet establish a finalized run. This includes reservations, unfinished ledgers and final-manifest transitions. | Check the execution process separately; repeat the snapshot or inspect an interrupted run. |
| `broken` | The observed complete records, manifest or sealed bindings fail validation. | Inspect the indicated error; never repair the original evidence in place. |

An unsealed manifest saying `running` does **not** establish process liveness. A
crashed process can leave exactly the same artifacts. The `process_alive` field
is therefore always `null`. Monitoring does not estimate completion percentages,
remaining time or unrecorded provider usage.

Only complete newline-terminated records are checked in an unsealed ledger. The
bytes after its last newline are reported as `partial_record_bytes`, without
silently repairing or parsing an unfinished write. A malformed complete record
is broken. A finalized manifest with a truncated ledger is also broken. If the
observed files change while validation is running, the snapshot is downgraded to
unsealed with a request to repeat it. This is best-effort concurrent inspection,
not a transaction or an assertion that a writer has stopped.

## JSON contract for agents

The top-level `schema_version` is `chl-monitor@1`. `counts` contains all four
state names. `runs` is sorted by artifact path and includes each directory once,
even when it has both a manifest and ledger. Manifest-only and empty-ledger
reservations are visible. A single run target has path `.`; a collection uses
paths relative to that collection. Equal default run IDs remain separate rows.

Each row contains the displayed study/condition/run IDs, `manifest_status`,
`status`, `integrity`, `event_count`, `last_seq`, `logical_time`,
`last_event_type`, `last_event_hash`, `partial_record_bytes`, `failure_reason`,
`process_alive` and `detail`. An absent last event uses null progress fields.
Logical time is the engine's zero-based round/boundary value, not elapsed time.

| Integrity value | Scope |
|---|---|
| `sealed_validated` | Full existing seal, scenario and branch validation; replay was not run. |
| `prefix_hashes_only` | Complete unsealed event records have valid hashes and basic ordering. Manifest labels and scenario bindings are not certified. |
| `not_checked` | No complete record, or the files changed during the snapshot. |
| `broken` | The snapshot failed its applicable checks. |

Exit code **0** means no failed or broken record was observed; it can include
unsealed records. Exit code **1** means at least one failed or broken record was
observed. Exit code **2** means an invalid/unreadable target or no run artifacts.
JSON remains valid on exit 1, so automation can consume the inventory before
deciding whether to investigate. Exit-2 errors go to stderr.

These are operational observations, not independent scientific samples or new
research results. A valid hash chain establishes consistency with recorded
content, not authenticity of the source or correctness of a scientific claim.
