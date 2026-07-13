# ADR-0001 — Own a narrow deterministic kernel; Concordia only behind an adapter

Status: **accepted** (2026-07-13)

## Context

Three options for the simulation substrate:
A. Build on the legacy NPDL simulator; B. Build on DeepMind Concordia (v2.4.0);
C. Own a small deterministic research kernel with optional adapters for both.

Discovery findings (docs/research/_discovery/): the legacy repo has four parallel,
non-equivalent engines, process-global RNG, float payoffs, no typed schemas, no ledger, and
a known reporting defect — disqualifying it as a kernel (its clean pure payoff functions
remain useful as a cross-check oracle). Concordia's Game Master resolves and narrates world
state through LLM calls — nondeterministic, unhashable, and scored variables would sit in
generative hands, violating locked principles 1–2.

## Decision

Option C. The mechanism engine, event ledger, evidence/claims model, study registry, and
metrics are owned by this repo (`src/collaborative_hill/`). Concordia may later supply
*cognition only* (entity components, memories) behind `adapters/concordia/`, subject to the
observation firewall: a Concordia-driven agent receives exactly the typed observation and
must return a member of the typed action union; it never resolves or scores world state.
The legacy simulator is used read-only as a reference oracle for Study 000 cross-checks.

**Determinism scope (binding):** kernel replay is deterministic GIVEN recorded typed
actions. Scripted policies are additionally rerun-deterministic from seeds. LLM cognition is
NOT reproducible; replay replays recorded actions, never model calls, and prompts/raw model
output live outside the hash chain (unhashed transcript sidecar).

## Consequences

- No multi-agent application framework in the core; adapters are additive and optional.
- Anything Concordia-shaped must pass the typed-action gate — a Concordia adapter cannot be
  "trusted" more than an LLM policy.
- We maintain our own engine surface (small: ~10 files) — accepted cost for verifiability.
