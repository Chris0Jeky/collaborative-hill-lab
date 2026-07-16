# AGENTS.md — Collaborative Hill Lab operating guide

Dual-purpose file: §1 is the Codex/agent runtime contract for this repo (thin, tier T1 —
`CLAUDE.md` is the single home for the repo's rules and wins on conflict); §2+ is the
working guide for any engineer or coding agent. The first slice has landed, so this file
now carries the architecture map, invariants, and commands it promised.

## 1. Runtime contract (Codex delta)

Codex does not read `~/.claude/settings.json`, so the same irreversible-command floor is wired
in `.codex/hooks.json` — a PreToolUse hook calling the shared dispatcher
(`~/.claude/hooks/dispatch.py --event pre --runtime codex`, floor v1.4.1): blocks force-push,
`rm -rf` outside the repo, pipe-to-shell, `sudo`, and secret-file writes. It is the SAME policy
Claude uses (no vendored repo copy to drift). Trusted-project defaults live in
`.codex/config.toml`: hooks are enabled and multi-agent fan-out is disabled at T1; approval and
sandbox choices remain user-level settings. After the hook file changes, review and trust its
new hash via `/hooks` before relying on it. Codex work style: `rg` for search, `apply_patch` for
edits, narrow diffs, inline work only at T1, concrete verification, and an explicit account of
what was NOT verified.

## 2. Mission

Which interaction structures, information structures, and institutional mechanisms move
LLM-agent populations from a **Tragic Valley** (free-riding, misinformation, coordination
failure) to a **Collaborative Hill** (accurate, sustainable cooperation)? Lineage: Tcaci &
Huyck's N-person IPD result (targeted pairwise accountability sustains reciprocity; diffuse
punishment collapses it), carried to LLM agents over evidence and institutions. First
environment: **Evidence Commons**. Full charter: `docs/research/RESEARCH_CHARTER.md`.

## 3. Architecture map

Scenario (5 planes) → compiler (content hashes; mechanism ≠ narrative) → deterministic
MechanismEngine → runner (observe → propose typed action → validate → resolve → checkpoint
→ seal) → hash-linked `events.jsonl` → replay/branch → metrics → reports. LLMs act only
through the typed-action gate; they never resolve or score world state. Decisions:
`docs/adr/0001…0007`; synthesis: `docs/FOUNDATION_REVIEW.md`.

## 4. Repository map

| path | contents |
|---|---|
| `src/collaborative_hill/engine/` | hashing, seeds, events, store, runner, replay, branching, interfaces |
| `src/collaborative_hill/domain/` | actions (typed union), evidence, claims, institutions, `world/` mechanisms (nipd, evidence_commons) |
| `src/collaborative_hill/agents/` | `scripted/` (TFT family, EC personas), `replay.py`, `llm/` (policy, providers, rendering) |
| `src/collaborative_hill/experiments/` | scenario (5 planes + skins + compiler), study lifecycle, manifests |
| `src/collaborative_hill/metrics/` | cooperation, epistemics, distribution, operations (versioned) |
| `src/collaborative_hill/reporting/` | run/study markdown + parquet derivation |
| `studies/000-…`, `studies/001-…` | executable studies (see their READMEs) |
| `tests/{unit,property,metamorphic,integration}` | the science-guarding suites |
| `docs/adr/`, `docs/research/` | decisions; research documents |

## 5. Invariants (breaking any of these is a defect, not a style choice)

1. An LLM is never authoritative for payoffs, world truth, evidence validity, permissions,
   or final metrics — typed deterministic code only.
2. No floats in hashed content; payoffs are exact `Fraction` strings (`frac_str`).
3. No global random state; every draw comes from `rng_for(<seed path>)`; no RNG state is
   ever persisted (ADR-0005).
4. Hidden truth fields (`true_propositions`, `truth_aligned`) never appear in observations
   or ledgers (leak tests scan whole ledgers).
5. Skins carry wording only; `mechanism_hash` must be skin-invariant (metamorphic test).
6. Invalid agent output is recorded (`ActionRejected`) and falls back to explicit
   abstention or run failure — never silently repaired.
7. Ledgers are append-only and hash-linked; replay must reproduce chains; branch prefixes
   are byte-identical copies.
8. Manifests never fabricate: unmeasured tokens/cost are `None`.
9. Studies freeze only by explicit human `chl study freeze … --yes`.
10. The runner never imports metrics (scorers cannot influence live runs).

## 6. Commands

`make doctor | setup | check | test | validate | study-000 | study-001-smoke |
replay-smoke | report | clean-generated`; CLI: `chl scenario validate`, `chl study
validate|freeze`, `chl run`, `chl replay`, `chl branch`, `chl report`, `chl doctor`.
Venv python: `.venv/Scripts/python.exe`. Quote all paths (spaces).

## 7. How to add things

- **Mechanism:** new module in `domain/world/` implementing the `MechanismEngine` protocol
  (state = canonical-JSON dict; events as payload dicts) + a world-plane variant in
  `experiments/scenario.py` + oracle tests with HAND-DERIVED literals + a certificate if it
  claims a dilemma.
- **Skin:** a `NarrativeSkin` JSON — naming/prose only; compiler rejects unknown ids; add
  it to the skin-isolation metamorphic test if it ships with a study.
- **Institution:** extend `InstitutionConfig` + implement its effects ONLY in observation
  shaping and credit assignment; add a C3-style invariance check (task unchanged for
  identical behaviour) to the study certificate.
- **Agent adapter:** implement `AgentPolicy` (`policy_id`, `propose(observation, rng)`);
  scripted policies must be observation-driven (no hidden memory — branch rebuilds
  instances); register in `experiments/study.py::build_policies`.
- **Metric:** versioned function in `metrics/`; reads sealed events only; bump
  `METRIC_VERSIONS` on any definition change.
- **Study:** directory with `study.json` + `scenarios/` + `skins/` (+ generator script as
  the canonical record); README with predictions BEFORE running; freeze is human-only.

## 8. Handoff checklist (before ending any substantial session)

1. `make check` and `make test` green (or failures explained in HANDOFF.md).
2. `make validate` passes for both studies.
3. After any review fix, rerun the relevant gates on the new exact HEAD.
4. HANDOFF.md updated: state, failures, open questions, next tasks, verify commands.
5. BUILD_LOG.md appended with decisions + commands actually run.
6. No fabricated numbers anywhere; unverified claims labelled.
7. Human-owned decisions untouched (list in HANDOFF.md).
