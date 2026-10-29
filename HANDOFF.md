# HANDOFF — current checkpoint, 2026-10-29

## Research engine advancement

The owner authorized broad repository work, parallel implementation and verified
merges in this session. The earlier bounded-work/feature-park checkpoint is
preserved byte-for-byte in
[the historical handoff](docs/history/HANDOFF-before-research-engine-2026-10-29.md).
Its no-CI statements and narrower session scope are historical. Repository tier,
hook trust, licensing and the ten human decisions below are unchanged.

### Implementation references

| PR | Result | Exact-head CI |
|---|---|---|
| [#69](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/69) | Persistent CI with pinned actions, read-only token, exact checkout and clean-workspace checks | [40802143735](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40802143735) |
| [#70](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/70) | Reject confounded factorial populations and conflicting retries; retain valid golden results | [40802529028](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40802529028) |
| [#73](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/73) | Study 002 design, execution, sealed-ledger readout and source provenance | [40803286824](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40803286824) |
| [#74](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/74) | Shared built-in policy parameter validation without rewriting scenario values | [40803342268](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40803342268) |
| [#75](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/75) | Strict study counts/IDs and complete output preflight, including aliases and nested destinations | [40803377416](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40803377416) |
| [#79](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/79) | Exact post hoc pTFT benchmark, reproducible figure, experiment targets and extended CI | [40805239775](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40805239775) |

The six implementation PRs above are merged; their pages retain the exact review
and check records. The combined first five
merges also passed [main-commit CI](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40803992791)
at `bfd49d5c3e1e00bcfba2497b42ba05e04373bf9b`. Use checks on the exact commit
being evaluated; a previous green run is not evidence for a changed head.

### Scientific result

Study 002 is an **executed, unfrozen exploratory experiment**, with 29 deterministic
controls and six stochastic pTFT cells × 32 independently seeded episodes, each
50 rounds long. All 29 deterministic full trajectories and payoff vectors match
local pre-execution predictions. The quorum boundary is inclusive at
`(m−1)/(N−1)`: 1/2 for N=3,m=2; 3/4 for N=5,m=4; and 1/2 for N=5,m=3.
The two-defector control shows why population composition cannot be ignored.
Targeted and linked pairwise TFT differ on the same interaction structure.

All 192 sampled stochastic episodes reached all-D by the last observed round;
all final ten-round windows were zero. The analytical expectations remain
positive. The original N=3,m=2 include-self analytical mean falls outside its
reported marginal bootstrap interval, and that discrepancy is retained in
[RESULTS.md](studies/002-nipd-sensitivity/RESULTS.md). No extra samples or retuned
settings were used to erase it.

The [exact benchmark](studies/002-nipd-sensitivity/EXACT_PTFT_BENCHMARK.md) was added
**after** those observations. It computes ideal rational-Bernoulli means, variances
including cross-round covariance, and absorption probabilities. Absorption by
`t=40` means the entire final ten-round window is zero; `t=49` means absorption by
the last observed round. For N=5,m=4 include-self, the ideal probability that all
32 final windows are zero is about 0.991639. A zero empirical variance therefore
coexists with positive model variance. Model MCSEs and event probabilities are
not normal confidence intervals or p-values. The SVG distinguishes observed
means from model expectations and retains all 50 rounds.

### Execution provenance and unchanged inputs

The original Study 002 episodes ran from clean local commit
`d4b8de90fe8317a0522764ca53b86727db93179c`. The
[published source snapshot](https://github.com/Chris0Jeky/collaborative-hill-lab/commit/16e7c45634eb2fdaa0d70e1933c7a966f3da6967)
has its exact Git tree, `4fb241428f18e8e4013324be6905d31b986edfe4`.
[SOURCE_PROVENANCE.json](studies/002-nipd-sensitivity/SOURCE_PROVENANCE.json)
records 88 per-file SHA-256 commitments. Local pre-execution predictions are not
claimed to be an externally timestamped preregistration. Later validation and
reporting changes do not become the source of the original run retroactively.

Original ledgers are generated artifacts outside Git. The original 221-run record
is also preserved in the session deliverable
`Study002_Original_Sealed_Runs_2026-10-29.zip` (archive SHA-256
`1a72382d9ca014b3856af4451c3c425b03fa3034a9a38674bf58627a49c3108d`).
Its 1,768 original files have individual SHA-256 commitments; all 221 terminal
hashes were matched to the retained readout before packaging. The checked-in readout retains
terminal event commitments, episode outcomes and exact analytical/measured curves.
The post hoc benchmark audits that summary's identities and arithmetic; it does
not independently reverify absent raw ledgers. Its source RESULTS.json SHA-256 is
`b0208013a4bbfe2b5cb59b8b4d767059a08c0c6093c6259d413d680bc5bc0080`.

| StudySpec | Content hash | Frozen |
|---|---|---|
| Study 000 | `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f` | false |
| Study 001 | `a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe` | false |
| Study 002 deterministic | `175140649a108a4f5ea33a4c7a1decf74cdc777a9d47057839a54b7e24ed22eb` | false |
| Study 002 stochastic | `728392210a4aa437ba2a1f6e4d8be73f99b96b896e596e81a8969c121623754f` | false |

Studies 000/001 retain their original input bytes and hashes. Study 001's current
placeholder weights still give C1=true, C2=false in every institution and no C3
violation: **social dilemma not certified; tested same-behavior accountability
integrity certified**. The incentive atlas gives finite-strategy admissible
regions, without choosing weights or demonstrating a behavioral response.

## Reproduce and verify

```bash
make setup
make check test validate acceptance check-atlas check-study002
make study-002-plan
make study-002 STUDY002_ARTIFACTS=artifacts/study-002-fresh
```

Use a fresh artifact root for execution. The last command generates both component
studies and their report. `make check-study002` validates canonical inputs and
byte-identical benchmark JSON/Markdown/SVG without running more episodes or
rewriting evidence. Setup downloads pinned dependencies; science gates call no
model provider. Direct commands and other workflows are in README and Makefile.

The integrated local code at `fe5c81d` passed Ruff, strict package mypy (45 files),
all **849 tests**, all four StudySpec validations, **11/11 acceptance scenarios**,
the atlas gate and the six study-module strict-mypy/generation checks on Python
3.12.14 with the committed dependency lock. This is 217 additional test cases over
the initial 632-case baseline. Documentation/provenance mapping edits were present
in the working tree; they are not described as a clean scientific execution.
The 55 core mathematical cases and 20 report cases were independently reviewed;
labelled-agent/history enumeration supplies oracles separate from the binomial
implementation. Review-found path blockers, ambiguous destinations, inherited
Decimal rounding and Matplotlib style drift all received regression fixes.

Exact published-head Actions logs are the hosted verification record. The final
integration/documentation PR carries its own current check; no human review is
claimed from automated or agent reviews. CI covers Ubuntu/Python 3.12, not a native
Windows/macOS or multi-version matrix.

## Remaining directions and limits

The next concrete increments are
[responsive Evidence Commons policies (#76)](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/76),
[a configurable offline-tested provider transport (#77)](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/77),
and [versioned graph semantics (#78)](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/78).
Each issue has a bounded scope and acceptance criteria. NEXT separates engineering
that can proceed now from pilot-dependent hypotheses, weights, sample size and
freeze decisions. No unfinished prototype is required to run this checkpoint.

The current C/F baselines do not respond to incentives or attribution. All measured
findings concern scripted algorithms, not LLMs or people. Exact pTFT calculations
use ideal rational Bernoulli assumptions; the simulator's finite-precision draws
are unchanged. Matching kernel seeds do not pair provider randomness. Factorial
metadata checks cannot authenticate code or reveal entire missing runs; incomplete
or unverifiable paired designs retain descriptive values but withhold inference.
Output preflight checks a static filesystem and does not claim an atomic defense
against concurrent ancestor replacement. Hash links establish consistency relative
to retained commitments, not authenticity against wholesale replacement.

## Human-owned decisions — unchanged

1. Study 001 final hypotheses and wording.
2. Primary outcomes (proposal: briefing quality and contribution rate).
3. Utility weights; ECParams defaults remain placeholders.
4. Full sample size after pilot and minimum effect of interest.
5. Model providers/versions and single- versus mixed-model populations.
6. Acceptable cost ceiling and stopping rules.
7. Whether Study 001 is publication-ready and its venue.
8. Whether any legacy result counts as replicated.
9. Novelty claims and their outstanding verification.
10. Any future publication, release or paid-run decision; the repository is already public.

No study was frozen and no real or paid provider was called. `human_todo=null` is
unchanged. Hook trust remains user-owned: review changed hook definitions before
relying on them; this pass did not modify hooks or their trust configuration.
Current licensing remains GPL-3.0-only with the historical MIT grant preserved.
