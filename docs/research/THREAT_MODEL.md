# Threat Model — Collaborative Hill Lab

This document maps threats to the implemented N-IPD, graph N-IPD and Evidence
Commons mechanisms, the runner, and the optional model-provider transport. It
supersedes architectural assumptions in `_discovery/security-adversarial.md`;
the shipped interfaces are `observe`, typed `ActionProposal`, `validate_action`
and `resolve`, rather than the discovery draft's proposed capability objects.

Tier: **T1 sandbox.** The primary adversaries are model outputs and deliberately
adversarial fixture prose. Harness code, installed Python policies, fixture
authors, operator-selected configuration and dependencies remain trusted. This
is an experiment boundary, not process isolation for malicious Python code.

Two execution scopes must be distinguished:

- **Scripted and fake-provider experiments** run without model-provider network
  requests. The deterministic science gates and mocked transport tests use this
  scope. Models have no action for invoking a shell, reading arbitrary files or
  selecting a network destination.
- **Explicitly enabled provider execution** uses `llm_openai_compatible` and makes
  HTTP requests to an operator-configured endpoint. Study/branch entry points
  require `allow_provider_requests=True` or CLI `--allow-provider-requests`.
  Offline validation does not authorize execution. Direct construction of a
  provider in trusted Python is not an operating-system security boundary.
  See [configuration.py](../../src/collaborative_hill/agents/llm/configuration.py),
  [study.py](../../src/collaborative_hill/experiments/study.py) and T11 below.

The protected assets are the information shown to each agent, the typed rules
governing state changes and scoring, the integrity of retained execution evidence,
and provider credentials and bounded request behavior when transport is enabled.
The full ledger, resolved scenario and checkpoints are **analyst/harness artifacts**,
not agent views: they can contain every agent's observations, actor identities,
world configuration and terminal truth-based scores. Agents receive only their
projected observation and rendered prompt.

There is an implemented `tests/` suite. The coverage references below identify
checked-in tests and the cases they exercise; they are not a blanket security
proof or evidence of a live-provider adversarial evaluation. Explicit gaps remain
where the previously proposed guard has not been implemented.

## Threat catalogue

### T1 — Prompt injection in evidence content

- **Scenario.** An inspected item's prose tells the model to ignore instructions,
  forge a verification or emit an unauthorized action.
- **Implemented mitigation.**
  [rendering.py](../../src/collaborative_hill/agents/llm/rendering.py) places inspected
  evidence prose in labelled data blocks. Those delimiters are a presentation
  convention, not an unbreakable prompt boundary. The structural control is
  [policy.py](../../src/collaborative_hill/agents/llm/policy.py)'s JSON/schema parser,
  the closed union in [actions.py](../../src/collaborative_hill/domain/actions.py),
  and the runner's mechanism legality check. No component evaluates model text as
  Python or treats prose as a direct state mutation.
- **Existing coverage.** [acceptance.py](../../scripts/acceptance.py), scenario I,
  checks that the malicious fixture reaches a rendered prompt and a fake-provider
  run remains rule-bound with a valid chain.
  [test_invalid_llm_output.py](../../tests/unit/test_invalid_llm_output.py) covers
  invalid JSON, unsupported action types and the illegal-action fallback paths.
- **Residual/gap.** A model can still be persuaded to choose a harmful **legal**
  action. The fake-provider fixture does not test resistance to persuasion. A
  dedicated clean-versus-injected prompt behavioral study is not established by
  these tests, and fixture authors can put answer-revealing material into prose.

### T2 — Tool/schema poisoning

- **Scenario.** Corpus data introduces a tool or changes the advertised action
  schema, or a completion attempts to invoke provider tools.
- **Implemented mitigation.** There is no agent-invokable tool registry or
  tool-call execution loop. `action_schema_for` selects fixed schemas from the
  mechanism/mode; the renderer does not derive them from evidence prose. The
  optional transport rejects unsupported completion forms, including tool calls,
  in [openai_compatible.py](../../src/collaborative_hill/agents/llm/openai_compatible.py).
  `EventType.TOOL_INVOKED` is reserved; the current engine does not emit it.
- **Existing coverage.**
  [test_graph_llm_schema.py](../../tests/unit/test_graph_llm_schema.py) checks graph
  schema dispatch.
  [test_openai_compatible_provider.py](../../tests/unit/test_openai_compatible_provider.py)
  covers unsupported completion outcomes with a mocked HTTP boundary.
  [test_hidden_truth_leak.py](../../tests/unit/test_hidden_truth_leak.py) pins the
  exact inspected-evidence fact keys.
- **Residual/gap.** There is no comprehensive closed-key test for every complete
  observation in every world/round. Adding a real tool surface would require a
  separate assessment of its arguments, results and side effects; current action
  validation is not evidence for such a future surface.

### T3 — Hidden truth leaking into agent observations

- **Scenario.** The agent learns which proposition is true from a hidden world
  field rather than from the declared evidence and interaction rules.
- **Implemented mitigation.**
  [EvidenceSpec.observable_facts](../../src/collaborative_hill/domain/evidence.py)
  explicitly selects evidence ID, source, version, slot, proposition, stance and
  freshness. It excludes `truth_aligned`, `adversarial` and initial holders.
  [EvidenceCommonsMechanism.observe](../../src/collaborative_hill/domain/world/evidence_commons.py)
  constructs the per-agent view without `true_propositions` or other agents'
  budgets, effort or credit. Candidate proposition IDs are public; the mapping
  identifying which candidate is true is hidden. Correctness is used in terminal
  scoring, after policy decisions, and may appear in the analyst's sealed summary.
- **Existing coverage.**
  [test_hidden_truth_leak.py](../../tests/unit/test_hidden_truth_leak.py) scans a
  full fixture's observations and ledger for the two hidden **field names**, and
  verifies the exact inspected-evidence projection. Acceptance scenario G checks
  the information boundary on its fixture.
- **Residual/gap.** These are not tests of secret **values** through every rendered
  prompt. An end-to-end prompt/observation canary or paired-world noninterference
  audit remains a gap; it must distinguish the hidden truth assignment from the
  already-public candidate IDs. Manual projections can regress, and no structural
  check detects an answer encoded in otherwise permitted skin prose.

### T4 — Cross-agent leakage and unintended communication

- **Scenario.** An agent sees another's private evidence or current proposal, or
  actor identities are exposed in an aggregate-accountability observation.
- **Implemented mitigation.** The EC projection follows private/shared-ledger
  evidence visibility and reveals facts only after that agent inspects the item.
  Aggregate claim views omit proposer/verifier/challenger identities while keeping
  self-knowledge flags; attributable views expose the configured identities.
  [runner.py](../../src/collaborative_hill/engine/runner.py) builds all observations
  before collecting proposals, validates against the pre-resolution state, then
  resolves once. [graph_nipd.py](../../src/collaborative_hill/domain/world/graph_nipd.py)
  exposes incident interactions or local counts, not nonneighbor actions/scores.
  `InteractionPlane` currently rejects `communication="messages"` rather than
  silently accepting an unimplemented routing mode.
- **Existing coverage.**
  [test_observation_visibility.py](../../tests/unit/test_observation_visibility.py)
  covers private/shared evidence and legacy N-IPD observation boundaries;
  [test_institution_rules.py](../../tests/unit/test_institution_rules.py) covers
  aggregate identities and self-flags;
  [test_graph_nipd.py](../../tests/unit/test_graph_nipd.py) changes nonincident
  actions/scores and checks observation equality;
  [test_interaction_plane.py](../../tests/unit/test_interaction_plane.py) checks the
  unsupported-message rejection.
- **Residual/gap.** There is no dedicated current-round proposal-leak sentinel
  test cited here. Aggregate observations do not provide cryptographic anonymity:
  actors may be inferred from context. Audit payloads deliberately retain real
  actor IDs, and the full ledger contains multiple agents' private observations;
  handing those artifacts to an agent would bypass the intended boundary.

### T5 — Illegal actions and identity spoofing

- **Scenario.** A completion attempts self-verification, exceeds a budget, changes
  actor identity or addresses a nonneighbor.
- **Implemented mitigation.** Action models reject extra fields; `ActionProposal`
  has no actor/agent-identity override. The runner binds identity from its own
  policy loop and calls `validate_action` before resolution. Mechanism-illegal
  proposals produce `ActionRejected` followed by failure or a separately validated
  fallback. Exhausted JSON-format retries instead produce a typed
  `AbstainAction(reason="invalid_llm_output")`; that action still passes through
  the mechanism gate. EC rejects `ApproveClaimAction` in v0. Graph direct resolution
  additionally validates the joint-action roster and exact neighbor coverage.
- **Existing coverage.**
  [test_capability_enforcement.py](../../tests/unit/test_capability_enforcement.py)
  checks self-verification, budgets, references and mode legality.
  [test_invalid_llm_output.py](../../tests/unit/test_invalid_llm_output.py) and
  [test_abstain_fallback_illegal.py](../../tests/unit/test_abstain_fallback_illegal.py)
  distinguish parser fallback from legality rejection and reject illegal fallbacks.
  [test_graph_pipeline.py](../../tests/integration/test_graph_pipeline.py) seals
  nonneighbor-action rejection under both fallback policies.
  [test_runner_start_meta.py](../../tests/unit/test_runner_start_meta.py) prevents
  supplemental metadata from overwriting reserved runner identity/seed fields.
- **Residual/gap.** Dedicated actor-field spoofing and explicit EC `ApproveClaim`
  rejection cases are not present among the cited tests. Trusted Python callers
  must follow the runner contract; this does not sandbox arbitrary policy code or
  establish that every legacy mechanism's direct `resolve` is an independent
  legality boundary.

### T6 — Forged or inappropriate evidence references

- **Scenario.** An agent cites a nonexistent or invisible item, or uses stale or
  mismatched evidence to obtain support.
- **Implemented mitigation.** EC `validate_action` checks cited IDs for existence
  and visibility. `_adjudicate_verification` and `_adjudicate_challenge` separately
  check accessibility, freshness, stance and slot/proposition match. Visibility
  permits citing an ID before inspection; inspection is not a citation prerequisite.
- **Existing coverage.**
  [test_capability_enforcement.py](../../tests/unit/test_capability_enforcement.py)
  includes nonexistent/invisible citation rejection and legal positive controls.
  [test_ec_transitions.py](../../tests/unit/test_ec_transitions.py) exercises fresh,
  stale, inaccessible, supporting and contradicting evidence, including unsuccessful
  adjudication. [test_provenance_graph.py](../../tests/unit/test_provenance_graph.py)
  checks citation and verification/challenge links against sealed events.
- **Residual/gap.** IDs are guessable, but guessing does not bypass visibility.
  Provenance checks are not truth verification: fresh, accessible misinformation
  can support an accepted wrong claim. Full adversarial citation-combination
  coverage is not claimed.

### T7 — Ledger, checkpoint and report tampering

- **Scenario.** An event, terminal seal, scenario binding or checkpoint is changed,
  or an incomplete run is presented as a completed result.
- **Implemented mitigation.**
  [events.py](../../src/collaborative_hill/engine/events.py) and
  [store.py](../../src/collaborative_hill/engine/store.py) check sequence, parent
  linkage and canonical event hashes. Floats are rejected in hashed content by
  [hashing.py](../../src/collaborative_hill/engine/hashing.py).
  [replay.py](../../src/collaborative_hill/engine/replay.py)'s `load_run` also checks
  scenario/manifest/terminal bindings through
  [validation.py](../../src/collaborative_hill/engine/validation.py); checkpoint
  validation binds state hashes to sealed boundary events. Replay re-executes
  recorded typed actions and compares event hashes. High-level reporting loads
  verified runs; standalone metric functions require the caller to provide valid
  events and do not independently authenticate every input.
- **Existing coverage.**
  [test_event_chain.py](../../tests/unit/test_event_chain.py),
  [test_checkpoint_tamper.py](../../tests/unit/test_checkpoint_tamper.py),
  [test_reporting_seal.py](../../tests/integration/test_reporting_seal.py),
  [test_replay_determinism.py](../../tests/metamorphic/test_replay_determinism.py)
  and [test_replay_provider_failure.py](../../tests/metamorphic/test_replay_provider_failure.py)
  cover corruption, mismatched/unsealed reporting and successful/failed replay.
  [test_branch_prefix.py](../../tests/metamorphic/test_branch_prefix.py) checks the
  preserved branch prefix. Acceptance C is the replay check; F is branching.
- **Residual/gap.** These artifacts are tamper-evident, not authenticated. A writer
  able to replace the whole record and recompute all commitments can create a
  self-consistent forgery. Event `meta`, manifests and transcripts are not all
  cryptographically covered by the event chain. Equal event hashes do not imply
  byte-identical raw files containing unhashed metadata. External signatures,
  independent custody and general protection against concurrent filesystem
  replacement are not provided by these checks.

### T8 — Request exhaustion, cost and non-termination

- **Scenario.** Invalid completions or transport faults trigger excessive calls,
  or a policy/provider never returns.
- **Implemented mitigation.** Built-in mechanisms have finite configured round
  horizons. `LLMPolicy` makes at most `max_retries + 1` format attempts per proposal;
  exhausted parsing yields a typed abstention and caught provider errors seal a
  failed run. The optional provider requires a completion-token limit, defaults
  to no format or HTTP retries, caps configured retry counts, limits response
  bodies to 1 MiB, and passes a bounded socket timeout. Only explicitly enabled
  HTTP 429 retries can repost at the transport layer; ambiguous transport failures
  are not automatically retried. Measured/unknown usage is distinguished by
  [accounting.py](../../src/collaborative_hill/agents/llm/accounting.py).
- **Existing coverage.**
  [test_llm_max_retries.py](../../tests/unit/test_llm_max_retries.py),
  [test_provider_failure.py](../../tests/unit/test_provider_failure.py),
  [test_openai_compatible_provider.py](../../tests/unit/test_openai_compatible_provider.py)
  and [test_provider_accounting.py](../../tests/unit/test_provider_accounting.py)
  cover retry bounds, typed failures, response limits and honest partial usage.
  [test_provider_workflow.py](../../tests/integration/test_provider_workflow.py)
  covers persisted usage and offline replay through a mocked transport.
- **Residual/gap.** Finite rounds/retry counts do not guarantee a wall-clock
  deadline. A synchronous custom policy can block; the socket timeout is not an
  end-to-end deadline or cancellation of remote generation. Token limits depend
  on the provider honoring them. There is no enforced total-token/dollar study
  budget or billing-idempotency guarantee, and missing usage remains unknown.

### T9 — Scorer manipulation

- **Scenario.** An agent stuffs its justification with grading instructions or
  repeatedly verifies/challenges a claim to inflate support.
- **Implemented mitigation.** Programmatic metrics and EC terminal scoring use
  typed events/state, not agent justification or an LLM judge. EC allows at most
  one verification and one challenge per agent/claim. Net support selects at most
  one accepted claim per slot, breaking ties by earliest claim. Truth-based quality
  and configured credits are computed by the mechanism, including wrong-claim
  penalties; arbitrary parameter choices are not guaranteed to make every form
  of misinformation unprofitable.
- **Existing coverage.**
  [test_ec_transitions.py](../../tests/unit/test_ec_transitions.py) covers acceptance,
  tie-breaking and exact reward arithmetic.
  [test_provenance_graph.py](../../tests/unit/test_provenance_graph.py) checks audit
  flags against terminal outcomes.
  [test_legacy_defect_regression.py](../../tests/unit/test_legacy_defect_regression.py)
  guards the historical error that reported zero cooperation for pairwise records.
- **Residual/gap.** Dedicated repeated-verification/challenge rejection cases and
  a paired-run test changing only adversarial justification text while asserting
  equal metrics are still absent. Legal strategic exploitation of the specified
  scoring rule remains an experimental outcome. Adding an LLM judge would
  introduce a new prompt-injection and validation problem.

### T10 — Narrative skins changing mechanisms or obscuring provenance

- **Scenario.** Flavor text is treated as a rule, or skin differences are mistaken
  for mechanism changes or unexplained ledger divergence.
- **Implemented mitigation.**
  [scenario.py](../../src/collaborative_hill/experiments/scenario.py) separates skin
  wording from the mechanism projection, hashes narrative separately, and rejects
  references to unknown agent/slot/proposition/evidence IDs. Built-in scripted
  policies operate on mechanical observations. LLM prompts deliberately depend on
  skin wording, so behavioral equality for LLMs is not promised.
- **Existing coverage.**
  [test_skin_isolation.py](../../tests/metamorphic/test_skin_isolation.py) checks
  mechanism/evidence hash invariance, changed narrative/scenario hashes, unknown
  references and scripted chain equality.
  [test_graph_invariance.py](../../tests/metamorphic/test_graph_invariance.py)
  applies the corresponding skin control to both graph action modes.
- **Required qualification.** Full event-chain equality in those tests requires
  the **same run configuration, identities and seeds, with no differing
  narrative-bearing `start_meta`**. Standard study execution records narrative
  and scenario identities in `RunStarted`; swapping skins can therefore change
  the chain even when mechanical actions and scores are identical. These finite
  tests are regression evidence, not proof for every possible policy or skin.
- **Residual/gap.** Arbitrary prose can reveal information or persuade the model;
  reference validation does not sanitize its meaning. LLM skin robustness remains
  a measurement target, not an established invariance result.

### T11 — Provider transport, credentials and external data disclosure

- **Scenario.** A configured endpoint receives unintended data, redirects a bearer
  token, returns oversized/malformed output or reflects credentials into audit files.
- **Implemented mitigation.**
  [configuration.py](../../src/collaborative_hill/agents/llm/configuration.py) requires
  explicit endpoint/model/token-cap configuration, rejects endpoint credentials,
  queries and fragments, requires HTTPS except explicitly enabled loopback HTTP,
  and accepts a credential environment-variable **name**, not a secret in the
  scenario. The registry/CLI opt-in is checked before configured execution.
  [openai_compatible.py](../../src/collaborative_hill/agents/llm/openai_compatible.py)
  refuses redirects, sanitizes transport errors, checks reflected occurrences of
  the configured bearer token, and rejects malformed/unsupported responses.
  Runtime policy checks reject configuration drift before a request. Replay uses
  recorded actions and does not require provider credentials.
- **Existing coverage.**
  [test_openai_compatible_provider.py](../../tests/unit/test_openai_compatible_provider.py)
  covers redirects, reflected credentials, malformed responses, timeout arguments,
  size limits, configuration immutability and bounded retry behavior.
  [test_provider_workflow.py](../../tests/integration/test_provider_workflow.py)
  covers offline validation, explicit opt-in, missing/rejected credentials,
  credential-free replay and scripted branch replacement. The HTTP boundary is
  mocked; these are not live TLS, endpoint, billing or adversarial-service tests.
- **Residual/gap.** The authorized provider receives the rendered prompt, including
  the agent's visible evidence and skin prose. There is no general destination
  allow-list, DNS/SSRF defense, retention guarantee or content-wide secret scrubber.
  Token-reflection checks concern the configured literal credential, not every
  encoding or unrelated secret. Endpoint selection, environment/proxy configuration
  and provider data handling remain trusted operator concerns. Transport safeguards
  do not establish that arbitrary endpoints or datasets are safe to use.

## Cross-cutting boundaries and remaining gaps

The strongest current information-boundary checks combine explicit projections,
exact evidence-key assertions, private/shared visibility cases and graph
nonneighbor noninterference. They do not establish a universal serialization-leak
proof. The missing prompt-level hidden-value audit, dedicated current-proposal
sentinel and justification-only scorer test remain explicit follow-up coverage.

Output paths are another harness boundary. The study and run-store code preflight
destinations, validate condition IDs and reserve runs;
[test_study_output_safety.py](../../tests/integration/test_study_output_safety.py),
[test_run_reservation.py](../../tests/unit/test_run_reservation.py) and
[test_branch_out_guard.py](../../tests/integration/test_branch_out_guard.py) cover
specified traversal, symlink, collision and overwrite cases. These guards do not
provide general filesystem isolation or an atomic defense against arbitrary
concurrent ancestor replacement.

## Explicitly outside the T1 assurance claim

- **Human-subject or sensitive-data deployment.** Current fixtures and recorded
  experiments contain no participant data. Real participant use would require the
  existing sensitive-data overlay and a revised threat assessment.
- **Malicious harness, dependencies or Python policies.** They run with the host
  process's privileges. This document does not change tier/hook trust assumptions
  or claim that a model's action restrictions sandbox installed code.
- **Provider confidentiality and supply-chain trust.** Optional transport exists;
  sending a prompt is a real disclosure to the selected service. Dependency locks
  and source hashes are provenance, not a defense against a malicious dependency
  or provider.
- **Cryptographic authenticity and access control.** Ledger hashes detect
  inconsistency relative to retained commitments; they do not authenticate the
  writer, encrypt private observations or make an audit archive safe for agents.
- **Universal termination or spend ceilings.** The implementation bounds configured
  rounds, attempts and response size, with the limitations in T8. It provides no
  general CPU/memory isolation, hard wall-clock cancellation or total study spend
  enforcement.

Preserving the observation boundary and the sealed evidence is necessary for an
interpretable experiment. It is not sufficient by itself to establish scientific
validity, model robustness or safety of a broader deployment.
