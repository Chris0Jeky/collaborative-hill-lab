# Original audit-feedback evidence

The original execution is retained in
`collaborative-hill-audit-feedback-original-evidence-2026-11-02.zip`.
It contains the original artifact tree, its complete file inventory, the
independent audit record, publication mapping and per-member SHA-256 checksums.
The archive is separate from verification regenerations and the Git checkout.

| Commitment | Value |
|---|---|
| Archive size | 1,515,408 bytes |
| Archive SHA-256 | `338f6a15611f4ae8d4db69140d44c857686ab633cda55489b346fab03ff36fe1` |
| Archive members | 952, including five archive-level metadata/checksum files |
| Original artifact files | 947 |
| Original artifact bytes | 10,283,384 |
| Original file-inventory digest | `4b7f21318c9e37789c4788ac534e588395d79efda41c0f019b9f51e73f795425` |
| Original terminal-hash inventory digest | `c81f363472fa631642868820a566c4f13c51d7049fb6b581c7ce2f853543b8a5` |

The [independent audit record](ORIGINAL_AUDIT.json) verifies 76 scientific runs,
four separate branch fixtures, all 80 chain replays and all 621 checkpoints.
There are 8,048 scientific events. The branch ledgers contain 409 records,
including copied prefixes; those records do not represent 409 additional
independent events or any additional scientific sample.

The auditor checked every manifest's original source commit, exact clean flag,
dependency lock, scenario identities, event count and completion seal. All
65 source digests matched Git blobs in the original execution commit. Read-only
recollection reproduced both readouts byte for byte, and the complete before/after
inventory confirmed that no original artifact was changed.

All P1–P8 held: 60 same-action comparisons, 42 truth controls and 720 exact
expectation rows. Those rows are reweightings of conditional trajectories under
a stated synthetic law; they are not additional sampled episodes.

## Public source commitments

The reviewed design was published at
[`a11a11f`](https://github.com/Chris0Jeky/collaborative-hill-lab/commit/a11a11feb8fd27dc619e237e60549de14c935f28)
before audit-enabled episode execution. The complete execution source was
published at
[`6727532`](https://github.com/Chris0Jeky/collaborative-hill-lab/commit/67275327133d00e161c38d2b56d1b21472927bcb)
before the original batch. Its tree is exactly
`d4494ee3557deb7ef6a4d736336070aae4c73373`, matching actual local execution commit
`ab9e3ec842c24ad12bc6b60b30a11843353df965`. The original manifests retain that
actual local commit; no provenance field was rewritten to the public commit.

[PUBLISHED_SOURCE.json](PUBLISHED_SOURCE.json) supplies the full correspondence
and original readout digests. [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json)
retains the measured execution environment and source-file commitments.
Hash commitments establish consistency relative to retained values; they do not
authenticate a record against wholesale replacement of files and commitments.
