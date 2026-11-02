# Evidence Commons: independent rule component ablations

Exploratory, unfrozen, deterministic synthetic experiment for issue #95.
The [design and hand predictions](DESIGN.md) were committed before execution.
The previous quality-safeguards experiment and v1 policies remain unchanged.

**192 behavioral episodes, 96 fixed-action controls, 288 verified ledger replays.** Each episode has 14 rounds.
There are 384 conditional single-component contrasts and 396 conditional interactions.
These counts enumerate a chosen finite design; they are not independent samples.

## Prediction audit

Held: P1, P2, P3, P4, P5, P6. Missed: none.
All misses, if any, remain in RESULTS.json with the original expected values.

| Prediction | Scope | Held |
|---|---|---|
| P1 | Truth action/observation identity and signed scores | True |
| P2 | Unchanged v1 endpoints | True |
| P3 | Complete hand-derived outcome table | True |
| P4 | Structural action nulls | True |
| P5 | Literal interactions and probe interaction nulls | True |
| P6 | Same-action integrity | True |

## Reading of the executed contrasts

S = evidence screen; H = share contradictions; C = challenges; R = require read support
among a claim's citations. All four are independently switched; every contrast holds
the other bits fixed. The quorum, costs and action priority remain the same.

All accurate/misleading pairs share their observation and action schedules if P1 holds.
Consequently any reduction in accepted false slots has a matched loss of accepted true
slots. No component acquires a truth signal. Corroborated false consensus remains a
negative control, and source labels do not establish independent information.

### Citation access probe (separate from the original corpus contexts)

- accurate: R=0 to R=1 changes quality 12 to 0, effort 10 to 8, and total utility 7 to -8.
- misleading: R=0 to R=1 changes quality -12 to 0, effort 10 to 8, and total utility -27 to -8.

The peer cites a public item the focal agent has not inspected after exhausting
its inspection budget. R gates that verification even though the proposition passes
the two-source screen. In the full-inspection contexts R's null effects are retained.

### Why the other components interact

Sharing changes who can inspect the contradiction and how many rounds remain.
Challenges precede verification but do not forbid later verification of the same claim.
The existing quorum counts proposals/verifications, not challenges; verification can
therefore reopen peers' participation. In the defender context a policy also cannot
challenge its own proposal. These are context-dependent paths, not additive safeguards.

## Matched single-component effects

Each row is eight pairs (every setting of the other three bits). Ranges retain the
conditional effects; no averaging across contexts or truths is used.

| Context | Truth | Switch | Action-changing pairs | Quality delta | Effort delta | Total utility delta |
|---|---|---|---:|---|---|---|
| corroborated-private | accurate | S | 0/8 | 0 | 0 | 0 |
| corroborated-private | accurate | H | 0/8 | 0 | 0 | 0 |
| corroborated-private | accurate | C | 0/8 | 0 | 0 | 0 |
| corroborated-private | accurate | R | 0/8 | 0 | 0 | 0 |
| corroborated-private | misleading | S | 0/8 | 0 | 0 | 0 |
| corroborated-private | misleading | H | 0/8 | 0 | 0 | 0 |
| corroborated-private | misleading | C | 0/8 | 0 | 0 | 0 |
| corroborated-private | misleading | R | 0/8 | 0 | 0 | 0 |
| conflicted-private | accurate | S | 8/8 | -24 to 0 | -24 to -10 | -28 to 18 |
| conflicted-private | accurate | H | 8/8 | -24 to 0 | -6 to 7 | -40 to 6 |
| conflicted-private | accurate | C | 6/8 | -24 to 0 | -6 to 4 | -32 to 1 |
| conflicted-private | accurate | R | 0/8 | 0 | 0 | 0 |
| conflicted-private | misleading | S | 8/8 | 0 to 24 | -24 to -10 | 18 to 62 |
| conflicted-private | misleading | H | 8/8 | 0 to 24 | -6 to 7 | -7 to 36 |
| conflicted-private | misleading | C | 6/8 | 0 to 24 | -6 to 4 | 0 to 44 |
| conflicted-private | misleading | R | 0/8 | 0 | 0 | 0 |
| echo-private | accurate | S | 8/8 | -24 | -24 | -14 |
| echo-private | accurate | H | 0/8 | 0 | 0 | 0 |
| echo-private | accurate | C | 0/8 | 0 | 0 | 0 |
| echo-private | accurate | R | 0/8 | 0 | 0 | 0 |
| echo-private | misleading | S | 8/8 | 24 | -24 | 62 |
| echo-private | misleading | H | 0/8 | 0 | 0 | 0 |
| echo-private | misleading | C | 0/8 | 0 | 0 | 0 |
| echo-private | misleading | R | 0/8 | 0 | 0 | 0 |
| conflicted-ledger | accurate | S | 8/8 | -24 to 0 | -30 to -24 | -14 to 30 |
| conflicted-ledger | accurate | H | 0/8 | 0 | 0 | 0 |
| conflicted-ledger | accurate | C | 4/8 | -24 to 0 | 0 to 6 | -44 to 0 |
| conflicted-ledger | accurate | R | 0/8 | 0 | 0 | 0 |
| conflicted-ledger | misleading | S | 8/8 | 0 to 24 | -30 to -24 | 30 to 62 |
| conflicted-ledger | misleading | H | 0/8 | 0 | 0 | 0 |
| conflicted-ledger | misleading | C | 4/8 | 0 to 24 | 0 to 6 | 0 to 32 |
| conflicted-ledger | misleading | R | 0/8 | 0 | 0 | 0 |
| defender-private | accurate | S | 8/8 | -24 to 0 | -12 to -6 | -32 to 8 |
| defender-private | accurate | H | 8/8 | -12 to 0 | 6 to 7 | -26 to -6 |
| defender-private | accurate | C | 8/8 | -24 to 0 | -1 to 4 | -38 to 1 |
| defender-private | accurate | R | 0/8 | 0 | 0 | 0 |
| defender-private | misleading | S | 8/8 | 0 to 24 | -12 to -6 | 15 to 44 |
| defender-private | misleading | H | 8/8 | 0 to 12 | 6 to 7 | -7 to 12 |
| defender-private | misleading | C | 8/8 | 0 to 24 | -1 to 4 | 1 to 30 |
| defender-private | misleading | R | 0/8 | 0 | 0 | 0 |
| unread-private | accurate | S | 0/8 | 0 | 0 | 0 |
| unread-private | accurate | H | 0/8 | 0 | 0 | 0 |
| unread-private | accurate | C | 0/8 | 0 | 0 | 0 |
| unread-private | accurate | R | 8/8 | -12 | -2 | -15 |
| unread-private | misleading | S | 0/8 | 0 | 0 | 0 |
| unread-private | misleading | H | 0/8 | 0 | 0 | 0 |
| unread-private | misleading | C | 0/8 | 0 | 0 | 0 |
| unread-private | misleading | R | 8/8 | 12 | -2 | 19 |

## Nonzero quality interactions

Alternating sums, not regression coefficients or averages. A dash in SHCR marks a
varied bit. Every zero and every effort/credit/utility interaction remains in JSON.

| Context | Truth | Factors | Background SHCR | Quality interaction |
|---|---|---|---|---:|
| conflicted-private | accurate | SH | --00 | -12 |
| conflicted-private | accurate | SH | --01 | -12 |
| conflicted-private | accurate | SH | --10 | 24 |
| conflicted-private | accurate | SH | --11 | 24 |
| conflicted-private | accurate | SC | -0-0 | -12 |
| conflicted-private | accurate | SC | -0-1 | -12 |
| conflicted-private | accurate | SC | -1-0 | 24 |
| conflicted-private | accurate | SC | -1-1 | 24 |
| conflicted-private | accurate | HC | 0--0 | -24 |
| conflicted-private | accurate | HC | 0--1 | -24 |
| conflicted-private | accurate | HC | 1--0 | 12 |
| conflicted-private | accurate | HC | 1--1 | 12 |
| conflicted-private | accurate | SHC | ---0 | 36 |
| conflicted-private | accurate | SHC | ---1 | 36 |
| conflicted-private | misleading | SH | --00 | 12 |
| conflicted-private | misleading | SH | --01 | 12 |
| conflicted-private | misleading | SH | --10 | -24 |
| conflicted-private | misleading | SH | --11 | -24 |
| conflicted-private | misleading | SC | -0-0 | 12 |
| conflicted-private | misleading | SC | -0-1 | 12 |
| conflicted-private | misleading | SC | -1-0 | -24 |
| conflicted-private | misleading | SC | -1-1 | -24 |
| conflicted-private | misleading | HC | 0--0 | 24 |
| conflicted-private | misleading | HC | 0--1 | 24 |
| conflicted-private | misleading | HC | 1--0 | -12 |
| conflicted-private | misleading | HC | 1--1 | -12 |
| conflicted-private | misleading | SHC | ---0 | -36 |
| conflicted-private | misleading | SHC | ---1 | -36 |
| conflicted-ledger | accurate | SC | -0-0 | 24 |
| conflicted-ledger | accurate | SC | -0-1 | 24 |
| conflicted-ledger | accurate | SC | -1-0 | 24 |
| conflicted-ledger | accurate | SC | -1-1 | 24 |
| conflicted-ledger | misleading | SC | -0-0 | -24 |
| conflicted-ledger | misleading | SC | -0-1 | -24 |
| conflicted-ledger | misleading | SC | -1-0 | -24 |
| conflicted-ledger | misleading | SC | -1-1 | -24 |
| defender-private | accurate | SH | --10 | 12 |
| defender-private | accurate | SH | --11 | 12 |
| defender-private | accurate | SC | -0-0 | -24 |
| defender-private | accurate | SC | -0-1 | -24 |
| defender-private | accurate | SC | -1-0 | -12 |
| defender-private | accurate | SC | -1-1 | -12 |
| defender-private | accurate | HC | 0--0 | -12 |
| defender-private | accurate | HC | 0--1 | -12 |
| defender-private | accurate | SHC | ---0 | 12 |
| defender-private | accurate | SHC | ---1 | 12 |
| defender-private | misleading | SH | --10 | -12 |
| defender-private | misleading | SH | --11 | -12 |
| defender-private | misleading | SC | -0-0 | 24 |
| defender-private | misleading | SC | -0-1 | 24 |
| defender-private | misleading | SC | -1-0 | 12 |
| defender-private | misleading | SC | -1-1 | 12 |
| defender-private | misleading | HC | 0--0 | 12 |
| defender-private | misleading | HC | 0--1 | 12 |
| defender-private | misleading | SHC | ---0 | -12 |
| defender-private | misleading | SHC | ---1 | -12 |

## All component combinations

Quality and utility are shown as accurate / misleading. Effort and contribution
are the same across the paired truth worlds. Per-agent data and full typed action
schedules are in [RESULTS.json](RESULTS.json).

### corroborated-private

| SHCR | Accepted slots | Quality | Effort | Contribution | Total utility |
|---|---:|---|---:|---|---|
| 0000 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0001 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0010 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0011 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0100 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0101 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0110 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0111 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1000 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1001 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1010 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1011 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1100 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1101 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1110 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1111 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |

### conflicted-private

| SHCR | Accepted slots | Quality | Effort | Contribution | Total utility |
|---|---:|---|---:|---|---|
| 0000 | 2 | 24 / -24 | 41 | 16/21 | -3 / -79 |
| 0001 | 2 | 24 / -24 | 41 | 16/21 | -3 / -79 |
| 0010 | 2 | 24 / -24 | 40 | 11/14 | -2 / -78 |
| 0011 | 2 | 24 / -24 | 40 | 11/14 | -2 / -78 |
| 0100 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0101 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0110 | 0 | 0 / 0 | 42 | 1 | -42 / -42 |
| 0111 | 0 | 0 / 0 | 42 | 1 | -42 / -42 |
| 1000 | 1 | 12 / -12 | 26 | 4/7 | -9 / -43 |
| 1001 | 1 | 12 / -12 | 26 | 4/7 | -9 / -43 |
| 1010 | 0 | 0 / 0 | 30 | 2/3 | -30 / -30 |
| 1011 | 0 | 0 / 0 | 30 | 2/3 | -30 / -30 |
| 1100 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1101 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1110 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1111 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |

### echo-private

| SHCR | Accepted slots | Quality | Effort | Contribution | Total utility |
|---|---:|---|---:|---|---|
| 0000 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0001 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0010 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0011 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0100 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0101 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0110 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0111 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 1000 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1001 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1010 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1011 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1100 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1101 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1110 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |
| 1111 | 0 | 0 / 0 | 24 | 4/7 | -24 / -24 |

### conflicted-ledger

| SHCR | Accepted slots | Quality | Effort | Contribution | Total utility |
|---|---:|---|---:|---|---|
| 0000 | 2 | 24 / -24 | 42 | 11/14 | -4 / -80 |
| 0001 | 2 | 24 / -24 | 42 | 11/14 | -4 / -80 |
| 0010 | 0 | 0 / 0 | 48 | 1 | -48 / -48 |
| 0011 | 0 | 0 / 0 | 48 | 1 | -48 / -48 |
| 0100 | 2 | 24 / -24 | 42 | 11/14 | -4 / -80 |
| 0101 | 2 | 24 / -24 | 42 | 11/14 | -4 / -80 |
| 0110 | 0 | 0 / 0 | 48 | 1 | -48 / -48 |
| 0111 | 0 | 0 / 0 | 48 | 1 | -48 / -48 |
| 1000 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |
| 1001 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |
| 1010 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |
| 1011 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |
| 1100 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |
| 1101 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |
| 1110 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |
| 1111 | 0 | 0 / 0 | 18 | 3/7 | -18 / -18 |

### defender-private

| SHCR | Accepted slots | Quality | Effort | Contribution | Total utility |
|---|---:|---|---:|---|---|
| 0000 | 2 | 24 / -24 | 41 | 16/21 | -3 / -79 |
| 0001 | 2 | 24 / -24 | 41 | 16/21 | -3 / -79 |
| 0010 | 2 | 24 / -24 | 40 | 11/14 | -2 / -78 |
| 0011 | 2 | 24 / -24 | 40 | 11/14 | -2 / -78 |
| 0100 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0101 | 2 | 24 / -24 | 48 | 13/14 | -10 / -86 |
| 0110 | 1 | 12 / -12 | 47 | 20/21 | -28 / -66 |
| 0111 | 1 | 12 / -12 | 47 | 20/21 | -28 / -66 |
| 1000 | 2 | 24 / -24 | 30 | 13/21 | 4 / -64 |
| 1001 | 2 | 24 / -24 | 30 | 13/21 | 4 / -64 |
| 1010 | 0 | 0 / 0 | 34 | 5/7 | -34 / -34 |
| 1011 | 0 | 0 / 0 | 34 | 5/7 | -34 / -34 |
| 1100 | 2 | 24 / -24 | 36 | 16/21 | -2 / -70 |
| 1101 | 2 | 24 / -24 | 36 | 16/21 | -2 / -70 |
| 1110 | 0 | 0 / 0 | 40 | 6/7 | -40 / -40 |
| 1111 | 0 | 0 / 0 | 40 | 6/7 | -40 / -40 |

### unread-private

| SHCR | Accepted slots | Quality | Effort | Contribution | Total utility |
|---|---:|---|---:|---|---|
| 0000 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 0001 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |
| 0010 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 0011 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |
| 0100 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 0101 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |
| 0110 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 0111 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |
| 1000 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 1001 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |
| 1010 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 1011 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |
| 1100 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 1101 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |
| 1110 | 1 | 12 / -12 | 10 | 3/14 | 7 / -27 |
| 1111 | 0 | 0 / 0 | 8 | 4/21 | -8 / -8 |

## Integrity and limits

Truth controls: 96. Endpoint bridges: 24. Fixed-action integrity: 96/96.
The aggregate controls replay the accurate world's exact action schedules and test
task/total-utility integrity. They do not estimate a behavioral accountability effect.
No incentive certificate, final weights, live provider or human inference is added.
These six diagnostic contexts do not specify how often any corpus structure occurs.

## Reproduce

```bash
python experiments/ec-rule-ablation/ec_rule_ablation.py --out artifacts/ec-ablation-new
python experiments/ec-rule-ablation/ec_rule_ablation.py --check
```

`--out` requires committed clean source and a fresh destination; it saves inputs,
sealed runs, controls and readout. `--check` regenerates and replays every run in a
temporary directory, then byte-compares JSON and Markdown. No provider is called.
[SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json) binds the original execution source.
Study hash: `eb4d1bcf9a3165a54e8b601c4e17fcb6d7da4f14033a9dcec93b17cd48f9b086`.
