# Responsive Evidence Commons: local pre-execution design

Status: exploratory, unfrozen, deterministic finite enumeration. This design is
recorded before executing this experiment. It is not an externally timestamped
preregistration, a live-model pilot, or a change to Study 001.

## Question and policy

Can attribution change an observation-responsive policy's contribution decisions,
and can the resulting task effect have either sign depending on evidence quality?

`ec_conditional_contributor` delegates to the existing contributor during a
declared warmup. Afterwards it contributes only when the observed lower bound
on distinct contributing peers, divided by `N-1`, reaches an inclusive quorum.
Proposals and verifications count as contribution, regardless of their truth or
usefulness. With identities, the bound is the union of visible proposers and
verifiers excluding self. Without identities, use the maximum per-claim count
of nonself proposer plus nonself verifiers. These actors are disjoint within a
claim because the engine disallows self-verification; they cannot safely be
deduplicated across anonymous claims. No hidden truth, utility weights, hidden
inspection history, scorer, or internal policy memory enters the rule.

## Fixed inputs

- Three agents (`a1`, `a2`, `a3`), three slots, twelve simultaneous rounds.
- One fresh supporting evidence item initially held by each corresponding agent.
  The accurate corpus supports the true candidate of every slot; the misleading
  corpus supports the false candidate of every slot. Sources are synthetic.
- Inspect budget 3, verify budget 3. Effort costs: inspect/share/propose/challenge
  1, verify 2. Correct/wrong slot value +12/-12. Accepted proposer credits +3/-3;
  successful verifier credits +2/-2. These are experimental settings, not a
  recommendation or final weights for Study 001.
- One plain narrative skin. Skin and actor-renaming properties are separate
  engineering tests, not extra experimental factors in this enumeration.
- Seed 20261029 with explicit `paired-policy-v2` blocks identified by corpus,
  policy rule and active/free-rider profile. All policies here are deterministic,
  so matching seeds do not supply independent samples or sampling uncertainty.
- Sorted IDs and the existing mechanism's earliest-claim tie rule are retained.
  Duplicate claims and the finite inspection horizon are part of this task.

## Full design, with no outcome-dependent selection

Cross two accountability levels (aggregate/attributable), two evidence topologies
(private/shared ledger), two corpora, and five policy rules:

| Rule | Peer quorum | Warmup rounds |
|---|---:|---:|
| response-free control | 0 | 5 |
| half-5 | 1/2 | 5 |
| all-5 | 1 | 5 |
| half-9 | 1/2 | 9 |
| all-9 | 1 | 9 |

For every cell enumerate all eight labeled three-agent profiles in `{C,F}^3`.
`C` means that cell's designated active policy, including the conditional rule;
`F` is the unchanged `ec_freerider`. The quorum-zero policy is exactly equivalent
to the legacy contributor, with its own explicit identity. There are **320
behavioral episodes**, each run once. Retain all cells; do not add replicates,
alter warmup/quorum, or change evidence after observing their outcomes.

## Predictions and negative controls

The response-free control should produce identical actions under the two
accountability levels within each topology/corpus/profile. Its total utility
should also be identical, although individual credit allocation may differ.
Anonymous history can prove at most one distinct peer before verifications
when only nonself proposal identities are hidden. Attribution can therefore
enable an all-peer quorum that the anonymous observation does not yet establish.
A longer warmup may remove this information bottleneck, and insufficient active
peers may make either accountability level stop contributing. These are
conditional predictions, not guaranteed positive institutional effects.

Fresh support is a provenance property, not a truth guarantee. If attribution
enables acceptance in the accurate corpus, quality can increase; if it enables
acceptance of fresh but false claims, quality can decrease. No particular sign
or magnitude is a success criterion. The misleading corpus is intentionally
extreme to make this limitation legible; it is not an empirical prevalence model.

## Three separate outputs

1. **Measured behavior:** accepted typed actions, contribution fraction, accepted
   correct/wrong slots, collective quality, effort, per-agent and total utility.
   Compute attributable minus aggregate contrasts for all 160 matched cells.
   Report exact rational descriptive values, without confidence intervals or
   claims about people or unmeasured LLM behavior.
2. **Finite-strategy incentives:** for every corpus/topology/accountability/rule,
   enumerate all twelve unilateral active-to-free-rider deviations. C1 means
   at least one strictly profitable deviation; C2 means total utility at CCC
   strictly exceeds FFF. Any certificate applies only to the two designated
   deterministic strategies and these experimental settings.
3. **Same-action task integrity:** replay each of the 160 aggregate action
   sequences under attributable accountability with the same world/topology.
   Require identical typed action schedules, briefing and effort, and identical
   total utility; individual credits may redistribute. These 160 controlled
   replay episodes are distinct from adaptive behavioral contrasts. Their
   observations and complete event hashes are expected to differ.

Seal every episode with a manifest and hash-linked ledger. The reproducible
readout records scenario/study identities, terminal commitments, exact summaries,
deviations and contrasts. Regeneration checks use fresh temporary directories;
the command never overwrites an existing experiment output directory. Retain
the original report and raw output of this local execution during the session.

## Limits

This baseline responds to contribution visibility, not to monetary incentives;
changing utility coefficients alone will not change its actions. Attribution
bundles identity visibility with credit assignment in the existing mechanism,
but this policy reads only identity/history, so its behavioral path is explicit.
The design does not identify optimal institutions, general equilibria, a general
social dilemma, sparse-network effects, or a confirmatory Study 001 result.
