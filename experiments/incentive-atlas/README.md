# Exact incentive-region atlas (exploratory, unfrozen)

This small experiment solves the stated C1/C2 inequalities over a two-dimensional
parameter plane. It does not change Study 000/001, their weights, or their freeze
states. It is not Study 002, a preregistration, or a production default.

## Reproduce and query

Use the repository's installed Python environment, from the repository root:

```bash
python experiments/incentive-atlas/atlas.py --out artifacts/incentive-atlas
python experiments/incentive-atlas/atlas.py --atlas artifacts/incentive-atlas/atlas.json --point 32 1
python -m pytest tests/unit/test_incentive_atlas.py
python -m ruff check experiments/incentive-atlas tests/unit/test_incentive_atlas.py
python -m mypy --strict --follow-imports=silent experiments/incentive-atlas/atlas.py
make check test validate
python scripts/acceptance.py
```

On Windows use `.venv/Scripts/python.exe`; on POSIX use `.venv/bin/python`.
The output directory must not exist and cannot be under `studies/`. A failed run
keeps its partial evidence; rerun in a new directory. No installation, provider,
network, GPU or stochastic sampling occurs in the experiment.

`atlas.json` is the reproducible exact artifact: all 32 payoff vectors, all 48
unilateral deviations, region inequalities, failure witnesses, source and original
study input hashes, baseline sealed summaries, and fresh-engine check receipts.
`REPORT.md` compares four admissible examples without choosing one. Baseline and
probe subdirectories hold standard manifests, resolved scenarios, hash-linked
ledgers and checkpoints. `chl replay RUN_DIRECTORY` can replay these episodes.
With identical source/input bytes, the atlas JSON, report and event chains are byte-reproducible;
manifests include the measured Python/platform. Hashes establish consistency,
not authenticity. A query trusts the supplied atlas file.

Generation performs 32 baseline episodes plus six explicitly chosen probes of
32 profiles each, with one replay per probe: 224 fresh episodes, six replays.
This finite validation set is not used to infer the region by interpolation.
The region follows algebraically from fixed action traces and exact payoffs.

## Domain, strategy set and inequalities

Three labelled agents `a1,a2,a3` each select `C=ec_contributor` or `F=ec_freerider`.
Every one of the eight ordered profiles is retained: evidence holdings and
deterministic agent ordering make permutation reduction unjustified. The four
institutions are aggregate/attributable accountability crossed with
private/shared-ledger evidence. Templates are read from the four original
Study 001 scenario JSONs, never from its certificate or generator. The optional
misinformer arm is outside this strategy set; misleading evidence remains in the
ordinary corpus and can be accepted even by contributors.

The rational domain is `b >= 0, r >= 0`:

| Quantity | Experiment value |
|---|---|
| Correct accepted slot collective benefit | `b` |
| Wrong accepted slot collective penalty | `12`, fixed |
| Correct/wrong accepted proposer credit | `+3r / -3r` |
| Correct/wrong accepted supported-verifier credit | `+2r / -2r` |
| Inspect/share/propose/verify/challenge effort costs | `1 / 1 / 1 / 2 / 1`, fixed |
| Rounds / inspection budget / verification budget | `12 / 6 / 3`, fixed |

The existing placeholder point is `(b,r)=(12,1)`. Both signed credits scale;
this is a deliberately limited two-parameter family, not an optimization over
all possible incentive mechanisms. Credit is created by the scoring rule: it
is **not** deducted from a fund or another agent. Raising `r` increases total
utility and can buy C2 without increasing briefing quality. No monetary budget,
welfare optimum or real incentive cost is inferred.

For each institution `I`, profile `p`, and agent `i`, define `p[i:=F]` by replacing
one `C` with `F`, holding the other strategies fixed. Use the original conditions:

* **C1:** there exists `p,i` with `p_i=C` and
  `U_i(p[i:=F];b,r) - U_i(p;b,r) > 0`. This is 12 tests per institution.
* **C2:** `sum_i U_i(CCC;b,r) - sum_i U_i(FFF;b,r) > 0`.
* **Admissible here:** C1 AND C2, with strict inequalities; ties fail.

These are exactly the stated weak certificate conditions, not a full
Prisoner's-Dilemma axiom set. C1 is existential; one unprofitable deviation does
not refute it. The query lists every profitable deviation and, were C1 to fail,
all 12 nonpositive gains. C2 failures carry both complete utility profiles.
The extra three exits from `CCC` are reported separately, never substituted for C1.

## Why sealed-trace coefficient reuse is valid

For a fixed trace, let `n+` and `n-` be the numbers of correct and wrong accepted
slots, `e_i` effort, and `k_i` the signed credit at `r=1` after the institution's
credit split. The exact utility is

`U_i(b,r) = (n+/3)*b + k_i*r - 4*n- - e_i`.

The atlas obtains `n+`, `n-`, `k_i` and `e_i` from completed, chain-verified
baseline seals at `(12,1)`; it does **not** regress slopes from sampled payoffs.
Wrong slots contribute a fixed `-4` per agent, not `-b/3`. Aggregate credits
are divided by three; attributable credits follow the actual proposer/verifier.

In the current engine, benefits and credits are consumed by `final_rewards`.
They cannot change budgets, legal actions, evidence, acceptance or transitions.
The two selected policies read neither rewards, effort totals nor attribution;
their RNG argument is ignored. Induction over the 12 rounds therefore keeps
their selected actions and accepted briefing fixed over this whole plane. This
argument would not apply to arbitrary policies. The artifact records source
hashes, and regression checks refuse changed actions or coefficient mismatches.

`ECParams` takes integers. For rational probe points the runner uses
`L=lcm(denominator(b),denominator(r))`, multiplies **all monetary weights** by L
(including fixed costs and wrong-slot penalty), and divides sealed monetary
results by L. Budgets/rounds are unchanged. This is an exact change of utility
units for these effort-insensitive policies, not rounding fractional parameters
or changing production `ECParams`. Direct unscaled production parameters still
require integer credit units. Probes exercise both fractional b and fractional r.

For each topology/profile, C3 additionally checks equal actions, briefing and
total payoff coefficients across accountability rules. Equality of all three
coefficients proves total-utility invariance throughout the plane, not merely
at the placeholder point. These scripts cannot test behavioral responses to
attribution; that invariance is a limitation, not evidence for an improvement.

## Exact atlas and hand calculation

| Institutions | C1 throughout the domain | C2 / admissible region |
|---|---|---|
| Both private-evidence cells | `CFF -> FFF`, a1 saves 7 | `b + 7r > 39` |
| Both shared-ledger cells | `CFF -> FFF`, a1 saves 9 | `b + 7r > 45/2` |

Thus the region satisfying both conditions in **every** institution is
`b >= 0, r >= 0, b+7r>39`. The complement for each cell is its closed C2 failure
half-plane. The C1 failure region is empty on this plane. The C2 boundary lines
have intercepts `(39,0),(0,39/7)` and `(45/2,0),(0,45/14)` respectively;
they and their endpoints are excluded. The coordinate axes are otherwise allowed.

Hand calculation: private `CCC` accepts only true slot s1. Its proposer gets 3r,
the other two agents get 2r each, and effort is 13 each. Its attributable utility
vector is `(b/3+3r-13, b/3+2r-13, b/3+2r-13)`; aggregate utility is
`(b/3+7r/3-13)` for each. Summing gives `b+7r-39`; `FFF` is exactly zero.
At `(12,1)` this is `-20`, at `(32,1)` it is `0` (still fails), and at `(33,1)`
it is `1`. Shared `CCC` accepts two true slots, earns total credit 14r and
spends 45, yielding `2b+14r-45`: the placeholder total is `-7`.

A negative-content check: private `FCC` accepts two true slots and one false.
Attributable utilities are `(2b/3-4, 2b/3+3r-18, 2b/3+2r-18)`.
The false slot's public penalty and negative verifier credit both survive
coefficient extraction. Counting all accepted slots as correct would fail the
literal oracle and fresh engine checks.

## Four admissible designs, no default

All rows satisfy C1/C2 in all four cells. Costs and accepted briefings stay fixed.
These rewards/credits are abstract utility units, not measured implementation costs.

| (b,r) | Private / shared total U(CCC) | Attributable private U(a1,a2,a3) | Attributable profitable exits from CCC (private/shared) |
|---|---|---|---|
| (40,0) | 1 / 35 | 1/3, 1/3, 1/3 | 3 / 3 |
| (33,1) | 1 / 35 | 1, 0, 0 | 3 / 3 |
| (12,4) | 1 / 35 | 3, -1, -1 | 3 / 2 |
| (0,7) | 10 / 53 | 8, 1, 1 | 0 / 0 |

The first three lie on the same `b+7r=40` line, isolating redistribution at equal
CCC total utility. `(12,4)` shows that C2 does not imply every contributor benefits.
`(0,7)` shows C1 can hold while **no** attributable exit from CCC is profitable.
Aggregate accountability retains profitable exits from CCC throughout the plane.

For attributable private evidence the three CCC deviation gains are
`b/3-3r+9`, `b/3-2r+13`, `b-2r+13`; at least one is positive exactly when
`r < (b+13)/2`. For shared evidence they are `b/3-6r+15`, `b/3-4r+15`,
`b/3-4r+15`; at least one is positive exactly when `r < (b+45)/12`.
These extra lines distinguish different incentive patterns inside the admissible
region; the artifact retains every remaining profile-specific line as well.

No claim extends to humans, LLM behavior, all strategies, statistical power or
published findings. Credit costs, final weights, hypotheses, providers, budget,
sample size, freezes and release decisions remain with the owner in `HANDOFF.md`.
