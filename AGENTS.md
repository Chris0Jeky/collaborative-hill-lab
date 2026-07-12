# AGENTS.md — Collaborative Hill Lab operating guide

Dual-purpose file: §1 is the Codex/agent runtime contract for this repo (thin, tier T1 —
`CLAUDE.md` is the single home for the repo's rules and wins on conflict); §2 is the project
brief for any engineer or coding agent. The platform code has not started, so this file stays
deliberately short — it grows with the first slice, not before.

## 1. Runtime contract (Codex delta)

Codex does not read `~/.claude/settings.json`, so the same irreversible-command floor is wired
in `.codex/hooks.json` — a PreToolUse hook calling the shared dispatcher
(`~/.claude/hooks/dispatch.py --event pre`, floor v1.3.0): blocks force-push, `rm -rf` outside
the repo, pipe-to-shell, `sudo`, secret-file writes. It is the SAME dispatcher Claude uses (no
vendored repo copy to drift). Codex work style: `rg` for search, `apply_patch` for edits,
narrow diffs, no subagent fan-out at T1, verify with concrete commands and state what was NOT
verified.

## 2. What this is

Collaborative Hill Lab is a research platform, benchmark, and agent-systems testbed for one
question: which interaction structures, information structures, and institutional mechanisms
move LLM-agent populations from a **Tragic Valley** of free-riding, misinformation, and
coordination failure to a **Collaborative Hill** of accurate, sustainable cooperation?

It transfers Chris's published N-person Prisoner's Dilemma result — targeted pairwise
accountability enables reciprocity, while aggregate/diffuse punishment obscures who
contributed or defected and weakens the ability to reward or punish individuals — from
classical and reinforcement-learning agents to LLM agents working with evidence, tools, and
conflicting information toward shared outputs.

First environment: **Evidence Commons** — an evidence-grounded commons where agents
contribute, cite, challenge, and depend on shared claims under mixed incentives. The project
draws together multi-agent orchestration, agent security and tool controls, and evaluation /
reproducibility / experimental methodology.

## 3. Structure arrives with the second item

No architecture map, invariants list, or command table yet — there is no code. When the first
slice lands (an environment scaffold, an agent harness, an eval), add here: a repository map,
the run/test/eval commands, and the invariants that must not break. Do not scaffold them
speculatively (second-occurrence rule). Tier and authority: `.claude/tier.json`.
