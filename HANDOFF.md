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

## Authoritative baseline and current work

The connected GitHub repository started this pass at main
`b8e072041f97314c6d4e8c00cbdd3dea8f208435`, with no open issues or PRs. The uploaded
ZIP matches all 418 file blobs and tree `17823dff30a1b3f039809168e1e829a3bd117be2`.
Main's [CI 41459865315](https://github.com/Chris0Jeky/collaborative-hill-lab/actions/runs/41459865315)
passed Ubuntu and Windows; both logs confirm the commit and all verification gates.
The local baseline passed all 2,171 tests with the committed dependency versions.

| Work | Tracker | Status at this working checkpoint |
|---|---|---|
| Experiment catalog and connected entry points | [#110](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/110) | Implemented and integrated; independent review pending |
| Verified interactive round/state inspector | [#111](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/111) | Implemented; 41 combined console/demo/walkthrough tests pass; browser CI and independent review pending |
| Operational text/JSON run inventory | [#112](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/112), [PR #114](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/114) | 19 focused tests and both complete CI jobs pass on `608ee950`; independent review pending |
| Identity, roadmap and repeatable issue seeds | [#113](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/113) | Implemented; 25 seed tests pass; independent review pending |
| Public-command reproduction walkthrough | [#115](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/115) | Real graph workflow test passes; integrated complete gate pending |

The implementation design and task plan are in
[the coherent-lab specification](docs/superpowers/specs/2026-11-05-coherent-lab-design.md)
and [implementation plan](docs/superpowers/plans/2026-11-05-coherent-lab.md).
Independent worktrees isolate changes. Remote publication uses connector-created
branches, commits and draft PRs; exact-head CI and review precede merge.

The bounded next issues are [#116](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/116)
(paired inspection), [#117](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/117)
(separate audit cost/timing experiment), and
[#118](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/118) (draft pilot
decision record). All eight seeds are pinned to their existing issue numbers.
Local Chromium is blocked by the workspace socket policy; actual browser
execution and screenshot review are delegated to the Ubuntu CI gate.

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
