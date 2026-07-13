# ADR-0003 — Five-plane ScenarioSpec with a validating compiler

Status: **accepted** (2026-07-13)

## Context

The lab must vary interaction structure, information structure, and institutions
independently — the legacy work's central confound was varying strategy and structure
together. Scenario composition needs typed validation so illegal combinations fail at
compile time, not mid-run.

## Decision

`ScenarioSpec` composes five planes (experiments/scenario.py):

- **world** — discriminated union (`nipd` | `evidence_commons`): true state, payoff
  parameters, termination. World truth (e.g. `true_propositions`) lives ONLY here.
- **information** — the evidence corpus (`EvidenceSpec`: source, stance, freshness,
  environment-only `truth_aligned`, `adversarial` marker, initial holders).
- **interaction** — structure (pairwise | neighbourhood | commons), simultaneous
  scheduling, complete graph (named topologies are a documented extension point).
- **institution** — `InstitutionConfig`: accountability (aggregate | attributable) ×
  evidence topology (private | shared_ledger). Reputation, sanctions, commitments, audits
  are documented extension points, not empty abstractions.
- **cognition** — per-agent `PolicySpec` (scripted registry, replay, llm adapters).

A compiler (`compile_scenario`) validates cross-plane combinations (NIPD carries no
evidence; commons requires evidence; interaction.structure must match the world mode;
skins may reference only existing ids) and emits a `ResolvedScenario` with four content
hashes (see ADR-0004).

Institutions act in exactly two places — observation shaping (attribution, visibility) and
credit assignment — never in world-truth resolution. Observations are projections built by
`observe()`; agents never see engine state (the observation firewall).

## Consequences

- New mechanisms implement the `MechanismEngine` protocol and a world-plane variant; the
  compiler and runner need no changes.
- Spec-level numbers are ints or exact rational strings — floats cannot enter hashes.
- Cross-plane invariants live in one place (the compiler) and are unit-tested.
