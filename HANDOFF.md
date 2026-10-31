# HANDOFF — current checkpoint, 2026-10-31

## Portability, feedback tooling and issues #84–#86

Native Windows reproduction was broken and invisible: `core.autocrlf` plus text-mode
writes changed bytes that evidence commits to. [#88](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/88) forces LF, fixes
every text write and runs the full gate on Windows in CI. No evidence byte or Linux
output changed.

Feedback tools from [#89](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/89) and [#93](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/93): `make quick`
(diff-selected checks), `chl lab` / `make lab` (film strips from verified ledgers,
terminal and HTML), `make mutants` (reproducible token-mutant sampler) and a
Hypothesis whole-episode fuzzer. A one-off 500-example fuzz search found no engine
defect. The first 72-mutant sample killed 55 using fast tests only; survivors
clustered in reported metrics, now pinned by `tests/unit/test_metric_oracles.py`.

[#90](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/90) (closes #86) adds `chl study plan` and `RequestBudget` (ADR-0015):
attempts are charged at admission, scopes never reset on a retry or fork, stops seal
`RunFailed` and replay offline, deadlines apply between requests only, and the budget
enters no hash or ledger. There is no default limit. All verification is mocked.

[#91](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/91) (closes #85) adds the
[exact sparse pTFT benchmark](experiments/sparse-ptft/EXACT.md): 16 exact cells,
complete-graph agreement with Study 002, an independent history oracle and the
four-cycle non-lumpability witness. An independent review re-derived key values by hand.

[#94](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/94) (closes #84) adds `ec_skeptical_contributor@1` (ADR-0013) and the
unfrozen [quality-safeguards experiment](experiments/quality-safeguards/RESULTS.md):
440 behavioral episodes and 220 same-action controls. **The rule does not separate
accurate from misleading evidence**: all 220 truth pairs have identical actions and
opposite quality, and unanimous false corroboration passes. Its bundled rule effect
trades on conflicted evidence, gaining where structure tracks truth and losing where
it inverts. One named skeptic blocks every accurate conflicted claim. C1 and C2 hold
together in 0 of 48 groups; C3 holds in all 220 replays. Sealed raw runs are local at
`C:/Users/Cristian3/chl-wt/kept-artifacts/quality-safeguards/`, outside Git and not
archived elsewhere; the checked-in readout retains terminal hashes.

Exact-head hosted CI passed on Ubuntu and Windows for every merged PR. No study was
frozen, no provider was called, and the ten human decisions below are unchanged.
Follow-ups: [#92](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/92), [#95](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/95), [#96](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/96).

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
| [#81](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/81) | Observation-responsive EC baseline, strict parameter primitives and 480-run sensitivity/control record | [40811251496](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40811251496) |
| [#82](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/82) | Configured provider transport, explicit execution opt-in, request accounting and continuation provenance | [40812620936](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40812620936) |
| [#83](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/83) | Versioned local graph N-IPD, 18 exact controls and historical-evidence regression gate | [40813963880](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40813963880) |

The implementation PRs retain their exact review and check records. The combined first five
merges also passed [main-commit CI](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40803992791)
at `bfd49d5c3e1e00bcfba2497b42ba05e04373bf9b`. Use checks on the exact commit
being evaluated; a previous green run is not evidence for a changed head.

### Current responsive Evidence Commons result

The new `ec_conditional_contributor` uses only visible contribution history. Its
exact peer quorum, warmup and anonymous lower-bound semantics are versioned in
ADR-0012. Legacy contributor/freerider policies and Study 001 are unchanged. Policy
inputs now reject float/byte coercion before normalization can alter their identity.

The [declared finite design](experiments/responsive-commons/DESIGN.md) executed
320 deterministic behavioral episodes and 160 separate fixed-action controls.
Across the 160 attributable-minus-aggregate contrasts, quality increased in 2,
decreased in 2 and was unchanged in 156; actions differed in 4. All 160 identical-
action controls preserved briefing, effort, quality and total utility. Nine of
40 two-strategy cells satisfy the declared strict C1/C2 pair. These are distinct
tests, not a general social-dilemma certificate or a population effect estimate.

Attribution sustains useful and harmful contribution in this grid. The rule does
not inspect hidden truth, assess evidence quality or optimize utility weights.
The [full readout](experiments/responsive-commons/RESULTS.md) preserves every cell,
the inaccurate-evidence cases and the warmup/threshold null controls. No inferential
interval is manufactured for deterministic enumeration.

### Current graph result

The new `nipd_graph` world has canonical undirected adjacency, local observations,
explicit sum/mean payoff aggregation and defined isolate semantics (ADR-0011).
It retains the historical complete-population engine and input hashes. The
[18-cell exploratory experiment](experiments/graph-topology/RESULTS.md) fixes N=5,
one AllD, eight rounds and mean edge payoff. All full cooperation curves match
the predictions made before execution; all original sealed runs replay.

The ring delays linked TFT's defection cascade by one round relative to the
complete graph. Star outcomes depend strongly on whether AllD occupies the hub
or a leaf. Pairwise cooperation counts directed edge votes, whereas neighborhood
cooperation counts one vote per nonisolated agent; these units must stay explicit.
Symmetry-equivalent seats add no independent replication. A four-cycle exact
counterexample shows why total cooperator count is insufficient to determine
the sparse-graph pTFT transition law. The complete-graph benchmark is not reused
without a new state-space justification.

### Provider execution capability

[PR #82](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/82) supplies an
explicit non-streaming OpenAI-compatible transport, selected-credential preflight,
run/branch opt-in and stable failure categories. Validation and recorded-action
replay stay offline. Measured per-request partial sums and coverage accompany
honest null totals when any usage is unknown. Costs remain null. A continuation
records only its own calls/transcripts and current source/runtime provenance;
known transport or reported-model confounds are rejected by factorial analysis.

Every transport response/failure used in verification was mocked. This does not
establish live compatibility, billing, provider determinism, a total wall-clock
deadline or an episode dollar budget. Configuration and operator commands are in
[PROVIDER_USAGE.md](docs/PROVIDER_USAGE.md).

### Preserved Study 002 result

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

The responsive EC original source was clean local
`25904e5ce84d9ed642bed5874192391ff1297729`, identical in full tree to the
[published source](https://github.com/Chris0Jeky/collaborative-hill-lab/commit/0e12c42fc8819e6d92c4153f06760c7996a5d237).
Its [provenance](experiments/responsive-commons/SOURCE_PROVENANCE.json) records
the actual original environment, including setuptools 84.0.0; later full-lock
84.1.0 validation reproduced the readout without rewriting that history.

The graph original source was clean local
`873666aa9dfe1de7cc76d31275b4828fa44e065d`, matching the published
[source checkpoint](https://github.com/Chris0Jeky/collaborative-hill-lab/commit/78caa2a98c62c1818227e90886525d6f2aa19eb0)
and tree `875823c171036dcf40a0b9f2834074bce7ad05f9` before execution. Its
[separate source mapping](experiments/graph-topology/SOURCE_PROVENANCE.json)
preserves the original JSON/Markdown/execution-source bytes and verifies 71 file
commitments. Original graph RESULTS.json SHA-256 is
`69349116386452e913e1eabc546082a9d052d8993fc3a2dbb5f134658fe6a099`.
Both new experiments remain unfrozen and separate from Studies 000/001/002.

The original 498-run evidence is also retained in the session deliverable
`collaborative-hill-pass2-original-evidence-2026-10-29.zip`, SHA-256
`107ea42fd282130b9f8d4cb3899d828205b1e37337c9cb73d13bcc83e0522459`.
It contains 2,374 original files, separate published-source mapping records,
per-file checksums and a byte-reproducible repack script. All 498 seals, 66,714
event records, 552 checkpoint bindings and 120 source-file commitments were
verified before packaging. Original on-disk artifact contents and modification
times are unchanged; ZIP entries use fixed timestamps for reproducible packaging.

## Reproduce and verify

```bash
make setup
make check test validate acceptance check-atlas check-study002 check-responsive check-quality-safeguards check-graph check-sparse-ptft
make study-002-plan
make study-002 STUDY002_ARTIFACTS=artifacts/study-002-fresh
```

Use a fresh artifact root for execution. The last command generates both component
studies and their report. `make check-study002` validates canonical inputs and
byte-identical benchmark JSON/Markdown/SVG without running more episodes or
rewriting evidence. Setup downloads pinned dependencies; science gates call no
model provider. Direct commands and other workflows are in README and Makefile.

The final graph head `535ad44062657023e50bc1ab48a714d823640abe` passed the full
**1,198-test suite** in hosted CI, Ruff, strict package mypy in 50 files, all four
historical StudySpec validations, **11/11 acceptance scenarios**, atlas/Study 002
checks, all 480 responsive regenerations and the 18-run graph gate. Its final
checkout was clean. All 38 committed dependency pins were installed, including
setuptools 84.1.0. Local integration used Python 3.12.14; hosted CI used 3.12.15.
The strengthened historical-provenance checks have 37 focused regression cases.
Engineering verification reruns add no independent scientific samples.

Independent reviews checked policy observation boundaries, provider failures and
continuation accounting, exact graph arithmetic and all 18 trajectories using a
separate payoff/action oracle. The graph gate compares all scientific/identity/
seal fields while allowing a new execution to record its own source annotations.
It separately checks the untouched original source and published-mapping records.

Exact published-head Actions logs are the hosted verification record. The final
integration/documentation PR carries its own current check; no human review is
claimed from automated or agent reviews. CI now covers Ubuntu and Windows on Python 3.12,
not macOS or a multi-version matrix.

## Dependency maintenance following the integration checkpoint

[PR #71](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/71) updates the
setuptools lock pin from 84.0.0 to 84.1.0. Its original successful CI predated
Study 002, so it was refreshed onto the integrated main branch for the complete
current gate set. The PR retains the original bot commit, review evidence and
exact-head checks; no force update was used.

A separate venv passed fresh locked setup/editable installation, all 38 pin checks,
sdist-to-wheel construction with the installed backend, wheel-content/license/
entry-point checks, `pip check`, and isolated installed-package CLI/Study 000
validation from outside the checkout. The original shared environment and run
records were not rewritten. This follow-up changes the build dependency pin and
the maintenance record, not simulator behavior or any scientific input/result.

## Remaining directions and limits

Issues #76–#78 and #84–#86 are implemented. NEXT separates these offline engineering/research tasks from pilot-dependent
hypotheses, weights, sample size and freeze decisions.

The legacy C/F baselines do not respond to incentives or attribution; the new
conditional policy responds to visible participation, not utility weights. All measured
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
