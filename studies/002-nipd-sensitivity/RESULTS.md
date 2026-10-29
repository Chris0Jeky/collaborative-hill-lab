# Study 002 — measured draft results

**Unfrozen exploratory simulation; no confirmatory or human-behavior claim.**

221 sealed episodes: 29 deterministic controls (one each) and six stochastic cells (32 independent episodes each). Fifty rounds, final ten-round window.

## Provenance

- deterministic study hash: `175140649a108a4f5ea33a4c7a1decf74cdc777a9d47057839a54b7e24ed22eb`
- stochastic study hash: `728392210a4aa437ba2a1f6e4d8be73f99b96b896e596e81a8969c121623754f`
- Local run source commits: d4b8de90fe8317a0522764ca53b86727db93179c; any dirty run worktree: False.
- These local commit IDs identify the execution checkout; they are not necessarily published GitHub revisions. `SOURCE_PROVENANCE.json` in the study directory provides source-content commitments for the checked-in run.
- Independent seed protocol: `legacy-independent-v1`; seed 20261029.
- The accompanying JSON retains exact fractions, every terminal event hash, per-episode outcomes, analytical curves and measured mean curves.

## Deterministic predictions versus measured results

**29/29 complete cooperation trajectories and terminal score vectors match their pre-execution analytical predictions exactly.** One run per cell supplies an algorithm check, not inferential replication.

| Condition | Expected mean | Measured mean | Expected final | Measured final | Path / scores exact |
|---|---:|---:|---:|---:|---|
| nb-n3-m2-q0 | 2/3 | 2/3 | 2/3 | 2/3 | True / True |
| nb-n3-m2-q49-100 | 2/3 | 2/3 | 2/3 | 2/3 | True / True |
| nb-n3-m2-q1-2 | 2/3 | 2/3 | 2/3 | 2/3 | True / True |
| nb-n3-m2-q51-100 | 1/75 | 1/75 | 0 | 0 | True / True |
| nb-n3-m2-q3-4 | 1/75 | 1/75 | 0 | 0 | True / True |
| nb-n3-m2-q76-100 | 1/75 | 1/75 | 0 | 0 | True / True |
| nb-n3-m2-q1 | 1/75 | 1/75 | 0 | 0 | True / True |
| nb-n5-m4-q0 | 4/5 | 4/5 | 4/5 | 4/5 | True / True |
| nb-n5-m4-q49-100 | 4/5 | 4/5 | 4/5 | 4/5 | True / True |
| nb-n5-m4-q1-2 | 4/5 | 4/5 | 4/5 | 4/5 | True / True |
| nb-n5-m4-q51-100 | 4/5 | 4/5 | 4/5 | 4/5 | True / True |
| nb-n5-m4-q3-4 | 4/5 | 4/5 | 4/5 | 4/5 | True / True |
| nb-n5-m4-q76-100 | 2/125 | 2/125 | 0 | 0 | True / True |
| nb-n5-m4-q1 | 2/125 | 2/125 | 0 | 0 | True / True |
| nb-n5-m3-q49-100 | 3/5 | 3/5 | 3/5 | 3/5 | True / True |
| nb-n5-m3-q1-2 | 3/5 | 3/5 | 3/5 | 3/5 | True / True |
| nb-n5-m3-q51-100 | 3/250 | 3/250 | 0 | 0 | True / True |
| nb-n3-all-q1 | 1 | 1 | 1 | 1 | True / True |
| nb-n3-alld | 0 | 0 | 0 | 0 | True / True |
| pw-n3-m2-tft | 17/50 | 17/50 | 1/3 | 1/3 | True / True |
| pw-n3-m2-linked | 1/75 | 1/75 | 0 | 0 | True / True |
| nb-n3-all-ptft-include | 1 | 1 | 1 | 1 | True / True |
| nb-n3-all-ptft-exclude | 1 | 1 | 1 | 1 | True / True |
| nb-n5-all-q1 | 1 | 1 | 1 | 1 | True / True |
| nb-n5-alld | 0 | 0 | 0 | 0 | True / True |
| pw-n5-m4-tft | 151/250 | 151/250 | 3/5 | 3/5 | True / True |
| pw-n5-m4-linked | 2/125 | 2/125 | 0 | 0 | True / True |
| nb-n5-all-ptft-include | 1 | 1 | 1 | 1 | True / True |
| nb-n5-all-ptft-exclude | 1 | 1 | 1 | 1 | True / True |

## pTFT: analytical expectations and independent-episode measurements

Expected values are closed-form mathematical predictions. Measured values are sample means from sealed runs. Equality is not required; no outcomes were tuned toward the predictions. Displayed decimals are approximations of the exact JSON fractions.

| Condition | n | Expected mean | Measured mean | 95% bootstrap interval | Observed sample variance | All-D by t=49 |
|---|---:|---:|---:|---|---:|---:|
| nb-n3-m2-ptft-include | 32 | 0.04 | 0.0316667 | [0.0254167, 0.0389583] | 0.000392832 | 32/32 |
| nb-n3-m2-ptft-exclude | 32 | 0.0266667 | 0.0252083 | [0.0216667, 0.0289583] | 0.000111066 | 32/32 |
| nb-n5-m4-ptft-include | 32 | 0.0799989 | 0.0945 | [0.0758719, 0.115878] | 0.00358581 | 32/32 |
| nb-n5-m4-ptft-exclude | 32 | 0.064 | 0.067 | [0.0529969, 0.0837531] | 0.00208619 | 32/32 |
| nb-n5-m3-ptft-include | 32 | 0.03 | 0.031 | [0.026, 0.0361281] | 0.000221935 | 32/32 |
| nb-n5-m3-ptft-exclude | 32 | 0.024 | 0.023125 | [0.021, 0.0255] | 4.72097e-05 | 32/32 |

**Visible finite-sample discrepancy:** the analytical mean lies outside the reported marginal 95% bootstrap interval in `nb-n3-m2-ptft-include`. These are separate cell intervals, not simultaneous coverage guarantees. The original 32 episodes and predeclared resampling settings are retained; this discrepancy is not hidden or repaired by adding runs.

| Condition | Expected final-window mean | Measured final-window mean | 95% bootstrap interval |
|---|---:|---:|---|
| nb-n3-m2-ptft-include | 1.77739e-08 | 0 | withheld (zero variance) |
| nb-n3-m2-ptft-exclude | 1.21148e-13 | 0 | withheld (zero variance) |
| nb-n5-m4-ptft-include | 4.74601e-05 | 0 | withheld (zero variance) |
| nb-n5-m4-ptft-exclude | 3.03688e-06 | 0 | withheld (zero variance) |
| nb-n5-m3-ptft-include | 1.993e-10 | 0 | withheld (zero variance) |
| nb-n5-m3-ptft-exclude | 1.09033e-13 | 0 | withheld (zero variance) |

## Denominator sensitivity contrasts

Each contrast is include-self minus exclude-self in episode mean cooperation. The cells are independently seeded; resampling is independent across them.

| Population | Analytical expected difference | Measured difference | 95% bootstrap interval |
|---|---:|---:|---|
| n3-m2 | 0.0133333 | 0.00645833 | [-0.000833333, 0.0141667] |
| n5-m4 | 0.0159989 | 0.0275 | [0.00262188, 0.0530062] |
| n5-m3 | 0.006 | 0.007875 | [0.002375, 0.0135] |

## Interpretation and limits

The quorum model predicts an inclusive boundary at (m−1)/(N−1): 1/2 for N=3,m=2, 3/4 for N=5,m=4, and 1/2 again for N=5,m=3. The table reports the actual agreement checks; increasing N while retaining one AllD also changes the defector fraction. The two-AllD control makes this composition dependence explicit.

For pTFT, the exact decay factor is m/N with self included and (m−1)/(N−1) with self excluded. Include-self has the larger expected finite-horizon cooperation. A positive expected final-window rate can coexist with an observed all-zero final window in 32 episodes. Observed absorption is finite-horizon evidence; the almost-sure eventual-absorption claim comes from the finite-chain argument in README.md.

The analytical fractions describe the rational Bernoulli model. The unchanged pTFT policy compares finite-precision PRNG draws with binary floating-point ratios; it is not an exact rational Bernoulli sampler. Scenario hashes and replay remain exact.

Intervals use 2000 whole-episode percentile bootstrap draws with seed 20261029 and type-7 endpoints. They describe exploratory Monte Carlo uncertainty, with no p-values or confirmatory significance labels. Zero observed between-episode variance suppresses an interval; it does not make the population outcome certain. Turns, votes and agents are not extra replicates.

Targeted and linked pairwise TFT, quorum TFT and pTFT differ in policy and observations. This draft therefore narrows a strategy/structure claim; it does not identify a structure-only causal effect. Raw pairwise and neighbourhood payoff scales differ. No new claim about people, LLM behavior, or a confirmed population-size effect follows. Studies 000 and 001 and all mechanism/policy semantics remain unchanged.
