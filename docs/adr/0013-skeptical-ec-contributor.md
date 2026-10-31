# ADR-0013 — Observation-grounded skeptical Evidence Commons contributor

Status: **accepted** (2026-10-30). Adds a versioned scripted baseline for issue #84;
preserves the legacy EC personas, ADR-0012's conditional contributor, engine
semantics and Study 001 inputs.

## Context

ADR-0012's quorum responds to visible participation. PR #81's grid showed it can
sustain activity on misleading evidence as readily as on accurate evidence: the
contributor cites any fresh support and verifies any peer claim.

The observation already carries more than that rule reads. Inspected items expose
`source_id`, `version`, `proposition_id`, `stance` and `freshness`. Claims expose
citations and support counts. This ADR uses that existing interface. It adds no
observation field, no institution, no engine rule and no mechanism version.

## Decision

Add registry name `ec_skeptical_contributor`, with behavior identifier:

```text
ec_skeptical_contributor[min_sources=<int>,peer_threshold=<fraction>,warmup=<int>,share=<bool>]@1
```

Parameters: `min_sources` (default `2`, integer >= 1), and `peer_threshold` (default
`"1/2"`), `warmup_rounds` (default `3`) and `share_evidence` (default `true`) with
ADR-0012's exact contract. Any behavior change is a new version, not an edit.

### The screen

Let `F(s)` be my **inspected, fresh** items in slot `s`. `screen(s, p)` holds iff:

- at least `min_sources` distinct `source_id`s in `F(s)` support `p`;
- no item in `F(s)` contradicts `p`;
- no item in `F(s)` supports a rival proposition of `s`.

### Decision order

At each observation, with no stored state:

1. Quorum: exactly ADR-0012's gate. If `t >= warmup` and the conservative peer count
   is below `peer_threshold * (N - 1)`, withhold.
2. Inspect the first pending visible item while inspect budget remains.
3. If `share_evidence` under private topology, share my first unshared inspected
   fresh item. Unlike the contributor this includes contradicting items, because
   withheld counter-evidence could not reach a peer's screen.
4. Challenge the first peer claim I have not challenged whose proposition has
   contradicting items in `F`, citing all of them.
5. Propose as the contributor does, restricted to slots I have no claim in,
   unclaimed propositions and `screen(s, p)`, citing my fresh supporting items.
6. If verify budget remains, verify the first peer claim I have not verified whose
   proposition passes `screen` and that cites one of my fresh supporting items.
7. Withhold.

Step 6's citation condition means the rule does not spend verification on a claim
whose provenance it has not read. Step 5 keeps the contributor's sorted greedy order
so that the safeguards, not a changed work order, are what differ from the controls.

### What these signals can and cannot distinguish

| Signal | Can distinguish | Cannot distinguish |
|---|---|---|
| `stance` | Whether items disagree about a proposition | Which side is true |
| distinct `source_id` | Repeated label from separate labels | Real independence, or a shared error |
| `freshness` | What the engine's provenance adjudication accepts | Whether a fresh item is accurate; stale items are ignored, even as a warning |
| rival support | That two propositions are both backed | Which is true |
| engine verification | Whether a citation is accessible, fresh and supporting | Truth; well-cited misinformation passes |

Consequences, stated rather than discovered later:

- **The rule cannot identify unanimously false, multi-source evidence.** Any two
  worlds with identical observations produce identical actions. This holds for every
  observation-only rule.
- **A veto cannot tell a false claim from a true claim falsely contradicted.** It
  trades accepted false slots for lost true ones.
- **Evidence it cannot read is not a signal.** A contradiction held by a
  non-sharing peer never reaches the screen. An unread visible item is not screened
  either, so budget exhaustion can pass a claim that reading would veto.
- **Single-source evidence fails `min_sources=2`** whether accurate or misleading.
- **Challenges are not read.** Cheap invalid challenges could otherwise veto a claim,
  and validity is not separately observed. Failed-verification inference from
  `net_support`, rival claims and evidence `version` are likewise unused.

### Not utility-responsive, not truth-responsive

The rule reads no reward weight, credit, effort, scorer or hidden field. It must not
be described as responding to quality or utility, only to evidential structure.
"Quality-sensitive" in the issue title is a hypothesis about corpora, never a property
of the rule.

### No new channel; what one would need

Within an EC episode no observation depends on truth: `my_credit` remains zero until
seal and the seal is not observed. This rule needs no new channel, and no version of
it can learn truth. A later design that wanted feedback would first need a separately
versioned contract: a new `EC_ENGINE_VERSION` and observation schema version, an
institution field such as an audit with declared timing and accuracy, a C3-style
check, and an ADR stating that the channel is an experimental input. It is proposed
here only as a boundary and is not implemented.

### No latent policy memory

As in ADR-0012: decisions are reconstructed from the current observation. No RNG, no
action history, no cross-round state.

## Compatibility and verification

Existing policies, their identifiers and all prior evidence bytes are unchanged. The
new policy reuses `visible_peer_contributor_count` and duplicates only a small part of
the contributor's selection, because the screen sits inside that selection.

Tests use real engine observations and hand-derived traces: each screen clause and
its boundary, stale and unread items, rival support, distinct-source counting, the
challenge and verify paths, truth-flip observation identity, renaming of actors,
sources and propositions, and purity. A separately declared unfrozen experiment
(`experiments/quality-safeguards/`) reports quality, contribution, effort, utility,
C1/C2 and C3 separately. It selects no weights and supports no confirmatory claim.
