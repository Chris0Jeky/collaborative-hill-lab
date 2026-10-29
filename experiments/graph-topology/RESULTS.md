# Graph topology — exact deterministic readout

**Executed, unfrozen exploratory controls; scripted agents only.**
18/18 complete cooperation curves match the local pre-execution predictions. Every original sealed run was independently replayed for this report.

N=5, one AllD, eight rounds t=0,…,7, zero exploration, and mean incident-edge payoff are fixed. Each row is one deterministic episode. Symmetry controls and regeneration checks add no independent outcome information.

## Measured outcomes

All entries are exact fractions. The JSON retains full predicted/measured curves, eligible vote counts, agent degrees, seed identities and terminal commitments.

| Topology | AllD seat | Reciprocator policy | Mean cooperation | Final round | Cumulative mean-edge scores (a1, a2, a3, a4, a5) | Prediction match |
|---|---|---|---:|---:|---|---|
| complete | a1 | targeted | 5/8 | 3/5 | 12, 79/4, 79/4, 79/4, 79/4 | True |
| complete | a1 | linked | 1/10 | 0 | 12, 37/4, 37/4, 37/4, 37/4 | True |
| complete | a1 | quorum | 4/5 | 4/5 | 40, 18, 18, 18, 18 | True |
| complete | a2 | targeted | 5/8 | 3/5 | 79/4, 12, 79/4, 79/4, 79/4 | True |
| complete | a2 | linked | 1/10 | 0 | 37/4, 12, 37/4, 37/4, 37/4 | True |
| complete | a2 | quorum | 4/5 | 4/5 | 18, 40, 18, 18, 18 | True |
| ring | a1 | targeted | 5/8 | 3/5 | 12, 31/2, 24, 24, 31/2 | True |
| ring | a1 | linked | 3/20 | 0 | 12, 21/2, 21/2, 21/2, 21/2 | True |
| ring | a1 | quorum | 4/5 | 4/5 | 40, 12, 24, 24, 12 | True |
| ring | a2 | targeted | 5/8 | 3/5 | 31/2, 12, 31/2, 24, 24 | True |
| ring | a2 | linked | 3/20 | 0 | 21/2, 12, 21/2, 21/2, 21/2 | True |
| ring | a2 | quorum | 4/5 | 4/5 | 12, 40, 12, 24, 24 | True |
| star | a1 | targeted | 1/16 | 0 | 12, 7, 7, 7, 7 | True |
| star | a1 | linked | 1/16 | 0 | 12, 7, 7, 7, 7 | True |
| star | a1 | quorum | 1/10 | 0 | 12, 7, 7, 7, 7 | True |
| star | a2 | targeted | 49/64 | 3/4 | 79/4, 12, 24, 24, 24 | True |
| star | a2 | linked | 5/32 | 0 | 49/4, 12, 9, 9, 9 | True |
| star | a2 | quorum | 4/5 | 4/5 | 18, 40, 24, 24, 24 | True |

## Interpretation and boundaries

Compare topologies within a fixed policy and defector-seat condition. The star has hub a1 and leaf a2; moving AllD changes policy placement. Targeted, linked and quorum TFT also differ in action/observation rules. Pairwise rates count directed edge votes and weight agents by degree; neighbourhood rates count one vote per positive-degree agent. The different star first-round rates already reflect AllD's degree before any reciprocal response.

This experiment fixes mean payoff in both modes. Legacy complete-graph equivalence separately uses pairwise/sum and neighbourhood/mean; the complete pairwise mean scores here equal legacy summed scores divided by four.

No uncertainty interval, p-value, population-size causal effect, human/LLM response or sparse-graph count-state pTFT model is inferred. Analytical predictions remain distinct from measured outcomes, including any mismatch.

## Execution provenance

- Study content hash: `8e4b5b5d2efc29c1e92918a21a74c2e0b590c4f1717a6c161890d571d512028a`; unfrozen.
- Local execution checkout: `873666aa9dfe1de7cc76d31275b4828fa44e065d`.
- Clean local tree commitment, when available: `875823c171036dcf40a0b9f2834074bce7ad05f9`.
- Worktree dirty before execution: `False`.
- Execution file commitment: `e82eb752e391c1ff68c27af6aaccd2784c850b11a40b9f5eb0bd0f5764987422` over 71 named source/input files.
- Report generator source SHA-256: `4c81e3831bb47fd57a2f42858a1319ed12d04d1dba851a5559877e0065a83105`.

Commit identifiers above describe local source identity; no published GitHub revision or external preregistration timestamp is asserted. The execution source record was captured before running; per-run manifests preserve their own dirty flags. The source commitment and hash-linked ledgers establish consistency relative to retained evidence, not independent authenticity.

Original ledgers and EXECUTION_SOURCE.json are generated artifacts. Rebuilding this readout requires those artifacts; running newer source is a new execution. Use graph_experiment.py --report-from <artifact-root> --output <fresh-prefix>.
