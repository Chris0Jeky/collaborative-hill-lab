# Compare two recorded runs

`chl compare` keeps its existing descriptive JSON on stdout. Add `--out` to
create a self-contained HTML comparison from those same verified artifacts:

```bash
chl compare path/to/left-run path/to/right-run
chl compare path/to/left-run path/to/right-run --out artifacts/comparison.html
chl compare path/to/parent path/to/child --verify-replay --out artifacts/branch.html
```

Open the new HTML file locally. It needs no server, network connection or extra
browser library. Select a logical round and agent to inspect the aligned panels.
Without JavaScript, all recorded rounds and agents remain readable. The page
includes the original JSON, and exporting does not change the JSON printed by
the command.

## What the page establishes

- **Two explicit sources.** Left and Right retain their directory, study,
  condition, run label, status and full final event hash. Duplicate default run
  IDs do not collapse the sources or imply independent replicates.
- **Compatibility before interpretation.** The existing comparator requires the
  same mechanism hash. The table also shows scenario, narrative, evidence,
  effective policy labels, seed protocol, recorded seed roots and scenario block.
  Differences are flagged as confounds. Evidence belongs to mechanism identity,
  so a changed evidence corpus is rejected rather than presented as compatible.
- **Recorded ancestry.** Common leading event hashes, each branch's parent label,
  fork event/hash and continuation round remain explicit. Every inherited event
  is labelled. Equal prefixes can also arise from repeated deterministic runs;
  prefix equality alone does not identify a parent-child relationship. Parent
  paths are not followed.
- **Exact existing results.** Utility deltas are Right minus Left for the entire
  episode, including common pre-fork history. Fractions remain exact. Failed
  episodes have no outcome delta. The original comparison JSON retains its
  operational metrics and first proposed-action difference.
- **Aligned recorded events.** Logical rounds use their actual zero-based values,
  including unresolved and terminal-only times. Agent observations precede
  actions; public audits, later outcomes and seals have a separate researcher
  section. Missing frames or events are shown explicitly, never carried forward.
  “Payloads match/differ” compares event types and payloads in order, excluding
  event envelope hashes and run IDs; it adds no metric or inference.

Seal, manifest and resolved-scenario consistency are always validated.
`--verify-replay` additionally re-executes recorded actions and checks both
chains. Replay remains offline and does not call providers. Policy labels name
configuration, not authenticated executable code. Equal kernel streams normalize
integer/string seed aliases and use the mechanism root when no separate policy
root is recorded; they do not establish matched provider sampling or variance.
Two episodes provide no statistical or causal estimate and no prediction about
people or live LLM populations.

## Export and implementation boundaries

The destination must be a new file outside **both** source evidence directories.
Resolved symlink aliases are checked, existing files and dangling symlinks are
refused, and exclusive creation protects an output that appears just before the
write. Sources are read only; parents of a valid fresh destination are created
after comparison succeeds. Destination ancestry remains pinned while rendering,
so replacing a parent path cannot redirect the write into either source. Do not
use shell redirection into either source.

The HTML is a reporting projection, using the existing comparison result and the
inspector's `round_frames` from the same validated event snapshot. It does not
reconstruct private checkpoint state or include unhashed event metadata. Dynamic
text is HTML-escaped; filters use only local DOM properties and text content.
Static panels were chosen over another application or analysis layer to keep
the evidence boundary small and the exported file useful offline.

Focused verification:

```bash
python -m pytest tests/metamorphic/test_run_comparison.py tests/metamorphic/test_comparison_view.py
```

Fixtures cover literal matched controls and branch deltas, duplicate default
IDs, scenario/policy/seed differences, evidence/mechanism rejection, failed and
missing frames, hostile identities/payloads, exclusive output creation, symlink
aliases, concurrent parent replacement and byte-for-byte source preservation. Full integration and browser
verification remain part of the repository's review and CI gate.
