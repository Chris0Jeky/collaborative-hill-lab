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
no code yet, no deploy, no consumer.

## How to run

Nothing to run yet — the platform is not started. Run/test/eval commands land here and in
`AGENTS.md` with the first slice, not before.

## Rules (T1 — keep it minimal)

- **The floor is the one guardrail.** The global PreToolUse deny hook
  (`~/.claude/hooks/dispatch.py`, floor v1.3.0) rides along for Claude and blocks only the
  irreversible: force-push, `rm -rf` outside the repo, pipe-to-shell, `sudo`, secret-file
  writes. It fires even under `bypassPermissions`. No repo-level hook copy (would double-spawn).
- **Permissions are `bypassPermissions`** (gitignored `.claude/settings.local.json`) — max
  trust by design at T1. Committed `.claude/settings.json` keeps `acceptEdits` + the deny floor.
- No secrets in the repo — API keys/tokens come from env. No real human-subject / participant
  data at T1; if any ever enters, flip `sensitive_data` first.
- Small diffs, commit per logical group; plain `git push` to `main` is fine (solo). Work
  inline — no subagent fan-out at T1.

## Growth

Promote to T2 on durable use: a 3rd+ return session, something consuming this repo's output (a
paper, a benchmark run, a 2nd contributor), or the first "wish I had a test" moment. Until then
add nothing (second-occurrence rule). Tier/authority: `.claude/tier.json`; row: `~/.claude/ESTATE.md`.
