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

## Next useful increments

### 1. Observation-responsive Evidence Commons baselines

[Issue #76](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/76).
The current contributor/freerider policies ignore attribution and utility weights.
They are useful controls for incentive inequalities, but cannot test behavioral
response to institutions. Add new versioned policies that respond to visible
contribution history and accountability; retain response-free controls and current
Study 001 inputs. Start with hand-checkable traces, observation/permutation tests
and a separate unfrozen experiment. Report incentives, identical-action integrity
and observed behavior as distinct results. This can proceed entirely offline.

### 2. Configurable provider transport and honest usage capture

[Issue #77](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/77).
Implement one explicitly configured endpoint behind the existing policy seam,
with mocked success, timeout, malformed output, refusal and unavailable-usage
cases. Record model and sampling metadata; keep unmeasured tokens/cost null.
Contract testing does not depend on choosing a live-study model and must never
make paid calls implicitly. A real pilot separately needs an approved endpoint,
model/version, budget and stopping rule.

### 3. Versioned graph-topology experiment

[Issue #78](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/78).
Study 002 covers N=3/N=5 complete graphs, not sparse networks. Specify graph
identity, payoff normalization, edge observations and isolated-agent semantics in
an ADR before implementation. Preserve current complete-graph behavior and hashes;
begin with ring/star oracles and a complete-graph equivalence control. Separate
topology changes from composition and policy changes. The pTFT count-state model
requires a new justification before use on a sparse graph.

## Path to a live Study 001 result

1. **Define a bounded pilot.** Choose the candidate institutions/weights, outcomes,
   provider/model/version, both skins, cost ceiling and stopping rules. Current
   weights fail the collective-stakes certificate; the incentive atlas presents
   admissible finite-strategy alternatives without selecting one. Record a separate
   pilot plan rather than presenting the current draft as confirmatory.
2. **Run the declared pilot.** After the provider transport is verified, measure
   episode-level variance, invalid-output rate and actual tokens/cost. The existing
   backlog proposed five episodes per cell; that is a candidate pilot budget, not
   an established power requirement.
3. **Finalize the confirmatory design.** Use pilot evidence to choose sample size,
   minimum effect of interest, hypotheses, exclusions/sensitivity threshold and SAP.
   Freeze the final study only after those human decisions are recorded.
4. **Execute and analyze once declared.** Preserve failures and negative findings,
   check skin robustness, and distinguish kernel seed pairing from provider
   randomness. Publication and novelty claims remain human decisions.

The analysis implementation and provider contract tests can proceed before the
pilot; pilot-dependent power and confirmatory choices cannot. This removes the
old backlog's circular dependency between preregistration and unknown pilot variance.

## Later, when a concrete experiment needs them

- **Deception-capable verification:** a new mechanism version with agent-reported
  outcomes and an engine audit trail, retaining v0 behavior and hashes.
- **Reputation or sanctions:** explicit institution rules and C3-style checks,
  preferably after a responsive behavioral baseline exists.
- **Concordia cognition adapter:** typed actions behind the observation firewall,
  pinned dependency and fake-provider contract tests.
- **Policy-override serialization:** make inherited counterfactual policy intent
  portable without claiming to serialize arbitrary executable objects.
- **Ledger compression / DuckDB views:** add when measured artifact volume warrants
  it. MCP tool-seam design remains deferred until an experiment needs it.
- **Publication:** Study 000's defect/deconfound and Study 002's sensitivity results
  may support methods work; venue, replication status and novelty claims remain
  owner decisions.
