# ADR-0009 — Self-contained counterfactual replay

Status: accepted for the engineering implementation, 2026-10-22.
Extends ADR-0002 without changing its copied-prefix ledger format.

## Problem

A branch ledger contains a parent prefix and a child suffix. Replaying the whole
ledger under the child's run ID changes the first event hash. Replaying the root
under its own ID also emits checkpoint markers that the fork intentionally omits.
Checkpoint self-hashes alone do not establish that a snapshot belongs to the
chosen ledger boundary. Rebuilding a nested branch from the root scenario can
silently discard its parent's policy overrides.

## Decision

Replay each contiguous run-ID segment with the recorded proposals. Stop an
ancestral segment at the next segment's round, verify the recomputed prefix, and
resume from the recomputed state. Remove only the temporary completion seal that
this boundary adapter generates. Never copy input events as replay evidence and
never load input checkpoints or follow parent directory paths during replay.

Before branching, validate the parent seal, manifest pins, scenario hashes and
seed bindings. Bind the checkpoint's sequence, parent hash, round and state hash
to the following sealed CheckpointCreated event (or the final RunCompleted state).
Reject reused ancestor run IDs before creating child artifacts.

New branch sidecars have schema version 2 and child manifests name the effective
policy labels. Legacy sidecars without a version remain readable. Labels are not
executable configurations: an inherited non-original policy must be supplied as
an explicit override when branching again. Refuse rather than silently restore
the root policy. This does not add general policy serialization or model memory.
Child usage and cost remain null because parent totals do not measure the child.

## Scope

No mechanism, seed allocation, scientific inputs or historical event format is
changed. Successful scripted N-IPD and Evidence Commons branches, nested branches,
terminal forks, and both seed protocols are covered. Replay validates deterministic
engine behavior given recorded actions; it does not reproduce model sampling or
arbitrary provider exceptions. Policy identity is descriptive metadata, not proof
of an executable's authenticity. Hash links provide consistency relative to a
retained commitment, not signatures against an actor who can rewrite everything.

The tests deliberately remove parent directories and input checkpoints before
replay, alter checkpoints while recomputing their self-hashes, protect occupied
outputs, and exercise invalid CLI inputs. Full-suite results and exact verification
commits are recorded in the pull request. No study is frozen or paid provider used.
