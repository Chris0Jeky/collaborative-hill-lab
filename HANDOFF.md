# HANDOFF — current checkpoint, 2026-10-22

The previous handoff is preserved byte-for-byte in
[the historical checkpoint](docs/history/HANDOFF-through-2026-10-21.md).
Its dated counts, paths and publication states are historical, not current status.
The operating rules remain in `CLAUDE.md` and `AGENTS.md`; the repository remains T1.

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

## Exact verification

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

## Boundaries and remaining engineering directions

Replay verifies deterministic engine transitions given recorded actions, not
provider sampling or arbitrary provider exceptions. Policy labels are not a
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

Useful next independent increments are a declared multi-replicate contrast design,
serializable policy-override specifications, and explicit replay support for
recorded provider failures. Real providers, condition-order randomisation for paid
pilots, and scientific preregistration still need the separate decisions below.
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
