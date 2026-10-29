# Study execution inputs

Study definitions are validated before a batch writes its first episode. The
original Study 000 and Study 001 definitions and content hashes are unchanged.

## Names and counts

Each `condition_id` is both part of the experiment's seed identity and an output
directory component. Use a nonempty portable name such as `nb-5ptft-incself`.
Absolute paths, directory separators, traversal components, control characters,
Windows-reserved names or characters, trailing dots, and surrounding whitespace
are rejected. IDs must be distinct even when compared without letter case.
Names are rejected rather than silently cleaned up, preserving seed identity.

A study must contain at least one condition. `replicates` is an integer of at
least one; `checkpoint_every` is a nonnegative integer, with zero meaning only a
final checkpoint. Booleans and numeric strings are not execution counts. The
same replicate rule applies to programmatic overrides, and the episode runner
checks its checkpoint cadence independently.

## Output preflight

Before starting, `run_study` checks every selected run destination:

- Its resolved path stays within the selected artifact root.
- Existing path components are directories, including any symlink targets.
- Two planned destinations neither resolve to the same directory nor contain
  one another.
- No run destination is occupied by an existing or partial episode.

An explicitly selected artifact root may itself be a symlink to a directory.
Existing empty run directories remain supported. Preflight errors preserve
existing files and avoid starting an earlier condition before a later static
path error is discovered. The CLI reports invalid configuration with exit code 2.

The runner rechecks each destination before reserving it. Reservation still
provides the existing exclusive-writer and cleanup behavior. These checks
describe the current filesystem layout: they are not a transaction against
another process swapping ancestor directories concurrently. No permission or
power-loss guarantee is inferred from a successful preflight.
