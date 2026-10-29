# ADR-0012 — Observation-responsive Evidence Commons contribution quorum

Status: **accepted** (2026-10-29). Adds a versioned scripted baseline for issue #76;
preserves the legacy EC personas, engine semantics and Study 001 inputs.

## Context

The existing contributor follows a fixed productive-action priority. It responds
to evidence availability and remaining tasks, but it does not condition effort on
peer participation. An incentive certificate over those policies can describe
their payoffs without showing an institutional effect on their decisions.

The current EC observation contains cumulative claims, anonymous verification
counts, and the observer's own participation flags. Attributable observations
also expose proposers and verifier identities. It does not expose a general peer
action history, the actors responsible for inspection/sharing, other agents'
budgets or effort, hidden truth, or the scorer's utility weights. The new policy
uses this existing interface; it does not extend observations or read world state.

## Decision

Add registry name `ec_conditional_contributor`, with behavior identifier:

```text
ec_conditional_contributor[peer_threshold=<fraction>,warmup=<integer>,share=<bool>]@1
```

Its parameters are `peer_threshold` (default `"1/2"`), `warmup_rounds` (default `3`),
and `share_evidence` (default `true`). Thresholds are exact integers or rational
strings in [0, 1], parsed as `Fraction`; binary floats and booleans are rejected.
Warmup is a nonnegative integer, also accepted as an integer string. The shared
policy contract validates these values without normalizing their stored scenario
representation or adding omitted defaults. The behavior ID uses the canonical
fraction, so `"2/4"` and `"1/2"` describe the same runtime rule.

Let `L` be the conservative visible count of distinct contributing peers and
`N` the observed population size. At decision round `t`:

- If `t < warmup_rounds`, use the existing `ECContributorPolicy` action rule.
- Otherwise use that same action rule iff `L >= peer_threshold * (N - 1)`.
- If the quorum is unmet, return `WithholdAction` and re-evaluate at the next
  observation. Withholding is not a permanent or internally stored state.

The boundary is inclusive and evaluated with rational arithmetic. With one
agent there are no peers to require, so the condition is vacuously satisfied.
Threshold zero is an exact response-free action/rationale control for the legacy
contributor with the same `share_evidence` setting. Its versioned policy ID still
differs; full ledgers that bind different policy IDs are not claimed identical.
The existing `ec_freerider@1` remains the unconditional no-effort control.

### What constitutes visible participation

Only public **claim proposals and verification attempts** count toward the quorum.
This is a participation signal, not a judgment that a contribution is correct,
helpful, supported, or deserving of credit. Failed verifications still represent
visible effort. Challenges, inspections and sharing do not enter this baseline's
signal. In particular, newly public evidence does not reveal who shared it.

For named observations, take the union of visible proposer and verifier IDs over
all claims and remove `self_id`. Repeated activity by one peer counts once.

For an anonymous claim `c`, the number of distinct other participants that can be
established from that claim is:

```text
L_c = int(not c.proposed_by_me)
      + c.n_verifications - int(c.verified_by_me)
```

The proposer and verifiers are disjoint because EC forbids self-verification.
Each agent can verify a claim at most once under EC engine version 2. These
mechanism rules justify adding the terms within one claim. Across anonymous
claims the same peers can recur; adding their counts would invent identities.
Use `max(L_c)` across claims instead, or zero with no claims.

`visible_peer_contributor_count(observation)` returns the maximum of this bound
and the known distinct identity count. For the engine's complete attributable
views this is the exact distinct-peer count; for anonymous views it is a lower
bound. This also handles partially available identity fields conservatively.
The helper reads the evidence fields themselves, never branches on the
`accountability` label, and does not infer actors from claim IDs or evidence IDs.

### No latent policy memory or outcome targeting

The instance stores only configuration and the unchanged contributor delegate.
Every decision is reconstructed from the current allowed observation. It does
not consume the RNG, inspect reward weights, call a scorer, or read hidden truth.
At the same public observation it acts identically whether fresh supporting
evidence happens to be true or false in the environment.

This permits productive continuation, coordination failure, and the propagation
of well-cited misinformation under the same explicit rule. None is selected by
a desired measured treatment effect. A short warmup can stop everyone before
any public claims appear; later externally supplied participation can reopen
contribution. The cumulative signal does not decay: historical participation
does not establish current willingness to contribute. These are deliberate
limits of this baseline, not claims about human or LLM reciprocity.

## Compatibility and verification

The existing EC policy implementations and their behavior IDs are unchanged.
The new policy delegates productive action selection rather than copying or
changing its ordering. Known EC claim-order ties still depend on the mechanism's
documented sorted-agent resolution. We claim actor-renaming invariance of the
signal and policy decisions when claim identities/order and available tasks are
held fixed, not arbitrary whole-run outcome invariance under simultaneous ties.

Tests start from real engine observations and hand-specified small action traces.
They cover anonymous lower bounds, named deduplication, own-action exclusion,
the distinct proposer/verifier roles within one claim, exact quorum boundaries,
warmup/reopening, threshold-zero equivalence throughout all four institutional
cells, and a literal inspect/share/withhold coordination-failure trace. Hidden
truth and inaccessible evidence facts do not enter decisions; actor renaming preserves
the signal. Other tests run compiled mechanisms across both skins, all four
institutional cells, fresh policy instances at each decision, and recorded-action
replay, comparing complete event hash chains under identical run metadata.

These tests do not themselves certify a social dilemma or an institutional
behavioral benefit. A separately declared unfrozen experiment must distinguish:
finite-profile incentive inequalities; task/quality invariance when identical
actions are replayed across attribution; and the actual decisions/outcomes when
policies receive different observations. Deterministic reruns do not create new
independent outcome information. No final utility weights, confirmatory hypotheses,
provider budget or study freeze is chosen here.
