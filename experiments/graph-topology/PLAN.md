# Graph N-IPD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independently versioned, locally observed graph game without changing historical complete-population mechanisms.

**Architecture:** A new graph module validates canonical adjacency and resolves exact edge payoffs. The scenario compiler selects the new world explicitly; graph-local policies preserve existing parameter contracts. This lane integrates the shared registry and CLI; renderer support belongs to the provider lane.

**Tech Stack:** Python 3.12, Pydantic 2, `fractions.Fraction`, existing deterministic runner and sealed replay.

**Spec:** `docs/adr/0011-versioned-graph-nipd.md`.

## Global constraints

- Legacy world `nipd`, existing input bytes and mechanism hashes remain unchanged.
- New world `nipd_graph` requires explicit undirected adjacency and sum/mean aggregation.
- At least one edge; isolates earn zero and cast no eligible interaction votes.
- No global RNG, floating-point hashed values, hidden truth or real providers.
- This lane changes `study.py` and CLI only to select the graph policy builder; provider work owns renderer support.

## Review focus

- A reordered adjacency must not change the new mechanism hash.
- A nonneighbor's changed action must not change the observer's observation.
- A direct `resolve` call must reject incomplete or extraneous neighbor moves.
- Isolates must not inflate cooperation or cause division by zero.
- Branch rebuilding must select local-degree policies, including pTFT denominator.

## Tasks

### 1. Canonical graph and exact mechanism

Files: new `domain/world/graph_nipd.py`, new unit tests, scenario extensions.
Interfaces: `UndirectedGraph`; `GraphNIPDWorld`; `GraphNIPDMechanism(agent_ids, mode, params, rounds, adjacency, payoff_aggregation)`.

- [x] Write failing literal ring/star/isolate, invalid adjacency/action, and noninterference tests.
- [x] Run focused tests to confirm missing implementation is the failure.
- [x] Implement canonical validation, local observations and exact sum/mean transitions.
- [x] Extend scenario validation/building/hash projection only for the new world.
- [x] Verify all literals, adjacency reorder identity, version binding and old hashes.

### 2. Local policies and execution integration

Files: new `agents/scripted/graph_nipd_policies.py`, focused policy/metamorphic/integration tests.
Interface: `build_graph_nipd_policy(name, mode, params) -> AgentPolicy`.

- [x] Write failing local denominator, quorum, isolate, and complete-graph policy controls.
- [x] Implement stateless graph policies with distinct local policy identities.
- [x] Select the graph builder in the registry and CLI; renderer support remains with the provider integration lane.
- [x] Verify sealed replay, branch prefix/divergence, deterministic relabelling and skin isolation.

The first strict typing pass found the seed-audit horizon dispatch also needed
the new world family. Its graph regression first failed with `NIPDParams.rounds`
missing, then passed after the narrow dispatch extension. Parent scope approval
included that integration. Core gates passed: 112 new focused cases, Ruff, strict
mypy in 47 package files, the complete existing/new suite, all four unchanged
StudySpec hashes and 11/11 acceptance. Full evidence remains in the final handoff.

### 3. Small deterministic experiment and final gates

Files: `experiments/graph-topology/README.md`, canonical fixture/generator, exact report and tests.

- [x] Commit analytical predictions before executing the experiment (`d22c659`).
- [x] Hold N=5, one AllD, eight rounds and mean payoff fixed; cross complete/ring/star, defector a1/a2, and targeted/linked/quorum TFT.
- [x] Use one episode per cell; distinguish role placement and policy from topology.
- [ ] Verify exact report regeneration and retain compact results without raw ledger bulk.
- [ ] Run focused tests, Ruff, strict package typing, full tests, validation and acceptance; obtain independent review and commit.

Execution ruling: `--run` writes only its fixed `RESULTS` prefix under the fresh
artifact root; custom prefixes belong to `--report-from`. A regression reproduced
the otherwise possible future collision with `EXECUTION_SOURCE.json` after all
episodes had run. Rejecting that combination before execution avoids partial
workflow completion without introducing a second destination-planning registry.
The cost is one separate readout command when a custom prefix is wanted.

The 11 experiment regressions pass, including exact regeneration, original-run
replay, missing/extra evidence rejection and a malformed source-file commitment.
The latter first raised an unhandled missing-dependency key error; explicit source
record validation now rejects it before readout. The mathematical witness also
enumerates count histories from the all-reciprocator-C initial state, proving the
initialized projected process is not Markov. An independent reviewer separately
enumerated all 18 experiment trajectories and literal edge rewards and agreed on
every action, cooperation count and terminal score.

Runtime ruling: the shared development environment has setuptools 84.0.0, whereas
the committed lock specifies 84.1.0. Its broad regression gates are retained as
development evidence, without claiming exact lock installation. The isolated
84.1.0 environment matches all 38 lock pins and will run the recorded execution
and final verification with this worktree's source explicitly on `PYTHONPATH`.

