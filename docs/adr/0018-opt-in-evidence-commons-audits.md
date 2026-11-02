# ADR-0018 — Opt-in Evidence Commons audits with scheduled public reports

Status: **accepted design for implementation** (2026-11-02). This document
precedes audit-enabled execution. It specifies issue #103's runtime integration;
the separately committed audit experiment design supplies its finite population,
literal predictions and reporting plan. It does not assert measured benefits.

## Context and alternatives

ADR-0013 establishes that evidence provenance and source counts do not reveal
truth. ADR-0017 defines `ec-audit-observation@1`, a standalone projection contract,
and six gates before enabling a truth-correlated public signal. Its original
prototype and noisy-corpus evidence remain byte-identical.

Adding an optional `audit=None` field to the existing institution would change
its default serialization and every mechanism hash that includes that model.
A new world kind would avoid this, but an observation-only institution does not
change the underlying world or action rules. We choose a required-audit
institution subtype, a separate EC v3 implementation, and an optional runner
phase before observations. Existing institutions and the EC v2 implementation
keep their fields, serialized shapes, observations and behavior.

Pre-sampling all findings into world state was also considered. We instead
generate a finding only when its publication round begins. Checkpoints never
contain future verdicts, and branches reconstruct unpublished findings from
unchanged keyed streams when due.

## 1. Explicit configuration and version selection

`AuditInstitutionConfig` extends the two-field `InstitutionConfig` with one
required field, `audit: AuditMechanismConfig`. `ScenarioSpec.institution` accepts
the audited subtype first and the legacy base second. Legacy default/explicit
institutions serialize exactly as before. An explicit null audit is invalid.

The audit setting contains two required strict models:

| Setting | Meaning |
|---|---|
| `contract` | The complete unchanged `AuditConfig` schema from ADR-0017 |
| `generation.generator_version` | Exactly `ec-audit-generator@1` |
| `generation.unavailable_probability` | Canonical rational string in `[0,1]` |
| `generation.draw_dependence` | Exactly `independent-per-target` |
| `generation.unavailable_dependence` | Exactly `independent-of-truth-source-errors-and-correctness` |

Accuracy remains `contract.accuracy`; there is no second accuracy parameter.
All additional fields, unknown versions, floats, bools and implicit scalar
coercions are rejected. Probability strings must equal their canonical
`Fraction` representation. Python construction uses typed models/tuples; JSON
arrays are accepted through JSON validation. Tests distinguish these input paths
without relaxing scalar strictness or changing the original contract.

Compilation/construction additionally requires:

- The world is `ECWorld`, with commons interaction and the existing valid corpus.
- Each scheduled slot exists and its proposition belongs to that slot.
- Each publication round is less than `world.params.rounds`.
- Each `(slot_id, proposition_id)` occurs at most once, as ADR-0017 requires.
- Audit ID and targeted slot/proposition IDs contain no reserved seed separator.
  Invalid seed components fail before run artifacts can be created.

The presence of this valid required audit setting explicitly selects
`AuditedEvidenceCommonsMechanism`, `EC_AUDIT_ENGINE_VERSION = 3`. Existing
institutions continue to select the unchanged `EC_ENGINE_VERSION = 2`.
Audited observations carry `observation_schema_version=3` and the versioned
audit envelope; legacy observation dictionaries gain no field.

The existing mechanism view hashes the complete institution, including both
contract and generation configuration, and selects engine version 3 only for
the audited subtype. The scenario hash consequently changes. Narrative and
evidence-corpus hashes do not change merely because an audit setting changes.
The existing `contract_hash` continues to cover only the public observation
contract; the mechanism hash additionally binds the generation law.

## 2. Exact synthetic generation law

For target `j`, let `T_j` be whether its proposition is true, `a` the configured
accuracy, and `u` the configured unavailable probability. Draw independently:

```text
U_j ~ Bernoulli(u)       # unavailable
C_j ~ Bernoulli(a)       # correct when available
```

All availability and correctness draws are mutually independent across targets
and independent of truth and source errors in this declared synthetic model.
This is a new explicit generation assumption; it was not implied by ADR-0017's
observation contract. Verdicts for different candidate propositions need not be
marginally independent, because their truth values can be related.

If `U_j` is true, publish `unavailable`. Otherwise publish `positive` exactly
when `T_j == C_j`, and `negative` otherwise. Thus:

| Target truth | Positive | Negative | Unavailable |
|---|---:|---:|---:|
| True | `(1-u)*a` | `(1-u)*(1-a)` | `u` |
| False | `(1-u)*(1-a)` | `(1-u)*a` | `u` |

Use `rng.randrange(p.denominator) < p.numerator` for each exact rational
Bernoulli draw. There is no float threshold, global RNG or persisted RNG state.
Skipping an unnecessary correctness draw for an unavailable result cannot
affect another draw because the purposes have separate keyed streams.

Only typed trusted audit code consults the world's truth map. The pure sampler
receives a boolean `target_is_true`, the public settings/target and supplied RNGs;
it returns only an `AuditFinding`. Neither a policy nor a public report receives
the map, correctness/unavailability draw bits, source-error flags, latent
explanations, scores or confidence estimates. The report's `unavailable` verdict
is the intentional public availability signal.

Accuracy 1 is a perfect synthetic oracle assumption, not calibrated accuracy of
people, tools, sources or deployed verification. Empirical outcome frequencies
are not a proof of the declared probability law; exact experiment expectations
must use the separately specified finite outcomes and their rational masses.

## 3. Runner seam, keys and publication order

The optional typed mechanism method is:

```python
prepare_round(
    state: dict[str, Any],
    rng_for_key: Callable[[SeedPath], random.Random],
) -> tuple[dict[str, Any], list[dict[str, Any]]]
```

The runner invokes it after the terminal check and before every observation for
the current round. It supplies a stateless factory with this prefix:

```text
(*config.seed_root, "mechanism", "round-opening", *key)
```

Each audit key is:

```text
("ec-audit-generator@1", "ec-audit-observation@1", audit_id,
 slot_id, proposition_id, purpose)
# purpose is exactly "availability" or "verdict"
```

There is no implicit round in the factory prefix. Keys exclude publication
round, schedule position, contract hash, policy root and child run ID. Adding
another target, reordering the schedule, moving publication, or changing a
policy therefore cannot reroll an existing target with the same mechanism root.
Branches retain that root. Existing policy and resolution streams are unchanged.
Different condition-specific mechanism roots do not promise common audit draws.

Optional dispatch uses `getattr`/`hasattr` plus a typed cast, preserving the
current replay boundary adapter's dynamic forwarding. A runtime-checkable
protocol test would miss methods forwarded through `_RoundBoundary.__getattr__`
under Python 3.12. The terminal check precedes preparation, so a replay segment
ending at round `t` does not publish round `t` before the child segment begins.

`prepare_round` produces a new state and sorted `AuditPublished` domain events.
The event payload is:

```text
contract_version, audit_id, contract_hash,
report: {slot_id, proposition_id, publish_round, verdict}
```

Each report exactly matches its public observation finding and is emitted once,
before any `ObservationIssued` in that round. Publication order is by round,
slot and proposition. Unavailable reports are emitted, never silently omitted.
At round `t`, preparation accepts exactly the findings scheduled before `t`
(the unprepared checkpoint state), or exactly the findings scheduled at or
before `t` (the already-prepared state). It rejects partial same-round batches,
missing older reports, future reports and duplicates. Preparation adds the
complete due batch atomically; repeated preparation of the already-prepared
state is idempotent.

## 4. State, observation and unchanged task rules

The audited subclass adds `audit_reports`, containing only already-published
findings, to the base state. It inherits unchanged legality, resolution,
acceptance and reward calculation. The base resolver's state copy preserves
these reports without granting them any task effect.

The production released-findings projector validates exactly the schedule
prefix due by the observed round. It rejects duplicates, unscheduled reports,
wrong publication rounds, missing due reports and future reports. Before the
first publication the audit envelope has an empty report list. All agents see
the same envelope, and reports persist. Observations return detached public
data so one caller cannot mutate the state or another agent's audit view.

The original full-schedule projector stays unchanged. Its fixtures remain an
independent reference for production envelope compatibility at each round.
Production code does not import an experiment script.

There is no audit action, implicit audit effort charge, budget change, evidence
creation, automatic retraction, acceptance gate, credit change or sanction.
Fixed accepted action schedules must retain identical final briefing, budgets,
effort, quality, total credit and utility with audit off/on. Observation and
chain hashes may differ because the auxiliary signal is intentional. A service
cost or sanction would require a further explicit versioned design.

## 5. Replay, branching and policy boundary

Checkpoint state contains published findings only. A branch at a publication
round's checkpoint generates that round's finding from its inherited root; a
branch after publication retains the existing finding. Full replay reconstructs
every segment without copying future verdicts or consulting ancestor paths.
Tests cover forks before, at and after publication, plus failure on a publication
round. No provider call is needed to generate or replay audits.

The new `ec_audit_veto_contributor@1` wraps the unchanged
`ECSkepticalContributorPolicy` selection with the same parameter defaults:
`min_sources=2`, `peer_threshold="1/2"`, `warmup_rounds=3`,
`share_evidence=True`. Its exact public identifier/parameter contract belongs
to the policy implementation and separate experiment design.

After validating any present audit envelope, it obtains the baseline proposal.
Only a selected `ProposeClaimAction` or `VerifyClaimAction` is changed to
`WithholdAction`, and only if a matching
published `(slot, proposition)` report is `negative`. There is no reranking.
Inspection, sharing and challenge priorities remain unchanged. Positive,
unavailable, absent and pending reports preserve the baseline choice; audits
are never citations. This rule uses observations only and has no latent memory.
It does not receive the generator or hidden truth and does not calibrate audit
accuracy. Existing policies and their identifiers remain byte-identical.

## 6. Required verification and experimental boundaries

The six ADR-0017 gates are implemented and assessed separately:

1. Strict opt-in config, candidate/horizon checks, engine/observation routing and
   full hash binding; literal legacy dumps, hashes and observations unchanged.
2. The exact generator above; hand-derived rational boundary/interior oracles,
   independent outcome enumeration and isolated seed-purpose/target checks.
3. Pre-observation publication, public allowlists, no future findings, detached
   identical all-agent views, checkpoint/replay/branch/failure support.
4. A separately versioned negative-only veto wrapper with baseline purity and
   no implicit audit retraction, evidence, acceptance or budget authority.
5. Integrated fixed-action C3; truth-flip observation equality before differing
   reports; later direct channel differences confined to audit reports under
   fixed actions; whole-ledger leaks and legacy literal regressions.
6. A separately committed audit-enabled experiment design and predictions,
   followed by exact/retained negative and zero outcomes, explicit missingness,
   selective accuracy, coverage, signed quality, effort and utility at declared
   placeholder action costs. No selection of final weights, freeze or paid run.

Reactive policies may change subsequent actions after different reports; C3
and direct truth-channel isolation therefore compare fixed accepted actions,
not two unrestricted trajectories that have already diverged.

## Implementation sequence and review focus

The runtime design is committed and published before audit-enabled episode
execution. Pure schema/generator tests may precede that publication; the audit
experiment additionally requires its own pre-execution design and source pin.

- Add failing strict model, sampler and released-projection tests, then implement
  `domain/audit.py`. Check compatibility against the unchanged contract fixture,
  both Python-tuple and JSON-array inputs, canonical rationals and exact masses.
- Add failing routing/legacy-hash tests, then add the required institution subtype,
  compiler selection and `domain/world/audited_evidence_commons.py`. Check audit
  subtype round trips, null-audit rejection, target/horizon validation and seed
  separators without running an episode before the publication gate.
- Integrate the separately owned runner hook/event enum and replay/branch tests.
  Check round-zero publication, exact fork-boundary preparation, old/future state
  rejection, repeated preparation and publication-round policy failure.
- Integrate the separately owned veto policy and experimental design. Verify the
  committed source, full existing suite and relevant byte-exact historical gates
  before treating any runtime or experimental claim as established.

The highest review risks are subtype serialization dropping audit fields, strict
Python versus JSON container handling, a replay wrapper silently losing the
optional hook, checkpoint timing publishing a verdict twice or too soon, and
unhashed displayed institution metadata disagreeing with the resolved audited
configuration. These require explicit regression cases, not only happy-path runs.
