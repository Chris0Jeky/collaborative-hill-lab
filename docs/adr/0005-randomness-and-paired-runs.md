# ADR-0005 — Stateless hierarchical randomness; paired runs by construction

Status: **accepted** (2026-07-13)

## Context

The legacy code used process-global RNG (or none at all in the figure-generating scripts).
Global streams make paired comparisons impossible and let an unrelated new random call
shift every later draw. Serializing RNG state into checkpoints (MT19937's ~2.5 kB state) is
brittle; a counter-based generator (Philox) was considered.

## Decision

**No persistent RNG state exists anywhere.** Every random decision draws from a fresh
stream derived at the point of use from a seed PATH:

    (study_seed, condition_id, replicate, "agent", agent_id, "round", t)     # policy draws
    (study_seed, condition_id, replicate, "mechanism", "round", t)           # world draws

Derivation (`engine/seeds.py`): SHA-256 over the version-tagged (`chl-seed-v1`),
unit-separated path; components may not contain the separator (raises), so distinct paths
cannot collide by concatenation ambiguity. Streams are `random.Random(derived_seed)` —
Python's Mersenne generator is only ever used WITHIN one round's decision, so its state is
never persisted, which is why Philox's O(1) fast-forward is unnecessary: fast-forward is
trivial when every (agent, round) has its own stream.

Consequences for the science:

- **Paired runs by construction:** replicate r of two conditions shares every policy stream
  for unchanged agents (condition_id is in the path, so world-level draws differ across
  conditions — pairing applies to policy behaviour given identical observations; for the
  institution-only contrasts of Study 001 the observations coincide under identical
  behaviour, giving full pairing).
- **Branch counterfactuals:** a branched run keeps the parent's seed root; unchanged agents
  reproduce identical draws after the fork.
- Adding a new random consumer (new component name) cannot shift any existing stream.
- Checkpoints contain no RNG state at all — state completeness is trivially testable.

Changing the derivation scheme is a breaking change to every sealed run and requires a new
domain tag (`chl-seed-v2`) plus an update to this ADR.
