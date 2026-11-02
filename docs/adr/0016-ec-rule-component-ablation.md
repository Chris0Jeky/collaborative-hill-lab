# ADR-0016 — Independently switchable Evidence Commons rule components

Status: accepted for the authorized exploratory issue #95 follow-up (2026-11-02).
Additive policy contract; ADR-0012 and ADR-0013 remain unchanged.

## Context

The quality-safeguards experiment compares whole conditional and skeptical rules.
Its contrast does not identify the effects of the evidence screen, sharing
contradicting evidence, challenges, and the requirement to have read a supporting
citation. A separately named factorial policy exposes these four switches.

## Decision

Add `ec_ablation_contributor` in a separate module and register it additively.
Its behavior identifier is:

```text
ec_ablation_contributor[screen=<bool>,share_contradictions=<bool>,challenge=<bool>,read_citation=<bool>,min_sources=<int>,peer_threshold=<fraction>,warmup=<int>,share=<bool>]@1
```

Parameters `evidence_screen`, `share_contradictions`, `challenge_claims`, and
`require_read_citation` default to true. They accept exactly the existing boolean
contract (booleans or case-insensitive strings `true`/`false`; no 0/1, null or
truthiness coercion). `min_sources`, `peer_threshold`, `warmup_rounds` and
`share_evidence` have ADR-0013's exact validation and defaults. Unknown keys fail.
Stored scenario parameter values are never normalized or given implicit keys.

The observation-only rule has the unchanged quorum, inspection priority and
proposal/claim ordering. Among inspected fresh evidence, sharing always permits
support and permits contradictions only if `share_contradictions` is true.
`share_evidence=false` still disables sharing entirely. When `challenge_claims`
is true, challenge the first peer claim not already challenged whose proposition
has fresh inspected contradictions, citing all such items. Then consider
proposals, followed by verification, then withhold. Enabling `evidence_screen`
requires ADR-0013's entire screen for both proposals and verification. Enabling
`require_read_citation` independently requires a verified claim to cite at least
one inspected fresh support for that slot and proposition. It does not require
every citation to be read.

All four switches false reproduce conditional v1's typed actions; all true
reproduce skeptical v1's typed actions, given matching remaining parameters and
observations. Policy identifiers differ deliberately. No old implementation or
identifier changes, and no old evidence artifact is rewritten. The new rule may
reuse the unchanged v1 screen and quorum helpers; it does not refactor them.

The factors interact with the existing action priority and finite budgets. In
particular challenges can delay verification, a challenger may subsequently
verify the same claim, and its own claims cannot be challenged by itself. These
are retained existing semantics, not new gates.

## Consequences and verification

No new truth signal, mechanism version, observation schema, metric, institution,
provider or memory is introduced. The rule ignores utility weights and hidden
truth. Current observations fully determine its decision; RNG is unused.

The separate `experiments/ec-rule-ablation/DESIGN.md` commits the six-context,
four-factor design and hand-derived traces before execution. All-factor endpoint
comparisons, literal action oracles, adversarial observation/parameter boundaries,
truth-swaps and same-action integrity establish the claimed contract. The earlier
440/220 quality-safeguards readout remains byte-identical and reproducible.

Future changes to this policy's behavior require a new policy version and ADR.
