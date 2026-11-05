# HANDOFF — current work, 2026-11-05

## Direction

Collaborative Hill Lab is a reproducible laboratory for explaining how interaction,
information and institutional rules affect cooperation and shared evidence. The
current research findings describe scripted agents in synthetic environments.
This engineering pass connects the existing experiments to a coherent discovery,
run and inspection workflow. It does not change the underlying scientific results.

Use [NEXT.md](NEXT.md) for the prioritized queue, [PLAN.md](PLAN.md) for milestones,
[BUILD_LOG.md](BUILD_LOG.md) for executed verification, and
[the research charter](docs/research/RESEARCH_CHARTER.md) for scientific scope.
The previous long checkpoint remains preserved in
[the November 2 handoff](https://github.com/Chris0Jeky/collaborative-hill-lab/blob/b8e072041f97314c6d4e8c00cbdd3dea8f208435/HANDOFF.md).
Its pending/next statements describe that historical checkpoint, not today's queue.

## Current capabilities and delivery

The core workflow, monitor and pilot decision aid are merged. The optional HTML
comparison is implemented, independently reviewed and verified; its publication
record is [PR #121](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/121).

| Work | Tracker | Delivery record |
|---|---|---|
| Experiment catalog and connected entry points | [#110](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/110) | Reviewed, verified and merged in PR #119 |
| Verified interactive round/state inspector | [#111](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/111) | Reviewed, verified and merged in PR #119, including ancestry and guarded exports |
| Operational text/JSON run inventory | [#112](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/112) | Reviewed, verified and merged in PR #114 |
| Identity, roadmap and repeatable issue seeds | [#113](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/113) | Reviewed, verified and merged in PR #119 |
| Public-command reproduction walkthrough | [#115](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/115) | Real 18-run graph workflow reviewed, verified and merged in PR #119 |
| Aligned HTML comparison of sealed runs | [#116](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/116) | Implemented, independently reviewed and verified; delivery recorded in PR #121 |
| Prepared pilot decision record | [#118](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/118) | Reviewed, verified and merged in PR #120; all owner choices remain unresolved |

[PR #119](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/119) merged as
`a4e8d43d`; [PR #120](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/120)
merged as `b7230795`. Monitor delivery is retained in
[PR #114](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/114). For the
comparison's published head, final checks and merge status, use
[PR #121](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/121).

## Completed verification

| Scope | Tested head | Result |
|---|---|---|
| Core workflow | `77381713` | Both complete Ubuntu/Windows jobs passed in [CI 42091406335](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091406335); full logs and inspector captures reviewed |
| Pilot decision aid | `f8fb3465` | Both complete platform jobs passed in [CI 42091419268](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091419268); full logs reviewed |
| HTML comparison | `59a4432` | Both complete platform jobs passed in [CI 42091563004](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/42091563004); full logs and all five inspector/comparison captures reviewed |
| Integrated local checkout | `4231ac9` | Complete required offline gate exited 0; 2,308 tests collected, with 10 native-Windows skips on Linux; checkout clean |

The comparison browser check passed **379 desktop and 379 mobile assertions**.
Retained views were readable without horizontal overflow. Native Windows checks
include the corrected directory sharing guards. The table identifies the exact
tested revisions; PR records retain subsequent publication checks and merge
history. Earlier checkpoints remain in [BUILD_LOG.md](BUILD_LOG.md).

The implementation design and task plan are in
[the coherent-lab specification](docs/superpowers/specs/2026-11-05-coherent-lab-design.md)
and [implementation plan](docs/superpowers/plans/2026-11-05-coherent-lab.md).
The next research item is
[#117](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/117): declare a
separate audit cost/timing experiment before execution. The
[pilot decision aid](docs/research/PILOT_DECISION_RECORD.md) is ready for owner
discussion and leaves weights, outcomes, models, allocation and spending unresolved.
All eight issue seeds retain their existing pinned numbers; closed work stays closed.

## Scientific state to preserve

- Studies 000, 001 and both 002 components remain unfrozen.
- Study 001's placeholder weights still fail collective stakes (C2); the configured
  dilemma is not certified. The incentive atlas describes finite-strategy alternatives.
- Graph, responsive-commons, quality-safeguards, rule-ablation, noisy-corpus and
  audit-feedback findings retain their original inputs, source records and results.
- Audit-feedback originals and the separate audit-aware prompt adapter are merged
  in [#107](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/107) and
  [#109](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/109).
- Provider transport and audit-aware prompts are capabilities verified offline.
  No measured live-model audit response or benefit has been established.
- Reproducing a result in verification does not replace original evidence or add samples.

## Verification commands

```bash
make check test validate acceptance check-atlas check-study002 check-responsive check-quality-safeguards check-graph check-sparse-ptft check-noisy-corpus check-ec-rule-ablation check-audit-feedback
```

Use the committed dependency lock through `make setup`. The CI matrix is Ubuntu
24.04 / Windows 2025 and Python 3.12. Preserve exact commit and clean-workspace
checks. For focused local commands consult [AGENTS.md](AGENTS.md) and the relevant
PR; final hosted evidence belongs to the exact published head, not its predecessor.

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
