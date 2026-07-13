# Collaborative Hill Lab

*A reproducible laboratory for whether LLM agents can build shared truth under mixed
incentives.*

**Research question:** which interaction structures, information structures, and
institutional mechanisms move heterogeneous LLM-agent populations from a **Tragic Valley**
(free-riding, misinformation, coordination failure) to a **Collaborative Hill** (accurate,
sustainable cooperation)?

The lab extends Cristian Tcaci's N-person Iterated Prisoner's Dilemma work (with Chris
Huyck, Middlesex University): *targeted pairwise accountability sustains cooperation;
diffuse aggregate accountability collapses it.* Here that question moves from classical/RL
agents to LLM agents working over evidence, provenance, and institutions. First
environment: **Evidence Commons**.

## Status (2026-07-13, foundation phase)

Working today, all offline and deterministic — **no LLM calls, no cost, synthetic data
only**:

- A deterministic simulation kernel: typed five-plane scenarios, hash-linked event
  ledgers, exact-fraction payoffs, stateless hierarchical seeding, replay verification,
  and counterfactual branching at checkpoints.
- Two mechanisms: **N-IPD** (pairwise + neighbourhood) and **Evidence Commons v0**
  (claims, evidence provenance, budgets, 2×2 accountability × evidence-topology
  institutions).
- **Study 000** (legacy reproduction): 11 conditions × 30 replicates; 5 exact analytical
  reproductions + 6 qualitative — and a deconfound showing the legacy effect needs BOTH
  the interaction structure and the right reciprocity rule
  (`docs/research/REPLICATION_REPORT.md`).
- **Study 001** (Evidence Commons): DRAFT preregistration awaiting human approval; runnable
  scripted fixture; mechanism certificate proving the social dilemma by enumeration.
- An LLM policy adapter (typed actions, bounded retries, safe abstention) exercised by a
  deterministic fake provider. No real provider is wired up yet — adding one is a
  human-gated step.

## Five-minute deterministic path

```bash
git clone <this repo> && cd collaborative-hill-lab
make setup          # venv + pinned deps (Python >= 3.12)
make doctor         # environment checks
make check          # lint + unit/property tests
make study-000      # 330 sealed episodes + replication report
make replay-smoke   # re-execute sealed runs, verify identical hash chains
make report         # per-run + per-study markdown reports
```

Direct equivalents (Windows/PowerShell without make):
`.venv/Scripts/python.exe -m collaborative_hill.cli <doctor|run|replay|report|...>` — see
`Makefile` for the exact commands behind each target.

## Architecture (one screen)

```
ScenarioSpec (5 planes: world / information / interaction / institution / cognition)
      │  compile_scenario()  → content hashes: mechanism ≠ narrative (skins can't touch rules)
      ▼
ResolvedScenario ──► MechanismEngine (typed deterministic world; LLM never authoritative)
      │                   ▲ typed ActionProposal only
      ▼                   │
run_episode()        AgentPolicy (scripted / replay / LLM adapter behind observation firewall)
      │
      ▼
events.jsonl (hash-linked, append-only) ──► replay (chain equality) / branch (CoW prefix)
      │
      ▼
metrics (cooperation / epistemics / distribution / operations) ──► report.md, parquet
```

Decisions with rationale: `docs/adr/0001…0007`. Synthesis: `docs/FOUNDATION_REVIEW.md`.

## Scientific limitations (read before citing)

- Results are claims about **LLM/scripted agent populations under configured mechanisms**
  — never predictions of human communities or policy outcomes.
- Evidence Commons v0 verification is engine-adjudicated provenance-checking: agents
  cannot lie about verification outcomes yet; deception is future work.
- Study 000 reproduces legacy *claims*, not legacy artifacts (the legacy pipeline was
  unseeded and its pairwise tracking defective — `docs/research/LEGACY_AUDIT.md`).
- LLM cognition is not reproducible; replays reproduce recorded actions exactly, not
  model calls (ADR-0001).
- Full list: `docs/research/CLAIMS_AND_LIMITATIONS.md`.

## Repository map

| path | contents |
|---|---|
| `src/collaborative_hill/` | kernel (`engine/`), domain models, agents, experiments, metrics, reporting, CLI |
| `studies/000-legacy-reproduction/` | reproduction study: scenarios, predictions, report generator |
| `studies/001-evidence-commons/` | DRAFT 2×2 study: scenarios, two skins, certificate, prereg, cost worksheet |
| `docs/adr/` | seven accepted architecture decision records |
| `docs/research/` | charter, legacy audit, related work, novelty matrix, methodology, SAP, threat model, replication report |
| `tests/` | unit / property / metamorphic / integration suites |
| `artifacts/` | generated sealed runs (gitignored) |

Contributor guide (humans and coding agents): `AGENTS.md`. Locked rules: `CLAUDE.md`.
Current state and next steps: `HANDOFF.md`, `NEXT.md`, `PLAN.md`.
