# Offline counterfactual workflow

This exploratory engineering workflow changes one agent's policy at a sealed
checkpoint, replays the resulting branch and compares the outcomes. It does not
freeze a study, call a model provider or establish a scientific treatment effect.

## Complete demonstration

After `make setup`, run:

```bash
.venv/bin/python scripts/counterfactual_demo.py --out artifacts/counterfactual-demo
```

On Windows use `.venv/Scripts/python.exe`. The output directory must not exist;
previous results are never overwritten, including when the existing directory is
empty. A failed run retains its partial artifacts for diagnosis; use another fresh
directory after correcting the error.

The demonstration runs one unmodified condition from each shipped study:
`pw-3tft` (N-IPD) and `attr-ledger` (Evidence Commons). Each produces a parent,
child and grandchild. It changes agent a3 to AllD in N-IPD and to a contributor
in Evidence Commons, then explicitly retains that policy in the second branch.
Every run is replay-verified. `summary.json` contains replay reports, relative
run directories, fresh metrics, exact utility differences, and the first changed
action; `README.md` gives a small outcome table.

The second branch should preserve actions and outcomes: changing a run ID changes
event hashes, not behavior. This is a useful control against confusing a different
hash chain with a different simulation trajectory.

## Inspect two existing runs

```bash
.venv/bin/python -m collaborative_hill.cli compare LEFT_RUN RIGHT_RUN
.venv/bin/python -m collaborative_hill.cli compare LEFT_RUN RIGHT_RUN --verify-replay
```

The command prints deterministic JSON to stdout and never writes to either input.
It validates the event chains, terminal seals, manifest bindings, resolved scenario
hashes and available branch provenance. It recomputes metrics in memory rather
than trusting or replacing `metrics.json` caches. `--verify-replay` additionally
re-executes both runs using temporary output outside the source directories and
includes the resulting reports. Provider sampling is never repeated.

Both runs must have the same mechanism hash. Different rules or units require a
separately specified analysis; the command refuses them rather than silently
comparing incompatible numbers. Scenario/narrative differences remain visible.

`utility_delta` is **right minus left**, encoded as exact rational strings. It
covers the entire episode, including shared pre-fork history. Failed episodes
retain operational metrics but have no outcome vector or utility delta.
`first_action_difference` compares proposed actions by round and agent, separately
from the common hash-linked prefix; policy rationale text is not an action.

## Branching and replay boundaries

Use the existing `chl branch` command with an available checkpoint sequence and a
fresh output directory. Checkpoint state must match the following sealed boundary,
not just its own recomputed hash. Child IDs must differ from all ancestor IDs.

Nested branches require explicit resupply of inherited non-original policies.
Policy IDs are descriptive labels, not sufficient data to reconstruct arbitrary
Python policy objects or provider memory. Refusal is preferable to silently
restoring a root scenario policy. A branch made at a final checkpoint can replay,
but branching its inherited terminal checkpoint again is rejected before writes:
the copied prefix would otherwise contain no event belonging to the direct parent.

Replay reconstructs all ancestral segments from recorded proposals; it does not
need the original parent directories or input checkpoint files. It checks engine
transitions given those actions, not the authenticity of policy implementations,
provider sampling or arbitrary provider exceptions. Hash commitments detect
inconsistency relative to a retained commitment; they are not signatures against
someone who can rewrite all artifacts.

Equal kernel stream paths do not guarantee equal actions, equal draw consumption,
paired provider randomness or reduced variance. These two-episode comparisons
are descriptive diagnostics, not p-values, confidence intervals, population
estimates or claims about human communities. Child token/cost measurements remain
null when unmeasured, rather than inheriting the parent's totals.
