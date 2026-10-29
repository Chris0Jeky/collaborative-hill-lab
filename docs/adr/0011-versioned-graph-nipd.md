# ADR-0011 — Versioned undirected graph N-IPD

Status: **accepted for implementation** (2026-10-29)

## Context

Legacy `nipd` has two complete-population interaction modes. Sparse graphs change
which games are played, which moves are visible, and the denominator of local
reciprocity. Quietly interpreting the old `graph="complete"` field differently
would change an existing scientific mechanism without changing its identity.

## Decision

Add world kind **`nipd_graph`**, with engine version 1, and retain the legacy
`nipd` implementation and serialized defaults. A graph world requires an explicit
`interaction.graph` object with `kind="undirected"`, `version=1`, and `adjacency`.
Every agent is a key, including isolates. Neighbor lists are reciprocal, contain
no duplicates or self-loops, and reference only declared vertices. The compiler
rejects incomplete rosters, unknown vertices, asymmetric edges and unsupported
versions. Keys and neighbor tuples are sorted before hashing. Reordering an
adjacency description does not identify a different game. Renaming agents does:
this is canonical labelled adjacency, not graph-isomorphism canonicalization.

Legacy worlds still require the literal `graph="complete"`. A graph world requires
the explicit object even when its adjacency happens to be complete. The new world
identity and version enter the existing mechanism projection; legacy projections
and content hashes remain unchanged. Graph mechanism rosters are sorted, while
the cognition plane retains the submitted order and its separate identity.

### Actions, payoffs and observations

The graph is fixed, simple, undirected and unweighted. Rounds are simultaneous.
Each world explicitly selects `payoff_aggregation="sum"` or `"mean"`:

- **Pairwise:** an agent supplies exactly one C/D move for each neighbor. Every
  undirected edge plays one two-person PD using its two directed moves.
- **Neighbourhood:** an agent supplies one C/D move broadcast to its neighbors.
  Each incident edge plays the same PD using those two agents' broadcast moves.
- **Sum:** add the incident PD rewards. **Mean:** divide that sum by the agent's
  degree. An isolated agent receives exactly zero under either aggregation.

The payoffs remain exact `Fraction` strings. No self-game is played. Complete
graph pairwise/sum and neighbourhood/mean reproduce legacy realized actions,
rewards and cooperation counts under matched policies; their mechanism hashes
intentionally differ because the new contract has a different world kind.

Observations carry the real population size, own id, round, own neighbors and
degree. Pairwise observations contain only moves directed along incident edges
toward the observer and its own directed moves. Neighbourhood observations reveal
only the count of cooperating neighbors and the observer's own prior move, not
which neighbor cooperated. No nonneighbor action, score or neighborhood is exposed.
Proposed actions must be legal even when `resolve` is called directly.

### Isolates and cooperation denominators

An isolated pairwise agent must submit an empty move map. An isolated neighbourhood
agent still submits C/D, but this is an unplayed proposal: it earns zero and is
excluded from eligible interaction votes. Transitions identify isolated agents.
Pairwise cooperation counts directed edge votes, with denominator `2|E|`;
neighbourhood cooperation counts one vote per positive-degree agent. Consequently
the two modes retain different voting units. Degree averages also differ from
population averages on an irregular graph.

Version 1 requires **at least one edge**. Isolated vertices are supported within
that graph; an entirely edgeless graph is rejected. This avoids assigning a
cooperation rate to an empty set of interactions and preserves the existing
cooperation metric's positive-denominator contract. Supporting entirely edgeless
games would require an explicit undefined-outcome metric contract.

### Policies and randomness

The existing policy names and parameter bounds remain usable. AllC, AllD, random,
targeted TFT and linked TFT already operate on the supplied opponent list. Graph
neighbourhood pTFT and quorum TFT have distinct versioned policy identities and
use local degree: exclude-self divides by degree; include-self divides by degree
plus one and includes the observer's own previous move. Quorum equality cooperates.
These graph policies start C. With degree zero they persist their own previous
move; the existing epsilon exploration can still replace that intended move.
An isolate's proposal does not affect interaction votes or rewards.

Every draw still uses the runner-supplied RNG; no global RNG or stateful policy
memory is added. The existing finite-precision Bernoulli sampling convention is
retained. Complete-graph equivalence includes matching supplied decision streams.
Agent renaming changes seed paths, so permutation invariance of realized outcomes
is asserted for deterministic policies, not for renamed stochastic trajectories.

## Alternatives and consequences

Extending legacy `nipd` in place would blur historical identity and could silently
apply population denominators to sparse graphs. Separate pairwise-only graph code
would avoid local neighbourhood semantics but leave the research comparison
incomplete. The separate versioned world supports both modes and keeps those
choices explicit without changing old records.

Topology, policy, population composition and the placement of each policy on a
graph are separate design factors. A defector at a star hub is not interchangeable
with a defector at a leaf. Tests use hand-derived ring/star payoffs, local-observation
noninterference, complete-graph controls, deterministic relabelling, skin isolation,
and sealed replay/branch checks. The small accompanying experiment is descriptive
and deterministic; repeated deterministic trajectories are not independent samples.

The complete-population pTFT count-state oracle does **not** extend to an arbitrary
sparse graph. Equal global numbers of cooperators can give different local signals
and different next-step laws. No count-state lumpability, topology-only causal
effect, human/LLM behavioral claim, power calculation or study freeze is implied.

### Exact counterexample to a sparse count-state shortcut

Consider the four-cycle `1—2—3—4—1`, with agent 4 permanently D and agents 1, 2,
3 using exclude-self pTFT. States `(C,C,D,D)` and `(C,D,C,D)` both have two
cooperators. Their local cooperation probabilities for the three dynamic agents
are respectively `(1/2,1/2,1/2)` and `(0,1,0)` under ideal independent Bernoulli
choices. The next cooperator count therefore has distribution `Binomial(3,1/2)`
in the first state and is identically one in the second. Even the conditional
means differ: `3/2` versus `1`.

The second state is reachable from the first with probability `1/8`, so this is
not a comparison involving an impossible next configuration. A literal Fraction
oracle enumerates the labelled outcomes and checks PMFs `(1/8,3/8,3/8,1/8)` and
`(0,1,0,0)`. Thus the global count alone is not a Markov state for this graph.
This counterexample is analytical; it is not a new stochastic experiment or a
complete sparse-graph benchmark.

The initialized count process also fails the Markov property. Starting at
`(C,C,C,D)`, count histories `(3,3,2)` and `(3,2,2)` have probabilities `1/8` and
`3/16`, respectively. Their next expected counts are `3/2` and `4/3`, despite the
same current count and time. The latter history leaves three equiprobable
two-cooperator configurations, whose next means are `3/2`, `3/2` and `1`.
The same independent labelled-history oracle checks these exact quantities.

