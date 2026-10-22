# HANDOFF — current checkpoint, 2026-10-22

The previous handoff is preserved byte-for-byte in
[the historical checkpoint](docs/history/HANDOFF-through-2026-10-21.md).
Its dated counts, paths and publication states are historical, not current status.
The operating rules remain in `CLAUDE.md` and `AGENTS.md`; the repository remains T1.

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
