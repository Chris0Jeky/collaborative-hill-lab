# NEXT — research and engineering direction

Current checkpoint: 2026-10-31. Engineering can advance with scripted agents while
model, budget and confirmatory-study decisions remain open. The unchanged
[human-owned decisions](HANDOFF.md#human-owned-decisions--unchanged) are the home
for those choices.

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

## Next useful increments

Issues #84, #85 and #86 are complete; see [HANDOFF](HANDOFF.md). Their results set
the next offline work.

### 1. Separate the components of the skeptical rule

[Issue #95](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/95). The quality-safeguards contrast bundles the screen,
disclosure of contradicting items, challenges and the read-citation requirement.
A labelled follow-up should vary them independently on the same fixed inputs, with
hand-derived predictions first.

### 2. Give structure a declared relation to truth

[Issue #96](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/96). Observation-only rules cannot separate corpora that differ
only in hidden truth. A corpus model with declared source noise rates, or a
separately versioned audit channel (ADR-0013), would make a quality-sensitive rule
testable.

### 3. Provider-budget follow-ups

[Issue #92](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/92) holds the remaining non-blocking items. Whether network
runs must declare a budget is an owner decision.

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
