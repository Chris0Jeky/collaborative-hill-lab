# Evidence Commons rule components: pre-execution ablation design

Status: exploratory, unfrozen, deterministic finite factorial for issue #95.
Written and committed before implementation and experiment execution. This is a
local pre-execution record, not an externally timestamped preregistration. It
does not change Study 001, the conditional or skeptical v1 policies, the 440
behavioral records or 220 fixed-action records in `quality-safeguards`, final
utility weights, provider authorization, or any human-owned decision.

## Question and identifying contrast

The earlier skeptical-minus-conditional contrast bundles four components. This
follow-up independently switches each component while holding each context's
world, evidence, budgets, timing, institution and peer policies fixed:

| Factor | Off (0) | On (1) |
|---|---|---|
| S: evidence screen | Propose from fresh support; no screen on verification | Require two distinct fresh supporting source labels, no fresh contradiction and no fresh support for a rival, for proposal and verification |
| H: share contradictions | Share inspected fresh supporting items | Also share inspected fresh contradicting items |
| C: challenge claims | Skip the challenge step | Challenge peer claims using inspected fresh contradicting evidence, before proposing or verifying |
| R: read cited support | No citation-read condition on verification | Require the claim to cite at least one inspected fresh supporting item |

The treatment label is the bit string `SHCR`. All 16 combinations are retained,
including null effects. `0000` must match conditional v1's **typed actions** and
`1111` skeptical v1's typed actions, on identical observations and parameter
values. Their new policy IDs remain distinct. The action priority is quorum,
inspect, share, challenge, propose, verify, withhold; disabling a component only
removes its corresponding condition or step. Sharing supporting evidence is
always enabled. The formal additive contract is ADR-0016.

These are policy interventions, not new observations or engine rules. A
challenge does not stop its author later verifying the same claim. A policy does
not challenge its own claim. These existing semantics create interactions that
single-component removals from `1111` alone would miss.

## Approaches and scope

Repeating the earlier entire strategy/profile/institution grid would mostly
duplicate uninformative cells. Four leave-one-out contrasts would confound
interactions with their chosen all-on background. The selected design is the
complete 2^4 factorial in six explicitly selected diagnostic contexts, with
both hidden truths. The first five use exactly the earlier corpus, costs,
budgets and horizon. The sixth is a separately labelled citation-access stress
probe, because full inspection otherwise makes R redundant. These design choices
are engineering/research choices under the authorized exploratory follow-up.

## Fixed contexts and inputs

All contexts have agents `a1,a2,a3`, attributable accountability, 14 simultaneous
rounds, verify budget 3, and the existing placeholder costs: inspect/share/
propose/challenge 1, verify 2; correct/wrong slot +12/-12; proposer +3/-3;
verifier +2/-2. The ablation policy has `min_sources=2`, `peer_threshold=1`,
`warmup_rounds=9`, `share_evidence=true`. These values are never tuned after
execution. Seed 20261102, `paired-policy-v2`, one deterministic execution per
cell; blocks are context identifiers, pairing every factor and hidden truth.

In the first five contexts, slots `s1,s2` have neutral candidates `sN-p,sN-q`.
Items `e1a,e1b,e1c,e2a,e2b,e2c` are fresh. Holders are `a1:*a,a2:*b,a3:*c`.
Inspect budget is 6. All evidence concerns `sN-p`:

| Structure | *a | *b | *c | Source labels |
|---|---|---|---|---|
| corroborated | supports | supports | supports | src-a, src-b, src-c |
| conflicted | supports | supports | contradicts | src-a, src-b, src-c |
| echo | supports | supports | supports | all src-a |

`A` denotes the same ablation variant for each A agent; `U` is unchanged
`ec_contributor[share=True]@1`; `F` is unchanged `ec_freerider@1`.

| Context | Structure | Topology | Profile | Purpose |
|---|---|---|---|---|
| corroborated-private | corroborated | private | AAA | All-component null control despite accurate or misleading consensus |
| conflicted-private | conflicted | private | AAA | Disclosure, screening, challenge and quorum interactions |
| echo-private | echo | private | AAA | Screen's distinct-source boundary |
| conflicted-ledger | conflicted | shared_ledger | AAA | Public contradiction; H must be a structural null |
| defender-private | conflicted | private | UUA | Challenge can act on externally proposed claims even when S prevents own claims |
| unread-private | corroborated, special holdings below | private | UFA | Read-citation effect at exhausted inspection budget |

**Citation-access probe only:** one slot `s1`, three fresh supports
`e1a,e1b,e1c` with distinct source labels; `a1` initially holds `e1c`, `a2`
holds nothing, `a3` holds `e1a,e1b`. Inspect budget is 2 for every agent. Other
parameters, horizon and accountability are unchanged. The peer's citation
becomes public before verification but remains unread by `a3`. No custom peer
script, state injection or special policy is needed.

For every context and variant, `accurate` makes `sN-p` true and `misleading`
makes `sN-q` true. Within a pair only `true_propositions` and the environment-only
`truth_aligned` flags differ. Actions and observations must be identical; quality
and total credit must change sign. Truth is a negative control, not a signal.

Count: **6 contexts x 16 variants x 2 truths = 192 behavioral episodes**.
Additionally replay every accurate schedule unchanged under aggregate
accountability: **96 fixed-action controls**. Comparing an attributable
behavioral episode to an aggregate replay tests task integrity, not a behavioral
attribution effect. Opposite-truth copies would duplicate the same integrity
check and are not added. Replay integrity is checked for every retained run.

## Hand-derived outcomes, before execution

The table below predicts accepted slots K, total effort E, positive total credit
G in the accurate world, and contribution fraction A (non-withhold actions / 42).
For both truth worlds quality is `+/-12K`; total credit is `+/-G`; total utility
is `+/- (12K+G) - E`. No prediction is fitted to a run. R is predicted to be
irrelevant in the first five contexts. H is irrelevant in the ledger context.
An asterisk denotes either setting of that factor.

| Context | S | H | C | R | K | E | G | A |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| corroborated-private | * | * | * | * | 2 | 48 | 14 | 13/14 |
| echo-private | 0 | * | * | * | 2 | 48 | 14 | 13/14 |
| echo-private | 1 | * | * | * | 0 | 24 | 0 | 4/7 |
| conflicted-private | 0 | 0 | 0 | * | 2 | 41 | 14 | 16/21 |
| conflicted-private | 0 | 0 | 1 | * | 2 | 40 | 14 | 11/14 |
| conflicted-private | 0 | 1 | 0 | * | 2 | 48 | 14 | 13/14 |
| conflicted-private | 0 | 1 | 1 | * | 0 | 42 | 0 | 1 |
| conflicted-private | 1 | 0 | 0 | * | 1 | 26 | 5 | 4/7 |
| conflicted-private | 1 | 0 | 1 | * | 0 | 30 | 0 | 2/3 |
| conflicted-private | 1 | 1 | 0 | * | 0 | 24 | 0 | 4/7 |
| conflicted-private | 1 | 1 | 1 | * | 0 | 24 | 0 | 4/7 |
| conflicted-ledger | 0 | * | 0 | * | 2 | 42 | 14 | 11/14 |
| conflicted-ledger | 0 | * | 1 | * | 0 | 48 | 0 | 1 |
| conflicted-ledger | 1 | * | * | * | 0 | 18 | 0 | 3/7 |
| defender-private | 0 | 0 | 0 | * | 2 | 41 | 14 | 16/21 |
| defender-private | 0 | 0 | 1 | * | 2 | 40 | 14 | 11/14 |
| defender-private | 0 | 1 | 0 | * | 2 | 48 | 14 | 13/14 |
| defender-private | 0 | 1 | 1 | * | 1 | 47 | 7 | 20/21 |
| defender-private | 1 | 0 | 0 | * | 2 | 30 | 10 | 13/21 |
| defender-private | 1 | 0 | 1 | * | 0 | 34 | 0 | 5/7 |
| defender-private | 1 | 1 | 0 | * | 2 | 36 | 10 | 16/21 |
| defender-private | 1 | 1 | 1 | * | 0 | 40 | 0 | 6/7 |
| unread-private | * | * | * | 0 | 1 | 10 | 5 | 3/14 |
| unread-private | * | * | * | 1 | 0 | 8 | 0 | 4/21 |

### T1: citation-read requirement in the unread-private probe

`I` inspect, `S` share, `P` propose, `V` verify, `X` challenge, `-` withhold.
The following typed actions hold for all settings of S,H,C. `a2` always withholds.

| Round | a1 (U) | a3 with R=0 | a3 with R=1 |
|---|---|---|---|
| 0 | I e1c | I e1a | same |
| 1 | S e1c | I e1b | same |
| 2 | P s1-p citing e1c (c1) | S e1a | same |
| 3 | I e1a | S e1b | same |
| 4 | - | V c1 | - |
| 5-13 | - | - | - |

At round 4, `a3` has read two independent labels supporting p and has no inspect
budget. The screen passes, but the public citation e1c is unread. Without R,
engine verification succeeds on the accessible fresh citation; R prevents it.
R=0: effort `(4,0,6)`, credit `(3,0,2)` accurate, quality 12, utility `(3,4,0)`,
total 7. Misleading: credit `(-3,0,-2)`, quality -12, utility `(-11,-4,-12)`,
total -27. R=1: effort `(4,0,4)`, zero quality and credit, utility `(-4,0,-4)`,
total -8 in both worlds. Thus R changes quality by -12 accurate/+12 misleading,
effort by -2, and total utility by -15/+19. It does not identify truth.

### T2: no disclosure, screen on, optional challenges (conflicted-private)

For H=0, the contradicting holder `a3` does not share its two items. The common
prefix through round 6 is:

| Round | a1 | a2 | a3 |
|---|---|---|---|
| 0 | I e1a | I e1b | I e1c |
| 1 | I e2a | I e2b | I e2c |
| 2 | S e1a | S e1b | - |
| 3 | I e1b | I e1a | I e1a |
| 4 | S e2a | S e2b | I e1b |
| 5 | I e2b | I e2a | I e2a |
| 6 | P s1 (c1) | P s1 (c2) | I e2b |

With S=1,C=0: round 7 is `(P s2 c3,P s2 c4,-)`; round 8 is
`(V c2,V c1,-)`; then everyone withholds. The two proposing agents see only
one contributing peer after warmup, and a3's screen rejects both propositions.
Only c1 survives: K=1, effort `(10,10,6)`, G=5.

With S=1,C=1: a3 challenges c1,c2,c3,c4 at rounds 7,8,9,10. Peers still stop
at round 9, since challenges do not count in their contribution quorum. Every
claim now has net support <=0. Effort `(10,10,10)`, quality 0.

With S=0,C=1: the same four challenges are followed by a3 verifying c1,c2,c3
at rounds 11,12,13. Its first verification reopens the peers' quorum: at round
12 they verify c4,c3, respectively. c1 and c3 now net 1 and are accepted.
Effort `(12,12,16)`, K=2, G=14. Challenges are not a permanent veto.

### T3: sharing and challenges can interact through the finite horizon

With H=1 the original eight-round inspect/share prefix is restored. In AAA,
S=0,C=1, everyone proposes s1 at round 8, challenges its two peer claims at
rounds 9 and 10, proposes s2 at round 11 and challenges its two peer claims at
rounds 12 and 13. Nobody reaches verification: quality 0, effort 14 each.
With C=0 they instead follow the original corroborated schedule and accept both
slots. In UUA at S=0,H=1,C=1 the two unconditional agents verify a3's own s1
claim; a3 cannot challenge itself, so that claim wins at net 2. Its four
challenges remove both s2 candidates. Quality is +/-12, effort `(16,16,15)`.

## Declared measurements and contrasts

Retain every cell, typed action schedule/hash, terminal event hash, briefing,
counts by action, accepted-slot count, quality, contribution, effort, per-agent
credit/utility, total utility and scenario/mechanism identity. No scalar combines
these outcomes. Null actions and negative results remain visible.

1. **P1: truth control.** All 96 pairs have identical action schedules and
   observation transcripts, equal effort/contribution, opposite quality/credit.
2. **P2: endpoint bridge.** All 24 endpoint cells match the corresponding
   unchanged conditional/skeptical rule's actions on the same observations. This
   is an online shadow check, not 24 additional experimental episodes.
3. **P3: complete literal outcome table.** Every one of the 192 cells agrees with
   the hand-derived K,E,G,A table above and the implied quality/total utility.
   A disagreement is reported and retained; predictions are never overwritten.
4. **P4: structural nulls.** All component flips are action-null in corroborated-
   private; H is action-null in conflicted-ledger; R is action-null in the first
   five contexts; S,H,C are action-null in unread-private. S alone separates echo.
5. **P5: factorial interactions.** Report all 384 matched single-factor pairs and
   all 396 matched second-/third-/fourth-order differences: for subset J, compute
   the alternating sum over its 2^|J| cells with the other bits fixed. No averaging
   across contexts or truths. For accurate conflicted-ledger, S-by-C quality
   interaction is +24 for every H,R background. For accurate conflicted-private,
   H-by-C at S=0 is -24; at S=1 it is +12; the S-by-H-by-C interaction is +36.
   Hidden truth inversion reverses these quality signs. The unread-private
   probe has no nonzero higher-order interaction for any reported scalar.
6. **P6: fixed-action integrity.** All 96 aggregate replays preserve actions,
   briefing, quality, effort and total utility. Individual credit can redistribute.

The interaction count per context/truth is `6*4 + 4*2 + 1 = 33`; first differences
are `4*8=32`. Twelve context/truth strata give 396 and 384 respectively. Report
the explicit conditioning bits and cell IDs, making every contrast auditable.
Use exact integer/Fraction arithmetic; these are exhaustive finite-design
contrasts, not samples, confidence intervals or tests of statistical significance.

## Execution, checks and provenance

First commit this design and ADR, then implement the additive policy/runner with
tests from the literal traces. Commit the implementation before recording an
execution. `--out` requires a clean committed source tree and a fresh output
directory; record source commit, design digest, lock digest and every relevant
source digest. Retain generated scenario inputs, sealed ledgers and manifests in
that output. `--check` reconstructs the full design in a temporary directory,
verifies every ledger by recorded-action replay, and byte-compares the readout.
The readout's deterministic fields exclude environment/source-commit metadata;
execution provenance is a separate file. A copied or stale manifest, altered
cell, incomplete schedule or rejected action must fail inspection.

Tests also cover unknown/bad toggle values, exact quorum boundaries, stale and
unread evidence, rival support, duplicate source labels, inspection and verify
budget exhaustion, citation mismatch, own/already-challenged claims, deterministic
ordering, no mutation/RNG use, and compiled/rebuilt policy identities. The old
quality-safeguards `--check` must still regenerate its unchanged committed bytes.

## Interpretation boundaries

This design can attribute a deterministic difference to one explicitly switched
component within its fixed context. Contexts are chosen diagnostics, not a sample
of corpora. Source labels do not establish independence; contradictions do not
establish falsehood. Every observed accuracy benefit has its truth-swapped loss.
Effort costs, quorum timing, sorted claim ties and the finite horizon can mediate
component interactions. The attribution replay establishes only same-action
integrity. No new incentive certificate, human claim, live model result, final
weights or freeze follows from this factorial. Post-execution interpretation is
labelled separately from these predictions.
