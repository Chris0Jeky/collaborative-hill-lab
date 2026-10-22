# BUILD_LOG — executed work and verification

All prior entries through 2026-10-21 are preserved byte-for-byte in
[the historical build log](docs/history/BUILD_LOG-through-2026-10-21.md).
This split keeps the current checkpoint readable without deleting its evidence.
The historical blob is `9b56ad16204941e080782f1459be3b156699c858`; the historical
handoff blob is `a3c817bc915147c00fa89eaffd1447358205d996`.

## Counterfactual replay, comparisons and tutorial — 2026-10-22

Authoritative starting main: `fa6c3875024704c5d774afece94dd872fc2f9b10`.
GitHub showed no open issues/PRs. The available ZIP was older; its runtime source
was reconciled with GitHub before development. Unpublished edits described by the
previous session did not survive. This pass rebuilt and published the work rather
than claiming those drafts were already landed. All publishing used connected
GitHub branches, trees, commits and PRs, with expected-head leases and no force push.

### Regression and implementation evidence

- The initial 49 counterfactual cases failed on the original runtime. The fixes
  re-execute ancestral run-ID segments, bind snapshots to sealed boundary events,
  check manifest/scenario/seed/seal consistency and protect inherited policies.
- Further fail-first cases reproduced inherited usage totals, malformed checkpoint
  records and invalid CLI inputs. The new child continuation has no measured
  tokens/cost, so those fields are null rather than copied parent measurements.
- The automated review on #54 found a terminal branch whose next fork copied no
  direct-parent event. Four new cases reproduced it. Such inherited checkpoints
  are rejected before output reservation; ordinary terminal branches still replay.
- All 21 comparison cases failed before the command was implemented. Their passing
  counterparts cover fresh metrics despite forged caches, deterministic read-only
  output, failed-run outcome exclusion, incompatible mechanisms and corrupt input.
- A hand-derived N-IPD oracle checks six rounds of AllC before/after a fork at round
  two: baseline utilities (36, 36, 36), child (24, 24, 52), deltas (-12, -12, 16).
- The real subprocess tutorial test failed before implementation and then passed.
  It covers six replays, changed first-fork actions, unchanged grandchild actions
  and utilities, occupied-output refusal and preservation of checked-in studies.

Hosted lint initially identified a complex validation function, fixture-import
formatting, one long tutorial line and missing explicit subprocess check flags.
These were corrected and the unchanged gates rerun; no lint rules were disabled.
Some combined local runs exceeded the 45-second execution limit. Those runs are
not recorded as passing; completed hosted runs below provide full-suite evidence.

### Exact hosted verification

A temporary branch `verify/counterfactual-20261022` supplied a read-only-permission
Actions workflow with pinned checkout/setup-python actions and no persisted Git
credentials. It was not included in either product PR or merged into main.
Each verification tree matched the product tree except for that workflow file.
The job logged exact source, test and script subtree hashes.

Commands executed on fresh Ubuntu/Python 3.12.15 runners:

```bash
make setup PYTHON=python
.venv/bin/python -m pip check
PYTEST_ADDOPTS='-o addopts=--strict-markers' make check test validate
.venv/bin/python scripts/acceptance.py
.venv/bin/python scripts/counterfactual_demo.py --out artifacts/verification-demo
```

The last command ran only for the comparison/tutorial candidate where it exists.
The pytest override preserves strict markers and exposes test counts in the log.
It does not filter tests or weaken the assertions.

| Candidate | Verification commit | Actions run | Results |
|---|---|---|---|
| PR #54 final head `2907186204fd8798a1bf0967ec6fb117a50156c8` | `b321c0c23b4143a7b50e79e0b6e0c9ff0a862ec0` | [39782298597](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/39782298597) | 499 full-suite / 266 unit-property; mypy 42 files; Ruff; both study hashes; acceptance 11/11 |
| PR #55 final head `4355c6c889667868fdad423af2a670055fe58dfa` | `24fd01f63a01e7673ba9499f30b9a29119ae1fde` | [39783806030](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/39783806030) | 521 full-suite / 266 unit-property; mypy 43 files; Ruff; both study hashes; acceptance 11/11; six-run tutorial |

Both fresh installations used the unchanged 38-pin dependency lock and passed
`pip check`. Unit/property counts are a subset of full-suite counts, not additive.
The final product tree is `5b5f7a480f621044f17cd825bf49962e1667d7f0`.
Its logged and GitHub-verified subtrees are:

| Path | Tree SHA |
|---|---|
| src | `2853a7b2dad161a91fe4a6db989bc336bc2913b6` |
| tests | `927173d2fb8b3ed21196ccd97496bddf9f5cfe5e` |
| scripts | `851e84275ed056bfb58aecfa5ede1748446e2d40` |
| studies (unchanged) | `434667ae30295e03a633397b7713831104c8b849` |

Preserved study hashes:

- Study 000: `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f`
- Study 001: `a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe`

### Published result

PR #54 merged as `e0428cf00bcf6ac423ab1dadd5a82090fb75babb`; its reproduced review
finding was fixed, replied to and resolved. PR #55 was initially stacked on #54,
then retargeted to main and merged as `e754a961b2ef3df438adb0b8bc7925c9b35a0867`.
No review threads were present on #55 at its merge check. The final documentation
checkpoint changes no executable code, tests, dependencies or scientific inputs.

The hosted tutorial produced fixture-specific child-minus-parent utility changes
(-81, -81, -152) in `pw-3tft` and (0, 0, -7) in `attr-ledger`. All six sealed runs
replayed. A grandchild explicitly retaining the policy has no action difference
and zero utility deltas despite different run IDs and event hashes. These are
operational demonstrations, not statistical or human-behavior findings.

### Unverified / unchanged boundaries

No native Windows/macOS execution, multiprocess stress, power-loss recovery,
real provider calls, provider-exception replay or independent human review was
performed. Local Python 3.13 was partially provisioned, not the lock environment.
Policy IDs remain descriptive labels, not executable serialization or signatures.
Equal kernel seeds do not imply coupled provider sampling or reduced variance.
No study was frozen, no owner scientific decision was changed, and no paid model
run was made. T1, hook trust and the absence of persistent main CI remain unchanged.

## 2026-10-22 — E2 notebook-free analysis skeleton (feat/chl-analyze)

Step 0 confirmed no `analyze` command or analysis implementation existed. Read-only
Git checks confirmed a clean linked worktree before edits. No Git command that
writes was used, per the task's explicit boundary; changes remain uncommitted.

Added `reporting/analysis.py`, dependency-free `analysis_stats.py`, `chl analyze`,
the canonical scripted golden JSON, and 38 regression/oracle cases. Only verified
completed ledgers supply episode outcomes. Failures and invalid artifacts remain
visible as exclusions; copied episodes and branches never inflate sample sizes or
attrition denominators. The original extra misinformer condition is not pooled
into the factorial. No scenario, study definition, lock or checked-in hash changed.

Draft choices are explicit in output: equal-cell weighting and independent
within-cell bootstrap for legacy runs; complete declared blocks for eligible v2
scripted runs; 2000 draws from recorded `rng_for` streams rooted at 20261022;
type-7 percentile CIs; two-sided centered bootstrap p-values with +1 correction;
Holm across E1/E2/E3. Paired t intervals are checked against reference quantiles.
Zero-variance cells/contrasts suppress inference. Secondary summaries and effects
are non-confirmatory. Attrition includes a Pearson chi-square test with a sparse
expected-count warning. Invalid-rate and predeclared-exclusion sensitivity rows
remain explicitly not run because the SAP supplies no threshold/rules. No
scientific choice was frozen, and no simulation is presented as predicting humans.

Commands actually run from this worktree (PowerShell; temporary files kept here):

```powershell
New-Item -ItemType Directory -Force artifacts/analysis-check/tmp | Out-Null
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = Join-Path (Get-Location) 'artifacts/analysis-check/tmp'
$env:TMP = $env:TEMP
& ../assess/.venv/Scripts/python.exe -m ruff check src tests studies scripts
& ../assess/.venv/Scripts/python.exe -m mypy
& ../assess/.venv/Scripts/python.exe -m pytest tests/unit/test_analysis_stats.py tests/integration/test_analysis.py -q -p no:cacheprovider -o addopts=--strict-markers --basetemp artifacts/analysis-check/pytest-final-analysis
& ../assess/.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider -o addopts=--strict-markers --basetemp artifacts/analysis-check/pytest-final-full
& ../assess/.venv/Scripts/python.exe -m collaborative_hill.cli study validate studies/001-evidence-commons
& ../assess/.venv/Scripts/python.exe -m collaborative_hill.cli study validate studies/000-legacy-reproduction
& ../assess/.venv/Scripts/python.exe scripts/acceptance.py
git diff --check
git diff --name-only -- studies
```

Results: Ruff all checks passed; strict mypy no issues in **45 source files**;
focused analysis suite **38 passed** (14.02s); final full suite **557 passed,
4 skipped** (88.63s), versus the supplied baseline 519 passed/4 skipped. Both
studies validate, unfrozen, with hashes preserved:

- Study 000: `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f`
- Study 001: `a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe`

Acceptance: **11/11**. `git diff --check` passed and the study-path diff was empty.
Initial local lint/type errors were repaired before these green results. The
final full suite also covers the last change adding per-cell invalid-action
summaries and keeping duplicate/branch artifacts out of attrition denominators.

NOT verified: R2 pilot/real-provider data, stochastic provider coupling, a frozen
SAP or confirmatory interpretation. Residual risk: bootstrap test/count/seed and
attrition estimator remain draft choices; sensitivity analysis awaits declared
rules. Human decisions remain in `HANDOFF.md` (`human_todo=null`). No Git writes,
publication, installs or network access. Intended commit:
`feat(analysis): add chl analyze for the Study 001 2x2 from sealed runs`.
