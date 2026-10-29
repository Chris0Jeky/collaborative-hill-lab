# Study 002 — N-IPD quorum and denominator sensitivity

**Status: unfrozen exploratory draft; scripted agents only.** These predictions are
committed before this study is executed. This is the R3 follow-up in `NEXT.md`,
extending Study 000's strategy/structure deconfound to N=5. No legacy result is an
optimization target. No LLM provider, paid run, or human data is involved.

## Question and scope

When does quorum TFT sustain cooperation in a neighbourhood containing fixed
defectors? How does including an agent's own previous move in probabilistic TFT
change its expected decay? Which conclusions survive increasing N from 3 to 5?

The game remains Study 000's exact N-IPD: T=5, R=3, P=1, S=0, simultaneous rounds,
complete interaction, and zero exploration. Neighbourhood agents cast one vote;
pairwise agents cast one vote per opponent. A pairwise score sums N−1 games;
neighbourhood payoffs average the contributions from N−1 opponents. Raw scores
across those structures therefore have different scales. Cooperation is always
cooperative **votes / eligible votes**, including AllD votes in the denominator.

This is a sensitivity analysis of specified algorithms, not evidence about people
or LLM behavior. It does not isolate a structure-only causal effect: targeted,
linked, threshold, and probabilistic TFT have deliberately different decision
rules and observation interfaces.

## Fixed design, before execution

50 rounds (indexed t=0,…,49); final window t=40,…,49; seed 20261029;
`legacy-independent-v1`. Every stochastic condition and replicate has a distinct
policy seed path. Equal replicate numbers across conditions are **not paired**.

The generator writes two component StudySpecs so repeat counts are part of each
component's study hash:

| Component | File | Conditions | Episodes per condition |
|---|---|---:|---:|
| Deterministic controls and quorum sweep | `study.json` | 29 | 1 |
| Stochastic pTFT denominator sensitivity | `stochastic/study.json` | 6 | 32 |

Total: 221 episodes, 11,050 rounds. The 32 episodes per stochastic cell are a
bounded exploratory Monte Carlo budget, **not** a power calculation or a chosen
confirmatory sample size. There is no optional stopping or adjustment to results.

Let m be the number of reciprocators and d=N−m the number of fixed AllD agents.
Reciprocators occupy a1,…,am and AllD the remaining seats; these observation-driven
scripted policies have no seat-dependent behavior. The deterministic component is:

| Population / control | Values |
|---|---|
| N=3, m=2, d=1 quorum TFT | q ∈ {0, 49/100, 1/2, 51/100, 3/4, 76/100, 1} |
| N=5, m=4, d=1 quorum TFT | same seven q values |
| N=5, m=3, d=2 quorum TFT | q ∈ {49/100, 1/2, 51/100} |
| All quorum TFT, N=3 and N=5 | q=1 (positive control) |
| AllD, N=3 and N=5 | neighbourhood negative control |
| Pairwise, one AllD, N=3 and N=5 | targeted TFT and linked TFT |
| All pTFT, N=3 and N=5 | include-self and exclude-self absorbing controls |

The stochastic component crosses {N=3,m=2; N=5,m=4; N=5,m=3} with pTFT
{include_self, exclude_self}. The second N=5 mixture separates a change in the
quorum from the simple observation that a single defector is a smaller population
fraction at larger N. It is not a factorial estimate of population-size causality.

## Analytical predictions (not measured results)

### Quorum threshold: inclusive boundary and population composition

Every reciprocator starts C. Its initial signal is the proportion of **other**
agents cooperating: q*=(m−1)/(N−1). The rule uses ≥, so equality cooperates.

- For q ≤ q*, all m reciprocators continue C forever; group cooperation is m/N.
- For q > q*, all reciprocators switch to D at t=1; because q>0, all-D persists.
- Thus q*=1/2 for N=3,m=2; q*=3/4 for N=5,m=4; q*=1/2 for N=5,m=3.

The 49/100 and 51/100 cells straddle Study 000's knife edge. The 3/4 and
76/100 cells locate the shifted N=5 boundary. At q=0 a reciprocator always
cooperates; at q=1 one AllD defeats the quorum. All-reciprocator q=1 remains C.

For a sustained mixed population, each reciprocator earns 3(m−1)/(N−1) per round
and each AllD earns 1+4m/(N−1). On collapse, those are the t=0 rewards and every
agent earns 1 in each remaining round. Exact 50-round oracles are:

| N,m | Sustained mean / final-window cooperation | Sustained score: each TFT / each AllD | Collapse mean / final-window cooperation | Collapse score: each TFT / each AllD |
|---|---|---|---|---|
| 3,2 | 2/3 / 2/3 | 75 / 250 | 1/75 / 0 | 101/2 / 54 |
| 5,4 | 4/5 / 4/5 | 225/2 / 250 | 2/125 / 0 | 205/4 / 54 |
| 5,3 | 3/5 / 3/5 | 75 / 200 | 3/250 / 0 | 101/2 / 53 |

### Pairwise controls: targeted reciprocity is a policy property

Targeted TFT with one AllD quarantines the defector after t=0. Reciprocators keep
C,C edges with one another. Linked TFT instead switches every edge to D at t=1.
The first-round vote rate is (N−1)/N in both cases. Targeted TFT's later rate is
(N−2)/N; linked TFT's later rate is zero.

| Control | Mean / final-window cooperation | Each TFT score / AllD score |
|---|---|---|
| N=3 targeted TFT + AllD | 17/50 / 1/3 | 199 / 108 |
| N=5 targeted TFT + AllD | 151/250 / 3/5 | 499 / 216 |
| N=3 linked TFT + AllD | 1/75 / 0 | 101 / 108 |
| N=5 linked TFT + AllD | 2/125 / 0 | 205 / 216 |

The all-reciprocator neighbourhood controls (quorum TFT and either pTFT
denominator) stay at cooperation 1 and score 150 per agent. AllD controls stay at
cooperation 0 and score 50 per agent. Repeating these deterministic trajectories
would be a reproducibility check, not extra independent outcome information.

### pTFT: exact expected decay, not a claim about each trajectory

Let K_t be the number of cooperating reciprocators at round t; K_0=m. With
include-self, every reciprocator has P(C at t+1 | K_t)=K_t/N, so
E[K_(t+1) | K_t]=(m/N)K_t. With exclude-self, K_t previous cooperators each use
(K_t−1)/(N−1), while the m−K_t previous defectors each use K_t/(N−1). Summing
their probabilities gives E[K_(t+1) | K_t]=((m−1)/(N−1))K_t.

Therefore expected group cooperation is **E[c_t]=(m/N)λ^t**, including the
initial round t=0, with:

| N,m | λ include-self | λ exclude-self |
|---|---|---|
| 3,2 | 2/3 | 1/2 |
| 5,4 | 4/5 | 3/4 |
| 5,3 | 3/5 | 1/2 |

The expected episode mean is (m/(50N)) Σ(t=0…49) λ^t; the expected final-window
mean is (m/(10N)) Σ(t=40…49) λ^t. The report retains these as exact Fraction
strings. Include-self has a larger expected cooperation rate for t>0 whenever
0<m<N, since its λ exceeds exclude-self by (N−m)/(N(N−1)). This is an ordering
of expectations, not a guarantee about any single episode or finite sample.

These fractions are exact expectations for the stated Bernoulli model. The
existing pTFT implementation compares finite-precision PRNG draws with a binary
floating-point ratio internally. That numerical sampling convention is unchanged;
this draft does not claim to replace it with an exact rational Bernoulli sampler.
Scenario hashes and replay remain exact and contain no floating-point values.

With at least one AllD and no exploration, zero cooperation is absorbing.
Every nonzero state has positive probability of reaching zero next round, so
the finite chain is absorbed almost surely as time tends to infinity. This does
**not** predict that every 50-round episode is absorbed, or that an empirical
final-window mean of zero proves a zero population expectation. All-pTFT
controls start at all-C and remain there under either denominator.

## Analysis and reporting contract

The unit of analysis is one independently seeded **episode**, never an agent,
vote, or round. The report reads hash-verified, terminally sealed runs, binds their
scenario, policy, seed, replicate and study identities to the two generated
specifications, and rejects missing/extra/duplicate/unsealed or failed runs.
It recomputes outcomes from ledger transitions, without trusting cached metrics.

Deterministic cells compare the complete cooperation curve and terminal scores
with exact analytical oracles; they receive no confidence intervals. Stochastic
cells report per-episode outcomes, sample means, sample variances, final-window
means, first all-D round (or right-censoring at 50), and observed absorption counts.
The empirical mean curve is shown separately from its analytical expectation.

For stochastic means and include-minus-exclude mean-cooperation contrasts, use
2,000 whole-episode percentile bootstrap draws, seed 20261029, type-7 endpoints
at 1/40 and 39/40. Contrast resampling is independent across conditions. These
intervals describe Monte Carlo sampling uncertainty; no p-values, multiplicity-
adjusted significance, or confirmatory decisions are reported. A metric with
zero observed between-episode variance receives no interval; it does not prove
a population constant. Independent episode counts remain explicit. No failed
episode is silently replaced and no post-hoc exclusions are permitted.

All study and analytical JSON uses integers, booleans, nulls and exact Fraction
strings, with no floating point in hashes. Display-only decimal approximations
in Markdown do not enter the experimental specification. Existing Study 000/001
inputs and hashes must remain unchanged. Study freezing remains human-only.

## Run and reproduce

From the repository root with the environment installed:

```sh
python studies/002-nipd-sensitivity/generate_study.py --check
python -m collaborative_hill.cli study validate studies/002-nipd-sensitivity
python -m collaborative_hill.cli study validate studies/002-nipd-sensitivity/stochastic
python studies/002-nipd-sensitivity/run_study.py --artifacts artifacts/study-002
python studies/002-nipd-sensitivity/generate_report.py --artifacts artifacts/study-002 --output artifacts/study-002/report
```

`generate_study.py` is the canonical specification record. `--check` compares
generated bytes without writing; `--output <new-directory>` creates a fresh copy.
The top-level runner executes both components with their declared repeat counts,
refuses occupied outputs, and never freezes either component. Artifacts remain
local; only the compact derived report is suitable for committing. A rerun needs
a fresh artifacts directory. The report is deterministic for a fixed set of
sealed episodes; timestamps and absolute host paths are not report inputs.

## Checked-in readout and source provenance

`RESULTS.md` and `RESULTS.json` contain the completed exploratory readout. The
original ledgers remain local generated artifacts and are not committed.
`SOURCE_PROVENANCE.json` records the execution source's relative-path SHA-256
commitments and Git tree identity. Its run commit identifies a local source
checkout reconstructed from the upstream files; it is **not** a claim that this
commit ID exists on GitHub. File-content commitments allow comparison after
publication gives the same changes different commit metadata. Report generation
refuses to replace differing existing output; choose a fresh prefix for a new
readout, while byte-identical regeneration is a no-op.
