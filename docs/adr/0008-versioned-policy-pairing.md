# ADR-0008 — Versioned policy pairing without rewriting legacy runs

Status: **accepted** (2026-10-21). Corrects ADR-0005's cross-condition pairing claim;
preserves its stateless RNG derivation and legacy paths.

## Context and reproduced defect

ADR-0005, the methodology, and the Study 001 SAP claimed common random numbers (CRN)
across conditions. The actual runner derived policy streams from
`(study_seed, condition_id, replicate, "agent", agent_id, "round", t)`. Changing the
condition changes the stream. Reusing a replicate index alone does not create CRN.
Branch pairing was working because branches retained the entire parent root; that
test did not exercise two conditions through `run_study`.

Before changing the implementation, the same probe policy was run through the
shipped Study 001 pipeline. Its first `rng.getrandbits(64)` for agent `a1`, round 0,
replicate 0 was:

| Condition | Legacy draw |
|---|---|
| `agg-priv` | `14442509083846134711` |
| `agg-ledger` | `15968561580677346032` |
| `attr-priv` | `17485811729684596417` |
| `attr-ledger` | `2761447364641609127` |

These values are now regression literals in
`tests/integration/test_seed_protocol.py`. The shipped EC personas are deterministic
and do not consume this randomness, so their existing outcomes are not evidence that
the old cross-condition stream allocation was paired.

## Decision

### 1. Preserve and label the legacy protocol

An absent `seed_protocol`, or explicit `legacy-independent-v1`, means the exact old
paths, study hash payload, and `RunStarted` payload. Study 000 and the checked-in
Study 001 JSON stay unchanged. New manifests explicitly label the protocol; loading
an older manifest supplies the legacy label in memory, without rewriting the file.
Run and study reports label old manifests as legacy independent as well.

The SHA-256 primitive and `_DOMAIN_TAG = b"chl-seed-v1"` are unchanged. A future change
to that primitive still requires a new derivation tag as specified by ADR-0005.
The new decision here versions the **allocation of paths**, with its own domain
component, separately from the primitive that hashes those paths.

### 2. Opt in to `paired-policy-v2` in a new draft

Every condition must declare a non-empty `scenario_block`. There is no implicit
default block and no inference of scientific comparability from filenames or hashes.
The study author is responsible for matching comparable scenario populations and
agent identities. A block field under the legacy protocol is rejected so it cannot
suggest pairing while being ignored by the old hash/stream scheme.

The new paths are:

```text
# Policy stream, shared across conditions in the same declared block/replicate
(study_seed, "paired-policy-v2", "block", scenario_block, "replicate", r,
 "agent", agent_id, "round", t)

# Mechanism stream, condition-specific
(study_seed, "paired-policy-v2", "condition", condition_id, "replicate", r,
 "mechanism", "round", t)
```

`engine/seeds.py::study_seed_roots` is the common source of the two roots. The manifest
retains `seed_root` as the mechanism root and records `policy_seed_root`, `seed_protocol`,
and `scenario_block` separately. New `run_study` manifests have schema version 2. The runner binds
the new fields into the v2 `RunStarted` event. Replay and branch continuation use the
recorded protocol and roots; branches never derive fresh roots from a child's run ID.

The v2 study hash uses domain `chl.study.v2` and commits to both the protocol and the
condition-to-block mapping. Changing either produces a new study hash, so the existing
freeze guard refuses a changed frozen study. Legacy hashes retain domain `chl.study.v1`
and the complete original hash payload.

The Study 001 generator requires both `--seed-protocol paired-policy-v2` and a fresh
`--output` directory. It emits a new `001-evidence-commons-paired-v2` draft with the four
factorial cells in block `factorial` and the optional altered-population misinformation
arm in block `misinformation`. It cannot overwrite the original directory or any frozen
output. This is a reproducible exploratory configuration, not a preregistration freeze.
The original no-argument generator remains byte-identical for unfrozen legacy inputs;
it refuses to downgrade an existing paired draft to the legacy protocol.

### 3. State the scientific scope precisely

- Equal (block, replicate, agent, round) keys provide the same initial PRNG stream.
  The same sequence of RNG calls therefore produces matching draws. If a policy's
  observation-dependent control flow consumes draws differently within a round, the
  semantic uses of those draws need not align. Other agents and rounds are isolated.
- Matching draws do **not** imply matching observations, actions, or outcomes. The
  institution is itself visible in EC observations, and topology changes information
  visibility. Neither equality of observations nor complete behavioural pairing follows
  from an institution-only contrast.
- Mechanism streams remain condition-specific. This protocol pairs kernel policy
  randomness; it does not claim to couple all stochastic world dynamics.
- `LLMPolicy.propose` currently discards the kernel RNG. Provider sampling is therefore
  **not** coupled by this protocol. Recorded-action replay proves engine determinism
  given actions, not reproducibility or CRN of a model call. A provider pairing design
  needs its own supported controls and empirical checks before paired inference.
- CRN can change the covariance of outcomes; variance reduction is not guaranteed.
  Deterministic personas still supply no stochastic replication merely because their
  stream protocol changes. Historical independent runs cannot be relabelled paired.

## Verification and boundaries

`tests/integration/test_seed_protocol.py` exercises the real study entry point with
an observable stochastic policy and a test-only stochastic mechanism consumer:
same-block policy draws match across all four cells; different agents, rounds,
replicates, and blocks separate; mechanism draws stay condition-specific; replay
matches; branch prefixes and unchanged post-fork draws are preserved. Legacy study
hash and full-chain literals for both shipped studies guard against silent changes.
Old manifests without protocol fields still replay and remain untouched on disk. Replay,
branch, and reporting reject v2 manifest metadata that disagrees with the sealed start event,
including removal of all v2 fields; a paired run cannot silently become legacy.

Schema tests reject incomplete metadata. Generator tests reproduce the old JSON bytes,
run/replay the opted-in draft, refuse frozen/occupied outputs, and check the freeze
guard when a legacy lock is paired with a changed protocol.

No hypotheses, providers, utility weights, cost ceilings, or sample sizes are selected
or frozen by this change. No real-provider CRN claim is made.
