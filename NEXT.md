# NEXT — research and engineering direction

Current checkpoint: 2026-10-29. Engineering can advance with scripted agents while
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

### 1. Quality safeguards grounded in visible evidence

[Issue #84](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/84).
The new conditional contributor responds to visible participation, but attribution
can sustain harmful activity on misleading evidence. Specify a new versioned rule
using only declared observable evidence/provenance/contradiction signals, with an
explicit negative control when those observations cannot distinguish false support.
Any new truth or credit feedback requires a separately versioned observation
contract. Hold budgets and evidence access fixed within each planned contrast;
retain all existing controls and original results. Report quality, activity,
effort, utility, finite-strategy incentives and identical-action integrity
separately. No final Study 001 weight choice or live provider is needed.

### 2. Exact labeled-state pTFT on small sparse graphs

[Issue #85](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/85).
ADR-0011 gives two reachable four-cycle configurations with the same cooperator
count and different next-count distributions. A sparse-graph benchmark must keep
enough labeled state to recover those local transition probabilities. Begin with
small connected graphs, fixed AllD actors, neighborhood broadcast and no
exploration. Check exact transition rows, complete-graph projections, relabeling
and an independent labeled-history oracle. Keep ideal rational-Bernoulli results
distinct from the finite-precision simulator and declare any new stochastic
sampling plan before execution.

### 3. Offline request planning and cumulative attempt budgets

[Issue #86](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/86).
The transport's token cap and socket timeout do not enforce a whole-episode
budget or deadline. Add an offline plan that counts action-format repair and
HTTP 429 attempts separately, then an explicit cumulative admission limit with
recorded scope and stopping reasons. Failed/unknown attempts still consume the
declared attempt budget. Keep partial measurements and unknown dollar totals
honest; define continuation behavior and preflight failure before requests.
Use mocked transports. Live provider/version, cost and stopping choices remain
human-owned.

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
The three engineering/research increments above can proceed before a live pilot;
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
