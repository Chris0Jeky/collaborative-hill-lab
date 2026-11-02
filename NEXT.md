# NEXT — research and engineering direction

Current checkpoint: 2026-11-02. Engineering can advance with scripted agents while
model, budget and confirmatory-study decisions remain open. The unchanged
[human-owned decisions](HANDOFF.md#human-owned-decisions--unchanged) are the home
for those choices.

## Next research step: a separately declared model pilot

The audit core is merged in
[PR #107](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/107), closing
[#103](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/103). Both platforms
passed the complete verification/reproduction gate on the published head, and the
merge has the identical tested tree. [HANDOFF.md](HANDOFF.md) records the exact
commits, logs and original-evidence commitments.

The separately selected `ec-audit@1` LLM prompt adapter is implemented and
independently reviewed in
[PR #109](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/109) for
[#108](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/108). Its 108 focused
offline cases cover strict public projection, absent/empty/unavailable channels,
fixed identity, legacy bytes, retry/accounting, preflight rejection, sealed replay
and continuation. Use the PR for the final integrated and hosted verification
and merge record. The original audit-feedback result remains a scripted-policy
experiment; the adapter establishes what is supplied to a provider, with no
measured live-model response or benefit.

A live effect needs its own declared experiment, model/version, institution and
weight choices, cost ceiling and stopping rule. The existing human decisions and
the pilot sequence below remain the prerequisites. Later engineering directions
remain available when a concrete experiment requires them.

## Completed foundations

- Persistent CI checks exact commits, the full suite, acceptance scenarios and
  standalone research outputs ([#69](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/69)).
- **E2 analysis implementation** reads sealed episodes, checks factorial
  comparability and conflicting attempts, and reports independent or explicitly
  paired contrasts ([#70](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/70)).
  Confirmatory interpretation still requires the pilot and frozen SAP; a working
  analysis pipeline does not supply either.
- **R3 N-IPD sensitivity follow-up** is executed as Study 002: 29 deterministic
  controls and 192 independent stochastic episodes, with exact predictions,
  preserved negative/discrepant findings and source provenance
  ([#73](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/73)).
- Built-in policy contracts and study execution inputs fail early on invalid
  settings or unsafe destinations ([#74](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/74),
  [#75](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/75)).
- A post hoc exact finite-state pTFT benchmark complements Study 002's original
  Monte Carlo results without changing its sample or settings
  ([#72](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/72)).
- **Responsive Evidence Commons** adds a versioned conditional contributor and
  an executed finite grid: 320 behavioral episodes, 160 matched contrasts and
  160 separate same-action controls. Positive, negative and null quality effects
  are retained ([#81](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/81)).
- **Configured provider execution** is integrated with explicit opt-in, offline
  validation/replay, request-level usage coverage, continuation accounting and
  known transport/model comparison checks. All transport validation uses mocked
  responses ([#82](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/82)).
- **Versioned graph N-IPD** provides local observations, canonical undirected
  adjacency and explicit payoff normalization. All 18 deterministic topology
  controls match their prior predictions and replay successfully
  ([#83](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/83)).
- **Quality safeguards (#84), sparse exact pTFT (#85), and offline provider
  planning/budgets (#86)** are complete. The skeptical rule's 440 behavioral and
  220 fixed-action records remain unchanged; its bundled contrast motivated the
  separately declared follow-ups below.

## Implemented follow-ups at this checkpoint

PRs #99, #100, #101 and #102 are merged after reviewed exact-head Ubuntu/Windows
logs and merge-tree equality checks. Issues #92, #95, #96 and #98 are closed.
Implementation, review and verification evidence is recorded in [HANDOFF.md](HANDOFF.md).

- **Component ablation (#95 / [PR #100](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/100)).**
  All 16 combinations of screen, contradiction sharing, challenges and read-citation
  requirement are retained in six contexts and both truth worlds: 192 behavioral
  episodes, 96 fixed-action controls, all P1–P6 and 288 replays passing. Effects
  interact through timing and quorum; the limited-inspection probe isolates the
  citation gate. No component distinguishes the matched hidden truths.
- **Noisy corpora and audit contract (#96 / [PR #99](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/99)).**
  The 64 behavioral worlds and 64 accounting controls satisfy P1–P8 under the
  declared exact model. With independent errors, accuracy among accepted claims
  can rise while coverage and signed quality fall; fully correlated errors give
  a null rule contrast with distinct labels. The historical standalone audit
  projection contract remains unchanged; engine integration is the separate
  #103 follow-up below.
- **Provider-budget follow-ups (#92 / [PR #101](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/101)).**
  Budgeted continuations reject omitted or mismatched budget objects before output or
  requests, retain cumulative accounting, and expose stable stop reasons in
  failed-run analysis. Shared-agent limits and interrupted-accounting boundaries
  have offline regressions. Whether network runs must always declare a budget
  remains an owner decision.
- **Lab branch integrity ([PR #102](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/102)).**
  Effective continuation policies, inherited prefixes and ancestry are validated
  from sealed artifacts. Review fixes separate branches with matching default run
  IDs and mark malformed seed fields broken. The 25 focused tests and re-review
  passed before the exact-head hosted checks and merge.
- **Shared recorded-seed validation (#104 / [PR #105](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/105)).**
  Implementation and independent review are complete. Both manifest and sealed
  start metadata reject malformed roots, protocols and blocks before replay or
  branch output, preserving valid legacy/paired behavior and original artifacts.
  The local 1,762-test suite, 303 targeted cases and relevant reproduction gates
  passed; the PR and [CI 41387542882](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41387542882)
  retain the authoritative hosted check and merge record.
- **Opt-in audits and the declared feedback experiment (#103 / [PR #107](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/107)).**
  EC v3, exact isolated audit generation, publication-before-observation,
  checkpoint/replay/branch support and a versioned negative-veto policy are
  implemented. The original 52 behavioral episodes and 24 fixed-action controls
  satisfy P1–P8, with 60 C3 comparisons, 42 truth controls and 720 exact mixture
  rows. Independent audit replayed all 76 originals and four separate branch
  fixtures, verified 621 checkpoints and 65 source digests, and preserved every
  original byte. The [readout](experiments/audit-feedback/RESULTS.md) separates
  selective accuracy, coverage and signed quality; the assumed audit law is not
  a measured accuracy claim. The [original-evidence record](experiments/audit-feedback/ORIGINAL_EVIDENCE.md)
  preserves the pre-execution source mapping and 947-file original inventory.
- **Audit-aware LLM prompting (#108 / [PR #109](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/109)).**
  ADR-0019 adds an explicit policy-owned renderer with a fixed template/policy
  identity, strict public projection and early non-EC rejection. Literal legacy
  fixtures remain unchanged. Fake-provider and intercepted-request checks verify
  actual prompts, identity, usage, replay and continuation; they do not measure
  model interpretation or a scientific audit effect.

The earlier combined local gate and 416-run noisy-corpus/ablation archive remain
historical evidence. The current audit integration also passed the complete local
gate, including all 76 audit runs, four branch fixtures and 720 exact rows in
`check-audit-feedback`; the exact published core also passed Ubuntu and Windows
checks before merge. The prompt follow-up has its own final-head verification.
Preserve both original archives and their actual clean source records.
Verification reruns do not replace evidence or add samples.

## Path to a live Study 001 result

1. **Define a bounded pilot.** Choose the candidate institutions/weights, outcomes,
   provider/model/version, both skins, cost ceiling and stopping rules. Current
   weights fail the collective-stakes certificate; the incentive atlas presents
   admissible finite-strategy alternatives without selecting one. Record a separate
   pilot plan rather than presenting the current draft as confirmatory.
2. **Run the declared pilot.** After endpoint-specific compatibility and operational
   budget controls are verified, measure
   episode-level variance, invalid-output rate and actual tokens/cost. The existing
   backlog proposed five episodes per cell; that is a candidate pilot budget, not
   an established power requirement.
3. **Finalize the confirmatory design.** Use pilot evidence to choose sample size,
   minimum effect of interest, hypotheses, exclusions/sensitivity threshold and SAP.
   Freeze the final study only after those human decisions are recorded.
4. **Execute and analyze once declared.** Preserve failures and negative findings,
   check skin robustness, and distinguish kernel seed pairing from provider
   randomness. Publication and novelty claims remain human decisions.

The analysis implementation and offline provider contract tests already work.
The engineering/research increments above can proceed before a live pilot;
pilot-dependent power and confirmatory choices cannot. Stop according to a
declared rule and preserve incomplete results if a budget binds. A revised design
is a separately declared follow-up, not a retroactive confirmation of the original.

## Later, when a concrete experiment needs them

- **Deception-capable verification:** a new mechanism version with agent-reported
  outcomes and an engine audit trail, retaining v0 behavior and hashes.
- **Reputation or sanctions:** explicit institution rules and C3-style checks,
  building on the new responsive behavioral baseline and its harmful controls.
- **Concordia cognition adapter:** typed actions behind the observation firewall,
  pinned dependency and fake-provider contract tests.
- **Policy-override serialization:** make inherited counterfactual policy intent
  portable without claiming to serialize arbitrary executable objects.
- **Ledger compression / DuckDB views:** add when measured artifact volume warrants
  it. MCP tool-seam design remains deferred until an experiment needs it.
- **Publication:** Study 000's defect/deconfound and Study 002's sensitivity results
  may support methods work; venue, replication status and novelty claims remain
  owner decisions.
