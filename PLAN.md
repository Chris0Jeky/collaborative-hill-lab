# PLAN — Collaborative Hill Lab

Milestones with checked status. Detail per item: NEXT.md; current state: HANDOFF.md.

## M0 — Foundation (this phase)

- [x] Phase 0 discovery: six-lens adversarial review of legacy repo, paper, methodology,
      architecture, security, related work (`docs/research/_discovery/`)
- [x] Architecture decision: own deterministic kernel, Concordia behind adapter (ADR-0001)
- [x] Kernel: canonical hashing (no floats), hierarchical stateless seeds, hash-linked
      event ledger, file stores
- [x] Five-plane ScenarioSpec + compiler; mechanism/narrative hash separation
- [x] Mechanisms: N-IPD (pairwise + neighbourhood, exact fractions) and
      Evidence Commons v0 (2×2 institutions, provenance verification)
- [x] Agents: deconfounded TFT family, EC personas, replay policy, LLM adapter + fake provider
- [x] Runner / replay / branching (copy-on-write prefix)
- [x] Metrics families + manifests + study lifecycle + reports + `chl` CLI + Makefile
- [x] Study 000 executed: 11/11 conditions reproduced (5 exact, 6 qualitative)
- [x] Study 001 drafted: scenarios, two skins, certificate, DRAFT prereg, cost worksheet
- [x] ADRs 0001–0007 + FOUNDATION_REVIEW
- [x] Research docs: charter, legacy audit, related work, novelty matrix, methodology,
      SAP, claims+limitations, threat model, prereg template, replication report
- [x] Test suites: unit, property, metamorphic, integration
- [x] Acceptance scenarios A–K executed
- [x] Final adversarial pass + accurate handoff

## M1 — First LLM pilot (needs human decisions)

- [ ] Human: approve Study 001 prereg fields (hypotheses, primaries, weights, models,
      ceiling); freeze study
- [ ] Real provider adapter (one provider, pinned model), token/cost capture
- [ ] 5-episode/cell pilot; variance + cost report; sample-size decision
- [ ] Skin-robustness pilot check (both skins)

## M2 — Study 001 confirmatory run

- [ ] Frozen study executed at decided replicate count; sealed; analysed per SAP
- [ ] Negative-results-preserving write-up

## M3 — Platform depth (as needed, second-occurrence rule)

- [ ] Deception-capable verification (agent-reported outcomes vs engine audit)
- [ ] Reputation/sanction institutions (SanctSim lineage)
- [ ] Concordia cognition adapter (behind observation firewall)
- [ ] N=5 populations; graph topologies
