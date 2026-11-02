# ADR-0017 — Declared noisy corpora and a separate audit observation contract

Status: **accepted for offline experiment and contract foundation** (2026-11-02).
Audit-enabled EC engine integration remains **proposed, not implemented**. This
decision addresses issue #96 after ADR-0013 and preserves all existing mechanism,
policy, scenario and experiment identities.

## Context

The skeptical contributor reads evidence structure. It cannot infer truth from
identical observations, and engine verification checks provenance rather than
truth. The quality-safeguards results deliberately supplied no probability model
linking observable structure to truth. A corpus model can supply such a link as
an explicit synthetic assumption. Truth feedback during an episode instead
requires a new observation channel with its own timing, trust and accuracy
contract. Neither follows from using more source labels.

## Decision 1: separate exact noisy-corpus experiment

`experiments/noisy-corpus/DESIGN.md` declares the complete finite grid before any
execution. It enumerates binary truth and three binary reports, uses unchanged
conditional and skeptical version-1 policies, and reports exact expectations at
six declared error rates under independent and perfectly correlated errors.
The `1/2` truth mixture is explicitly synthetic; conditional-on-truth expectations
check label symmetry. A distinct/collapsed source-label control separates visible
labels from the generator's dependence assumption. Every finite outcome remains
available, even when its probability is zero at some rates.

No empirical frequency, independent-replication count, selected best corpus,
general-benefit claim or final reward choice is inferred. Existing results stay
byte-identical. The experiment does not need an engine change or an audit channel.

## Decision 2: `ec-audit-observation@1`

Implement a standalone strict contract and projection prototype inside the new
experiment. Its inputs and outputs are JSON-safe, versioned and hashable. It is
not registered with `ScenarioSpec`, `InstitutionConfig`, the runner or policies.
The only implemented artifact is validation plus a pure public projection.

### Configuration and trust boundary

The contract configuration contains these fields:

| Field | Version-1 meaning |
|---|---|
| `contract_version` | Exactly `ec-audit-observation@1` |
| `audit_id` | Nonempty public identifier of this audit channel |
| `accuracy` | Canonical exact rational string in `[0,1]` |
| `accuracy_semantics` | Exactly `symmetric-conditional-on-availability` |
| `oracle_kind` | Exactly `synthetic-trusted-oracle` |
| `dependence` | Exactly `independent-of-source-errors` |
| `visibility` | Exactly `public` |
| `selection` | Exactly `fixed-ex-ante-targets` |
| `unavailable_semantics` | Exactly `explicit-no-verdict` |
| `schedule` | Nonempty unique targets `(slot_id, proposition_id, publish_round)` |

`accuracy=a` means `P(positive | target proposition true, available)=a` and
`P(negative | target proposition false, available)=a`. The complementary
probabilities give the wrong verdict. Accuracy 1 is a perfect **synthetic
trusted-oracle assumption**. It is not established accuracy of people, tools,
sources or deployed verification. The prototype validates this declaration;
it does not estimate accuracy or attest that supplied findings satisfy it.

This v1 contract assumes that available audit errors are independent of source
errors, conditional on truth; that assumption requires justification or a new
declared model in any later experiment. It does not assert independence between
different audit targets. The prototype has no stochastic generator or empirical
calibration. Unavailability is explicit and its generation must be separately
declared in an integrated experiment; the schema alone supplies no missingness
rate or missing-at-random guarantee.

Targets and publication rounds are set before the episode, independent of claims
or actions. Each `(slot, proposition)` is targeted at most once in this version.
IDs and rounds must be nonempty strings/nonnegative integers; bools, floats,
coercions, noncanonical rational strings and extra fields are rejected. Integration
must additionally bind targets to the scenario's candidate propositions and
require `publish_round < rounds`, so a scheduled signal can be observed.

### Public report and timing

A supplied finding identifies exactly one scheduled target and contains only
`slot_id`, `proposition_id`, `publish_round`, and
`verdict in {positive, negative, unavailable}`. Findings must cover the schedule
exactly once. An unavailable result is still a report; omission is an input error,
not silent negative evidence.

`project(config, findings, round)` returns a public audit envelope containing
`contract_version`, `audit_id`, `contract_hash`, and `reports`. `reports` contains
only scheduled entries with `publish_round <= round`, sorted by publication round,
slot and proposition. Before publication the target's verdict is absent. At
publication every agent receives the same report, which persists afterward.
Findings carry no source error bit, world truth map, true-proposition field,
`truth_aligned`, score, hidden explanation, confidence estimate or agent identity.
The envelope is a new auxiliary observation field in a future integration,
never an overwrite of evidence, existing verification or reward fields.

`contract_hash` covers the full validated public configuration, including timing,
accuracy and selection. Any changed contract parameter changes this identity.
The scenario mechanism hash must cover that identity in a future integration;
the prototype's hash alone does not make it an engine-bound channel.

### Future generation, events and C3 obligations

An integrated audit engine may consult environment truth only within a typed
trusted audit generator. Existing policies never receive hidden truth fields or
the generator. The public verdict is the sole intentional truth-correlated signal.
Generation must use a separate deterministic seed path containing the channel
version, `audit_id`, slot and proposition; adding another consumer must not shift
old outcomes. The declared accuracy and missingness model must use exact rational
sampling without global RNG. Replays and branches must reconstruct the same
already-public findings without provider calls or rerolling.

A future `AuditPublished` domain event must match the public finding exactly and
be emitted once at the start of its publication round, before any observations
for that round. It must never dump the environment truth or unredacted internal
generation inputs. Audits have no implicit world-state, legal-action, acceptance,
credit or effort effect in this contract; they change observations only. A future
cost, sanction, acceptance gate or endogenous selection rule needs another
versioned design and its own task-invariance analysis.

For identical accepted action schedules, audit on/off must preserve final
briefing, budgets, effort, quality, total credit and utility. Full observations
and event-chain hashes may differ because the new public signal is intentional.
Truth-flip observations must stay identical before the first differing audit;
any later difference must be confined to the declared public audit reports.
This is the required C3-style gate for integration. The standalone projector's
nonmutation test is narrower and must never be described as that engine gate.

## Compatibility and remaining integration gates

The legacy engine remains `EC_ENGINE_VERSION=2` and legacy observation dictionaries
remain byte-identical. Audit integration must explicitly select a new EC engine
version (planned v3) plus `ec-audit-observation@1`; compiler routing must preserve
v2 for existing no-audit scenarios. A global constant bump that silently changes
all existing hashes would violate this decision. If this needs a separate world
kind or version selector, that routing is part of the integration work.

Before any audit-enabled episode or claim, all of the following remain necessary:

1. Explicit opt-in institution/scenario fields, candidate/horizon validation,
   mechanism/observation version selection and hash binding, preserving v2 inputs.
2. A declared exact audit error and unavailability generator, dependency model,
   deterministic seed paths, and trusted internal truth access isolated from policy.
3. Engine timing, public event type, identical all-agent projection, checkpoint,
   replay and branch support with no new hidden-field leaks.
4. A separately versioned observation-driven audit policy (if any), with no
   hidden state and no alteration of the skeptical version-1 baseline.
5. C3 action-fixed task invariance, truth-flip timing isolation, malformed-input,
   all-ledger leak, seed, replay, branching and legacy-hash regression tests.
6. A separately committed design for audit-enabled experiments with declared
   timing, error, dependence and missingness parameters, costs if any, negative
   controls, and honest distinction between toy oracle and deployed verification.

## Verification for this foundation

Tests will check strict exact probability parsing, unknown versions and fields,
invalid IDs/rounds, duplicate/unscheduled/missing findings, fixed timing,
unavailable reports, hash sensitivity, public allowlists and deterministic pure
projection. The noisy-corpus experiment separately checks complete typed action
schedules against hand-derived literals, exact world masses and metrics against
an independent algebraic oracle, truth-flip observation identity, C3 accounting
controls, full replay and byte-identical reproduction. No deployed audit accuracy,
learning, provider behavior, new equilibrium or real-world effect is verified.
