# Quality safeguards for responsive Evidence Commons: local pre-execution design

Status: exploratory, unfrozen, deterministic finite enumeration. This design is
committed before the rule is implemented or anything is executed. It is not an
externally timestamped preregistration, a live-model pilot, a confirmatory study,
or a change to Study 001. Nothing here selects final weights. The policy contract
is [ADR-0013](../../docs/adr/0013-skeptical-ec-contributor.md).

## Question

PR #81's conditional contributor sustained activity on misleading evidence as well
as accurate evidence, because it responds to visible participation. Can a rule
that also reads explicitly observable evidence, provenance and contradiction
signals change that, and which false support can it not identify in principle?

## What the observation can and cannot distinguish

An agent's observation contains inspected items' `source_id`, `version`, `slot_id`,
`proposition_id`, `stance`, `freshness`; visible items' `source_id`, `slot_id`,
`public`; and claims' citations, `net_support`, counts, and (attributable) names.

The experiment's identifying argument is this: **the matched accurate and
misleading corpora of every design point differ only in `true_propositions` and
the environment-only `truth_aligned` flag.** Neutral proposition IDs keep
observations identical byte for byte. Any observation-only rule, however clever,
must therefore act identically in both worlds, and quality must exactly change
sign. Accurate/misleading is thus a negative control for every rule here, not a
treatment a rule could respond to. A rule can only respond to *structure*
(corroborated, conflicted, single-source). Whether structure tracks truth is a
property of a corpus. The experiment takes no position on it: it reports both the
aligned and the inverted pairing, and no prevalence of either.

In particular `source_id` is a label: distinct labels do not prove independence,
and all sources may share an error. Verification is a provenance check, not a
truth check. A contradiction shows disagreement, not which side is right. Nothing
in an EC episode feeds truth back (`my_credit` stays zero until the unobserved
seal), so this rule needs no new channel but also cannot learn truth; ADR-0013
records what a separately versioned audit channel would have to be.

## Rule under test

`ec_skeptical_contributor[min_sources=2,peer_threshold=1,warmup=9,share=True]@1`
(ADR-0013). In short, evaluated each round from the current observation:

1. The conditional rule's warmup and peer quorum, unchanged. Unmet: withhold.
2. Inspect pending evidence while budget remains.
3. Private topology: share any unshared inspected **fresh** item, of either stance.
4. Challenge each peer claim on a proposition for which I hold an inspected fresh
   contradicting item.
5. Propose a proposition only if it passes the screen.
6. Verify a peer claim only if its proposition passes the screen and it cites one
   of my inspected fresh supporting items.
7. Withhold.

The **screen** for proposition `p` in slot `s`, over my inspected fresh items:
at least `min_sources` distinct `source_id`s support `p`, nothing contradicts `p`,
and nothing supports a rival proposition in `s`. The rule reads no truth, reward
weight, credit, effort or scorer. It is not utility-responsive and not
truth-responsive.

## Fixed inputs

- Three agents, two slots (`s1`, `s2`, candidates `sN-p`, `sN-q`), three evidence
  items per slot, 14 simultaneous rounds.
- Items `e1a e1b e1c e2a e2b e2c`. Private holders: `a1` holds `*a`, `a2` `*b`,
  `a3` `*c`, so every agent holds one item per slot.
- Inspect budget 6, verify budget 3: the budgets differ from PR #81 only so all
  six items can be read and the 14-round horizon can finish. All costs, slot values
  and credits are PR #81's placeholders: inspect/share/propose/challenge 1, verify
  2; correct/wrong slot +12/-12; proposer +3/-3; verifier +2/-2. They are not a
  recommendation or final weights.
- The evidence access, budgets, horizon and composition are identical across each
  planned contrast, and every policy is deterministic. Seed 20261029 with
  `paired-policy-v2` blocks of structure, rule and profile. One execution per design
  point supplies exact outcomes, not independent samples.

Evidence structure, always about `sN-p`, fresh, with the same IDs and holders:

| Structure | `*a` | `*b` | `*c` | Sources |
|---|---|---|---|---|
| corroborated | supports p | supports p | supports p | `src-a src-b src-c` |
| conflicted | supports p | supports p | **contradicts** p | `src-a src-b src-c` |
| echo | supports p | supports p | supports p | **all `src-a`** |

Truth: `accurate` means `sN-p` is true in every slot; `misleading` means `sN-q` is.

## Full design, with no outcome-dependent selection

Rules supply the active strategy `C` of a cell:

| Rule | Policy | Quorum | Warmup |
|---|---|---:|---:|
| unconditional | `ec_contributor[share=True]@1` | none | none |
| conditional | `ec_conditional_contributor` | 1 | 9 |
| skeptical | `ec_skeptical_contributor`, `min_sources=2` | 1 | 9 |

**Core:** {unconditional, conditional, skeptical} x {corroborated, conflicted} x
{accurate, misleading} x {private, shared_ledger} x {aggregate, attributable} x
all eight `{C,F}^3` profiles = 384 episodes.

**Provenance probe:** echo, both truths, both topologies, both accountabilities,
profile `CCC`, all three rules = 24 episodes.

**Defender probe:** profile `UUC`, meaning `a1` and `a2` are `ec_contributor@1` and
`a3`, the holder of `*c`, is the conditional or skeptical rule. Corroborated and
conflicted, both truths, both topologies, both accountabilities = 32 episodes. The
all-unconditional comparison is the core `CCC` unconditional cell. Without this
probe the challenge clause would never fire, because an all-skeptical population
proposes nothing it would itself challenge.

This totals **440 behavioral episodes** plus **220 same-action replays**, one for
each aggregate cell, replayed under attributable. Retain all. Do not add
replicates, alter parameters or change evidence after observing outcomes. The
warmup of 9 was chosen from the hand traces below, as the first round at which
private `CCC` corroborated claims are visible: it is the analogue of PR #81's
all-5 in this timeline, chosen before any run.

## Hand-calculated traces

Each cell lists action per round. `I x` inspect, `S x` share, `P s c` propose, `V c`
verify, `X c` challenge, `-` withhold. Claim IDs follow sorted agent order within a
round. Utilities are `credit + quality/3 - effort`.

### T1: skeptical, corroborated, private, attributable, CCC

| Round | a1 | a2 | a3 |
|---|---|---|---|
| 0 | I e1a | I e1b | I e1c |
| 1 | I e2a | I e2b | I e2c |
| 2 | S e1a | S e1b | S e1c |
| 3 | I e1b | I e1a | I e1a |
| 4 | I e1c | I e1c | I e1b |
| 5 | S e2a | S e2b | S e2c |
| 6 | I e2b | I e2a | I e2a |
| 7 | I e2c | I e2c | I e2b |
| 8 | P s1 c1 | P s1 c2 | P s1 c3 |
| 9 | P s2 c4 | P s2 c5 | P s2 c6 |
| 10 | V c2 | V c1 | V c1 |
| 11 | V c3 | V c3 | V c2 |
| 12 | V c5 | V c4 | V c4 |
| 13 | - | - | - |

Net support: c1 2, c2 2, c3 2, c4 2, c5 1, c6 0. Accepted: c1, c4, both by a1. The
verify budget caps duplicated claims, as in PR #81, so here both slots are accepted.
Contribution 13/14. Effort 16 each.

- accurate: quality 24, credit 6/4/4, utility -2/-4/-4, total -10.
- misleading: quality -24, credit -6/-4/-4, utility -30/-28/-28, total -86.

The unconditional rule's actions equal this schedule here.

### T2: skeptical, conflicted, private, either accountability, CCC

Rounds 0 to 7 are T1's, with `e1c`, `e2c` now contradicting: fresh contradictions
are shared too. Every proposition fails the screen, so rounds 8 to 13 are all
withhold. Quality 0 under both truths, contribution 4/7, effort 8 each, utility
-8/-8/-8, total -24 under both truths.

### T3: conditional, corroborated, private, CCC

Rounds 0 to 8 are T1's. At round 9 the three visible claims are `s1` claims with no
verifications. Attributable: two named peers, the quorum is met, and the remainder
matches T1 (total -10 accurate, -86 misleading). Aggregate: the bound is 1 and
unchanging, so all withhold through round 13: quality 0, contribution 9/14, effort
9 each, total -27. This is PR #81's attribution effect: +24 accurate, -24 misleading.

### T4: skeptical, conflicted, private, CCF (hidden contradiction)

`a3` free-rides and holds the only contradicting items, so `a1` and `a2` see no
conflict.

| Round | a1 | a2 |
|---|---|---|
| 0 | I e1a | I e1b |
| 1 | I e2a | I e2b |
| 2 | S e1a | S e1b |
| 3 | I e1b | I e1a |
| 4 | S e2a | S e2b |
| 5 | I e2b | I e2a |
| 6 | P s1 c1 | P s1 c2 |
| 7 | P s2 c3 | P s2 c4 |
| 8 | V c2 | V c1 |
| 9-13 | - | - |

At round 9 only one peer is visible, so the quorum stops both. Net: c1 1, c2 1, c3
0, c4 0. Accepted: c1. Effort 10/10/0. Under attributable:

- accurate: quality 12, credit 3/2/0, utility -3/-4/4, total -3.
- misleading: quality -12, credit -3/-2/0, utility -17/-16/-4, total -37.

Under `shared_ledger` the same profile reads `*c` and vetoes: quality 0.

### T5: defender, skeptical `a3`, conflicted, private, UUC

| Round | a1 (U) | a2 (U) | a3 attributable | a3 aggregate |
|---|---|---|---|---|
| 0 | I e1a | I e1b | I e1c | same |
| 1 | I e2a | I e2b | I e2c | same |
| 2 | S e1a | S e1b | S e1c | same |
| 3 | I e1b | I e1a | I e1a | same |
| 4 | I e1c | I e1c | I e1b | same |
| 5 | S e2a | S e2b | S e2c | same |
| 6 | I e2b | I e2a | I e2a | same |
| 7 | I e2c | I e2c | I e2b | same |
| 8 | P s1 c1 | P s1 c2 | - | - |
| 9 | P s2 c3 | P s2 c4 | X c1 | - |
| 10 | V c2 | V c1 | X c2 | - |
| 11 | V c4 | V c3 | X c3 | X c1 |
| 12 | - | - | X c4 | X c2 |
| 13 | - | - | - | X c3 |

Attributable: every claim nets 0, nothing is accepted, quality 0 under both truths,
effort 14/14/12, total -40. Aggregate: the anonymous bound reaches 2 only at round
11, the horizon ends with c4 unchallenged at net 1, and c4 is accepted: quality +12
accurate, -12 misleading. Attribution here *helps* in the misleading world and
*hurts* in the accurate world, the reverse of T3.

## Declared contrasts

1. **Truth negative control** (all 220 pairs): accurate versus misleading, all else
   equal.
2. **Screen effect** (152 pairs): skeptical minus conditional, same quorum.
3. **Structure** (192 pairs): conflicted minus corroborated, core cells.
4. **Attribution** (220 pairs): attributable minus aggregate, PR #81's direction.
5. **Observable alignment** (96 pairs of core cells): quality summed over the
   *aligned* pairing (accurate corroborated plus misleading conflicted) and the
   *inverted* pairing (accurate conflicted plus misleading corroborated). This is
   an unweighted sum, not an expectation; no prevalence is claimed.

Each reports quality, contribution, effort and utility deltas separately.

## Predictions

Evaluated mechanically in the readout. A wrong prediction is retained, not edited.

- **P1** Every truth pair has identical action schedules and exactly opposite
  quality (the identification argument). Failure would mean an observation leak.
- **P2** `CCC` corroborated: skeptical and conditional have identical schedules in
  every cell, so the screen removes no false support here. In particular the
  skeptical rule's quality is -24 in misleading/private/attributable and
  misleading/shared_ledger, the same as the conditional control. This is the
  negative control where observations cannot identify false support.
- **P3** `CCC` conflicted: skeptical quality is 0 in all eight cells, while the
  conditional control has +24 accurate and -24 misleading. The screen thus gains
  +24 in the misleading world and loses 24 in the accurate world, a trade rather
  than a discrimination.
- **P4** Echo `CCC`: skeptical quality is 0, unconditional is +24/-24, with
  distinct-source labels the only input difference from corroborated.
- **P5** Hidden contradiction, `CCF` conflicted misleading: skeptical quality is
  -12 under private and 0 under shared_ledger.
- **P6** Defender, `UUC` conflicted, private: skeptical quality is 0 attributable
  and +12/-12 aggregate; under shared_ledger it is 0 in both accountabilities,
  because the warmup still allows challenges before the quorum applies. The
  conditional control under attributable has +24/-24.
- **P7** `CCC` attribution contrast: nonzero quality delta only for corroborated
  private conditional and skeptical cells, +24 accurate, -24 misleading. Conflicted
  private conditional is 0 because its earlier claims and round-8 verifications meet
  the anonymous bound at round 9. All unconditional contrasts have equal actions.
- **P8** Observable alignment, `CCC`, private, attributable: skeptical sums to +24
  aligned and -24 inverted; conditional and unconditional sum to 0 and 0.
- **P9** C2 is false in every core group, because effort exceeds the quality and
  credit value at these placeholders, and C1 is true in every core group. No cell is
  a finite-strategy dilemma.
- **P10** Every same-action replay preserves schedule, briefing, effort, quality and
  total utility.

No sign or magnitude is a success criterion. Any overall benefit from the screen
would need a corpus claim this design does not make.

## Three separate outputs

1. **Measured behavior:** typed actions, contribution fraction (all non-withhold
   agent-rounds), correct/wrong slots, signed quality, effort, per-agent and total
   utility, exact rational descriptive values.
2. **Finite-strategy incentives:** for every core truth/structure/topology/
   accountability/rule group, all twelve active-to-free-rider deviations. C1 means at
   least one strictly profitable deviation; C2 means `CCC` total utility strictly
   exceeds `FFF`. This applies only to the tested pair. Same definition as PR #81.
3. **C3 same-action integrity:** the 220 replays, required to hold.

Seal every episode with a manifest and hash-linked ledger outside Git under
`artifacts/`; the readout retains terminal hashes. `--check` regenerates everything
in a temporary directory and byte-compares the checked-in readout.

## Limits

Evidence here is deliberately extreme and all-or-nothing. Every source agrees within
a corroborated corpus and each slot has the same structure, so the grid is not a
prevalence model. Stale evidence, rival-proposition support and public challenges are
outside this grid: the first two have unit tests only, and the third is unused.
Inspect budgets suffice to read everything, so budget-limited screening is untested.
The design cannot identify optimal institutions, general equilibria, a social dilemma
beyond two strategies, or anything about people or LLMs. If anything changes after
execution it is recorded as a separately labelled follow-up and this file stays as
committed.
