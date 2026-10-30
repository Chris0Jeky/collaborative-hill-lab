# Quality safeguards — deterministic sensitivity results

This is an unfrozen scripted-policy experiment, not a live-model or human result.
The design and predictions precede execution in [DESIGN.md](DESIGN.md). The checked-in
[RESULTS.json](RESULTS.json) retains every cell, terminal hash, contrast and unilateral
deviation. Execution identity is in [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json).
The closing reading was added after execution and is labelled as such.

**440 behavioral episodes and 220 controlled action replays**, each 14 rounds.
Counts describe this finite grid. They are not frequencies or significance tests.

## Declared predictions

Held: P1, P2, P3, P4, P5, P6, P7, P8, P9, P10. Not held: none.

## Truth negative control

Across 220 accurate/misleading pairs, 220 have identical action schedules and 220 have exactly opposite quality. Corpora in a pair differ only in hidden truth.

## All-active profile

Quality is signed accepted-slot value. Contribution is the fraction of agent-rounds
not withheld. Effort and total utility sum over agents.

| Truth | Structure | Topology | Accountability | Rule | Correct/wrong | Quality | Contribution | Effort | Utility a1/a2/a3 | Total utility |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| accurate | corroborated | private | aggregate | unconditional | 2/0 | 24 | 13/14 | 48 | -10/3/-10/3/-10/3 | -10 |
| accurate | corroborated | private | aggregate | conditional | 0/0 | 0 | 9/14 | 27 | -9/-9/-9 | -27 |
| accurate | corroborated | private | aggregate | skeptical | 0/0 | 0 | 9/14 | 27 | -9/-9/-9 | -27 |
| accurate | corroborated | private | attributable | unconditional | 2/0 | 24 | 13/14 | 48 | -2/-4/-4 | -10 |
| accurate | corroborated | private | attributable | conditional | 2/0 | 24 | 13/14 | 48 | -2/-4/-4 | -10 |
| accurate | corroborated | private | attributable | skeptical | 2/0 | 24 | 13/14 | 48 | -2/-4/-4 | -10 |
| accurate | corroborated | shared_ledger | aggregate | unconditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | corroborated | shared_ledger | aggregate | conditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | corroborated | shared_ledger | aggregate | skeptical | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | corroborated | shared_ledger | attributable | unconditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | corroborated | shared_ledger | attributable | conditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | corroborated | shared_ledger | attributable | skeptical | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | conflicted | private | aggregate | unconditional | 2/0 | 24 | 16/21 | 41 | -4/3/-4/3/-1/3 | -3 |
| accurate | conflicted | private | aggregate | conditional | 2/0 | 24 | 16/21 | 41 | -4/3/-4/3/-1/3 | -3 |
| accurate | conflicted | private | aggregate | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| accurate | conflicted | private | attributable | unconditional | 2/0 | 24 | 16/21 | 41 | 0/-2/-1 | -3 |
| accurate | conflicted | private | attributable | conditional | 2/0 | 24 | 16/21 | 41 | 0/-2/-1 | -3 |
| accurate | conflicted | private | attributable | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| accurate | conflicted | shared_ledger | aggregate | unconditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | conflicted | shared_ledger | aggregate | conditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | conflicted | shared_ledger | aggregate | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |
| accurate | conflicted | shared_ledger | attributable | unconditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | conflicted | shared_ledger | attributable | conditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | conflicted | shared_ledger | attributable | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |
| misleading | corroborated | private | aggregate | unconditional | 0/2 | -24 | 13/14 | 48 | -86/3/-86/3/-86/3 | -86 |
| misleading | corroborated | private | aggregate | conditional | 0/0 | 0 | 9/14 | 27 | -9/-9/-9 | -27 |
| misleading | corroborated | private | aggregate | skeptical | 0/0 | 0 | 9/14 | 27 | -9/-9/-9 | -27 |
| misleading | corroborated | private | attributable | unconditional | 0/2 | -24 | 13/14 | 48 | -30/-28/-28 | -86 |
| misleading | corroborated | private | attributable | conditional | 0/2 | -24 | 13/14 | 48 | -30/-28/-28 | -86 |
| misleading | corroborated | private | attributable | skeptical | 0/2 | -24 | 13/14 | 48 | -30/-28/-28 | -86 |
| misleading | corroborated | shared_ledger | aggregate | unconditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | corroborated | shared_ledger | aggregate | conditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | corroborated | shared_ledger | aggregate | skeptical | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | corroborated | shared_ledger | attributable | unconditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | corroborated | shared_ledger | attributable | conditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | corroborated | shared_ledger | attributable | skeptical | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | conflicted | private | aggregate | unconditional | 0/2 | -24 | 16/21 | 41 | -80/3/-80/3/-77/3 | -79 |
| misleading | conflicted | private | aggregate | conditional | 0/2 | -24 | 16/21 | 41 | -80/3/-80/3/-77/3 | -79 |
| misleading | conflicted | private | aggregate | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| misleading | conflicted | private | attributable | unconditional | 0/2 | -24 | 16/21 | 41 | -28/-26/-25 | -79 |
| misleading | conflicted | private | attributable | conditional | 0/2 | -24 | 16/21 | 41 | -28/-26/-25 | -79 |
| misleading | conflicted | private | attributable | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| misleading | conflicted | shared_ledger | aggregate | unconditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | conflicted | shared_ledger | aggregate | conditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | conflicted | shared_ledger | aggregate | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |
| misleading | conflicted | shared_ledger | attributable | unconditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | conflicted | shared_ledger | attributable | conditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | conflicted | shared_ledger | attributable | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |
| accurate | echo | private | aggregate | unconditional | 2/0 | 24 | 13/14 | 48 | -10/3/-10/3/-10/3 | -10 |
| accurate | echo | private | aggregate | conditional | 0/0 | 0 | 9/14 | 27 | -9/-9/-9 | -27 |
| accurate | echo | private | aggregate | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| accurate | echo | private | attributable | unconditional | 2/0 | 24 | 13/14 | 48 | -2/-4/-4 | -10 |
| accurate | echo | private | attributable | conditional | 2/0 | 24 | 13/14 | 48 | -2/-4/-4 | -10 |
| accurate | echo | private | attributable | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| accurate | echo | shared_ledger | aggregate | unconditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | echo | shared_ledger | aggregate | conditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | echo | shared_ledger | aggregate | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |
| accurate | echo | shared_ledger | attributable | unconditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | echo | shared_ledger | attributable | conditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | echo | shared_ledger | attributable | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |
| misleading | echo | private | aggregate | unconditional | 0/2 | -24 | 13/14 | 48 | -86/3/-86/3/-86/3 | -86 |
| misleading | echo | private | aggregate | conditional | 0/0 | 0 | 9/14 | 27 | -9/-9/-9 | -27 |
| misleading | echo | private | aggregate | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| misleading | echo | private | attributable | unconditional | 0/2 | -24 | 13/14 | 48 | -30/-28/-28 | -86 |
| misleading | echo | private | attributable | conditional | 0/2 | -24 | 13/14 | 48 | -30/-28/-28 | -86 |
| misleading | echo | private | attributable | skeptical | 0/0 | 0 | 4/7 | 24 | -8/-8/-8 | -24 |
| misleading | echo | shared_ledger | aggregate | unconditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | echo | shared_ledger | aggregate | conditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | echo | shared_ledger | aggregate | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |
| misleading | echo | shared_ledger | attributable | unconditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | echo | shared_ledger | attributable | conditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | echo | shared_ledger | attributable | skeptical | 0/0 | 0 | 3/7 | 18 | -6/-6/-6 | -18 |

## Screen effect: skeptical minus conditional

Same quorum, same cell otherwise.

| Truth | Structure | Pairs | Quality up | Quality down | Quality unchanged | Actions equal |
|---|---|---:|---:|---:|---:|---:|
| accurate | corroborated | 36 | 0 | 0 | 36 | 30 |
| accurate | conflicted | 36 | 0 | 18 | 18 | 6 |
| accurate | echo | 4 | 0 | 3 | 1 | 0 |
| misleading | corroborated | 36 | 0 | 0 | 36 | 30 |
| misleading | conflicted | 36 | 18 | 0 | 18 | 6 |
| misleading | echo | 4 | 3 | 0 | 1 | 0 |

## Conflicted minus corroborated

Core cells, access and budgets identical.

| Truth | Rule | Pairs | Quality up | Quality down | Quality unchanged |
|---|---|---:|---:|---:|---:|
| accurate | unconditional | 32 | 0 | 0 | 32 |
| accurate | conditional | 32 | 5 | 0 | 27 |
| accurate | skeptical | 32 | 0 | 13 | 19 |
| misleading | unconditional | 32 | 0 | 0 | 32 |
| misleading | conditional | 32 | 0 | 5 | 27 |
| misleading | skeptical | 32 | 13 | 0 | 19 |

## Observable alignment

Aligned sums accurate-corroborated and misleading-conflicted quality; inverted sums
accurate-conflicted and misleading-corroborated. These are unweighted sums over the
`CCC` cells, not expectations: nothing here says which pairing occurs.

| Topology | Accountability | Rule | Aligned | Inverted |
|---|---|---|---:|---:|
| private | aggregate | unconditional | 0 | 0 |
| private | aggregate | conditional | -24 | 24 |
| private | aggregate | skeptical | 0 | 0 |
| private | attributable | unconditional | 0 | 0 |
| private | attributable | conditional | 0 | 0 |
| private | attributable | skeptical | 24 | -24 |
| shared_ledger | aggregate | unconditional | 0 | 0 |
| shared_ledger | aggregate | conditional | 0 | 0 |
| shared_ledger | aggregate | skeptical | 24 | -24 |
| shared_ledger | attributable | unconditional | 0 | 0 |
| shared_ledger | attributable | conditional | 0 | 0 |
| shared_ledger | attributable | skeptical | 24 | -24 |

## Hidden contradiction: conflicted, `CCF`

`a3` free-rides and holds the only contradicting items.

| Truth | Structure | Topology | Accountability | Rule | Correct/wrong | Quality | Contribution | Effort | Utility a1/a2/a3 | Total utility |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| accurate | conflicted | private | aggregate | unconditional | 2/0 | 24 | 10/21 | 24 | -2/3/-2/3/34/3 | 10 |
| accurate | conflicted | private | aggregate | conditional | 1/0 | 12 | 3/7 | 20 | -13/3/-13/3/17/3 | -3 |
| accurate | conflicted | private | aggregate | skeptical | 1/0 | 12 | 3/7 | 20 | -13/3/-13/3/17/3 | -3 |
| accurate | conflicted | private | attributable | unconditional | 2/0 | 24 | 10/21 | 24 | 2/0/8 | 10 |
| accurate | conflicted | private | attributable | conditional | 1/0 | 12 | 3/7 | 20 | -3/-4/4 | -3 |
| accurate | conflicted | private | attributable | skeptical | 1/0 | 12 | 3/7 | 20 | -3/-4/4 | -3 |
| accurate | conflicted | shared_ledger | aggregate | unconditional | 2/0 | 24 | 10/21 | 24 | -2/3/-2/3/34/3 | 10 |
| accurate | conflicted | shared_ledger | aggregate | conditional | 1/0 | 12 | 3/7 | 20 | -13/3/-13/3/17/3 | -3 |
| accurate | conflicted | shared_ledger | aggregate | skeptical | 0/0 | 0 | 2/7 | 12 | -6/-6/0 | -12 |
| accurate | conflicted | shared_ledger | attributable | unconditional | 2/0 | 24 | 10/21 | 24 | 2/0/8 | 10 |
| accurate | conflicted | shared_ledger | attributable | conditional | 1/0 | 12 | 3/7 | 20 | -3/-4/4 | -3 |
| accurate | conflicted | shared_ledger | attributable | skeptical | 0/0 | 0 | 2/7 | 12 | -6/-6/0 | -12 |
| misleading | conflicted | private | aggregate | unconditional | 0/2 | -24 | 10/21 | 24 | -70/3/-70/3/-34/3 | -58 |
| misleading | conflicted | private | aggregate | conditional | 0/1 | -12 | 3/7 | 20 | -47/3/-47/3/-17/3 | -37 |
| misleading | conflicted | private | aggregate | skeptical | 0/1 | -12 | 3/7 | 20 | -47/3/-47/3/-17/3 | -37 |
| misleading | conflicted | private | attributable | unconditional | 0/2 | -24 | 10/21 | 24 | -26/-24/-8 | -58 |
| misleading | conflicted | private | attributable | conditional | 0/1 | -12 | 3/7 | 20 | -17/-16/-4 | -37 |
| misleading | conflicted | private | attributable | skeptical | 0/1 | -12 | 3/7 | 20 | -17/-16/-4 | -37 |
| misleading | conflicted | shared_ledger | aggregate | unconditional | 0/2 | -24 | 10/21 | 24 | -70/3/-70/3/-34/3 | -58 |
| misleading | conflicted | shared_ledger | aggregate | conditional | 0/1 | -12 | 3/7 | 20 | -47/3/-47/3/-17/3 | -37 |
| misleading | conflicted | shared_ledger | aggregate | skeptical | 0/0 | 0 | 2/7 | 12 | -6/-6/0 | -12 |
| misleading | conflicted | shared_ledger | attributable | unconditional | 0/2 | -24 | 10/21 | 24 | -26/-24/-8 | -58 |
| misleading | conflicted | shared_ledger | attributable | conditional | 0/1 | -12 | 3/7 | 20 | -17/-16/-4 | -37 |
| misleading | conflicted | shared_ledger | attributable | skeptical | 0/0 | 0 | 2/7 | 12 | -6/-6/0 | -12 |

## Defender probe: `UUC`

`a1` and `a2` are unconditional; `a3` holds `*c` and runs the rule.

| Truth | Structure | Topology | Accountability | Rule | Correct/wrong | Quality | Contribution | Effort | Utility a1/a2/a3 | Total utility |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| accurate | corroborated | private | aggregate | conditional | 2/0 | 24 | 19/21 | 47 | -10/3/-10/3/-7/3 | -9 |
| accurate | corroborated | private | aggregate | skeptical | 2/0 | 24 | 19/21 | 47 | -10/3/-10/3/-7/3 | -9 |
| accurate | corroborated | private | attributable | conditional | 2/0 | 24 | 13/14 | 48 | -2/-4/-4 | -10 |
| accurate | corroborated | private | attributable | skeptical | 2/0 | 24 | 13/14 | 48 | -2/-4/-4 | -10 |
| accurate | corroborated | shared_ledger | aggregate | conditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | corroborated | shared_ledger | aggregate | skeptical | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | corroborated | shared_ledger | attributable | conditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | corroborated | shared_ledger | attributable | skeptical | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | conflicted | private | aggregate | conditional | 2/0 | 24 | 16/21 | 41 | -4/3/-4/3/-1/3 | -3 |
| accurate | conflicted | private | aggregate | skeptical | 1/0 | 12 | 5/6 | 39 | -25/3/-25/3/-16/3 | -22 |
| accurate | conflicted | private | attributable | conditional | 2/0 | 24 | 16/21 | 41 | 0/-2/-1 | -3 |
| accurate | conflicted | private | attributable | skeptical | 0/0 | 0 | 6/7 | 40 | -14/-14/-12 | -40 |
| accurate | conflicted | shared_ledger | aggregate | conditional | 2/0 | 24 | 11/14 | 42 | -4/3/-4/3/-4/3 | -4 |
| accurate | conflicted | shared_ledger | aggregate | skeptical | 0/0 | 0 | 5/7 | 34 | -12/-12/-10 | -34 |
| accurate | conflicted | shared_ledger | attributable | conditional | 2/0 | 24 | 11/14 | 42 | 0/-2/-2 | -4 |
| accurate | conflicted | shared_ledger | attributable | skeptical | 0/0 | 0 | 5/7 | 34 | -12/-12/-10 | -34 |
| misleading | corroborated | private | aggregate | conditional | 0/2 | -24 | 19/21 | 47 | -86/3/-86/3/-83/3 | -85 |
| misleading | corroborated | private | aggregate | skeptical | 0/2 | -24 | 19/21 | 47 | -86/3/-86/3/-83/3 | -85 |
| misleading | corroborated | private | attributable | conditional | 0/2 | -24 | 13/14 | 48 | -30/-28/-28 | -86 |
| misleading | corroborated | private | attributable | skeptical | 0/2 | -24 | 13/14 | 48 | -30/-28/-28 | -86 |
| misleading | corroborated | shared_ledger | aggregate | conditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | corroborated | shared_ledger | aggregate | skeptical | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | corroborated | shared_ledger | attributable | conditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | corroborated | shared_ledger | attributable | skeptical | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | conflicted | private | aggregate | conditional | 0/2 | -24 | 16/21 | 41 | -80/3/-80/3/-77/3 | -79 |
| misleading | conflicted | private | aggregate | skeptical | 0/1 | -12 | 5/6 | 39 | -59/3/-59/3/-50/3 | -56 |
| misleading | conflicted | private | attributable | conditional | 0/2 | -24 | 16/21 | 41 | -28/-26/-25 | -79 |
| misleading | conflicted | private | attributable | skeptical | 0/0 | 0 | 6/7 | 40 | -14/-14/-12 | -40 |
| misleading | conflicted | shared_ledger | aggregate | conditional | 0/2 | -24 | 11/14 | 42 | -80/3/-80/3/-80/3 | -80 |
| misleading | conflicted | shared_ledger | aggregate | skeptical | 0/0 | 0 | 5/7 | 34 | -12/-12/-10 | -34 |
| misleading | conflicted | shared_ledger | attributable | conditional | 0/2 | -24 | 11/14 | 42 | -28/-26/-26 | -80 |
| misleading | conflicted | shared_ledger | attributable | skeptical | 0/0 | 0 | 5/7 | 34 | -12/-12/-10 | -34 |

## Attribution: attributable minus aggregate

| Structure | Rule | Pairs | Quality up | Quality down | Quality unchanged | Actions differ |
|---|---|---:|---:|---:|---:|---:|
| corroborated | unconditional | 32 | 0 | 0 | 32 | 0 |
| corroborated | conditional | 36 | 1 | 1 | 34 | 4 |
| corroborated | skeptical | 36 | 1 | 1 | 34 | 4 |
| conflicted | unconditional | 32 | 0 | 0 | 32 | 0 |
| conflicted | conditional | 36 | 0 | 0 | 36 | 0 |
| conflicted | skeptical | 36 | 1 | 1 | 34 | 2 |
| echo | unconditional | 4 | 0 | 0 | 4 | 0 |
| echo | conditional | 4 | 1 | 1 | 2 | 2 |
| echo | skeptical | 4 | 0 | 0 | 4 | 0 |

## Incentives over the tested strategy pair

0 of 48 core groups satisfy both C1 (some strictly profitable active-to-free-rider deviation) and C2 (`CCC` total utility strictly exceeds `FFF`). This applies only to the two designated strategies and these placeholder settings.

| Truth | Structure | Topology | Accountability | Rule | C1 | C2 | CCC−FFF |
|---|---|---|---|---|---|---|---:|
| accurate | corroborated | private | aggregate | unconditional | True | False | -10 |
| accurate | corroborated | private | aggregate | conditional | True | False | -27 |
| accurate | corroborated | private | aggregate | skeptical | True | False | -27 |
| accurate | corroborated | private | attributable | unconditional | True | False | -10 |
| accurate | corroborated | private | attributable | conditional | True | False | -10 |
| accurate | corroborated | private | attributable | skeptical | True | False | -10 |
| accurate | corroborated | shared_ledger | aggregate | unconditional | True | False | -4 |
| accurate | corroborated | shared_ledger | aggregate | conditional | True | False | -4 |
| accurate | corroborated | shared_ledger | aggregate | skeptical | True | False | -4 |
| accurate | corroborated | shared_ledger | attributable | unconditional | True | False | -4 |
| accurate | corroborated | shared_ledger | attributable | conditional | True | False | -4 |
| accurate | corroborated | shared_ledger | attributable | skeptical | True | False | -4 |
| accurate | conflicted | private | aggregate | unconditional | True | False | -3 |
| accurate | conflicted | private | aggregate | conditional | True | False | -3 |
| accurate | conflicted | private | aggregate | skeptical | True | False | -24 |
| accurate | conflicted | private | attributable | unconditional | True | False | -3 |
| accurate | conflicted | private | attributable | conditional | True | False | -3 |
| accurate | conflicted | private | attributable | skeptical | True | False | -24 |
| accurate | conflicted | shared_ledger | aggregate | unconditional | True | False | -4 |
| accurate | conflicted | shared_ledger | aggregate | conditional | True | False | -4 |
| accurate | conflicted | shared_ledger | aggregate | skeptical | True | False | -18 |
| accurate | conflicted | shared_ledger | attributable | unconditional | True | False | -4 |
| accurate | conflicted | shared_ledger | attributable | conditional | True | False | -4 |
| accurate | conflicted | shared_ledger | attributable | skeptical | True | False | -18 |
| misleading | corroborated | private | aggregate | unconditional | True | False | -86 |
| misleading | corroborated | private | aggregate | conditional | True | False | -27 |
| misleading | corroborated | private | aggregate | skeptical | True | False | -27 |
| misleading | corroborated | private | attributable | unconditional | True | False | -86 |
| misleading | corroborated | private | attributable | conditional | True | False | -86 |
| misleading | corroborated | private | attributable | skeptical | True | False | -86 |
| misleading | corroborated | shared_ledger | aggregate | unconditional | True | False | -80 |
| misleading | corroborated | shared_ledger | aggregate | conditional | True | False | -80 |
| misleading | corroborated | shared_ledger | aggregate | skeptical | True | False | -80 |
| misleading | corroborated | shared_ledger | attributable | unconditional | True | False | -80 |
| misleading | corroborated | shared_ledger | attributable | conditional | True | False | -80 |
| misleading | corroborated | shared_ledger | attributable | skeptical | True | False | -80 |
| misleading | conflicted | private | aggregate | unconditional | True | False | -79 |
| misleading | conflicted | private | aggregate | conditional | True | False | -79 |
| misleading | conflicted | private | aggregate | skeptical | True | False | -24 |
| misleading | conflicted | private | attributable | unconditional | True | False | -79 |
| misleading | conflicted | private | attributable | conditional | True | False | -79 |
| misleading | conflicted | private | attributable | skeptical | True | False | -24 |
| misleading | conflicted | shared_ledger | aggregate | unconditional | True | False | -80 |
| misleading | conflicted | shared_ledger | aggregate | conditional | True | False | -80 |
| misleading | conflicted | shared_ledger | aggregate | skeptical | True | False | -18 |
| misleading | conflicted | shared_ledger | attributable | unconditional | True | False | -80 |
| misleading | conflicted | shared_ledger | attributable | conditional | True | False | -80 |
| misleading | conflicted | shared_ledger | attributable | skeptical | True | False | -18 |

## C3 same-action integrity

All 220 replays of an aggregate action schedule under attributable preserve the schedule, briefing, effort, quality and total utility.
Individual credit can redistribute.

## Reading (follow-up F1, written after execution)

Nothing was changed after the first execution at commit `139eb9a` except this text:
no rule, parameter, evidence or cell, and RESULTS.json is byte-identical. All predictions
held, which is expected of hand-traced deterministic rules and is not evidence of a
benefit. Figures are descriptive values of one synthetic grid at placeholder weights.

**The rule does not separate accurate from misleading evidence.** Matched corpora differ
only in hidden fields, so no observation-only rule can. Unanimous false corroboration
passes: `CCC` corroborated schedules equal the conditional control's everywhere, and
PR #81's +24/-24 attribution pattern reappears under the skeptical rule.

**It trades, in both directions.** Against the conditional control at `CCC` conflicted,
private, attributable, misleading quality goes -24 to 0 and total utility -79 to -24,
while accurate quality goes +24 to 0 and total utility -3 to -24. Across 36 conflicted
pairs per truth the screen raises quality in 18 misleading cells and lowers it in 18
accurate cells. The skeptical rule sums +24 aligned and -24 inverted, except 0 and 0 at
private aggregate, so its value depends on whether structure tracks truth, which this
laboratory cannot observe. No prevalence and no net value is claimed.

**Harmful and null findings.**

- Lost true slots: one named skeptic in `UUC` blocks every accurate conflicted claim at
  private attributable, quality +24 to 0.
- Paid reading with no return: skeptical `CCC` conflicted spends 24 effort at private
  for zero quality, so total utility is -24 under either truth.
- Hidden contradiction: when the contradiction holder free-rides (`CCF`), the screen never
  fires under private and quality is -12, equal to the control. A shared ledger gives 0.
- Attribution can reverse: in `UUC` conflicted private, anonymity delays the skeptic and
  one claim survives, so attribution moves quality +12 to 0 and -12 to 0, the opposite
  pattern to PR #81.
- Control quirk: at private aggregate the conditional control is more active on conflicted
  than corroborated evidence, because unshared contradictions let claims and verifications
  appear before warmup ends. Its aligned sum is -24 and inverted +24.
- Solo agents go silent: a lone skeptic cannot reach two sources, which changes actions
  in six corroborated pairs per truth but not quality.
- No group satisfies C1 and C2 at these placeholders.

The rule responds to evidential structure, never to quality or utility. A next step would
be a corpus model with declared noise rates or the audit channel sketched in ADR-0013,
each versioned separately. Neither is implied here, and nothing selects final weights.

## Reproduce

```bash
python experiments/quality-safeguards/quality_safeguards.py --out artifacts/quality-new
python experiments/quality-safeguards/quality_safeguards.py --check
```

`--out` needs a clean worktree and a fresh directory, and retains inputs, sealed
ledgers, manifests and the readout there. `--check` regenerates everything in a
temporary directory and byte-compares the readout. Neither calls a provider.

Study hash: `d581831a899608d28ebb8dd66bd0feccbfcf661f0f86f0b488a62f9695111715`. The study remains unfrozen.
