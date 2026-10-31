# AGENTS.md — Collaborative Hill Lab operating guide

Dual-purpose file: §1 is the Codex/agent runtime contract for this repo (thin, tier T1 —
`CLAUDE.md` is the single home for the repo's rules and wins on conflict); §2+ is the
working guide for any engineer or coding agent. The first slice has landed, so this file
now carries the architecture map, invariants, and commands it promised.

## 1. Runtime contract (Codex delta)

Codex does not read `~/.claude/settings.json`; its irreversible-command floor is wired
in `.codex/hooks.json` — a PreToolUse hook calling the shared dispatcher
(`~/.claude/hooks/dispatch.py --event pre --runtime codex`; the floor is versioned outside this
repo and moves — do not pin its number here): blocks force-push,
`rm -rf` outside the repo, pipe-to-shell, `sudo`, and secret-file writes. It is the same policy a
Claude floor applies where one is wired (none on DESKTOP-IHKOOJS; no vendored repo copy to drift). Trusted-project defaults live in
`.codex/config.toml`: hooks are enabled and multi-agent fan-out is disabled at T1; approval and
sandbox choices remain user-level settings. After the hook file changes, review and trust its
new hash via `/hooks` before relying on it. Codex work style: `rg` for search, `apply_patch` for
edits, narrow diffs, inline work only at T1, concrete verification, and an explicit account of
what was NOT verified.

## 2. Mission

Which interaction structures, information structures, and institutional mechanisms move
LLM-agent populations from a **Tragic Valley** (free-riding, misinformation, coordination
failure) to a **Collaborative Hill** (accurate, sustainable cooperation)? The motivating
lineage is Tcaci & Huyck's N-person IPD comparison of targeted and diffuse reciprocity.
Study 000/002 show that both structure and policy matter; the legacy comparison does
not identify a structure-only effect. The longer-term target is LLM agents over
evidence and institutions. First environment: **Evidence Commons**. Full charter:
`docs/research/RESEARCH_CHARTER.md`.

## 3. Architecture map

Scenario (5 planes) → compiler (content hashes; mechanism ≠ narrative) → deterministic
MechanismEngine → runner (observe → propose typed action → validate → resolve → checkpoint
→ seal) → hash-linked `events.jsonl` → replay/branch → metrics → reports. LLMs act only
through the typed-action gate; they never resolve or score world state. Decisions:
`docs/adr/0001…0015`; synthesis: `docs/FOUNDATION_REVIEW.md`. Legacy `nipd` keeps
its complete-population contract; `nipd_graph` explicitly selects local graph rules.

## 4. Repository map

| path | contents |
|---|---|
| `src/collaborative_hill/engine/` | hashing, seeds, events, store, runner, replay, branching, interfaces |
| `src/collaborative_hill/domain/` | actions (typed union), evidence, claims, institutions, `world/` mechanisms (nipd, graph_nipd, evidence_commons) |
| `src/collaborative_hill/agents/` | `scripted/` (global/local TFT, EC personas and contribution quorum), `replay.py`, `llm/` (policy, transport, accounting, rendering) |
| `src/collaborative_hill/experiments/` | scenario (5 planes + skins + compiler), study lifecycle, manifests |
| `src/collaborative_hill/metrics/` | cooperation, epistemics, distribution, operations (versioned) |
| `src/collaborative_hill/reporting/` | run/study reports, counterfactual comparison, sealed factorial analysis |
| `studies/000-…`, `studies/001-…`, `studies/002-…` | executable studies, methods and research readouts |
| `experiments/incentive-atlas/` | exact finite-strategy incentive-region exploration |
| `experiments/responsive-commons/` | deterministic contribution-history sensitivity, finite incentives and fixed-action controls |
| `experiments/quality-safeguards/` | skeptical EC rule, truth negative control, finite incentives and fixed-action controls |
| `experiments/sparse-ptft/` | exact labeled-state pTFT on small connected graphs with an independent history oracle |
| `experiments/graph-topology/` | explicit graph/placement/policy controls and original-artifact readout tooling |
| `docs/PROVIDER_USAGE.md` | optional network transport, explicit opt-in, redaction and measured usage contract |
| `tests/{unit,property,metamorphic,integration}` | the science-guarding suites |
| `.github/workflows/ci.yml` | exact-commit offline verification on PRs and main, Ubuntu and Windows |
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
6. Invalid agent output is never silently repaired: unparsable/schema-invalid output
   abstains (`invalid_llm_output`) after bounded retries; provider errors seal the run
   `RunFailed`; only a schema-valid illegal action is `ActionRejected` and follows
   `invalid_action_policy` (`fail` default | `abstain`).
7. Ledgers are append-only and hash-linked; replay must reproduce chains; branch prefixes
   are byte-identical copies.
8. Manifests never fabricate: unmeasured tokens/cost are `None`. A known partial
   token sum is not a complete total; continuation usage excludes the parent prefix.
9. Studies freeze only by explicit human `chl study freeze … --yes`.
10. The runner never imports metrics (scorers cannot influence live runs).

## 6. Commands

`make doctor | setup | quick | lab | mutants | check | test | validate | acceptance | check-atlas |
check-study002 | check-responsive | check-quality-safeguards | check-graph | check-sparse-ptft | study-000 | study-001-smoke | study-002-plan | study-002 |
replay-smoke | report | clean-generated`; CLI: `chl scenario validate`, `chl study
validate|audit-seeds|freeze`, `chl run`, `chl replay`, `chl branch`, `chl compare`,
`chl analyze`, `chl report`, `chl lab`, `chl doctor`.
Venv python: `.venv/bin/python` on POSIX, `.venv/Scripts/python.exe` on Windows.
Quote all paths (spaces).

Feedback loop: `make quick` runs ruff, mypy, tests and gates selected from the diff
against `origin/main` by import graph and path mentions (`scripts/quick.py --plan`
shows the selection; unclassified files select everything). `make lab` regenerates a
small sealed sample and renders per-agent film strips to the terminal and
`artifacts/lab/console.html`; `chl lab <dir>` does the same for any run or artifacts
root and exits 1 on a broken ledger. Neither replaces the complete CI gate.

`make validate` checks all four shipped StudySpecs (Study 002 has two components).
`make study-002` needs a fresh output root; choose another with
`STUDY002_ARTIFACTS=artifacts/study-002-repeat`. Persistent CI runs
`make check test validate acceptance check-atlas check-study002 check-responsive check-quality-safeguards check-graph check-sparse-ptft` on the exact
published commit and checks that verification leaves the checkout clean.
Setup downloads pinned dependencies; the science checks call no model provider.
`chl run` and `chl branch` require `--allow-provider-requests` for effective network
policies. Validation and recorded-action replay remain offline. A scripted override
can replace a provider policy without resolving its credentials. This engineering
boundary does not select a live model, authorize spend or freeze a study.

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
2. `make validate` passes for all shipped StudySpecs; changed standalone research
   code also passes `make check-atlas`, `make check-study002`, `make check-responsive`,
   `make check-quality-safeguards`, `make check-graph` or `make check-sparse-ptft` as applicable.
3. After any review fix, rerun the relevant gates on the new exact HEAD.
4. HANDOFF.md updated: state, failures, open questions, next tasks, verify commands.
5. BUILD_LOG.md appended with decisions + commands actually run.
6. No fabricated numbers anywhere; unverified claims labelled.
7. Human-owned decisions untouched (list in HANDOFF.md).
