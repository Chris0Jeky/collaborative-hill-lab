# ADR-0004 — Mechanism/narrative separation with independent content hashes

Status: **accepted** (2026-07-13)

## Context

LLM behaviour is prompt-sensitive; scientific mechanisms must not be. Results must be
attributable to the mechanism, with wording varied for robustness — so the two need
independent identities and a structural guarantee that wording cannot move mechanics.

## Decision

- `mechanism_hash` covers world + information + interaction + institution + the agent-id
  roster (the GAME). `narrative_hash` covers the `NarrativeSkin` only. `scenario_hash`
  covers mechanism_hash + narrative_hash + the cognition plane. `evidence_corpus_hash` is
  additionally recorded. All hashes are domain-tagged (`chl.mechanism.v1`, `chl.skin.v1`,
  `chl.scenario.v1`, `chl.evidence.v1`).
- `NarrativeSkin` is STRUCTURALLY inert: its schema has only naming/prose fields (names,
  titles, wording, evidence content). It has no numeric or rule-bearing fields, so a skin
  cannot express a payoff, budget, visibility, or rule change. The compiler rejects skins
  referencing unknown ids.
- Both hashes are recorded in every run manifest and in the RunStarted event meta.
- Adversarial evidence TEXT (prompt-injection fixtures) lives in skins; the mechanism-level
  `adversarial` flag marks the fixture so every skin carries it.

Guarantees, as tested (tests/metamorphic/test_skin_isolation.py): swapping skins leaves
`mechanism_hash` unchanged, changes `narrative_hash`, and leaves scripted-run event chains
byte-identical.

## Consequences

- Skin robustness checks for LLM studies are first-class: same mechanism hash, different
  narrative hash, compare outcomes.
- Renderers (`agents/llm/rendering.py`) take all FACTS from typed observations and all
  WORDING from skins; a skin cannot add or remove information, only re-dress it.
