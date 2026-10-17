# BUILD_LOG — decisions made and commands actually run

Chronological, foundation session 2026-07-13 (Claude Fable 5, ultracode). Only entries
that were actually executed/verified are listed.

## Discovery

- Cloned legacy repo read-only to scratchpad (`git clone` + `core.longpaths=true` for
  Windows MAX_PATH). HEAD `f7f1cceb`.
- First-hand reads: `prisoners.tex` (claims source; draft), `npdl/core/utils.py`
  (payoffs; duplicate `get_pairwise_payoffs`), `CORRECTED_RESULTS_SUMMARY.md` (defect
  admission).
- Six parallel discovery agents (Opus 4.8) → `docs/research/_discovery/*.md`. One agent
  returned a junk structured summary but a good report file (kept; noted).

## Key decisions (full rationale in ADRs)

- Option C kernel; Concordia cognition-only behind adapter (ADR-0001).
- Floats forbidden in hashed content; exact `Fraction` strings (hashing.py).
- Stateless per-(agent,round) seed streams; no persisted RNG state (ADR-0005) — chosen
  over Philox after realizing per-round derivation removes the need for fast-forward.
- Branch = copy-on-write byte prefix; shared events keep parent run_id (ADR-0002).
- Propositions are a finite typed space; NL only in skins (ADR-0003/0004).
- EC verification = engine-adjudicated provenance-checking, NOT truth oracle; documented
  as v0 limitation (CLAIMS_AND_LIMITATIONS).
- ApproveClaim deferred to v1 (in type union, not legal in v0).
- Self-knowledge flags (`verified_by_me` etc.) added to EC observations so scripted
  personas stay stateless (branch-rebuild safe).

## Commands run and verified (chronological highlights)

- `python -m venv .venv` + `pip install -e ".[dev,analysis]"` → all extras import on
  Python 3.14.3/Windows.
- Inline smoke: pairwise 2TFT+AllD 10 rounds → scores 39/39/28 (= hand-derived theory);
  replay + fresh-rerun chain equality both True.
- EC smoke: briefing 2/2 correct; free-rider advantage +1.5; ledger canary scan clean.
- `chl run "studies/000-legacy-reproduction"` — 270 then (after erratum, see below) 330
  episodes, all completed; `generate_report.py` → REPLICATION_REPORT.md, 11/11 reproduced.
- **Erratum (recorded honestly):** first prediction encoding misread prisoners.tex —
  its 75%/25% TFT-E figures refer to the AllC/AllD pairings. Fixed the reading, added the
  two missing AllC conditions, reran. No mechanism change; README of Study 000 documents it.
- `studies/001-evidence-commons/generate_study.py` → 5 conditions; skin-pair mechanism-hash
  equality asserted at generation. `chl run` fixture: 15/15 episodes completed.
- `certificate.py` → dilemma certified in all 4 institutions (C1/C2); intervention
  integrity C3: 0 violations across 16 profile pairs.
- Prompt-size measurement for COST_WORKSHEET: 36 prompts/episode, mean 2,524 chars.
- `make doctor` / `make validate` / `make replay-smoke` (replays of both studies' sealed
  runs verified chain-identical).
- Test suites (unit/property/metamorphic/integration) written by three supervised agents +
  reconciled; final pytest results in HANDOFF.md.

## Final verification (end of founding session)

From a clean generated state, in sequence, all exit 0:
`make clean-generated` → `make doctor` (10/10) → `make check` (ruff + mypy --strict +
unit/property) → `make test` (**125 passed**: 91 unit + 24 property + 9 metamorphic +
10 integration — 1 metamorphic file contributes 4 parametrizations) → `make validate` →
`make study-000` (330 episodes; REPLICATION_REPORT regenerated, **11/11 REPRODUCED**,
5 exact) → `make study-001-smoke` (certificate: C1 dilemma everywhere TRUE, C3 violations
0) → `make replay-smoke` (both studies chain-verified) → `make report` →
`scripts/acceptance.py` (**11/11 A–K pass**). Adversarial pass found and fixed: EC
verify/challenge duplication exploits (engine v2), engine-version-in-hash gap,
`_find_repo_root` wrong-repo provenance, ornamental interfaces duplication (deleted).

## Process notes

- One mid-flight commit accidentally included agent work-in-progress test files
  (harmless at T1; final state supersedes it).
- All work local; nothing pushed (task constraint), no remote/legacy-repo modification.

## Codex runtime refresh — 2026-07-17

- Guard preflight: confirmed authoritative estate row, T1 tier, clean `main` at
  `65a387ff13ea81e5c67ca290f32eff3a007e61c3`, one clean worktree, and
  `main...origin/main` with no divergence.
- Fetched the current Codex manual and checked the supported trusted-project surfaces:
  `AGENTS.md`, `.codex/config.toml`, and `.codex/hooks.json`.
- Compared the repo's Claude/Codex contracts, the live dispatcher, the current
  `agent-harness` template, and the handoff. Found and fixed floor-version drift, missing
  `--runtime codex`, missing project feature defaults, stale no-code metadata, and a
  PowerShell-hostile `&&` handoff instruction.
- Focused verification: parsed both JSON files and `.codex/config.toml`; a synthetic
  `git status --short` hook payload exited 0; a synthetic `git push --force origin main`
  payload returned `permissionDecision=deny` under floor v1.4.1 Codex semantics.
- Repository verification: `make check` passed (ruff, mypy strict, unit/property tests),
  `make test` passed (125 tests), and `make validate` passed for studies 000 and 001.
- Not run in this refresh: `make study-000`, `make study-001-smoke`, `make replay-smoke`,
  `make report`, or `scripts/acceptance.py`; no product/science code changed.
- Adversarial review pass 1 (runtime/security) exercised five hook cases and found that the
  installed floor v1.4.1 differs materially from the designated `agent-harness` template
  v1.4.0. The working floor was not downgraded; the cross-repo drift is tracked in HANDOFF.
- Adversarial review pass 2 (operations/science boundaries) found a remaining PowerShell
  `&&` command, a stale push-status sentence, and an unacknowledged T2 promotion signal.
  The command/status text was fixed and the tier decision was deferred explicitly to the
  human while retaining declared T1 authority.

## GPLv3-only licensing — 2026-08-12

- The owner relicensed current and future owner-authored software as
  `GPL-3.0-only`, while preserving the historical MIT grant for earlier revisions.
- Release identity advanced from 0.1.0 (MIT) to 0.1.1 (GPLv3-only); package and
  citation metadata now agree and the current package exposes only `LICENSE` as
  its `License-File`.
- Verification: `make check`, `make test`, and `make validate` all exited 0 using
  the repository-locked Ruff 0.15.21; `git diff --check` passed.

## Distribution metric correction — 2026-10-06

Reproduced the worker test's initial import failure with the system interpreter,
then set PYTHONPATH to this worktree's src and reproduced the actual zero-sum
negative-utility Gini failure. Moved the zero-total guard after the existing
negative shift without changing the formula. Updated distribution versions to 2
because derived results change. Kept the worker's contract tests and added the
hand-derived 0.5 oracle and version consistency assertion.

Commands actually run from this worktree (PYTHONPATH=worktree/src):
- py -3 -m pytest tests/unit/test_distribution_metrics.py -q: failed before
  correction, passed after correction (one test).
- Temporary mutations removing the shift and reversing free-rider subtraction:
  each failed the regression test; source restored byte-for-byte in finally.
- Primary locked venv python -m ruff check src tests studies scripts:
  failed on two pre-existing E501 errors in test_checkpoint_list_seqs.py:15-16.
  git show HEAD:tests/unit/test_checkpoint_list_seqs.py confirmed both in base.
- Primary locked venv python -m ruff check src/collaborative_hill/metrics
  tests/unit/test_distribution_metrics.py: passed.
- Primary locked venv python -m mypy: passed (40 source files).
- Primary locked venv python -m pytest tests/: passed.
- Primary locked venv python -m pytest tests/unit tests/property -q: passed.
- Primary locked venv python -m collaborative_hill.cli study validate
  studies/000-legacy-reproduction: passed.
- Primary locked venv python -m collaborative_hill.cli study validate
  studies/001-evidence-commons: passed.
- git diff --check: passed.

No hosted CI, report regeneration or merge claim. The primary checkout was
preserved. Human-owned HANDOFF decisions remain untouched. Host owns teardown;
ignored contents are disposable Python, Hypothesis, pytest, mypy and Ruff caches.

## Estate-night publication verification — 2026-10-05

Continue reporting later studies after a run/study reporting error, return nonzero, and skip aggregate generation for any study whose run report failed. Coordinator reproduced cached-metrics reuse and added a real corrupt-ledger regression.

The team HIGH claim was reproduced with a corrupt ledger and cached metrics and fixed by skipping that study's aggregate. The stub-only coverage concern is resolved by a real-ledger regression. Broad Exception handling is intentional for the contracted batch failure isolation; programming errors are logged and return nonzero. The error-text notice is informational on this synthetic-only surface.

Commands run from this worktree with PYTHONPATH pointing at its src:
- py -3 -m pytest tests/unit/test_report_all.py -q (passed after environment setup).
- Primary locked venv python -m ruff check src tests studies scripts (passed).
- Primary locked venv python -m mypy (passed, 39 source files).
- Primary locked venv python -m pytest tests/unit tests/property -q (passed).
- Primary locked venv python -m pytest tests/ -q (passed).
- Primary locked venv python -m collaborative_hill.cli study validate studies/000-legacy-reproduction (passed).
- Primary locked venv python -m collaborative_hill.cli study validate studies/001-evidence-commons (passed).
- Primary locked venv python scripts/acceptance.py (11/11 passed).
- Temporary pre-worker source substitution, restored in finally: new regression
  module exited 1 as expected. Reporting's cached-metrics regression also failed
  against the worker draft and passed after the coordinator fix.
- git diff --check (passed).

These are direct equivalents of make check/test/validate; no venv files or
artifacts were written into the owner's primary checkout. No hosted CI or
full-size study campaign claimed. Owner decisions remain in HANDOFF.md.

## Estate-night publication verification — 2026-10-05

Reject unknown invalid_action_policy values in RunConfig, StudySpec and RunManifest; preserve exact fail/abstain behavior. Coordinator corrected Ruff import spacing.

The team verification blocker is resolved by executed regression and repository checks. The three identical Literal aliases are retained: consolidation is a non-blocking future-maintenance suggestion, with no current behavioral mismatch.

Commands run from this worktree with PYTHONPATH pointing at its src:
- py -3 -m pytest tests/unit/test_runner_invalid_policy.py -q (passed after environment setup).
- Primary locked venv python -m ruff check src tests studies scripts (passed).
- Primary locked venv python -m mypy (passed, 39 source files).
- Primary locked venv python -m pytest tests/unit tests/property -q (passed).
- Primary locked venv python -m pytest tests/ -q (passed).
- Primary locked venv python -m collaborative_hill.cli study validate studies/000-legacy-reproduction (passed).
- Primary locked venv python -m collaborative_hill.cli study validate studies/001-evidence-commons (passed).
- Primary locked venv python scripts/acceptance.py (11/11 passed).
- Temporary pre-worker source substitution, restored in finally: new regression
  module exited 1 as expected (nine invalid-policy assertions failed).
- git diff --check (passed).

These are direct equivalents of make check/test/validate; no venv files or
artifacts were written into the owner's primary checkout. No hosted CI or
full-size study campaign claimed. Owner decisions remain in HANDOFF.md.

## Swarm draft qualification - 2026-10-01

- Adds an Evidence Commons verification regression for stale cited evidence and an inaccessible supporting item. Both targeted guard-removal probes failed at the new assertions, and the source was restored byte-for-byte.
- Rejects malformed and unknown branch override parameters with usage errors and accepts rational epsilon values. The three regression cases failed against the original CLI; plain policy overrides remain covered.
- Ran the item's targeted pytest command, `make check`, the full pytest suite,
  and `make validate` for both studies from this candidate worktree.
- Initial worker verification failed because the checkout package was not installed.
  Shared-site-package experiments exposed an unrelated PyArrow typing error and,
  in one run, a Hypothesis input-generation health check under concurrent load.
  Development-only isolation also exposed the doctor test's analysis-extra requirement.
  Installed the complete `requirements-lock.txt` in the isolated environment.
- No primary-checkout edits, study freeze, paid provider call, or human decision.
  Muse wrote the first draft; the coordinator reviewed and qualified it for a PR.

## Integrity guard repairs — 2026-10-17 (issues 36, 37, 13)

Worktree: `C:\Users\jekyt\wt\chl`, branch `fix/integrity-batch-36-37-13`,
implementation base `983412097231ad5a7e030ab0bd64b8933fb3d06a`.
These guards landed in PR #39 at merge commit
`e6c6033b1d979a4abe7851b2b0d5c18801103dcc`.
Initial Git status was clean. Read CLAUDE.md, HANDOFF.md and tier authority;
no owner decisions or shipped study parameters/results were changed.

- #36: reject chain-valid prefixes, missing/duplicate/misplaced seals and
  manifest status/identity/count/hash mismatches before writing derived output.
  Pin new run/branch manifests; revalidate cached aggregate inputs; keep failed
  status while excluding partial outcomes from study tables.
- #37: publish a complete flushed lock with `os.link` (exclusive, no replacement),
  preserve byte-identical idempotence and refuse changed commitments. Only
  temporary synthetic copies of Study 001 were frozen in tests.
- #13: reserve the ledger with `open("x")` before artifacts, reject nonempty
  directories/duplicate condition IDs and map CLI collisions to exit 2.
  Real filesystem interleavings test competing claims and preserve winner bytes.
- Red evidence: before production edits, the focused test command below (then
  using `-q --tb=short --basetemp=C:/Users/Public/codex-shell-home/chl-integrity-red`)
  failed at the expected missing-refusal, rewritten-lock, collision-exit and
  missing-pin assertions. The failed-run outcome test separately failed with
  partial NIPD cooperation included in the study table.
- Fix-round failures: one Ruff line-length violation was corrected; a new race
  fixture initially expected LF after a Windows text write, corrected by setting
  `newline="\n"`. Its isolated rerun passed, then the entire focused set passed.

Exact final checks, run from this worktree (the primary venv is used only as
an interpreter/tool installation; PYTHONPATH selects this worktree's source):

```powershell
$env:PYTHONPATH=(Resolve-Path 'src').Path
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\Users\jekyt\Desktop\Printer Config\Others\Git\collaborative-hill-lab\.venv\Scripts\python.exe' -m pytest tests/integration/test_reporting_seal.py tests/integration/test_study_freeze_guard.py tests/integration/test_study_rerun_guard.py tests/integration/test_branch_out_guard.py tests/unit/test_run_study_validation.py -o addopts=--strict-markers -q --tb=short --basetemp=C:/Users/Public/codex-shell-home/chl-integrity-closeout
& 'C:\Users\jekyt\Desktop\Printer Config\Others\Git\collaborative-hill-lab\.venv\Scripts\python.exe' -m pytest tests/unit/test_report_all.py tests/unit/test_manifest.py tests/unit/test_cli_override_validation.py tests/integration/test_clean_state_manifest.py tests/metamorphic/test_branch_prefix.py -o addopts=--strict-markers -q --tb=short --basetemp=C:/Users/Public/codex-shell-home/chl-caller-final
& 'C:\Users\jekyt\Desktop\Printer Config\Others\Git\collaborative-hill-lab\.venv\Scripts\python.exe' -m ruff check src/collaborative_hill/reporting/report.py src/collaborative_hill/experiments/manifests.py src/collaborative_hill/experiments/study.py src/collaborative_hill/engine/store.py src/collaborative_hill/engine/branching.py src/collaborative_hill/cli.py tests/integration/test_reporting_seal.py tests/integration/test_study_freeze_guard.py tests/integration/test_study_rerun_guard.py tests/integration/test_branch_out_guard.py tests/unit/test_run_study_validation.py
& 'C:\Users\jekyt\Desktop\Printer Config\Others\Git\collaborative-hill-lab\.venv\Scripts\python.exe' -m mypy --follow-imports=silent src/collaborative_hill/reporting/report.py src/collaborative_hill/experiments/manifests.py src/collaborative_hill/experiments/study.py src/collaborative_hill/engine/store.py src/collaborative_hill/engine/branching.py src/collaborative_hill/cli.py
git -c safe.directory=C:/Users/jekyt/wt/chl -c core.safecrlf=false diff --check
```

Results: 57 tests passed in 11.14s; 15 caller tests passed in 2.07s;
Ruff clean; mypy clean on six source files; diff whitespace clean.
The Git safe-directory setting was per-command, with no config writes.

NOT verified: full suite/gates, mutation testing, long builds, multiprocess
stress, power-loss recovery or GitHub state (driver prohibited these broader
checks/access). Freeze publication was exercised on this Windows filesystem;
other filesystems must support hard links or publication fails closed.
Legacy manifests remain readable without pins, with mandatory seal checks.
No version-creation/lineage feature was added. Human-action file is null and
HANDOFF.md retains all owner decisions. The guard implementation is part of PR #39.

## Issue 40: reporting and reservation repair - 2026-10-17

Worktree `C:/Users/jekyt/wt/chl-40`, branch
`fix/report-readonly-reservation-cleanup-40`, starting HEAD
`e6c6033b1d979a4abe7851b2b0d5c18801103dcc` (PR #39). Initial status was clean.
Edits only; no Git writes, GitHub calls, parallel runners or full suites.

Changed / regression mapping:

| issue | status | files / shared hunks | regression test |
|---|---|---|---|
| Study reporting rewrites runs | fixed | reporting/report.py, test_reporting_seal.py | test_study_report_reads_archived_runs_without_writes (cached/missing metrics, valid/later invalid run) |
| Failed pre-manifest reservations | fixed | engine/store.py, engine/branching.py, run_study reservation hunk in experiments/study.py; test_study_rerun_guard.py, test_branch_out_guard.py, test_run_reservation.py | test_pre_manifest_failure_releases_reservation_for_retry, test_branch_pre_manifest_failure_releases_reservation, test_reservation_setup_failure_removes_owned_directory |
| Preserve manifested/competing runs | fixed | same item-2 files | test_post_manifest_failure_preserves_run, test_failed_reservation_preserves_manifest_or_new_owner; existing test_atomic_reservation_preserves_competing_writer |
| CLI freeze ValueError | fixed | cli.py, test_study_freeze_guard.py | test_cli_refreeze_changed_study_is_usage_error |
| Hard-link publication failure | fixed | freeze_study exception hunk in experiments/study.py, test_study_freeze_guard.py | test_freeze_link_failure_is_clear_and_fail_closed (existing/absent lock) |
| Stale #39 publication wording | fixed | HANDOFF.md, BUILD_LOG.md | live starting HEAD identifies merged PR #39; no behavior test needed |
| mkstemp POSIX 0600 mode | skipped | none | Access-widening policy is unspecified; POSIX permission semantics cannot be proved on this Windows host. |

The reporting helper retains all #39 chain/seal/status/identity/count/hash checks.
The archived-run regression denies write opens and compares bytes and mtimes;
cached metric values survive a simulated METRIC_VERSIONS change. Missing metrics
are computed in memory without creating metrics/parquet output. A later invalid
run leaves earlier artifacts and the study report untouched.

Reservation cleanup checks the original ledger's filesystem identity and absence
of a manifest, removes owned preparation artifacts, then releases the ledger last.
The run root is removed only with nonrecursive rmdir, so a new reservation or
manifest cannot be removed with it. Both reserve callers use its context manager;
study setup leaves that context after writing the initial manifest. Branch setup
holds it through its final manifest. Errors during cleanup do not mask the original
exception. Existing manifested runs and replacement-ledger bytes survive tests.

Red evidence (before source edits): the first focused command produced eight
expected failures (four archived-run writes, two leaked study reservations,
CLI exit 1 instead of 2, and raw OSError). The preservation control passed.
The second command reproduced leaked branch and reservation-setup directories.

Exact commands run from this worktree (same environment for each):

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:/Users/jekyt/Desktop/Printer Config/Others/Git/collaborative-hill-lab/.venv/Scripts/python.exe' -m pytest tests/integration/test_reporting_seal.py tests/integration/test_study_rerun_guard.py tests/integration/test_study_freeze_guard.py -k 'archived_runs or pre_manifest_failure or post_manifest_failure or cli_refreeze or link_failure' -q --tb=short --basetemp=C:/Users/Public/codex-shell-home/chl40-red
& 'C:/Users/jekyt/Desktop/Printer Config/Others/Git/collaborative-hill-lab/.venv/Scripts/python.exe' -m pytest tests/integration/test_branch_out_guard.py tests/unit/test_run_reservation.py -k 'pre_manifest_failure or setup_failure' -q --tb=short --basetemp=C:/Users/Public/codex-shell-home/chl40-reservation-red
& 'C:/Users/jekyt/Desktop/Printer Config/Others/Git/collaborative-hill-lab/.venv/Scripts/python.exe' -m pytest tests/integration/test_reporting_seal.py tests/integration/test_study_rerun_guard.py tests/integration/test_study_freeze_guard.py tests/integration/test_branch_out_guard.py tests/unit/test_run_reservation.py -q --tb=short --basetemp=C:/Users/Public/codex-shell-home/chl40-green
& 'C:/Users/jekyt/Desktop/Printer Config/Others/Git/collaborative-hill-lab/.venv/Scripts/python.exe' -m pytest tests/integration/test_reporting_seal.py tests/integration/test_study_rerun_guard.py tests/integration/test_study_freeze_guard.py tests/integration/test_branch_out_guard.py tests/unit/test_run_reservation.py -o addopts=--strict-markers -q --tb=short --basetemp=C:/Users/Public/codex-shell-home/chl40-final
& 'C:/Users/jekyt/Desktop/Printer Config/Others/Git/collaborative-hill-lab/.venv/Scripts/python.exe' -m ruff check src/collaborative_hill/reporting/report.py src/collaborative_hill/engine/store.py src/collaborative_hill/engine/branching.py src/collaborative_hill/experiments/study.py src/collaborative_hill/cli.py tests/integration/test_reporting_seal.py tests/integration/test_study_rerun_guard.py tests/integration/test_study_freeze_guard.py tests/integration/test_branch_out_guard.py tests/unit/test_run_reservation.py
& 'C:/Users/jekyt/Desktop/Printer Config/Others/Git/collaborative-hill-lab/.venv/Scripts/python.exe' -m mypy --follow-imports=silent src/collaborative_hill/reporting/report.py src/collaborative_hill/engine/store.py src/collaborative_hill/engine/branching.py src/collaborative_hill/experiments/study.py src/collaborative_hill/cli.py
git -c safe.directory=C:/Users/jekyt/wt/chl-40 -c core.safecrlf=false diff --check
```

Verified: interim green 61 tests, final 62 passed in 15.56s after extending the
link-failure test to protect an existing lock as well. Ruff initially found one
import-order issue, corrected; final Ruff passes. Mypy passes on five source
files. Diff whitespace passes. No venv files in the primary checkout were changed.

NOT verified: full make gates/suites, forced process death/power loss, multiprocess
stress, POSIX permissions or GitHub state. Residual risk: cleanup is best effort
if the filesystem refuses deletion, and cannot run after abrupt process death.
Manifested incomplete runs stay preserved and fail seal validation. Hard-link
publication still requires filesystem support; there is no unsafe overwrite
fallback. The mkstemp permission LOW is skipped pending a POSIX sharing policy.
human_todo=null; HANDOFF.md retains all owner decisions. Driver owns commit/PR.
