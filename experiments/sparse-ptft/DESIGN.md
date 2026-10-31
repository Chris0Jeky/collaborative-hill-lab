# Exact labeled-state sparse pTFT benchmark

Issue #85. Offline analytical extension, not a study freeze or a stochastic
execution. Existing Study 002 and graph-topology evidence stays unchanged.

## Declared design

Retain eight observed rounds t=0,...,7, including initialization: every pTFT
actor starts C and every fixed AllD actor starts D. Cross both denominator rules
with these six mixed-population conditions:

- Complete K3, two pTFT actors, AllD at c.
- Complete K5, four pTFT actors, AllD at e.
- Complete K5, three pTFT actors, AllD at d and e.
- Four-cycle a-b-c-d-a, three pTFT actors, AllD at d.
- Four-vertex star, hub a, three pTFT actors, AllD at hub a.
- The same star, three pTFT actors, AllD at leaf d.

Add all-pTFT and all-AllD four-cycle controls under both rules: 16 exact cells
in total. Complete graphs match the three existing Study 002 benchmark
populations, with the horizon explicitly shortened to eight rounds. Complete
projection tests additionally cover N=2,...,5 and every pTFT population size.
Hub and leaf placements are different conditions, not independent repetitions.
No stochastic samples or discrepancies are populated; their JSON fields are null.
No stochastic simulation is authorized or needed by this design. Any later
simulation needs its own declared design, samples and discrepancy records.

The model accepts connected simple undirected labeled graphs with 2 to 6
vertices, at most 2^6=64 states, and 1 to 50 observed rounds. It rejects larger,
disconnected, isolated, malformed or self-loop cases. All non-AllD actors are
pTFT with zero exploration; heterogeneous rules, weighted/directed graphs and
other action modes are outside the API. The small cap is a computational
contract, not an approximation. No new dependencies or simulator changes.

## Local transition law and state

ADR-0011 and GraphNIPDMechanism.observe define the local observation. For full
binary action vector x, vertex i has d_i incident neighbors and sees
k_i=sum(j adjacent to i) x_j. GraphProbabilisticTFTPolicy uses

- exclude-self: q_i(x)=k_i/d_i;
- include-self: q_i(x)=(k_i+x_i)/(d_i+1).

A fixed AllD actor has q_i=0. Under **ideal independent rational Bernoulli**
choices, P(x,y)=product_i q_i(x) if y_i=1, and (1-q_i(x)) otherwise.
All arithmetic is Fraction. States are full binary vectors in sorted vertex
order, lexicographically ordered with fixed AllD seats zero; all 2^m labeled
pTFT configurations remain present, including unreachable configurations.
Every transition row is checked for exact normalization and nonnegativity.

The shipped simulator compares a finite-precision random.Random draw with a
binary-float division. The exact model is its ideal rational analogue, not an
assertion that finite-precision sampling is identical. Tests capture the actual
policy threshold from real local observations for every retained ring/star state
under both sum and mean payoff aggregation. They compare it with the rounded
model probability, and explicitly demonstrate that float(1/3) is not exactly 1/3.
No policy formula mismatch was found in these controls.

Graph structure, pTFT/AllD composition, AllD placement, denominator convention
and payoff normalization are separate choices. This benchmark computes action
cooperation only and assigns no payoffs. Both sum and mean incident-edge rewards
leave these zero-exploration pTFT transition laws unchanged because the policy
reads no reward. Connectedness makes every actor an eligible neighborhood vote;
c_t=X_t/N weights vertices equally, not incident edges or degrees.

## Moments and absorption

S_t=sum(s=0,...,t) X_s. The forward state weights are
p_t(x)=P(X-vector_t=x), a_t(x)=E[S_t 1(state_t=x)] and
b_t(x)=E[S_t^2 1(state_t=x)]. For r(y)=sum_i y_i:

- p_next(y)=sum_x p_t(x) P(x,y);
- a_next(y)=sum_x (a_t(x)+r(y)p_t(x)) P(x,y);
- b_next(y)=sum_x (b_t(x)+2r(y)a_t(x)+r(y)^2 p_t(x)) P(x,y).

Thus Var(S)=sum_x b(x)-(sum_x a(x))^2 includes cross-time covariance.
The record separates sum_t Var(X_t), sum(s<t) Cov(X_s,X_t), and
Var(mean cooperation)=Var(S)/(N R)^2. Sparse graphs do not inherit the complete
graph scalar decay shortcut. An independent test oracle enumerates uniform
source-neighbor copying choices and entire labeled histories without importing
the transition implementation. It checks means, second moments, cumulative
variance, covariance, terminal probabilities and absorption on rings/stars,
including vertex relabeling.

T0 is the first all-D round, not entry into any absorbing/recurrent class.
All-D is absorbing; F_t=P(T0<=t) equals its state probability. The record gives
F_t, first-hit masses and E[min(T0,R-1)] =
sum(t=0,...,R-2)(1-F_t). This restricted time is not E[T0], a conditional mean
among absorbed paths, or a claim of eventual absorption. All-pTFT starts at
absorbing all-C, so F_t=0. Exclude-self bipartite graphs can have recurrent cycles
from other states; no general eventual-absorption result is asserted.

## Count projection and scope

count_projection checks strong lumpability against every labeled state before
returning a count transition matrix. It raises ValueError for unsupported
aggregation rather than approximating. The four-cycle witness is retained:
with d fixed D, states (1,1,0,0) and (1,0,1,0) both have two C but next-count
laws (1/8,3/8,3/8,1/8) and (0,1,0,0). The initialized count-history witness
(3,3,2) versus (3,2,2) also remains tested. A global count is not the state.

The exact readout establishes only these declared finite analytical conditions.
It implies no general topology ranking, topology-only causal claim, sampling
uncertainty estimate, power calculation, human behavior or LLM result.

## Regeneration and source identity

From the repository root with PYTHONPATH=src and the installed dependencies:

    python experiments/sparse-ptft/generate.py --check
    make check-sparse-ptft

Generation creates EXACT.json and EXACT.md; identical outputs are no-ops.
Divergent existing files are refused before either file is written. --check
regenerates both in memory and byte-compares without rewriting evidence or
creating a missing output directory. JSON contains exact fraction strings,
integers, nulls and source SHA-256 commitments, with no floats or timestamps.
Markdown displays exact fractions as well. The source manifest binds this model,
generator and design; tests guard the shipped semantics and reference benchmark.
It is a consistency commitment, not an external timestamp or proof
of an independently published source revision. No historical execution source
or readout is rewritten; existing Study 002 and graph provenance gates remain
part of final verification. Human-owned decisions remain in HANDOFF.md.
