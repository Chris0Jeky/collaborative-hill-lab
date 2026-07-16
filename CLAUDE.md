# CLAUDE.md — Collaborative Hill Lab

Tier: sandbox (T1) — authority: push free / merge free · dual-runtime (Claude + Codex).
Harness bootstrapped 2026-07-12 per `agent-harness/BLUEPRINT.md` §1 (T1 Sandbox).
This is the shared agent contract; Codex reads `AGENTS.md`, which points back here.

## What this is

Collaborative Hill Lab — a reproducible laboratory for whether LLM agents can build shared
truth under mixed incentives: which interaction, information, and institutional structures
move agent populations from the **Tragic Valley** (free-riding, misinformation, coordination
failure) to the **Collaborative Hill** (accurate cooperation). It carries Chris's N-person
Prisoner's Dilemma finding — targeted pairwise accountability breeds reciprocity, diffuse
punishment breeds the valley — from RL/classical to LLM agents over evidence and tools. First
environment: **Evidence Commons**. Blast radius today: only irreversible loss matters (T1) —
no deploy, no consumer. Foundation code landed 2026-07-13 (see `HANDOFF.md`).

## How to run

`make doctor | check | test | validate | study-000 | study-001-smoke | replay-smoke |
report` (Git Bash), or `.venv/Scripts/python.exe -m collaborative_hill.cli …` directly.
Full map + how-to-extend: `AGENTS.md`. Current state: `HANDOFF.md`.

## Locked decisions (change requires a new ADR, not a refactor)

ADR-0001 own deterministic kernel, Concordia cognition-only · ADR-0002 hash-linked JSONL
ledger, CoW branches · ADR-0003 five-plane scenarios · ADR-0004 mechanism/skin hash
separation · ADR-0005 stateless hierarchical seeds · ADR-0006 human-gated freezing,
exhaustive manifests · ADR-0007 typed LLM actions, safe abstention, no hidden CoT storage.

## Never-do list

- Never let a model (or prose) determine payoffs, world truth, evidence validity,
  permissions, or metrics.
- Never put floats or wall-clock time in hashed content; never use global RNG.
- Never silently repair invalid agent output into the expected action.
- Never freeze a study or launch a paid LLM run without the human (`--yes` is human-only).
- Never fabricate token counts, costs, or prices; `None` means unmeasured.
- Never edit a frozen study (new version = new hash); never manipulate results to match
  the legacy publication.
- Never present simulations as predictions of human communities or policy outcomes.
- Never store hidden chain-of-thought; public justifications only.

## Workflow & quality bar

Small diffs, commit per logical group; plain `git push` to `main` is fine (solo). The founding
session kept its work local; that foundation is now on `origin/main`. Work inline — no
subagent fan-out at T1 (the founding session had explicit ultracode authorization; that does
not carry forward). Tests guard science, not coverage numbers: hand-derived oracles,
leak canaries, chain equality, metamorphic invariance. A result without a reproducible
method does not count. Close work per `AGENTS.md` §8 checklist.

## Rules (T1 — keep it minimal)

- **The floor is the one guardrail.** The global PreToolUse deny hook
  (`~/.claude/hooks/dispatch.py`, floor v1.4.1) rides along for Claude and blocks only the
  irreversible: force-push, `rm -rf` outside the repo, pipe-to-shell, `sudo`, secret-file
  writes. It fires even under `bypassPermissions`. No repo-level hook copy (would double-spawn).
- **Permissions are `bypassPermissions`** (gitignored `.claude/settings.local.json`) — max
  trust by design at T1. Committed `.claude/settings.json` keeps `acceptEdits` + the deny floor.
- No secrets in the repo — API keys/tokens come from env. No real human-subject / participant
  data at T1; if any ever enters, flip `sensitive_data` first.

## Current milestone

M0 foundation complete → M1 needs the human: approve/freeze Study 001 prereg, pick
provider+model+budget, then pilot. Human-owned decisions live in `HANDOFF.md` — do not
decide them silently.

## Growth

Promote to T2 on durable use: a 3rd+ return session, something consuming this repo's output (a
paper, a benchmark run, a 2nd contributor), or the first "wish I had a test" moment. Until then
add nothing (second-occurrence rule). Tier/authority: `.claude/tier.json`; row: `~/.claude/ESTATE.md`.
