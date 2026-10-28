# HANDOFF — current checkpoint, 2026-10-28

## Social-dilemma certificate correction

Changed: the certificate now requires C1 **and** C2 in every institution. Its verdict,
failed-condition explanation, console summary and current documentation agree. The
unchanged Study 001 parameters yield C1 true, C2 false in all four institutions, and
zero C3 violations: **social dilemma NOT CERTIFIED; intervention integrity CERTIFIED**.
Historical reports remain historical; the earlier false certification is superseded here.

Verified on Python 3.12.10 / Windows from base `5a66e57de42d750171a68597470beabf0a7a3369`:
the original 32-episode generator reproduced the contradictory report without a diff;
the new report-level regression failed before the fix. Seven focused tests now pass,
including C1-true/C2-false, a positive control, equal totals and a single failing
institution. `make check test validate` passes: Ruff, strict mypy (45 files),
293 unit/property tests and 601 full-suite tests, with four pre-existing filesystem
skips. Acceptance passes 11/11. Regeneration is byte-identical; all numeric sections,
scenario identities, study hashes and freeze states are unchanged. See `BUILD_LOG.md`.

Publication goes through a ready PR with an independent review and the post-push age
gate; the PR records the final review and merge state. No publication state is inferred
from these local checks.

NOT verified: the four skipped filesystem cases, real providers, human behaviour,
or a social dilemma beyond the enumerated scripted strategies. No persistent CI exists.
Residual risk: placeholder utility weights still fail C2; this repair reports that
failure and does not retune the study. Feature work remains parked under the owner's
product-direction decision. No study was frozen and no real/paid provider was used.
The human-action home is the ten unchanged decisions below (`human_todo=null`),
including weights, hypotheses, publication readiness and any paid run.

Earlier checkpoints below retain their dated evidence and publication state.

The previous handoff is preserved byte-for-byte in
[the historical checkpoint](docs/history/HANDOFF-through-2026-10-21.md).
Its dated counts, paths and publication states are historical, not current status.
The operating rules remain in `CLAUDE.md` and `AGENTS.md`; the repository remains T1.

## Issue #60 — unambiguous provider-failure replay (local worktree)

Changed: `agents/replay.py` identifies the failed provider at the runner's first
unproposed agent in sorted order for the terminal round, then checks that agent's
error prefix. Agent IDs containing `: ProviderError: ` no longer cause valid
ledgers to be rejected. Existing ledger bytes and the provider-error format are
unchanged. Four regression cases cover identical seal text from two different
failing agents, both immediately and after two completed rounds.

Verified on Python 3.12.10 / Windows, against base
`8b7cdc1739c036be42206304f8013bf7ba7ea526` plus this uncommitted diff: the corrected
regression fails twice before the production fix (two controls pass), then all
four cases pass. `make check test validate` passes: Ruff clean, strict mypy clean
in 45 source files, 286 unit/property tests and 594 full-suite tests pass, with
four pre-existing skips. Acceptance is **11/11**; both study hashes are unchanged.
Exact commands and initial fixture correction are recorded in `BUILD_LOG.md`.

NOT verified: real providers, the four skipped filesystem cases, hosted CI or
independent review. Residual risk: decoding relies on the runner's sorted proposal
order; full regenerated-chain comparison continues to reject inconsistent histories.
The human-action home remains the unchanged human-owned decision list below
(`human_todo=null`). No Git writes or publication occurred under the task's rule.
Intended commit: `fix(replay): decode provider failures at the proposal boundary`.
Earlier checkpoints below retain their historical evidence and publication status.

## PR #58 fix round — 2026-10-22

Both review findings were confirmed at `e6bf84b171d2b26daa76c1db59a0682c1505a233`.
Analysis now reports `invalid_llm_output_abstentions` per episode and per cell,
separately from mechanism `invalid_action_count` and `fallback_abstentions`.
Its `invalid_action_rate` includes parser-failure abstentions plus mechanism
rejections once each; ordinary abstentions are excluded. The mean per-cell rate
uses that same definition for draft SAP invalid-output/sensitivity reporting.
Sensitivity exclusions still require a human-declared threshold. Existing
versioned operational metrics are unchanged. The golden JSON changes only by
adding this field, zero-valued in its 12 episodes and four cell summaries.

Two integration cases cover all-malformed replies and mixed parser failures,
ordinary abstentions and mechanism rejections. Both failed on the missing field
before the fix. An independent RNG oracle pins three indices per bootstrap
replicate and hand-computed means. The in-memory doubled-observation/2n mutation
passed all 21 original statistics tests but fails the new oracle. Production
bootstrap code needed no change. Exact verification commands and results are
in the latest `BUILD_LOG.md` entry.

Verification: Ruff clean; strict mypy clean in 45 source files; focused suite
41 passed; full suite **560 passed, 4 skipped** (112.04s); acceptance **11/11**.
Both studies validate with their original content hashes. Real-provider data,
provider randomness coupling and confirmatory/SAP freeze decisions remain unverified.

Changes remain uncommitted: the task prohibits Git writes and network access.
No study inputs, hashes, freeze state or human-owned decisions were changed.
The human-action home remains the decision list below (`human_todo=null`).
Intended commit:
`fix(analysis): count invalid-LLM-output abstentions and pin the bootstrap draw size`.

## E2 analysis skeleton — local worktree checkpoint

`chl analyze artifacts/<study-prefix> [--out analysis.json]` now reads verified
sealed runs into one row per completed episode, recording failed/unsealed/invalid
artifacts as exclusions. Analysis never re-executes episodes or trusts metric
caches. The four original factorial conditions are explicit; the misinformer
condition and counterfactual branches are not independent factorial data.

The draft SAP's E1/E2/E3 use equal-cell contrasts for legacy independent runs;
explicit complete paired-policy-v2 blocks use within-block differences and block
bootstrap, with a supplementary Student-t interval. Unverified policy/provider
coupling suppresses paired inference. All output remains `sap_status: draft`.
Bootstrap uses `rng_for` with recorded seed 20261022 and 2000 draws by default,
type-7 percentile intervals, centered two-sided bootstrap p-values and Holm over
the three primary tests. Secondary outcomes are descriptive. Zero-variance cells
have `n_effective=1` and no intervals/p-values. Missing sensitivity thresholds and
exclusion rules are explicitly marked not run, rather than inferred.

Local proof on Windows, using `../assess/.venv/Scripts/python.exe` with this
worktree's `src` on `PYTHONPATH`: Ruff clean, strict mypy clean (45 source files),
**557 passed, 4 skipped** in the full suite (88.63s); **38** new focused tests pass.
The golden fixture runs three scripted episodes in each of four cells and checks
canonical JSON byte-for-byte, read-only behavior, and episode sample sizes.
Both study validations retain their original hashes; acceptance is **11/11**.
Exact commands are in the latest `BUILD_LOG.md` entry.

R2 pilot data, preregistration/SAP choices and the human freeze remain required
before confirmatory use. No real provider, paid run, freeze, Git write, commit,
push or network access was performed. `NEXT.md` records the E2 skeleton; the
human-owned decision list below is unchanged (`human_todo=null`). Intended commit:
`feat(analysis): add chl analyze for the Study 001 2x2 from sealed runs`.

The remaining sections preserve the earlier counterfactual milestone checkpoint.

## Landed in this pass

PR #54 (`e0428cf00bcf6ac423ab1dadd5a82090fb75babb`) repairs counterfactual replay:
all ancestral run-ID segments are re-executed from recorded proposals and
recomputed state, without following parent directories or trusting input checkpoints.
Branch checkpoints must match sealed boundaries. Reused ancestor IDs and silently
reset inherited policy overrides are refused before writing child artifacts.
Child manifests carry effective policy labels; unmeasured child usage/cost is null.
An automated-review finding about nested terminal forks was reproduced and fixed:
inherited checkpoints with no direct-parent prefix segment are rejected before writes.

PR #55 (`e754a961b2ef3df438adb0b8bc7925c9b35a0867`) adds `chl compare` and a complete
offline tutorial. Comparisons validate inputs, recompute metrics in memory, show
exact rational utility differences and the first changed action, and optionally
replay both ledgers. Failed runs retain operational metrics but no outcome delta.
The tutorial runs parent, child and grandchild for N-IPD and Evidence Commons.
All six replay; the second fork retaining its inherited policy preserves actions
and utilities even though run IDs and hashes differ.

Read [the workflow guide](docs/COUNTERFACTUAL_WORKFLOW.md) and
[ADR-0009](docs/adr/0009-counterfactual-replay.md) before extending this behavior.
The prior paired-policy seed protocol and read-only seed audit remain available.
Neither shipped study's inputs or content hash changed.

## Reproduce

```bash
make setup
make check test validate
.venv/bin/python scripts/acceptance.py
.venv/bin/python scripts/counterfactual_demo.py --out artifacts/counterfactual-demo
.venv/bin/python -m collaborative_hill.cli compare LEFT_RUN RIGHT_RUN --verify-replay
```

On Windows substitute `.venv/Scripts/python.exe` for `.venv/bin/python`.
The tutorial output directory must not already exist. Its `README.md` and
`summary.json` contain the comparisons and replay reports. Failed attempts retain
partial artifacts for diagnosis; use a new output directory for a retry.

## Previous published verification

The combined product tree `5b5f7a480f621044f17cd825bf49962e1667d7f0` passed fresh
committed-lock installation, pip check, Ruff, strict mypy (43 source files),
266 unit/property tests, **521 full-suite tests**, both study validations, and
**11/11 acceptance scenarios**. The separate tutorial execution also passed.
Evidence: [Actions run 39783806030](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/39783806030),
verification commit `24fd01f63a01e7673ba9499f30b9a29119ae1fde`.
The verification branch differs only by a temporary workflow; source, test and
script subtrees were checked against the product tree. This documentation update
does not alter executable source, tests, configuration, dependencies or studies.
See `BUILD_LOG.md` for the earlier review-fix evidence and exact subtree hashes.

Verification used Ubuntu and Python 3.12.15 with the committed 38-pin lock.
Local focused tests used partially installed Python 3.13 dependencies; some
combined local reruns exceeded their execution limit and are not passing evidence.
Native Windows/macOS execution, multiprocess stress and power-loss recovery were
not verified. No independent human review is claimed. The temporary verification
workflow was not merged into main; there is still no persistent main-branch CI.

## Local replay-failure verification

The uncommitted `replay-fail` worktree passed Ruff, strict mypy (43 source files),
**549 passed / 4 skipped** on Windows using `../assess/.venv/Scripts/python.exe`,
**11/11 acceptance scenarios**, and both unchanged study validations. The 30 new
offline regression cases cover provider failures at different policy boundaries,
retry exhaustion, failure during retry, failed branches, illegal-action handling,
and rehashed inconsistent failure histories. The original pre-fix 17-event failure
fixture now replays identically; isolated replay smoke passes. Commands and the
unfiltered smoke's negative-fixture limitation are recorded in `BUILD_LOG.md`.
No Git writes, network, installs, or owner decisions were made in this slice.

## Boundaries and remaining engineering directions

Replay verifies deterministic engine transitions given recorded actions and
typed `ProviderError` outcomes in existing `RunFailed` seals, including episodes
with `invalid_llm_output` abstentions after bounded retries. Replay calls no
provider: it raises the recorded error only when the engine reaches that agent's
proposal boundary at the recorded round, then compares the regenerated prefix
and terminal state/seal. Conflicting proposals and inconsistent failure histories
are refused. Existing event bytes, versions, and study hashes are unchanged;
no ADR-level architecture change was needed. Provider sampling, retry transcripts,
and arbitrary exception classes are not reproduced. Failure messages are recorded
inputs, not independently authenticated evidence of an outage. Policy labels are not a
serialization of executable policy objects or an authentication scheme. Nested
branches require explicit resupply of inherited non-original policies. A terminal
branch can replay, but its inherited terminal checkpoint cannot be forked again
without an explicit representation for a zero-length parent segment.

Comparisons require the same mechanism hash and report full-episode totals,
including shared pre-fork history. Two episodes are not statistical evidence of
a treatment effect. Equal kernel streams do not imply paired provider randomness,
equal draw consumption or reduced variance. Hash links check consistency relative
to a retained commitment, not authenticity against a writer who can replace every
artifact. Existing best-effort cleanup and filesystem hard-link limitations remain.

Useful next independent increments are a declared multi-replicate contrast design
and serializable policy-override specifications. Real providers, condition-order
randomisation for paid pilots, and scientific preregistration still need the
separate decisions below.
No unfinished prototype from this pass is required to run the new workflow.

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
