# Noisy corpus: local pre-execution design

Status: exploratory, unfrozen, exact finite enumeration for issue #96. This file
and [ADR-0017](../../docs/adr/0017-noisy-corpus-and-audit-contract.md) are committed
before implementation or execution. This is a local design record, not an
externally timestamped preregistration, a live-model pilot or a confirmatory
study. Existing studies and experiment evidence are unchanged. Nothing selects
final weights, a model, paid execution or a study freeze.

## Question and scope

The quality-safeguards experiment establishes that observationally identical
accurate and misleading worlds produce identical actions. Its aligned/inverted
sums do not specify a probability model. This follow-up supplies an explicitly
synthetic probability model and asks what the unchanged skeptical rule does
under its assumptions. A separate audit observation contract is specified and
validated as a foundation; no audit channel is enabled in the EC engine here.

We enumerate possible corpora once and weight their sealed outcomes exactly.
There are no random corpus samples, estimated parameters, empirical prevalence
claims, confidence intervals, significance tests or selected best rates.

## Declared corpus models

There is one slot, `s1`, and two neutrally named propositions, `p` and `q`.
Each of three report positions publishes one fresh item supporting one of them.
Let `T` be truth and `R=(R1,R2,R3)` be the report triple. All 16 combinations
`T in {p,q}` and `R in {p,q}^3` are retained, including zero-probability worlds.
The explicit synthetic truth mixture is `P(T=p)=P(T=q)=1/2`; it is not a claim
about real proposition prevalence. Results are also reported conditional on
each truth, to expose rather than assume the intended label symmetry.

Rates are exactly `0`, `1/10`, `1/4`, `1/2`, `3/4`, `1`. For each rate `e`:

1. **Independent errors, conditional on truth.** Every position independently
   reports the false proposition with probability `e`. If a triple has `k`
   errors, `P(T,R) = (1/2) e^k (1-e)^(3-k)`. The exponent counts labeled
   positions; no binomial multiplicity belongs in an individual world's mass.
2. **Fully correlated errors.** A single common error bit is wrong with
   probability `e`; all three positions report the same proposition. The
   all-correct world has mass `(1-e)/2`, the all-wrong world `e/2`, and all
   mixed triples have mass zero, for each truth. Each source has the same
   marginal error rate as in model 1, but there is no independent corroboration.

Each model is evaluated under two visible label assignments:

- `distinct`: `src-1`, `src-2`, `src-3`;
- `collapsed`: all reports display `src-1`.

The label assignment changes no report or probability. In the independent model,
`collapsed` is an intentionally uninformative relabeling of independently generated
report positions, not an assertion that one real source makes independent errors.
In the correlated model, distinct labels intentionally fail to reveal the common
error. Labels alone never establish independence in either direction.

## Fixed episode inputs and rules

Three agents `a1,a2,a3`, all active; one slot; three items `e1,e2,e3` with
the report positions in that order. All items use `stance=supports`, version 1,
freshness `fresh`, and initial holders `a1`, `a2`, `a3` respectively. The shared
ledger exposes every item's existence to every agent at round 0. Inspection is
still required. Inspect budget 3, verify budget 2, 8 simultaneous rounds.

The behavioral episodes use aggregate accountability. Each recorded action
schedule is replayed under attributable accountability as a C3 control. This
isolates accounting from behavior; it does not claim an institutional effect.

The two policies are unchanged registered version-1 rules:

```text
ec_conditional_contributor[peer_threshold=0,warmup=0,share=True]@1
ec_skeptical_contributor[min_sources=2,peer_threshold=0,warmup=0,share=True]@1
```

A zero quorum removes participation gating so this experiment isolates the
evidence response. With full inspection and only supporting items, challenges,
sharing and the read-citation condition do not distinguish accepted schedules.
The whole-rule comparison is not an ablation of the earlier experiment.

Costs and credit are existing placeholders: inspect/share/propose/challenge 1,
verify 2, correct/wrong slot +12/-12, accepted proposer +3/-3, accepted verifier
+2/-2. The horizon permits all declared actions and two final withhold rounds.
Seed `20261102`, protocol `paired-policy-v2`, one run per design point. Neither
policy draws randomness; the seed is provenance, not independent replication.

The grid is exactly **64 behavioral episodes**: 16 truth/report worlds x 2 rules
x 2 label assignments, plus **64 same-action replays**. The two probability
models and six rates reweight these same outcomes, never add fake replicates.

## Hand-derived behavioral oracle

All agents inspect `e1`, `e2`, `e3` at rounds 0, 1, 2. For the conditional rule,
all propose the proposition reported by `e1` at round 3, citing every supporting
item for that proposition. Simultaneous proposals become `c1,c2,c3`. At round 4
the agents verify `c2,c1,c1`; at round 5 they verify `c3,c3,c2`; rounds 6 and 7
are all withhold. Each claim has net support 2; the earliest, `c1`, wins.

The skeptical rule follows that exact schedule iff the labels are distinct and
all three reports agree. Any mixed report triple supports a rival and vetoes
each candidate. Collapsed labels cannot meet the two-source requirement. In
either rejected case the agents inspect at rounds 0-2 and withhold at 3-7.

Accepted schedules have total effort 24, contribution fraction `3/4`, and
total utility `-5` for a correct claim or `-43` for a wrong claim. At aggregate,
each utility is `-5/3` or `-43/3`. At attributable, the correct utilities are
`-1,-2,-2` and the wrong utilities `-15,-14,-14`. Rejected schedules have total
effort 9, contribution fraction `3/8`, no accepted slot, and utility `-3` per
agent. These are literals to be checked independently of the production policy.

## Exact probabilistic oracle

Let `C=P(correct accepted)`, `W=P(wrong accepted)`, `A=C+W`, and `D=C-W`.
No accepted slot has probability `1-A`. Selective accuracy is `C/A` when `A>0`,
and JSON `null` when `A=0` (not zero). Signed expected quality is `12D`.

| Model and rule | C | W | A |
|---|---|---|---|
| either model, conditional, either label assignment | `1-e` | `e` | `1` |
| independent, skeptical, distinct | `(1-e)^3` | `e^3` | `(1-e)^3+e^3` |
| correlated, skeptical, distinct | `1-e` | `e` | `1` |
| either model, skeptical, collapsed | `0` | `0` | `0` |

All rules' expected effort is `9+15A`, contribution fraction `3(1+A)/8`, total
credit `7D`, and total utility `19D-9-15A`. All arithmetic is exact `Fraction`;
hashed/readout numbers are integer or rational strings, never floats.

Under independent errors and distinct labels, the skeptical-minus-conditional
quality difference is `-12 e(1-e)(1-2e)`. It is negative for `0<e<1/2`, zero at
`0,1/2,1`, and positive for `1/2<e<1`; positive there means a smaller negative
quality, not accurate inference. The screen rejects correct as well as wrong
claims. Improved selective accuracy is not an overall quality benefit.

Hand-calculated checkpoints for the independent distinct-label skeptic:

| e | C | W | A | Selective accuracy | Expected quality |
|---|---|---|---|---|---|
| `0` | `1` | `0` | `1` | `1` | `12` |
| `1/10` | `729/1000` | `1/1000` | `73/100` | `729/730` | `1092/125` |
| `1/4` | `27/64` | `1/64` | `7/16` | `27/28` | `39/8` |
| `1/2` | `1/8` | `1/8` | `1/4` | `1/2` | `0` |
| `3/4` | `1/64` | `27/64` | `7/16` | `1/28` | `-39/8` |
| `1` | `0` | `1` | `1` | `0` | `-12` |

## Predictions and checks declared before execution

- **P1:** All 32 matched truth-flip pairs have identical observations and typed
  action schedules, opposite quality, and equal effort. No hidden truth fields
  occur anywhere in their ledgers; sealed correctness outcomes remain allowed.
- **P2:** Every complete behavioral schedule and reward matches the hand oracle
  above. This checks first-source ordering, unanimous acceptance and abstention.
- **P3:** Every declared mass distribution sums to one; each truth has mass
  `1/2`; each source's marginal error probability is `e`.
- **P4:** Every weighted row matches the independent closed-form oracle, including
  the conditional-on-truth rows. All rows are retained if a prediction fails.
- **P5:** Independent distinct-label screening lowers signed quality at `1/10`
  and `1/4`, raises it at `3/4`, and leaves it equal at `0,1/2,1`.
- **P6:** Fully correlated distinct-label rules have identical accepted outcomes
  and expected metrics at every rate; unanimity cannot diagnose a common error.
- **P7:** Collapsed-label skeptics never accept; selective accuracy is undefined.
- **P8:** All 64 C3 replays preserve typed actions, briefing, effort, quality and
  total utility. All 128 sealed runs reproduce their hash chains on replay.

The implementation validates inputs against this grid, checks completed manifests
and hashes, retains every cell and terminal hash, and writes a source-provenance
record from a clean commit. `--check` reruns in a fresh temporary directory and
byte-compares both JSON and Markdown readouts. Execution artifacts stay outside
tracked evidence; original studies/experiments are not regenerated in place.

## Separate audit contract foundation

ADR-0017 defines `ec-audit-observation@1` with an exact declared accuracy,
fixed public publication rounds and targets, explicit unavailable outcomes and
trusted-oracle provenance. The standalone prototype will strictly validate
configurations and reports, expose nothing before its scheduled round, reject
unknown targets/duplicates/extra fields, emit only the versioned public projection,
and demonstrate nonmutation of the base observation. A perfect audit is explicitly
a synthetic oracle assumption, not a measured feature of deployed verification.

Audit schema fixtures and projection tests are not audit-enabled episodes. They
cannot demonstrate changed policy behavior, learning, trustworthiness, costs,
social-dilemma certification or C3 for an integrated audit mechanism. Required
engine/compiler/policy/replay integration is enumerated in the ADR. No existing
observation schema, mechanism version or scenario hash changes here.

## Limits and reporting

The source error rates, independence and truth mixture are imposed modeling
choices, not estimates. Correlation is only probed at the fully correlated extreme;
no intermediate mixture, adversarial adaptation, selection bias, noisy provenance,
staleness, multiple slots, private-access dynamics or budget-limited reading is
claimed. Unanimity is a consequence of this three-report corpus plus the unchanged
screen, not a universal recommendation. No incentives or equilibrium claims are
made from one all-active profile; quality, coverage, effort, contribution and
utility are separate outputs. There is no general-benefit, real-population, LLM,
human or optimal-institution conclusion. Any post-execution change to the design
must be a separately labeled follow-up, with this file preserved.
