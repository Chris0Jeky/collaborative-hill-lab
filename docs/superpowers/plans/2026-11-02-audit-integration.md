# Opt-in Evidence Commons audits implementation plan

> **For agentic workers:** Use the executing-plans and test-driven-development workflows for each owned lane, followed by independent whole-branch review. Steps use checkboxes to record verified completion.

**Goal:** Complete issue #103 with a versioned audit mechanism, observation-driven policy and predeclared offline experiment, preserving every legacy scenario and original research artifact.

**Architecture:** An audit-bearing institution subtype selects a separate EC v3 mechanism. A typed optional round-opening hook receives runner-owned keyed randomness and publishes due findings before observations. The new negative-veto policy wraps the unchanged skeptical baseline; a separate exact experiment measures timing, accuracy and missingness effects.

**Tech stack:** Existing Python 3.12, Pydantic, Fraction, pytest/Hypothesis, Ruff/mypy and committed dependency lock. No new dependencies.

**Spec:** ADR-0017; `docs/adr/0018-opt-in-evidence-commons-audits.md`; `experiments/audit-feedback/DESIGN.md`. Issue #103 supplies the acceptance gates. The user authorized another autonomous implementation/review/merge pass; the implementation choices below are agent decisions within that scope.

## Global constraints

- Existing `InstitutionConfig` fields and defaults, EC v2 behavior, v1 policy implementations, study inputs and original experiment files remain byte-identical where possible; all legacy serializations, hashes and outcomes must remain identical.
- All probabilities are canonical exact rational strings. No floats or global RNG in hashed content or audit generation.
- All randomness comes from runner-supplied streams; no RNG state or unpublished verdict is stored in checkpoints.
- No hidden truth fields, correctness draws, future verdicts or private generator inputs enter observations or ledgers. The declared public verdict is the intentional truth-correlated signal.
- Audits only change observations: no legal-action override, implicit acceptance/retraction, fabricated citation, credit adjustment or service cost.
- Commit and publish the experimental design before audit-enabled episodes; commit and publish the experiment source before its original execution. Verification reruns never replace original artifacts.
- No live/paid provider calls, final weight selection or study freeze. Preserve the human-owned decision section and append to BUILD_LOG.

## Review focus

1. A checkpoint at round `t` precedes that round's audit publication: fork exactly at and after publication, then nested replay without ancestor files.
2. Python 3.12 runtime protocol detection misses `_RoundBoundary.__getattr__`: use attribute lookup plus a typed cast, and test the actual replay adapter.
3. Strict audit schemas must reject null opt-ins, bool/float/coerced IDs/rounds, extra fields, invalid probabilities, wrong candidates, out-of-horizon rounds and reserved seed separators before output creation.
4. Target addition/reordering and timing changes must not reroll existing findings under the same mechanism seed root; policy roots and child IDs must not affect audit generation.
5. Exact expectation mixtures must be labeled as mixtures of conditional trajectories; behavioral downstream divergence after feedback must not be mistaken for hidden information leakage. Bind displayed manifest audit settings to the canonical resolved configuration.

## Task 1: audit model and opt-in mechanism

**Owner:** audit-model lane.

**Files:** new `src/collaborative_hill/domain/audit.py`, new `src/collaborative_hill/domain/world/audited_evidence_commons.py`, additive changes to `domain/institutions.py` and `experiments/scenario.py`, focused unit tests, ADR-0018.

**Interfaces:**

- `AuditInstitutionConfig(InstitutionConfig)` adds required `audit: AuditMechanismConfig`; `ScenarioSpec.institution` accepts the audit subtype first, then the unchanged legacy base.
- `AuditMechanismConfig` contains the unchanged v1 observation-contract fields under `contract` and required versioned generation assumptions under `generation`.
- Generation has `generator_version="ec-audit-generator@1"`, `unavailable_probability`, `draw_dependence="independent-per-target"`, and `unavailable_dependence="independent-of-truth-source-errors-and-correctness"`.
- For each target, independently draw unavailability with probability `u` and correctness with probability `a`; when available, verdict is positive iff target truth equals correctness. Sample with `rng.randrange(denominator) < numerator`.
- Audit RNG key is `(generator_version, contract_version, audit_id, slot_id, proposition_id, purpose)` with purpose `availability` or `verdict`. It excludes config hashes, publication round, schedule position, run ID and policy roots.
- `prepare_round(state, rng_for_key)` returns new state and domain event dictionaries. Only released findings persist. `observe` supplies a cloned v1 audit envelope and `observation_schema_version=3`.

- [ ] Commit ADR-0018 separately before implementation.
- [ ] Write and observe failing tests for exact generation thresholds, strict schemas, staged publication, projection equivalence and compiler routing/hash isolation.
- [ ] Implement package schemas/generator and opt-in mechanism; leave the original standalone contract and base EC engine unchanged.
- [ ] Verify complete due-prefix coverage, idempotence, no future findings, event/report equality, direct-constructor validation and observation nonmutation.
- [ ] Run focused tests, Ruff and strict mypy; record commands and commit implementation.

## Task 2: kernel lifecycle and artifact integrity

**Owner:** root lane.

**Files:** `engine/interfaces.py`, `engine/runner.py`, `engine/events.py`, narrowly required `engine/validation.py` changes, new unit/integration/metamorphic tests and compatibility fixtures.

**Interfaces:**

- Optional `RoundOpeningMechanism.prepare_round(state: dict[str, Any], rng_for_key: Callable[[SeedPath], random.Random]) -> tuple[dict[str, Any], list[dict[str, Any]]]`.
- Runner supplies `rng_for(*config.seed_root, "mechanism", "round-opening", *key)` and emits returned events before any observation at the current round.
- Add `EventType.AUDIT_PUBLISHED = "AuditPublished"`; legacy mechanisms receive no new events or changed payloads.
- Keep `_RoundBoundary` delegation effective via `getattr`/typed cast, preserving replay's existing lifecycle.

- [ ] Capture pre-change legacy scenario dumps/hashes and representative chain commitments from authoritative base `e1f8f119b2709f4370303786c2796383eb6b8fa9`.
- [ ] Write and observe failing lifecycle tests before implementing the optional hook.
- [ ] Implement opening dispatch and domain event support without changing existing policy/resolution RNG paths.
- [ ] Verify actual audit runs, simultaneous publication, final-round timing, policy failure after publication, fixed-action C3 and truth isolation.
- [ ] Verify forks before/at/after publication, inherited finding persistence, nested replay without parent paths/checkpoints and byte-identical branch prefixes.
- [ ] Reject audited manifest institution settings that disagree with the canonical resolved scenario; retain documented legacy omission behavior.
- [ ] Run targeted kernel/seed/replay/branch tests and the full suite; commit changes and integrate the model lane.

## Task 3: observation-driven negative-veto policy

**Owner:** audit-policy lane.

**Files:** new `agents/scripted/ec_audit.py`, additive factories/registries in `ec_policies.py`, `params.py`, `experiments/study.py`, focused policy tests.

**Interfaces:**

- Separately versioned `ec_audit_veto_contributor@1`, parameterized like the skeptical baseline.
- Delegate selection to unchanged `ECSkepticalContributorPolicy.propose`; veto only a selected proposal/verification whose `(slot, proposition)` has a published negative finding.
- Positive, unavailable, pending and absent audits preserve baseline choice. Do not rerank claims, mutate the supplied observation, synthesize evidence, challenge from audit alone or retract previous acceptance.

- [ ] Commit the experiment DESIGN separately and send it for publication before any audit-enabled episode.
- [ ] Write and observe failing factory/behavior tests against the old registry.
- [ ] Implement the separate policy and additive registration; validate public contract version and reject malformed/future public findings.
- [ ] Check parameter boundaries, exact baseline action/proposal identity for controls, false negatives, target/slot isolation and rebuilding policy instances from the same observation.
- [ ] Run focused tests and relevant legacy policy tests; commit separately from experiment source/results.

## Task 4: predeclared audit-feedback experiment

**Owner:** audit-policy lane, with independent scientific review.

**Files:** `experiments/audit-feedback/DESIGN.md`, executable source, readouts, source provenance and publication mapping; focused tests. Root adds Make/CI gates after reproduction is implemented.

- [ ] Declare the complete finite grid, literal action/outcome predictions, timing and missingness laws, negative/zero cases, fixed-action controls and exact expectation equations before execution.
- [ ] Independently review the declared design; resolve ambiguity before committing source.
- [ ] Implement all conditional trajectories and exact probability mixtures with separate accuracy/coverage/quality/effort/utility reporting. Preserve undefined selective accuracy rather than substituting zero.
- [ ] Commit source, publish through GitHub, and verify local/published tree equality before original execution.
- [ ] Run to a fresh artifact root; retain all prediction outcomes and original sealed runs. Rebuild the readout only from those artifacts.
- [ ] Independently check exact expectations, controls, provenance, every replay and byte-identical reproduction.
- [ ] Add a dedicated Make/CI check and archive original evidence with verified checksums.

## Task 5: review, integration and handoff

**Owner:** root with independent reviewer.

- [ ] Review all implementation diffs and scientific claims; add failing reproducers and fix material findings.
- [ ] Run the complete package, acceptance, study and historical experiment gates plus the new experiment gate.
- [ ] Publish draft PRs using connected GitHub tools, reconcile current main, inspect exact-head Ubuntu/Windows CI logs and resolve review comments.
- [ ] Merge safe PRs with expected-head leases; compare each merge tree with the tested tree.
- [ ] Update README/HANDOFF/NEXT/PLAN/guides, append BUILD_LOG, update issue #103 and PR records with measured results and remaining scope.
- [ ] Verify final main CI and provide the original evidence archive and an accurate completion report.

## Progress and decisions

- Repository restoration: all 382 blobs matched the authoritative GitHub tree; exact signed base commit reconstructed locally. GitHub remains authoritative for publishing.
- Builder review: no architectural blockers; the five review-focus items above are mandatory test cases.
- Policy choice: negative veto preserves the existing inspection/share/challenge priorities and makes false-negative and late-signal effects explicit. A positive-only gate is a different policy and is outside this first experiment.
- Observation isolation applies under fixed accepted actions. Adaptive feedback can legitimately change later ordinary observations through changed actions; tests distinguish those effects.
