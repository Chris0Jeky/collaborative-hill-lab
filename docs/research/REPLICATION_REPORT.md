# Replication report — Study 000 (legacy reproduction and audit)

Study hash: `5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f` | conditions: 11 | replicates/condition: 30 | rounds: 50 | seed: 20260713

Derived from sealed event ledgers only. Predictions were stated in the study
README before execution. Legacy artifacts were NOT used as targets: the legacy
pipeline was unseeded and its pairwise tracking was defective
(`docs/research/LEGACY_AUDIT.md`), so this study reproduces *claims*, not CSVs.

## Condition results vs analytical predictions

| condition | replicates | mean coop (mean±sd) | final-window mean [95% CI] | prediction | verdict |
|---|---|---|---|---|---|
| pw-3tft | 30 | 1.0000±0.0000 | 1.0000 [1.0000, 1.0000] | cooperation 1.0 every round; scores 300 each | REPRODUCED (exact) |
| pw-2tft-alld | 30 | 0.3400±0.0000 | 0.3333 [0.3333, 0.3333] | quarantine: mean vote rate = (4/6 + 49*(2/6))/50 ≈ 0.3467 | REPRODUCED (exact) |
| pw-2tftlinked-alld | 30 | 0.0133±0.0000 | 0.0000 [0.0000, 0.0000] | collapse despite pairwise structure: all-D from round 2 | REPRODUCED (exact) |
| nb-3ptft-incself | 30 | 1.0000±0.0000 | 1.0000 [1.0000, 1.0000] | all-C absorbing: cooperation 1.0 | REPRODUCED (exact) |
| nb-2ptft-alld-incself | 30 | 0.0482±0.0316 | 0.0000 [0.0000, 0.0000] | Tragic Valley: final-window ~0 (collapse) | REPRODUCED (qualitative) |
| nb-2ptft-alld-excself | 30 | 0.0260±0.0164 | 0.0000 [0.0000, 0.0000] | valley, faster decay than include_self | REPRODUCED (qualitative) |
| nb-2tftthresh-alld | 30 | 0.6667±0.0000 | 0.6667 [0.6667, 0.6667] | NO collapse: sustained 2/3 group rate (knife-edge quorum) | REPRODUCED (exact) |
| pw-2tfte-alld | 30 | 0.2027±0.0679 | 0.1433 [0.1072, 0.1806] | legacy: 'pair with the always defect agent largely defect' ~25% (prisoners.tex) | REPRODUCED (qualitative) |
| nb-2ptfte-alld-incself | 30 | 0.1231±0.0553 | 0.0700 [0.0444, 0.0956] | legacy: ~20% cooperation with AllD (prisoners.tex) | REPRODUCED (qualitative) |
| pw-2tfte-allc | 30 | 0.8496±0.0583 | 0.8439 [0.8106, 0.8756] | legacy: 'pair with the collaborative agent largely collaborate' ~75% (prisoners.tex) | REPRODUCED (qualitative) |
| nb-2ptfte-allc-incself | 30 | 0.9184±0.0591 | 0.8756 [0.8256, 0.9144] | legacy: ~80% cooperation with AllC (prisoners.tex) | REPRODUCED (qualitative) |

Deterministic conditions: `identical_summaries` must be true across replicates (determinism check, not variance):

- pw-3tft: identical summaries across replicates = True
- pw-2tft-alld: identical summaries across replicates = True
- pw-2tftlinked-alld: identical summaries across replicates = True
- nb-3ptft-incself: identical summaries across replicates = True
- nb-2tftthresh-alld: identical summaries across replicates = True

## Legacy claim classification

| legacy claim | condition here | status |
|---|---|---|
| 3 TFT pairwise sustained cooperation | pw-3tft | qualitatively reproduced |
| 2 TFT + AllD pairwise: quarantine, largely collaborative | pw-2tft-alld | qualitatively reproduced |
| 2 TFT + AllD neighbourhood: descent into the Tragic Valley | nb-2ptft-alld-incself | qualitatively reproduced |
| TFT-E + AllD: pairwise ~25% vs neighbourhood ~20% | pw-2tfte-alld | qualitatively reproduced |
| TFT-E + AllC: pairwise ~75% vs neighbourhood ~80% | pw-2tfte-allc | qualitatively reproduced |
| Q-learning pairwise ~80% vs neighbourhood ~20% | — | blocked (out of scope: RL agents not in foundation) |

## Deconfound findings

- `pw-2tftlinked-alld` (npdl's linked 'pairwise' TFT): REPRODUCED (exact) — collapse *inside* the pairwise structure shows targeted per-opponent reciprocity (not the pairwise payoff structure alone) carries the Collaborative Hill.
- `nb-2tftthresh-alld` (npdl's threshold TFT): REPRODUCED (exact) — sustained cooperation *inside* the neighbourhood structure shows the Tragic Valley depends on the reciprocator's decision rule, not the structure alone.

The legacy contrast (per-opponent TFT in pairwise vs probabilistic pTFT in neighbourhood) therefore conflates strategy with structure; both matter. This does not overturn the legacy qualitative story for its chosen strategy pair, but it narrows the claim that structure alone explains the effect.

## Exact-number reproduction status

Deterministic conditions reproduce their analytical oracle exactly (table above). Exact reproduction of legacy CSVs/figures is NOT claimed and NOT possible: unseeded legacy runs, contaminated pairwise CSVs, and an underspecified cooperation denominator in the draft (whether 66%/75% style figures count TFT votes only, all votes, or agents-mostly-cooperating is not stated).

Whether any legacy result is considered 'replicated' for publication purposes is a HUMAN decision (see HANDOFF.md).