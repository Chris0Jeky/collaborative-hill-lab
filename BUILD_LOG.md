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
