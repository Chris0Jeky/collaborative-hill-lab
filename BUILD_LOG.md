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

## 2026-10-22 — PR #58 analysis review fix round

Step 0: clean linked worktree on `feat/chl-analyze`, HEAD
`e6bf84b171d2b26daa76c1db59a0682c1505a233`. Both findings still existed.
No network, installs or Git writes were used. All temporary outputs stayed under
ignored `artifacts/analysis-fix/`; only the supplied sibling venv was used.

Added `invalid_llm_output_abstentions` to episode rows and per-cell summaries.
Count only proposed abstentions with reason `invalid_llm_output`, once per
proposal, rather than counting both proposed and accepted ledger entries.
Mechanism rejection and fallback counts retain their meanings. The analysis
invalid-action rate now includes parser failures plus rejections; it does not
double-count rejection fallbacks or count ordinary abstentions. This combined
rate feeds the existing per-cell invalid-output reporting. Sensitivity exclusions
remain explicitly not run until a threshold is declared. Existing versioned
operational metrics, production bootstrap code and study inputs are unchanged.

Regression evidence:

- All-malformed and mixed-output integration cases failed before the production
  fix with `KeyError: invalid_llm_output_abstentions` (2 failed, 17 deselected).
  A preliminary test-authoring typo (`spec.agents` rather than
  `spec.cognition.agents`) was corrected before this meaningful red run.
- The all-malformed case produces 36 exhausted-parser abstentions per episode;
  the mixed case produces 12 parser abstentions, 12 mechanism rejections/fallbacks
  and 12 ordinary abstentions, with invalid-output rate `2/3`.
- The new independent bootstrap oracle supplies nine literal indices for three
  replicates of size three, asserts all nine `randrange(3)` calls, and checks
  hand-derived replicate means `[4, 10, 4]` for values `[0, 6, 12]`.
- An in-memory mutation doubled the observation list before calling the original
  bootstrap helper, hence sampling 2n. Before adding the oracle, all 21 statistics
  tests still passed (1.84s). With the oracle, that same mutation failed on the
  exhausted index stream (1 failed, 0.93s). The normal helper passes.
- Re-executing the original analysis source from `git show HEAD:...` in memory
  on the same 12 verified completed malformed-output episodes gave rejection=0,
  fallback=0, rate=0. Fixed analysis gave parser=36, rejection=0, fallback=0,
  rate=1 for every episode; neither analysis excluded an episode.
- The golden JSON was compared against `HEAD`: stripping the 16 new zero-valued
  fields (12 episodes, four cell summaries) exactly reproduces the old canonical
  JSON. No existing field/value was changed.

Commands actually run (PowerShell, from this worktree):

```powershell
New-Item -ItemType Directory -Force artifacts/analysis-fix/tmp | Out-Null
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = Join-Path (Get-Location) 'artifacts/analysis-fix/tmp'
$env:TMP = $env:TEMP
$env:HYPOTHESIS_STORAGE_DIRECTORY = Join-Path (Get-Location) 'artifacts/analysis-fix/hypothesis'
& ../assess/.venv/Scripts/python.exe -m pytest tests/integration/test_analysis.py -k parser_failure -q -p no:cacheprovider -o addopts=--strict-markers --basetemp artifacts/analysis-fix/pytest-parser-red-verified
& ../assess/.venv/Scripts/python.exe -m pytest tests/unit/test_analysis_stats.py tests/integration/test_analysis.py -q -p no:cacheprovider -o addopts=--strict-markers --basetemp artifacts/analysis-fix/pytest-focused
& ../assess/.venv/Scripts/python.exe -m ruff check src tests studies scripts --cache-dir artifacts/analysis-fix/ruff
& ../assess/.venv/Scripts/python.exe -m mypy --cache-dir artifacts/analysis-fix/mypy
& ../assess/.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider -o addopts=--strict-markers --basetemp artifacts/analysis-fix/pytest-full

## 2026-10-22 — Recorded provider-failure replay (local, uncommitted)

Step 0 reproduced the gap before product edits: FakeProvider failed for `a2` on
call 1 in `attr-ledger`; its sealed 17-event ledger diverged on replay at seq 16
(`RunFailed` versus a different `RunFailed` reason). The first new regression also
failed before the fix, at seq 4 for an immediate `a1` outage.

Replay now decodes the existing `policy error for AGENT: ProviderError: MESSAGE`
seal and raises that typed error from ReplayPolicy at the recorded round. The
unchanged runner regenerates every engine event and final state/seal; conflicting
proposals refuse explicitly and chain mismatches report an inconsistent recorded
failure. Invalid-output abstentions remain recorded typed proposals. No event,
manifest, seed protocol, study hash, runner behavior, or ADR was changed. Messages
are recorded inputs; provider sampling and arbitrary exception classes are outside
this replay scope. Thirty offline regressions include rehashed/pinned mutations,
absent transcripts/checkpoints/parents, no-provider guards, both seed protocols,
failure during retry, and attempted failure after engine completion.

All commands ran from this worktree with `PYTHONPATH` set to its `src`,
`PYTHONDONTWRITEBYTECODE=1`, and `TEMP`/`TMP` set to the existing
`artifacts/replay-failure-step0` directory. No installs or network were used.

```powershell
& ../assess/.venv/Scripts/python.exe -m ruff check src tests studies scripts --cache-dir artifacts/ruff-cache
& ../assess/.venv/Scripts/python.exe -m mypy --cache-dir artifacts/mypy-cache
& ../assess/.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider -o addopts=--strict-markers --basetemp=artifacts/replay-failure-full
& ../assess/.venv/Scripts/python.exe scripts/acceptance.py
& ../assess/.venv/Scripts/python.exe -m collaborative_hill.cli study validate studies/000-legacy-reproduction
& ../assess/.venv/Scripts/python.exe -m collaborative_hill.cli study validate studies/001-evidence-commons
git diff --check
git diff --exit-code HEAD -- studies
```

The two mutation runs used this in-memory wrapper via the supplied Python's
stdin; `selection` was the whole statistics module before adding the oracle,
then the new oracle's node ID. `output` was respectively
`artifacts/analysis-fix/pytest-mutation-baseline` and
`artifacts/analysis-fix/pytest-mutation-red`:

```python
import pytest
from collaborative_hill.reporting import analysis_stats
original = analysis_stats.bootstrap_means

def doubled(values, **kwargs):
    return original(list(values) * 2, **kwargs)

analysis_stats.bootstrap_means = doubled
raise SystemExit(pytest.main([selection, '-q', '-p', 'no:cacheprovider',
    '-o', 'addopts=--strict-markers', '--basetemp', output]))
```

Final results: focused analysis suite **41 passed** (19.79s); Ruff all checks
passed; strict mypy no issues in **45 source files**; full suite **560 passed,
4 skipped** (112.04s), against baseline 557 passed/4 skipped. Acceptance
**11/11**. Both studies validate, unfrozen, with unchanged hashes:

- Study 000: `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f`
- Study 001: `a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe`

`git diff --check` passed; the diff against HEAD under `studies/` is empty.
NOT verified: real-provider runs, provider randomness coupling, R2 pilot or
confirmatory inference/SAP freeze. Residual risk: analysis remains draft and
sensitivity exclusions await human-declared rules. Human decisions remain in
`HANDOFF.md` (`human_todo=null`). Work remains uncommitted under the explicit
no-Git-writes rule. Intended commit:
`fix(analysis): count invalid-LLM-output abstentions and pin the bootstrap draw size`.

```

Results: Ruff clean; strict mypy clean (43 source files); **549 passed, 4 skipped
in 142.97s** (baseline 519 passed, 4 skipped); acceptance **11/11**; both studies
valid with unchanged hashes `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f`
and `a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe`.
The pytest addopts override keeps strict markers and exposes the result counts.
The earlier focused suite passed 28 cases before the final two cases were added;
all 30 are included in the passing full suite.

The preserved Step-0 ledger now replays all 17 events with identical hashes/seal.
An optional `python scripts/replay_smoke.py` run refused deliberately corrupted
negative-test ledgers and a replay scratch ledger lacking a frozen scenario,
because its broad `artifacts/*/*/*/events.jsonl` glob also discovers test output.
No script repair was needed for this fixture-layout issue. The same smoke entry
point passed **1/1** with only the unchanged Step-0 fixture in scope:

```powershell
@'
from pathlib import Path
from shutil import copytree
import runpy
source, = Path('artifacts/replay-failure-step0/runs').glob('*/*/*/events.jsonl')
root = Path('artifacts/replay-failure-smoke')
copytree(source.parent, root / 'artifacts' / 'fixture' / 'attr-ledger' / 'original')
smoke = runpy.run_path('scripts/replay_smoke.py')
smoke['main'].__globals__['REPO'] = root
raise SystemExit(smoke['main']())
'@ | & ../assess/.venv/Scripts/python.exe -
```

Use a fresh smoke root if repeating the copy. Arbitrary provider exception classes,
real providers, external publication, and independent human review were not
verified. Git was read only; nothing was staged, committed, pushed, or merged.
`human_todo=null`; HANDOFF.md's human-owned scientific decisions remain unchanged.
Intended commit: `feat(replay): replay sealed runs that ended in recorded provider failures`.

## 2026-10-25 — Issue #60: decode provider failures at the proposal boundary

Worktree: `.wt/ex-collaborative-hill-l-1`, branch `sol/ex-collaborative-hill-l-1`,
base/HEAD `8b7cdc1739c036be42206304f8013bf7ba7ea526` (equal to local `origin/main`).
The worktree started clean. Issue #60 was verified open through the GitHub connector.
All commands below ran from this worktree's root. No Git-writing command ran.

The initial shared Python 3.14 suite could not collect because Typer was missing.
An isolated Python 3.12.10 environment was installed without changing the lock:

```powershell
py -3.12 -m venv .venv
& .venv/Scripts/python.exe -m pip install --disable-pip-version-check -r requirements-lock.txt
& .venv/Scripts/python.exe -m pip install --disable-pip-version-check --no-build-isolation -c requirements-lock.txt -e '.[dev,analysis]'
& .venv/Scripts/python.exe -m pip check
```

Installation and pip check passed. Temporary files were directed into ignored
`artifacts/session-temp` using process-local `TEMP` and `TMP`; pytest outputs,
logs, caches, and the local venv are also ignored.

Before editing production code, the full suite passed **590 existing tests**,
with four skips. The four new cases initially failed scenario validation because
the fixture omitted required evidence; a valid synthetic item corrected that
fixture. The actual fails-without-fix proof then ran:

```powershell
& .venv/Scripts/python.exe -m pytest tests/metamorphic/test_replay_provider_failure.py -k prefix_ids -o addopts=--strict-markers -q --basetemp artifacts/red-tests
```

Result: **2 failed, 2 passed, 30 deselected**. The valid failed runs for agent
`a: ProviderError: alias` were decoded as failures of `a`, raising
`recorded provider failure for a conflicts with a recorded proposal`.
Both agents deliberately produce identical seal text, so choosing the longest
textual prefix would break the passing short-ID controls instead.

The decoder now uses the first unproposed agent in the terminal round's sorted
proposal order, then decodes only that agent's exact provider-error prefix.
The same regression command with `--basetemp artifacts/green-tests` gives
**4 passed, 30 deselected**. It verifies whole-chain and seal equality, CLI replay,
unchanged source artifacts, and that no provider is invoked during replay.

Final gate commands:

```powershell
& .venv/Scripts/python.exe -m collaborative_hill.cli doctor
$env:PYTEST_ADDOPTS = '-o addopts=--strict-markers --basetemp=artifacts/gate-tests'
make check test validate
& .venv/Scripts/python.exe scripts/acceptance.py
git diff --check
```

All passed: doctor all OK; Ruff clean; strict mypy clean in **45 source files**;
**286 passed, 4 skipped** for unit/property; **594 passed, 4 skipped** for the
full suite (175.61s); acceptance **11/11**. Study hashes remain
`5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f` and
`a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe`.
Generated logs live under ignored `artifacts/` and are not publication artifacts.

NOT verified: real providers, four pre-existing skipped filesystem cases, hosted
CI, or independent review. Residual risk: decoding depends on sorted runner
proposal order; regenerated-chain comparison remains authoritative. Human-owned
scientific decisions remain in `HANDOFF.md` (`human_todo=null`). Changes are
uncommitted; no PR was published under the no-Git-writes rule. Intended commit:
`fix(replay): decode provider failures at the proposal boundary`.

## 2026-10-28 — reject the false Study 001 social-dilemma certificate

Owned isolated worktree, freshly fetched base
`5a66e57de42d750171a68597470beabf0a7a3369`; primary checkout untouched.
Free RAM before setup: 13.38 GiB; before the serial gates: 11.26 GiB.
Installed the committed lock with
`make setup PYTHON=C:/AI/voice-lab-kokoro/python312/python.exe` (Python 3.12.10;
`pip check` clean). Git Bash did not find `make`; the existing Windows `make.cmd`
wrapper successfully ran the same Makefile. No dependency or policy edit.

Before editing the generator,
`.venv/Scripts/python.exe studies/001-evidence-commons/certificate.py` ran 32 episodes
and reproduced the checked-in report without a diff: four C2 failures (-20/-7 vs 0)
alongside a false CERTIFIED verdict. The new
`.venv/Scripts/python.exe -m pytest tests/unit/test_certificate.py -q` failed all seven
cases before the fix (the positive control reached its console-summary assertion;
the false-positive cases failed the verdict assertion). All seven pass after the fix.
The synthetic positive control uses benefit=1/2 per contributor and own cost=1:
unilateral gain=1/2 and all-contribute total=3/2 > all-freeride total=0.
Other controls cover absent C1, equal C2 totals, both absent and one failed institution.
The real-study case exercises the 32 sealed episodes without mocking the engine.

The verdict now requires every institution's C1 and C2; failed conditions are named.
C3 remains a separate integrity verdict, with truthful failure prose as well.
Removed the unconditional genuine-dilemma claim and corrected its current consumers
(READMEs, research claims, draft preregistration rationale and mechanism docstrings).
No policy, hypothesis selection, weights, scenario bytes or legacy reports changed.

Proof on this diff: `make check test validate` exits 0 (Ruff; strict mypy, 45 files;
293 unit/property passed, 4 skipped; 601 full-suite passed, 4 skipped).
`.venv/Scripts/python.exe scripts/acceptance.py` exits 0, 11/11 scenarios using synthetic
data and FakeProvider only. `git diff --check` passes. Fixed one new test line-length
error before the full gates; no pre-existing failures were dismissed.

Compared the entire pre-verdict report section against the executed baseline: identical,
including all C1/C2 numeric rows and C3 counts. A second corrected generator execution
is byte-identical (report SHA-256
`cba5d90334bb9473e6b5d04f827eb609693442ea6618080ad604a9e19f9fd92e`).
Full `validate_study` results before/after compare equal, including all scenario,
mechanism, narrative and evidence hashes, seed protocol and frozen=false for both studies.
Study 000: `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f`.
Study 001: `a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe`.
Git also confirms unchanged study JSON, Study 000, generator inputs, legacy replication
report and harness configuration. Proof logs are outside the checkout, not committed.

NOT verified: the four existing filesystem skips, real providers/humans, persistent
hosted CI (none configured), or full-strategy-space incentives. Independent review and
publication status are recorded on the PR. Residual risk: unchanged placeholder weights
fail C2. The owner product-direction park and all ten HANDOFF decisions remain in force;
this correctness repair neither unfreezes/freezes a study nor starts feature research.

## 2026-10-29 — Exact incentive-region atlas (bounded offline experiment)

Started from fresh `5a66e57` in an isolated detached worktree, then created
`codex/incentive-atlas-20261028`. Incorporated the separate certificate repair by
fast-forward to `4cfd4070f4f6d96346ec6625a056a9b2d153dca0`; this slice does not edit its
certificate, generator, report or production engine. Implementation is `51ba8c4`.
The owner-authorized exception covers this one offline experiment; the wider park
and all human scientific decisions remain in force.

The new experiment enumerates 32 ordered scripted profiles, extracts exact payoff
vectors from completed chain-verified seals, and derives 48 strict unilateral gain
inequalities plus four C2 comparisons. Wrong accepted slots retain the fixed public
penalty, while both positive and negative private credit scale. C1 always holds via
CFF->FFF; C2 gives private `b+7r>39`, shared `b+7r>45/2`. The README hand calculation,
CCC-exit contrasts and four admissible examples distinguish collective sums from
individual welfare, subsidy costs, equilibrium and behavioral response.

Red/green: the literal misinformation coefficient test failed against the initial
zero-vector stub, then passed with `U_i=(n_correct/3)b+k_i*r-4*n_wrong-effort_i`.
27 focused cases now include strict ties and near-boundaries, negative domain and
float refusal, C1 false/true controls, unchanged input identities, overwrite refusal,
detected action/payoff drift, and all 32 profiles at six fresh-engine probe points.
Each point also replays one standard run; denominators 2 and 3 are tested together.

Proof commands, from the owned repository root, with its `src` on `PYTHONPATH` and
the existing installed environment's Python 3.14.3 (no install or dependency change):

```text
python -m pip check
python -m ruff check experiments/incentive-atlas tests/unit/test_incentive_atlas.py
python -m mypy --strict --follow-imports=silent experiments/incentive-atlas/atlas.py
make PY=<installed-python> SHELL=<Git-Bash-sh> check test validate
python scripts/acceptance.py
python experiments/incentive-atlas/atlas.py --out artifacts/atlas-first
python experiments/incentive-atlas/atlas.py --out artifacts/atlas-repeat
```

All exit 0: no broken dependencies; Ruff/strict mypy clean; 320 unit/property and
628 full-suite tests pass with the same four pre-existing filesystem skips;
acceptance 11/11. Collection inventories are 324 and 632, including those skips.
A standard `run_report` also reads `baseline/atlas-attr-priv-CCC` and reports its
expected -6/-7/-7 utilities. The larger commands used the shared exclusive heavy-job
helper and its 6 GiB admission guard (measured 8.07-9.33 GiB free at admission).
Occupied-slot deferrals launched nothing and were not counted as test failures;
the slot was released to the queued product lane after the finite proof.

Each generation ran 224 fresh episodes and six replays. Compared both `atlas.json`
and `REPORT.md` byte-for-byte, then all 224 `events.jsonl` files: identical. Atlas
SHA-256 is `925596962b752f49a9f46cefe83bfda3332f7e40e98aba74c97b3a05e918310b`;
report SHA-256 is `ab6554bfb849c03eabe6a4818ba7d616861abf89d3e06c7d12183f5329fd3cc6`.
Generated operational artifacts remain outside Git; reproducible code and methods
are committed. Original study JSON is byte-unchanged from `5a66e57` and all studies
are unchanged from repair merge `4cfd407`. Both full validation snapshots agree:
Study 000 `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f`;
Study 001 `a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe`;
both frozen=false. No new lock or freeze was created.

One fresh-context Terra high read-only review of `4cfd407..51ba8c4` and the generated
artifact found no blocking mathematical/methodological or correctness findings.
The reviewer checked quantifiers, complete coverage, strict boundaries, wrong-slot
penalties, rational scaling, C3 and the literal oracles; it did not rerun generation
or the full suite. PR publication/merge state is recorded on the PR, not inferred.

NOT verified: other platforms, four skipped filesystem cases, real providers/humans,
full-strategy-space incentives, behavioral effects, power or published findings.
Residual risk: minted credit can buy C2 without improved quality; collective sums
do not imply Pareto improvement or equilibrium. No default weights were selected.

## 2026-10-29 — Repository-wide research engine advancement

The owner authorized broad inspection, implementation, parallel work, PR updates
and merging safe changes. GitHub was authoritative throughout. On entry, main was
`8f4e25e8861fe5ba85f2cc7d83ee9319c167914e`, with no open issues or PRs. The uploaded
source ZIP's archive identity and all 206 file blob hashes matched its remote tree
`44a304134490fab0afc09d150163e35a1acf5aa5`; executable modes were reconciled before
local work. Remote reads and publication used the connected GitHub API. Local Git
commits have different ancestry from the published commits and are identified as local.

The Python 3.12.14 environment installed the committed 38-pin lock through
`make setup`, followed by `pip check`. Initial local network restriction blocked
the install; approved execution of the same setup command succeeded. No equivalent
GitHub network workaround was attempted. Baseline `make check test validate` and
acceptance passed: 632 tests and 11/11 scenarios. Studies 000/001 were unfrozen
with the unchanged hashes recorded in HANDOFF.

### Persistent verification and integrity repairs

- **#69 / #64:** added persistent Ubuntu/Python 3.12 CI with immutable official
  action refs, read-only token, exact-head checkout, lock installation, complete
  quality/study/acceptance gates, atlas generation and a clean-workspace check.
  The atlas gate generates under a temporary directory and removes it afterwards.
- **#70 / #65:** fifteen pre-fix failing regressions reproduced non-treatment
  confounds, contradictory retries, misplaced identities and failed-only protocol
  loss. The analysis now compares declared populations, checks failed eligible
  attempts, preserves identical-copy exclusions and rejects conflicting units.
  Independent-run and paired-block scopes differ explicitly. Valid golden output
  and statistical formulas remain unchanged; literal bootstrap-tail and Holm
  expectations add an independent numerical check.
- **#74 / #68:** shared built-in policy contracts reject unknown keys, invalid
  epsilon/threshold ratios and denominator settings before execution. Validation
  does not rewrite stored values or insert defaults. Forty-six new cases cover
  direct configuration and CLI boundaries, including exact rational endpoints;
  all 16 original resolved scenarios retain their serialization. Unknown policy
  names remain schema extension points, subject to the existing execution registry.
- **#75 / #67:** thirty initial failing cases reproduced invalid condition paths,
  count coercion and escaping output links. Review then reproduced later static
  file/dangling-link blockers, canonical aliases and nested run destinations.
  All 35 new real-filesystem/validation cases pass after complete destination
  preflight plus per-run rechecks. Explicit root symlinks and empty directories
  remain supported; concurrent ancestor replacement is outside this static guard.

The individual PRs passed exact-head Actions, with every job step and the logs
inspected, and no unresolved threads/comments at merge. Their run URLs are in
HANDOFF. The combined first five merges passed main CI at
`bfd49d5c3e1e00bcfba2497b42ba05e04373bf9b`:
[Actions 40803992791](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40803992791).
Local combined verification before the mathematical extension passed all 774 tests,
Ruff, strict package mypy, study validation, 11/11 acceptance and the atlas gate.

### Study 002 execution (#73 / #66)

Local commit `cf08170937d7a0b50fc6b23bf02b2649bddeb154` recorded the analytical
predictions before execution. Local implementation commit
`d4b8de90fe8317a0522764ca53b86727db93179c` supplied the clean run source. The
design has 29 deterministic cells × 1 episode plus six stochastic cells × 32,
50 rounds per episode, independent condition streams and a predeclared final
ten-round window. Canonical generation, plan mode, safe fresh-output execution
and identity-bound sealed-ledger reporting are included.

Commands executed in the study worktree with its source on `PYTHONPATH`:

```text
python studies/002-nipd-sensitivity/generate_study.py --check
python studies/002-nipd-sensitivity/run_study.py --artifacts artifacts/study-002
python studies/002-nipd-sensitivity/generate_report.py --artifacts artifacts/study-002 --output studies/002-nipd-sensitivity/RESULTS
```

All 221 episodes completed and sealed. All 29 full deterministic cooperation
paths and exact payoff vectors match hand-derived predictions. The measured
N=5,m=4 include-self replicate r000 replay verified 1,056 events; three deterministic
replay integration cases also passed. Report regeneration was byte-identical.
Review found a report-output overwrite gap; both destinations
are now preflighted, identical output is a no-op, and divergent output is refused.
The final isolated study branch passed 677 tests, explicit strict mypy for its
four modules, all four StudySpec validations and 11/11 acceptance.

All 192 observed stochastic episodes absorbed within the horizon and all final
windows were zero. Positive analytical expectations are retained. The N=3,m=2
include-self expectation outside its marginal bootstrap interval is reported
explicitly; the original 32 episodes and 2,000-draw bootstrap settings were not
changed. The report is exploratory and does not treat agents or rounds as replicates.

To make source-content provenance remotely recoverable, published commit
`16e7c45634eb2fdaa0d70e1933c7a966f3da6967` preserves the exact execution tree
`4fb241428f18e8e4013324be6905d31b986edfe4`. Tree equality was checked through the
GitHub API. SOURCE_PROVENANCE retains 88 file commitments and maps local to
published identity. Publication timing is not represented as preregistration
timing. The raw ledgers remain generated artifacts; the committed summary retains
per-episode terminal commitments and outcomes.

The original execution artifacts were subsequently packaged as
`Study002_Original_Sealed_Runs_2026-10-29.zip`: 1,768 unchanged original files,
12,362,482 compressed bytes, SHA-256
`1a72382d9ca014b3856af4451c3c425b03fa3034a9a38674bf58627a49c3108d`.
All 221 terminal hashes match RESULTS.json. The archive includes extraction and
rederivation instructions plus per-file SHA-256 commitments; ZIP CRC and every
included file checksum were verified. It is supplied separately to the owner,
while generated raw ledgers remain outside Git.

### Exact finite-population pTFT extension (#79 / #72)

This deliberately post hoc extension derives transition probabilities and first/
second moments using exact rational arithmetic. The episode/window variance
includes both halves of the cross-round covariance sum. The report distinguishes
F40 (a completely zero final window) from F49 (absorption by the last round),
computes independent contrast variance by addition and keeps large probability
powers as exact base/exponent expressions. Only displayed decimal approximations
use Decimal. It changes no simulator sampling, original readout, source provenance,
study input or bootstrap setting.

Core local commit `9660902b39932fdd1966c0efbd426869217d0294` adds 55 tests,
including literal moments and independent labelled-state/history enumeration.
The independent reviewer separately enumerated N=5,m=3, four-round full/window
moments and confirmed the six geometric mean curves. Report local commit
`3468e936870cf25fe4de709a77eb4683b42a8fdf` adds 20 integration tests, Markdown,
exact JSON and an SVG. Independent report review reproduced ambient Decimal
rounding drift; the author also reproduced inherited Matplotlib style drift.
Both failed before fixes and pass with isolated contexts and restoring style
settings. The committed figure matches a freshly regenerated SVG byte-for-byte;
its Inkscape PNG was visually inspected by two reviewers. No layout or misleading
scale issue remained. The report lane's exact HEAD passed all 752 tests and
11/11 acceptance independently of root integration.

The report validates the two study hashes, all 221 episode identities, six fixed
stochastic cells, 32 episodes per cell, and retained summary arithmetic. It records
the original RESULTS.json SHA-256 and the benchmark source hash. This is a
summary-level consistency audit, not a fresh replay of the original ledgers.
For N=5,m=4 include-self, P(all 32 final windows zero) is approximately
0.991638924269 under the ideal model. That event probability is not a p-value.

### Integrated commands, documentation and verification

The Makefile now exposes `study-002-plan`, `study-002` and `check-study002`;
`STUDY002_ARTIFACTS` selects a fresh root, with paths quoted. Validation includes
the two Study 002 components. CI additionally checks the six study modules and
read-only byte regeneration of the benchmark JSON/Markdown/SVG. Dry-runs checked
an artifact path containing spaces; `make study-002-plan` confirmed the 221-episode
plan without creating output. Full execution/report behavior is covered by the
study pipeline and report tests; no extra 221-episode exploratory sample was
added merely to exercise a Make wrapper.

At integrated local code commit `fe5c81d`, these commands completed successfully:

```text
make check test validate acceptance check-atlas check-study002
python -m pytest --collect-only -o addopts='' -q tests
make study-002-plan
git diff --check
```

Result: Ruff clean; strict package mypy in 45 files; 438 unit/property cases and
**849 total tests**, with no skips in this Linux run; all four unfrozen StudySpecs;
11/11 acceptance; exact atlas verification; strict mypy in six study-local modules;
canonical study bytes; and byte-identical benchmark/figure regeneration. The 438
cases are part of the 849, not additional independent tests. Documentation and
the published-provenance mapping were uncommitted at this local verification;
this is not described as a clean study execution. Exact-head hosted evidence for
the published integrated source is attached to #79; the documentation PR carries
its own current check.

README, NEXT, PLAN, HANDOFF and the contributor commands now describe the actual
engine. The prior handoff was archived with identical SHA-256
`dac1e69557d4fdc098defa8237adecc75f8919c149ae37cbf9e567edca14d647`.
Scientific review corrected older structure-only causal claims, C3 overgeneralization,
the false exclusion of institution from mechanism hashes, unconditional skin-chain
equality, assumed original CRN pairing and blanket requirements for uncertainty
intervals. A second review confirmed the revisions. The ten owner decisions are
verbatim, and tier/hook/permission rules are unchanged.

Issues #76–#78 provide bounded next increments: responsive Evidence Commons
baselines, configurable provider transport with offline contract tests, and
versioned graph semantics. The roadmap separates immediate engineering from a
bounded pilot and the later pilot-dependent confirmatory design, removing the
old circular sample-size/freeze dependency. No utility weights, confirmatory
hypotheses, provider budget or publication claim were chosen. No study was frozen,
and no real or paid provider or human-subject data was used.

## 2026-10-29 — Review and refresh Dependabot PR #71

The final open-PR sweep found Dependabot's setuptools 84.0.0→84.1.0 update.
Its original head `662cad71e8f4954af6633899ea1d3c675c432d8b` has a one-line
lock diff and green [CI 40802634286](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/40802634286),
but that run predates Study 002. It had no comments or review threads. The
source/test/workflow integration and documentation had since landed through #80.

The [official release notes](https://setuptools.pypa.io/en/stable/history.html#v84-1-0)
describe unsafe-archive rejection and legacy namespace-install hardening. The
repository uses the PEP 517 `setuptools.build_meta` backend, with no inspected
calls to `archive_util`, `install_as_egg` or `setup_requires`, no custom backend
and no compiled extensions. A separate read-only compatibility review agreed
that the inspected build path does not exercise the changed legacy APIs.

Local review commit `abe311c1e17adc67f1005e79107051d9ab418d41`, based on the
integrated `4cc9119` tree, changes only the same lock line as the bot PR. The
reviewer created an isolated worktree/venv, leaving the shared environment at
84.0.0. `make setup` initially hit the sandbox proxy restriction; the approved
retry installed the new committed lock and editable package successfully.
All 38 installed versions match their pins, including setuptools 84.1.0.

Packaging proof used `setuptools.build_meta.build_sdist`, followed by pip wheel
with `--no-index --no-deps --no-build-isolation` against that sdist. The first
wheel invocation encountered the read-only default pip cache; an explicit
task-specific cache under `/tmp` resolved that environment issue. The resulting
wheel contains all 45 project Python files with source-identical bytes, the
correct project metadata, Python requirement, GPL license file and `chl` entry
point. It was installed only into the private venv. From `/tmp`, `python -I`
loaded the installed package and entry point from `site-packages`; `chl --help`
and Study 000 validation passed. `pip check` passed after both editable and wheel
installation. The exact committed lock diff matches the connector's PR patch,
and the review worktree is clean.

The bot branch is refreshed without force, preserving its original head and
current main as parents. The final PR retains the one-line dependency change
plus this short maintenance/handoff record. Its exact-head CI and final merge
state are recorded on [PR #71](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/71).
The broad local scientific suite was not repeated for this build-only update;
the refreshed hosted run checks all 849 tests, four StudySpecs, acceptance,
atlas and benchmark regeneration with the new pinned backend.
# 2026-10-29 — responsive Evidence Commons experiment (#76 / PR #81)

Added the observation-only conditional contributor described in ADR-0012, with
an exact inclusive peer quorum, declared warmup and conservative anonymous
distinct-contributor bound. The original contributor/free-rider behavior and
Study 001 inputs are unchanged. A review-found schema gap is closed: policy
parameters retain strict integer/string/boolean types instead of normalizing
float or byte inputs before hashing.

The locally predeclared design is in `experiments/responsive-commons/DESIGN.md`.
Its implementation was executed from clean local commit
`25904e5ce84d9ed642bed5874192391ff1297729`, whose tree exactly matches published
source commit `0e12c42fc8819e6d92c4153f06760c7996a5d237` in draft PR #81.
All 320 behavioral episodes and 160 fixed-action controls completed. Across
160 attributable-minus-aggregate comparisons, quality increased in 2, decreased
in 2, and was unchanged in 156. Actions differed in 4 comparisons. All 160
same-action controls preserved briefing, effort, quality and total utility.
Nine of 40 finite two-strategy cells satisfied the declared strict C1/C2 pair.
These are exact scripted outcomes of the declared grid, without sample-based
intervals, live providers, final Study 001 weight selection or a study freeze.

Independent review reproduced the positive/negative all-active trace arithmetic
and found a collector configuration-binding gap. Collection now requires the
declared policy IDs, study/run/replicate/seed metadata and fresh-run protocol in
addition to verified seals and matching resolved scenarios. The complete readout
retains every cell and deviation; `SOURCE_PROVENANCE.json` distinguishes original
source commitments and the actual shared interpreter from later verification.

Local validation: Ruff, strict package mypy (45 files), 907 tests, all four shipped
StudySpec hashes, 11/11 acceptance, the incentive atlas, six Study 002 standalone
modules/canonical inputs/exact benchmark, and the new `make check-responsive`
480-episode byte-identical regeneration gate. A first broad invocation used the
shared interpreter without the worktree's `PYTHONPATH`; it was discarded and
replaced by the correct worktree invocation. A local mypy SQLite cache was then
found malformed; the remaining standalone checks passed with a fresh cache.
These were local execution-environment problems, not skipped checks. The final
published head must pass the complete Actions gate with the full dependency lock.

# 2026-10-29 — configurable provider transport and complete workflow integration (#77)

Added an explicitly configured OpenAI-compatible, non-streaming transport using
only the standard library. Endpoint, requested model and token cap are required;
sampling remains exact in configuration, with wire representations recorded.
Credentials resolve only from the selected environment variable or direct Python
argument and never enter artifacts. Default requests do not retry ambiguous
failures; optional bounded HTTP 429 and action-format retries are separate.
Actual response model IDs, per-request token coverage and measured partial sums
are recorded. Incomplete totals and all unmeasured costs remain null.

Study/CLI execution requires an explicit provider-request flag, checks all
selected credentials before any request or output, and retains the existing
exclusive run reservation before policy construction. Validation and recorded
replay remain offline. Scripted replacements can branch a provider-parent run
without credentials. Real provider overrides still need execution opt-in.
Continuation manifests and transcripts include only new calls, clear inherited
provider/pricing data, and record the continuation's code/environment/timestamps.
The latter also fixes the old copying of parent execution provenance.

Independent review exposed two defects before publication: mutable execution
settings could disagree with captured provenance, and huge/deep action JSON
could escape the retry/abstain path. Read-only transport settings, drift checks
and bounded JSON-error handling fix both, with failure replay regressions.
The analysis layer also rejects known transport or reported-model confounds
within a declared block, retaining unknown pre-response failures as attrition
and preserving legacy scripted golden bytes.

The combined EC/provider tree passed all 1,037 tests, Ruff, strict package mypy
(48 files), four unchanged shipped StudySpec hashes, 11/11 acceptance, atlas,
Study 002 and the 480-episode responsive regeneration check. This local gate used
the isolated Python 3.12 environment with all 38 committed dependency pins,
including setuptools 84.1.0, and explicit source PYTHONPATH. Existing CLI/seed/
reservation/reporting test doubles were adapted to the new keyword interface;
the actual reservation and seed contracts were retained. Independent reviewers
also passed 14 workflow cases, 15 analysis provenance/golden cases and zero-
request credential/selection probes. Exact published-head CI remains the merge
gate. No live endpoint, billing, provider determinism or paid pilot was tested;
all provider responses and failures were mocked.

## 2026-10-29 — local graph semantics and original topology controls (#78 / #83)

Added `nipd_graph` as a separately versioned world with canonical undirected
adjacency, exact neighbor actions, local observations, explicit sum/mean edge
payoffs and isolate/vote-denominator rules. Local pTFT and quorum policies use
the actor's neighborhood; existing targeted/linked controls work through the
same opponent interface. Legacy complete-population mechanics and all four
historical StudySpec hashes are unchanged. Registry, CLI branches, seed audit
and provider observation rendering recognize the graph world.

ADR-0011 and the graph experiment README recorded analytical predictions before
implementation tests and original execution. Clean local source
`873666aa9dfe1de7cc76d31275b4828fa44e065d` has the identical full tree
`875823c171036dcf40a0b9f2834074bce7ad05f9` as published source checkpoint
`78caa2a98c62c1818227e90886525d6f2aa19eb0`, published before execution. All 18
deterministic episodes completed (144 rounds, 3,114 events), all full curves
matched their declared predictions and every original sealed run replayed.
An independent implementation reproduced every action, vote and terminal score.
Mean edge payoff, N=5, one AllD, eight rounds and zero exploration are fixed;
complete/ring/star topology, defector seat and reciprocity rule are explicit.
Symmetry-equivalent seats are controls, not independent replications.

The graph source record's 71 named file commitments match execution-commit blobs.
Original RESULTS.json, RESULTS.md and EXECUTION_SOURCE.json remain unchanged;
SOURCE_PROVENANCE.json adds the published mapping separately. Original JSON
SHA-256 is `69349116386452e913e1eabc546082a9d052d8993fc3a2dbb5f134658fe6a099`.
A four-cycle exact counterexample has the same number of cooperators in two
reachable configurations but different next-count laws, showing why the
complete-graph pTFT count-state shortcut needs a new justification on sparse graphs.

The integrated EC/provider/graph tree passed 1,167 tests, Ruff, strict package
mypy in 50 files, all four historical StudySpec validations, 11/11 acceptance,
atlas/Study 002 gates, the 480-run EC regeneration and all 18 graph regenerations.
A focused review then demonstrated that the first graph checker could ignore a
corrupted standalone source record and equate JSON `true` with integer `1`.
The retained-record checker now validates byte commitments, self-commitments,
cross-record source/tree/study/dependency links, inventory totals and original
cleanliness before running; canonical comparison preserves JSON types. All 37
focused cases pass, and the strengthened 18-run gate passes. The final suite
contains 1,198 cases. Original provenance is checked against historical evidence,
not against today's changed source, and no authenticity claim is added.

`make check-graph` validates canonical inputs, strict standalone types, original
records and fresh trajectories/payoffs/identities/seals. CI runs the same gate.
Final graph publication preserves the original source checkpoint as a parent,
merges current main after #81/#82 as another parent, and exactly matches the
reviewed local full tree `bf0135cfa4a164fdd49becbb92dde79458a86543`.
Hosted verification is attached to [PR #83](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/83)
at exact head `535ad44062657023e50bc1ab48a714d823640abe`.

## 2026-10-29 — research guidance, evidence retention and next increments

Updated current README/contributor guidance, the foundation review, research
charter, methods, claims, analysis inputs and study-input documentation for the
implemented EC/provider/graph capabilities. The original Study 002 data and
benchmark remain unchanged. The methodological review also corrected claims
that every scripted seat permutation is inert, that replicate ledger hashes
must match, or that equal stochastic observations imply a sample size of one.
Budget shortfalls now preserve the declared confirmatory reference and incomplete
record; adaptations must be predeclared, and later redesign belongs to a separate
follow-up. Provider repair completions and HTTP 429 attempts are separate in the
cost worksheet; historical measurements/formulas are retained.

The 498 original EC/graph runs are preserved in
`collaborative-hill-pass2-original-evidence-2026-10-29.zip` (7,073,568 bytes),
SHA-256 `107ea42fd282130b9f8d4cb3899d828205b1e37337c9cb73d13bcc83e0522459`.
Its 2,374 original files total 55,714,184 bytes. All 498 completed seals,
66,714 event-chain records, 552 checkpoint bindings and 120 source-file
commitments were checked; every terminal hash matches its retained report.
The archive keeps original and enriched provenance distinct, includes a per-file
manifest and repack script, and reproduces byte-for-byte after extraction/repack.
Original on-disk source/run files and modification times were not changed;
archive entries use fixed timestamps for reproducible packaging.

PR #81 merged after exact-head CI 40811251496; PR #82 merged after exact-head CI
40812620936. PR #83 merged after exact-head CI 40813963880/job 123250572911 passed
the full 1,198-case suite and every experiment gate on Python 3.12.15 with a clean
checkout. Merged main `1e759dd95b845a222ec65e95076c6d0d162f6403` has the exact
reviewed graph tree. The final documentation PR carries its own exact-head
check record. Follow-up issues #84–#86 define observable quality safeguards,
labeled-state sparse-graph pTFT and cumulative provider request planning/budgets.
The ten owner decisions, tier, hooks, licenses and unfrozen StudySpecs remain
unchanged. No real or paid provider, human-subject data or new confirmatory claim
was used. Verification reruns are regression checks, not added scientific samples.

## 2026-10-31 portability, feedback tooling and issues #84–#86

Local Windows 3.12 first showed 10 failures in `pytest tests/` over 6 minutes: nine were
CRLF byte differences, and one came from the desktop app's virtualized `AppData` Temp and
passes with `--basetemp` on a real path. Hosted Windows then exposed text-mode generator
writes. #88 merged at exact-head CI 41146442106 on Ubuntu and windows-2025.

Slices ran in worktrees outside OneDrive with one shared venv and `PYTHONPATH=src`: #85 by
GPT-6.1 Sol, #86 by a Sonnet worker, #84 by an Opus worker, and the fuzzer drafted by Muse
and repaired by the driver. Every substantive PR received a fresh-context review. Codex
confirmed one real defect in #90: a retry sent after cancellation during its delay. A
driver slip pushed conflict markers to the #91 branch; they were removed before merge and
never reached main.

`make mutants` with seed 20261030 and 6 mutants per file killed 55 of 72 using fast tests
only. After the metric oracles, a sample of 16 metric mutants killed 15, and the last
survivor gained its own test. Verification reruns add no scientific samples.

## 2026-11-02 — EC rule ablations, declared noisy corpora and review fixes

Completed the authorized offline follow-ups for #92, #95 and #96 in separate
checkouts and published reviewable draft PRs. At this checkpoint: noisy-corpus
PR #99 is at `f501a9a`, ablation PR #100 at `985defa`, provider PR #101 at
`66f50ce`, and lab PR #102 at `c0e810b`. PR #101 merged as
`a23a68a5bf8f04cd7bfd0be0293cfd9062ebdbff` after both exact-head jobs passed
CI 41385412412 and their logs were inspected; merge tree `8600b02` matches its
tested head. PR #99 passed both jobs in CI 41386097110, with logs inspected, and
remains a draft. No other merge is claimed here. Local integration includes later
review/type corrections `4306a2b` and `344b5e2` and has passed the complete local
gate. PRs #100 and #102 have passed Ubuntu; Windows and final integration remain
pending. Historical build-log entries and human-owned decisions are retained.

### Research designs, execution and findings

For #95, committed the complete four-component design and literal outcome table
before implementation. Local design `2ea2d56` maps to public `dde9b1b`; clean
execution source `160ed5b` maps to public `768c9a7`, with identical tree
`894ba0718172fba36985dd019e7972b188e8a619`. Both publications preceded original
`python experiments/ec-rule-ablation/ec_rule_ablation.py --out artifacts/ec-rule-ablation-20261102`.

The separately named ablation policy exposes screening, contradiction sharing,
challenges and the read-citation requirement without editing either v1 rule.
All 16 settings in six contexts and two hidden truths were retained: 192 behavioral
episodes, 96 fixed-action controls and 288 complete replays. All P1–P6 held,
including every hand-derived outcome. The readout keeps 384 single-component
contrasts and 396 higher-order contrasts with their conditioning bits and nulls.
The limited-inspection probe isolates citation reading; enabling it removes one
accepted slot under either truth and saves two effort units. Sharing, challenge
priority, finite time and quorum reopening explain nonadditive effects. All
96 truth pairs retain identical observations/actions, and 24 endpoints match the
unchanged conditional/skeptical typed actions. No prediction was revised.

For #96, local design `ecbc31c` maps to public `c675c63`; clean execution source
`f8c466d` maps to public `f04fa8a`, with identical tree
`606be7f7fb5952b7b701c1fd29505667f0c17954`. Both publications preceded original
`python experiments/noisy-corpus/noisy_corpus.py --out artifacts/noisy-corpus-original`.
All 64 behavioral worlds, 64 same-action controls and 128 complete replays were
retained. P1–P8 held. Six exact source-error rates and independent/fully correlated
error models reweight those same outcomes; they do not add samples.

At independent error `e=1/10` with distinct labels, skepticism raises selective
accuracy from `9/10` to `729/730`, lowers acceptance from `1` to `73/100`, and
lowers signed quality from `48/5` to `1092/125`. Its exact quality contrast is
`-12 e(1-e)(1-2e)`. Fully correlated distinct labels give identical expected
outcomes under both rules; collapsed labels make the skeptic abstain even with
perfect evidence. These findings depend on declared synthetic assumptions and
retain effort and utility separately.

ADR-0017 also implements the strict standalone `ec-audit-observation@1` contract
and fixed-time public projection, with exact declared accuracy and explicit
unavailability. It supplies no audit-enabled engine or demonstrated audit accuracy.
Issue #103 now carries the six remaining version/hash, generator, engine/event,
policy, integrated-test and pre-execution-design gates. Original #96's corpus
model and versioned observation-contract deliverables are complete.

### Provider and lab corrections

The provider slice rejects omitted/mismatched budget objects for budgeted network
continuations before requests or child output, records cumulative continuation
admissions, and carries stable budget stop codes into failed-run analysis. Tests
cover shared-agent episode limits and inconsistent manifest/seal accounting.
The guide states what abrupt termination cannot establish: counters are in memory,
there is no per-request checkpoint, and an unsealed artifact cannot supply final
requests, billing or a stop cause. Unlimited execution remains valid when no
budget is configured; no default limit or live-run decision was introduced.

The retry fixture failure was traced to globally replacing `time.sleep`, which
also affected subprocess provenance collection. Five fixture clock bindings now
patch the provider seam only. The provider branch passed 1,374 full-suite tests
and 153 independent focused cases; all requests were mocked.

The lab now validates branch ancestry and effective policies from sealed artifacts,
labels inherited-prefix actions and separates counterfactual summaries. Independent
review reproduced pooling when branches reused the default run ID and a rendering
crash for malformed seed fields. Four expected failing regressions preceded
`4306a2b`; 25 focused lab tests and independent re-review pass. The shared recorded-
seed validator follow-up is tracked separately as #104 and is still in progress.

### Verification and evidence retention

The ablation slice passed 208 focused tests and its full 1,475-case suite. Its
original `--check` reproduced JSON/Markdown while replaying all regenerated runs;
the unchanged quality-safeguards check reproduced the original 440+220 readout.
The noisy-corpus slice passed 158 focused tests, `make check`, `make validate` and
its 128-run regeneration gate. Fresh independent science reviews approved both
experiments and checked the original artifacts, input controls and exact arithmetic.

Added `make check-noisy-corpus` and `make check-ec-rule-ablation` to persistent CI;
the existing quick selector picks them automatically. The new ablation target's
strict standalone mypy pass first exposed four errors. Commit `344b5e2` fixes
tuple unpacking, removes obsolete ignores and asserts the paired root is non-null.
Ruff, strict mypy over both modules and the complete 288-run replay/readout gate
then passed. Independent integration review verified all 62 original source
commitments and the public design/source trees and approved this correction.
Original source records and readout bytes were not rewritten.

The combined local `make check test validate acceptance check-atlas check-study002
check-responsive check-quality-safeguards check-graph check-sparse-ptft
check-noisy-corpus check-ec-rule-ablation` exited successfully. The full suite
collected 1,658 tests; every listed standalone gate passed and preserved the original
research readouts. Remaining exact published-head Windows checks and final merges
are separate obligations. No additional merged status is claimed.

Preserved the two original experiments in
`collaborative-hill-original-evidence-2026-11-02.zip`: 416 sealed runs, 61,400 events
(12,296 noisy-corpus and 49,104 ablation), 1,930 original files and 54,450,912
original bytes. All source-commit, clean-worktree, dependency-lock, seal, scenario
and manifest bindings pass; all terminal hashes match their retained readouts.
Original readout/provenance bytes match Git, and original file contents are unchanged.
The archive has 1,936 entries: the original files plus two public-source mappings,
a manifest, README, repack script and checksums. Size is 6,130,217 bytes; SHA-256:

```text
ca58443e691fcd74f7b2311c1aaee825e577f551f7da46f0f1d3e9870504a17a
```

Each experiment's `PUBLISHED_SOURCE.json` preserves the actual original clean
local commit and equal public source tree; 62 ablation and 61 noisy-corpus source
digests were checked. Regeneration gates replay newly regenerated sealed runs and
compare retained readouts; the raw archive has its separate original-evidence audit.
No old experimental evidence or any of the four unfrozen StudySpecs changed. No
real/paid provider, study freeze, final-weight selection or human decision was used.

## 2026-11-02 — core merges and shared recorded-seed validation (#104)

This checkpoint supersedes the earlier same-day draft status. The four core PRs
merged after both Ubuntu and Windows passed on their exact published heads,
their job logs were inspected and each merge tree was checked against its tested
head. Issues #92, #95, #96 and discovered #98 are closed.

| PR | Tested head | Merge | Exact-head CI |
|---|---|---|---|
| [#99](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/99) | `f501a9a` | `a166a55` | [41386097110](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41386097110) |
| [#100](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/100) | `985defa` | `c5f2fa2` | [41386233859](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41386233859) |
| [#101](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/101) | `66f50ce` | `a23a68a` | [41385412412](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41385412412) |
| [#102](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/102) | `c0e810b` | `ff3c3e1` | [41386055377](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41386055377) |

The lab review's shared-validator follow-up #104 is implemented and independently
reviewed. Local `a7e40e169fc817d93c783df7887a756056cdb10d` and public PR #105 head
`bdc3de068c07a8e61f8db398e6d68a235cf7cb70` share tree
`be5962d74c4fb1d515428e88fc69ccb5f0c65a02`. Its
[PR](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/105) and
[CI 41387542882](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41387542882)
retain the hosted check and merge record; the counts below describe completed
local verification.

The change validates seed roots, protocol and scenario block in both the manifest
and hash-valid `RunStarted` payload before string conversion. Malformed recorded
values raise `ValueError` before replay or branching creates output; the CLI exits
2 with an error message and no traceback. No source artifacts are repaired or
rewritten. Mechanism-root binding remains enforced for both protocols. Valid
integer/string aliases, empty mechanism-root prefixes, absent legacy protocol
fields, paired streams and replay hashes remain unchanged. Source comparison
confirmed `derive_seed`, `rng_for` and `study_seed_roots` are exactly unchanged.

The author reproduced 53 failing-before cases. All 119 focused cases and 303
targeted cases then passed. The full suite passed all 1,762 tests in 209.87 seconds;
Ruff, strict mypy over 54 package files, all four StudySpecs, 11 acceptance
scenarios and the quality-safeguards/noisy-corpus/ablation gates also passed.
Independent read-only review of the exact local head passed these commands with
the shared interpreter and `PYTHONPATH=src`:

```bash
python -m pytest -q tests/unit/test_seed_protocol.py tests/integration/test_recorded_seed_validation.py
python -m pytest -q tests/property/test_seed_properties.py tests/integration/test_seed_protocol.py tests/metamorphic/test_replay_determinism.py tests/metamorphic/test_branch_prefix.py
```

Those commands passed 119 and 23 tests respectively. Additional actual runs with
empty mechanism roots passed parent and child replay under both protocols,
preserved byte-identical branch prefixes and left every parent artifact byte
unchanged. The review found no correctness or compatibility issue. Test fixtures
rehash altered sealed starts so malformed-field checks reach the metadata trust
boundary; CLI regressions also assert no output and no source mutation.

The roadmap marks this engineering implementation complete and leads with audit
engine integration issue #103, retaining all six ADR-0017 gates. Documentation
records core merges separately from the seed follow-up's local and hosted evidence.
Earlier build-log entries and experiment records remain unchanged; all four
StudySpecs remain unfrozen and byte-identical. No live/paid provider, freeze,
final-weight selection or human-owned decision was used.

The documentation pass changed only seven authorized Markdown files. `git diff --check`
passed; 61 relative link targets and heading anchors resolved. Comparison
against integration base `6d2b969` confirmed that the historical HANDOFF evidence
is unchanged and BUILD_LOG is append-only. The complete human-owned decision
section and closing paragraphs remain byte-identical, SHA-256
`bb98e30eb28e12a2d7c3323043244007a5d9b3f584da290fc6a5d9a48e64bafe`.

## 2026-11-02 — opt-in audit engine and original feedback experiment (#103 / PR #107)

Implemented the six ADR-0017 gates under
[ADR-0018](docs/adr/0018-opt-in-evidence-commons-audits.md): strict required audit
configuration, isolated exact generation, EC v3/observation v3 routing,
publication before observations, published-only checkpoint state, replay and
branch support, a separately versioned observation-driven policy, and a declared
experiment. Existing EC v2 behavior, historical source/readout files and the four
unfrozen StudySpecs remain unchanged. The audit channel changes information,
without an audit effort charge, new action, acceptance gate or reward change.

The new `ec_audit_veto_contributor@1` validates every present envelope and wraps
the unchanged skeptical selection. Only a selected proposal/verification with a
matching public negative finding becomes Withhold. There is no reranking,
calibration, citation creation or automatic retraction. Strict manifest institution
validation binds displayed settings to the resolved scenario. Runtime tests cover
first/final-round publication, exact publication-boundary forks, nested branches,
provider failure at publication and replay without provider calls or ancestor files.

### Pre-execution publication and source identity

The reviewed design was published as
`a11a11feb8fd27dc619e237e60549de14c935f28`, matching local
`e93e8b324ae6a946adf10cc127756b6b57e4cd43` at tree
`e87a3a7caec0596cc5707e50f209f0ed3cf4039f`, before audit-enabled episodes.
Complete tested source was published as
`67275327133d00e161c38d2b56d1b21472927bcb`, matching actual local execution source
`ab9e3ec842c24ad12bc6b60b30a11843353df965` at tree
`d4494ee3557deb7ef6a4d736336070aae4c73373`, before the original scientific batch.
The source record retains that actual local identity, clean flag, dependency lock
and 65 source digests. Public mappings do not relabel original provenance.

The policy slice is `a98be04`, the independent arithmetic oracle `bc906ec`, and
the corrected experiment/collector source `eec165a`. The policy's 82 pure fixtures
first failed against the absent factory and then passed. The arithmetic tests use
literal A/B/C/D traces, hand-calculated checkpoints and separate finite enumeration
of all 720 law rows. They obtain no expected answer by executing the policy or engine.

Independent source review found and reproduced three collector/reporting defects:
unconditional success prose when predictions failed; weak dirty/source-shape
validation; and branch labels that were not bound to the declared intervention.
The first two yielded 12 expected failing cases before correction; a forged
old-policy branch label separately yielded the expected failure. The corrected
renderer separates measured and expected traces, original provenance requires an
exactly false `worktree_dirty` flag and valid schema, and every branch binds exact active IDs
and changed/unchanged partitions. All 36 artifact tests passed in independent
re-review. Failure records retain all declared cells and leave incomplete
predictions null instead of inventing results.

### Original result and independent artifact audit

The original batch retained **76 scientific runs: 52 behavioral and 24 fixed-action
controls**, plus **four separate branch-integrity fixtures**. All P1–P8 held, with
60 C3 comparisons, 42 truth controls and 720 exact mixture rows. The fixed-action
negative-audit controls still accepted wrong claims under the unchanged task rules.

At source error `1/10`, audit accuracy `3/4`, zero unavailability and round-3
publication, the exact mixture raises selective accuracy from `9/10` to `27/28`,
reduces acceptance from `1` to `7/10`, and reduces signed quality from `48/5` to
`39/5`. The early quality contrast is `12(1-u)(a+e-1)`; accuracy `9/10` gives a
zero contrast in this example. Round-5 negative findings save redundant effort
without changing the accepted claim; round 6 is a task null. These are synthetic
conditional-response mixtures with assumed accuracy, independence and free audit
cost. They are not extra samples or evidence of deployed audit performance.

Independent recollection used the exact 65 original source-file bytes and checked
each digest against `git show ab9e3ec:<path>`. All **80 chains replayed**, **621
checkpoints** passed validation, every source/clean/lock/scenario/seal binding
passed, and recollected JSON/Markdown matched the original readouts byte for byte.
The complete before/after inventory was identical: **947 files / 10,283,384 bytes**.
There are 8,048 scientific events and 409 branch-ledger records including copied
prefixes, or 8,457 stored event records. The four branches are software fixtures,
not additions to the scientific sample.

The [original-evidence record](experiments/audit-feedback/ORIGINAL_EVIDENCE.md)
and [independent audit](experiments/audit-feedback/ORIGINAL_AUDIT.json) retain the
bindings and exact readout hashes. Saved archive
`collaborative-hill-audit-feedback-original-evidence-2026-11-02.zip` is **1,515,408
bytes**, with **952 members**: 947 original files plus five metadata/checksum
entries. SHA-256:

```text
338f6a15611f4ae8d4db69140d44c857686ab633cda55489b346fab03ff36fe1
```

### Verification and next work

Runtime integration passed 2,026 full-suite tests and 111 final focused cases.
The corrected `eec165a` source passed 2,062 tests in 215.28 seconds, Ruff across
source/tests/experiment, strict package mypy in 57 files and standalone mypy in
three experiment modules. The final combined integration passed **2,063 tests**
with no failures or skips, all four StudySpec validations, acceptance, atlas,
Study 002, responsive EC, quality safeguards, graph, sparse pTFT, noisy corpus,
EC ablation and the new audit-feedback gate. That gate regenerated and replayed
all 76 scientific runs plus four separate branch fixtures and reproduced all
720 exact rows and both readouts byte for byte. This regeneration is distinct
from the read-only audit of the original artifacts above.

[PR #107](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/107) is not
merged at this checkpoint; the final published-head hosted checks and merge
remain pending. The PR is their authoritative record. The current LLM EC prompt
renderer omits the audit envelope, so no LLM audit-response result is claimed.
[Issue #108](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/108) has
an approved design and separate implementation in progress for a versioned
audit-aware renderer with unchanged legacy hashes. It does not select a model,
authorize spend, freeze a study or choose final weights.

Documentation verification resolved all 49 relative links against this slice and
the integrated evidence files. The historical handoff body is unchanged apart
from its two checkpoint headings, and BUILD_LOG is append-only. The human-owned
decisions and closing paragraphs remain byte-identical, SHA-256
`bb98e30eb28e12a2d7c3323043244007a5d9b3f584da290fc6a5d9a48e64bafe`.

## 2026-11-02 — Audit core merge and separate LLM prompt adapter

Merged [PR #107](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/107) at
`3caf6d8fcc58f8627aaec0a8a92ff032fd82f689`, closing #103, after inspecting both
complete logs in [CI 41454553709](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41454553709).
The tested head `7ea6f236692f58c0db80889ac5f668139de305d1` and merge share tree
`4ad2a6b737d66ae51c7e484aa947d3a13732a9bb`. Ubuntu passed all 2,063 tests; Windows
passed 2,062 with one skip. Both passed all four StudySpec validations, all 11
acceptance scenarios, every historical research gate and the new audit reproduction,
then verified exact checkout identity and cleanliness. The merge's check run is
[41456028690](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41456028690).

The separately scoped #108 implementation is in draft
[PR #109](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/109), based on the
actual merged main. Its initial public head `72645ddbf24acc6fe1e4a750d62e895049f47ef7`
matches local `14a62c8a695cb0bda377412d05f4bd2524a13afa` at tree
`4f184c0a070353fdedd9b8cc2f383210f0ea8c6d`; later integrated checks and publication
are separate evidence. Repository inspection and publication use the connected
GitHub tools; the local merged commit was reconstructed from its verified signed
payload and exact tree, with no shell GitHub networking.

ADR-0019 was committed before implementation. Literal pre-change v1 prompt,
identity, retry, metadata and ledger fixtures were committed before source edits
(fixture SHA-256 `98503f015754f9decb98c602435aa32204c51880e8dc2a7e5affa70749c5e035`).
The opt-in `ec-audit@1` binding uses a fixed template identity and `@2` policy label;
default/explicit legacy prompting retains prior behavior. The renderer validates
strict public findings and EC round/candidate context, distinguishes missing and
unavailable information, and rejects opt-in skin/template drift before a request.
It adds no HTTP transport field or authority to the findings.

Failing-first evidence included 55 absent core-behavior cases and 19 factory cases.
Independent review then found an effective-override path that bypassed EC-only
preflight; fake and compatible regressions failed before the correction. The fix
preserves valid scripted/legacy replacements of unused originals. Actual branch
tests now prove rejection before output. Independent intercepted-request checks
verified the template/provider suffix, actual prompt digest, measured usage and
zero calls/accounting on invalid envelopes or drift.

The final author slice `b6d441cb` has **108 focused passing cases**: 57 adapter,
31 configuration, 13 literal legacy and seven sealed workflow cases. The reviewer
independently reran all of them, plus 14 credential/network-free preflight probes
and an audit-off EC study with nine absent-channel prompts. Sealed tests cover
released findings, prompt digests, fixed identities, unknown usage, byte-identical
branch prefixes, fresh continuation and offline replay after parent relocation.
Two added tests cover audit-mode format repair and bounded exhaustion, with
independently calculated actual prompt digests and exactly two unknown-usage
attempts. Ruff and strict mypy over 58 package files passed in the implementation
worktree. No blocking review finding remains; the complete merged-main local and
final published-head hosted gates remain the next verification stage.

Updated usage, claims, roadmap and handoff to distinguish the implemented prompt
path from the original scripted findings. Architecture and threat-model updates
cover released audit information and strict institution binding while preserving
the broader hidden-value, persuasion and authenticity limits. Human/tier authority
and original science inputs, source records and readouts are unchanged. No live
provider call, model selection, final weights or study freeze is part of this work.

### Integrated follow-up verification and final documentation review

The complete local command on clean `db6efe00c543525ccc4c0e5fc9adf9a3dc0877f1` exited 0:

```sh
make check test validate acceptance check-atlas check-study002 check-responsive check-quality-safeguards check-graph check-sparse-ptft check-noisy-corpus check-ec-rule-ablation check-audit-feedback
```

The full suite passed **2,171 cases with no skips or failures**. Ruff, strict
package/experiment typing, all four StudySpec validations, all 11 acceptance
scenarios and every historical research reproduction passed. Audit feedback
reproduced 76 runs, 76 original-chain replays, four separate branch fixtures and
720 exact-law rows. The gate left the checkout clean. The later edits correct
documentation and record these results; they change no production/test bytes.

The core merge's [CI 41456028690](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41456028690)
also passed on exact merge `3caf6d8f`, with both complete logs inspected: Ubuntu
2,063 passed; Windows 2,062 passed and one skipped; every research step and final
identity/cleanliness guard succeeded.

Independent documentation review confirmed the 108 focused cases from their
static definitions and found two stale pre-merge/future-work statements plus an
ambiguous reference to an empty envelope. Those were corrected to merged core,
implemented opt-in renderer, and envelopes with no published reports. General
hidden-value/prose-canary, persuasion and authenticity limitations remain explicit.
Protected authority and the human-owned tail remain exact; BUILD_LOG is append-only.

Final read-only evidence preservation matched the original inventory exactly:
**947 files / 10,283,384 bytes**, with zero missing, unexpected or changed files.
The saved ZIP remains **1,515,408 bytes**, SHA-256
`338f6a15611f4ae8d4db69140d44c857686ab633cda55489b346fab03ff36fe1`.
No replay or regeneration was used for that preservation check. PR #109 retains
the final published-head hosted checks and merge record as their authoritative
evidence; the earlier initial-head run is not its final merge gate.

## 2026-11-05 — Connect discovery, monitoring, inspection and the development queue

The repository began this pass at `b8e072041f97314c6d4e8c00cbdd3dea8f208435`
with no open issues or pull requests. The uploaded source matched all 418 live
GitHub tree blobs. The committed dependency lock installed cleanly, `pip check`
passed, and the local baseline passed 2,171 tests. Main CI 41459865315 passed
both platforms; full job logs confirmed the tested commit and clean checkout.

Inspection found all eight standalone experiment packs already implemented with
readouts and verification gates. The integration gap was discovery, consistent
execution entry points, representative demos and detailed visual inspection.
The coherent-lab specification and plan record the chosen scope. Isolated
implementation worktrees supplied a 12-entry catalog, a sealed-run inspector and
an explicit, validated issue-seeding workflow. The integration lane supplied the
read-only run monitor, public-command walkthrough and browser check.

The monitor has 19 focused regression cases covering valid seals/failures,
unsealed prefixes, partial final records, corrupt complete records, reservations,
source-byte preservation and non-provider execution. Its published tree exactly
matches the local implementation tree. Draft PR #114 at
`608ee950ea31e8bba740697e3a5fe8e05842a5fa` passed complete Ubuntu and Windows
[CI 42079937314](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42079937314).
Both full logs were inspected, including all research reproduction gates and final
checkout checks. Independent review remains pending at this checkpoint.

Catalog planning/execution tests verify safe argument arrays, source/output
boundaries, honest check/reference-only entries and existing runner provenance.
The expanded demonstration adds two Study 002 samples and three declared audit
cells, explicitly marked as incomplete inspection samples. The inspector adds
all-run, agent and round selection, observed claims/budgets, released audits,
actions, pairwise interactions, recorded hashes and branch context; existing
outputs and evidence directories are protected from exports. Curated seeds
#110–113 and #115–118 are pinned in the manifest. The seeder previews by default,
reconciles all pages of open/closed issues, never reopens closed seeds, and
stops after an unconfirmed write failure.

Actual commands executed on the integrated tree at this checkpoint:

- Focused catalog/demo/walkthrough/monitor suite: 48 passed.
- Focused console/demo/walkthrough suite: 41 passed.
- `python -m ruff check src tests studies scripts`: passed.
- Strict mypy on `scripts/check_lab_browser.py` and `scripts/seed_issues.py`: passed.
- Browser fixture generation: five completed runs, all replay identical; Node
  syntax validation of the browser harness and DOM-result parser probes passed.

Local Chromium cannot open its required socket in this managed workspace. No
sandbox bypass was attempted. The new Ubuntu Actions step runs the real Chrome
CLI against local generated HTML, exercises round/agent/run navigation and audit
publication timing, and retains desktop/mobile screenshots and DOM snapshots.
Actual browser execution and integrated complete-gate results are still pending
at this checkpoint. The shared workflow, roadmap, handoff and agent command maps
now document the same interfaces. Original studies, scenarios, research scripts,
results, policy identities and human-owned scientific decisions are unchanged.

## 2026-11-05 — Delivery checkpoint, HTML comparison and prepared pilot choices

The monitor is reviewed, verified and merged in
[PR #114](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/114).
Catalog, inspector, roadmap/seeder and the real graph walkthrough are implemented
in draft [PR #119](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/119).
The prepared pilot decision aid is in draft
[PR #120](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/120), and the
implemented optional HTML comparison is now in draft
[PR #121](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/121).
Final integrated review and CI remain open; these three PRs are not recorded as merged.

The completed predecessor evidence is retained with its actual scope:

- Core `f7c268de1960202d2626321cdc4e8b41941701ee` passed both full platform jobs in
  [CI 42083386775](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42083386775);
  both logs were inspected. Its corresponding local head `24a16d3` passed the
  full offline gate with 2,258 tests.
- Browser head `d2571ad0f744f4f24da66113f25fc80f917cca3c` passed the six-fixture
  Chrome check in [CI 42086283996](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42086283996).
  Graph, branch and mobile captures recorded 653, 652 and 654 assertions respectively.
  Artifact `13444630117` contains the reviewed unscrolled desktop/mobile screenshots;
  the views were readable at 1440×2400 and 420×2400.
- The complete local core gate later passed at `23e5089`. This precedes the latest
  Windows-only export flag correction; it is not native Windows verification of that fix.

Source review found an ancestor-swap export race and misleading root fork metadata.
Shared guarded exports and presentation provenance checks address those cases.
Native Windows CI then exposed the attribute-only directory handle's failure to
enforce sharing restrictions. The corrective directory-access flags have independent
source review; actual native verification remains pending at this checkpoint.
The current core published head is `77381713dfadfb91fb440f82b3bbc6828186fc44`, with
[CI 42091406335](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091406335)
in progress. Pilot head `f8fb34652f1c1a351c41abfe6c3fcc871f01339d` has
[CI 42091419268](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091419268)
in progress. Comparison PR #121 was opened at
`59a4432be5450ff62b77abca17c2c52a077a31a1`; its final review and platform/browser gates
remain pending. The PRs retain the authoritative record for successor heads.

Direction and usage documentation now distinguish implemented features from
pending delivery gates. NEXT makes the separately declared audit cost/timing
experiment (#117) the next research design. The pilot decision record remains an
owner discussion aid: no weights, outcome, model, allocation, budget or stop rule
has been selected. The walkthrough documents same-mechanism comparisons,
unchanged default JSON, full-episode utility deltas and inherited/shared history.
The runtime command maps include the comparison and guarded-export checks.

Documentation verification resolved 94 relative links and checked their Markdown
anchors. `python scripts/seed_issues.py --check` accepted all eight curated seeds.
The comparison CLI and comparison-browser `--help` output match the documented
options. Resolving the two graph examples confirms identical mechanism hashes
for the targeted and linked policies on the same ring/defector placement.
The human-owned HANDOFF tail remains byte-identical, SHA-256
`bb98e30eb28e12a2d7c3323043244007a5d9b3f584da290fc6a5d9a48e64bafe`;
the prior 86,698-byte BUILD_LOG prefix is preserved. No scientific inputs,
original results, authority rules or provider settings were changed by this documentation pass.

Before this documentation commit, the corrected core Ubuntu job completed and its
full log was inspected; Windows passed the native unit and complete pytest steps
and continued through the remaining research gates. Comparison predecessor
`59a4432be5450ff62b77abca17c2c52a077a31a1` passed 379 desktop and 379 mobile assertions
in [CI 42091563004](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091563004).
All five inspector/comparison captures were downloaded, digest-verified and
visually reviewed as readable without horizontal overflow. Later comparison
wording and documentation edits still require final integrated-head verification;
the three delivery PRs remain drafts at this checkpoint.

## 2026-11-05 — Verified workflow and final comparison delivery record

Core [PR #119](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/119) merged as
`a4e8d43dad17455f680f07a472a36d1582dd87b5` after independent review and complete
Ubuntu/Windows [CI 42091406335](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091406335)
on `77381713dfadfb91fb440f82b3bbc6828186fc44`. Both full logs and the three inspector
captures were reviewed; the merge tree matches the reviewed head. This includes
the corrected native Windows export guards. Monitor PR #114 was already merged.

Pilot decision-record [PR #120](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/120)
merged as `b7230795caf55ebcdd52f2c605d72d1da729e13f`. Reviewed head
`f8fb34652f1c1a351c41abfe6c3fcc871f01339d` passed both complete platform jobs in
[CI 42091419268](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091419268),
and both full logs were inspected. The document is prepared; the scientific and
spending choices remain unresolved.

Comparison code head `59a4432be5450ff62b77abca17c2c52a077a31a1` passed both complete
platform jobs in [CI 42091563004](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091563004).
Both full logs and all five inspector/comparison captures were reviewed. Chrome
recorded 379 desktop and 379 mobile comparison assertions; the captured views were
readable without horizontal overflow. The comparison implementation has independent
source review, including shared exports, ancestry and inert rendering.

The full required offline gate then passed on clean integrated local head
`4231ac9026ddaaa8223b31294c8ce493d50b9de1`, which includes the reviewed documentation
and minor comparison wording follow-up. Every required target exited successfully;
the suite collected 2,308 tests, with 10 native-Windows skips on Linux. The gate
left the checkout clean. This is the verification boundary before the final
documentation status pass.

Current documentation now records the core, monitor and pilot-document merges,
the verified comparison implementation, and #117 plus unresolved owner choices
as the next development work. PLAN records completed review/testing and the
prepared comparison delivery documentation, with
[PR #121](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/121) as the
authoritative publication record. At this historical checkpoint, the final docs
head still needs publication and new exact-head CI before that PR can merge;
no PR #121 merge is claimed here.

This final status pass changes documentation only. Verification is limited to
relative links/anchors, the exact human-owned HANDOFF tail, the unchanged BUILD_LOG
prefix from `4231ac9`, and a clean diff check. No additional tests or scientific
regeneration were run. The human-owned tail remains SHA-256
`bb98e30eb28e12a2d7c3323043244007a5d9b3f584da290fc6a5d9a48e64bafe`.
