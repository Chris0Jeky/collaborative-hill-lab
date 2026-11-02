# PLAN — Collaborative Hill Lab

Milestones as of 2026-11-02. [NEXT.md](NEXT.md) gives dependencies and acceptance
criteria; [HANDOFF.md](HANDOFF.md) records evidence and remaining decisions.
Checked engineering follow-ups are implemented, reviewed and locally verified.
Core PRs #99–#102 are merged after exact-head Ubuntu/Windows checks; the seed
follow-up's public check and merge record is [PR #105](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/105).
Audit integration and its original experiment are implemented and independently
audited in [PR #107](https://github.com/Chris0Jeky/collaborative-hill-lab/pull/107),
which is not merged at this checkpoint. The integrated local 2,063-test suite and
complete verification/reproduction gate passed; final hosted CI and merge are
pending. Versioned audit-aware LLM prompts ([#108](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/108))
have an approved design and a separate implementation in progress.

## M0 — Offline foundation

- [x] Legacy discovery, methodological review and research charter
- [x] Own deterministic kernel; Concordia retained as a possible cognition adapter
- [x] Exact payoffs, canonical hashing, hierarchical seeds and sealed event ledgers
- [x] Five-plane scenarios and mechanism/narrative hash separation
- [x] N-IPD and Evidence Commons v0 mechanisms
- [x] Scripted policy family, replay policy and typed LLM adapter with fake provider
- [x] Replay, counterfactual branches and read-only comparisons
- [x] Metrics, manifests, study lifecycle, reports, CLI and reproducible setup
- [x] Study 000 executed and policy/structure confound characterized
- [x] Study 001 drafted; certificate correctly reports its failing collective stakes
- [x] Independent and declared paired-policy analysis with input-integrity checks
- [x] Finite-strategy incentive atlas with exact constraints and boundary controls
- [x] Input/path safety and shared built-in policy parameter validation
- [x] Shared recorded-seed validation, actual-artifact/CLI regressions and valid legacy/paired compatibility (#104)
- [x] Persistent exact-commit CI, full regression suite and A–K acceptance checks
- [x] Architecture records 0001–0018, research documentation and current handoff

## M1 — First live pilot

- [x] Observation-responsive scripted institutional baselines and controls (#76 / #81)
- [x] Configurable provider transport, mocked contract tests and measured-usage accounting (#77 / #82)
- [x] Offline request planning and cumulative provider attempt budgets (#86)
- [x] Continuation budget identity/accounting, stable analysis stop reasons and crash limits (#92)
- [ ] Human-approved pilot specification: institutions/weights, outcomes, model,
      sampling settings, skins, cost ceiling and stopping rules
- [ ] Declared pilot executed with measured variance, invalid-output rate and cost
- [ ] Skin-robustness assessment and sample-size/effect-size alternatives

## M2 — Study 001 confirmatory run

- [ ] Human finalizes hypotheses, primaries, weights, sample size, exclusions and SAP
- [ ] Human freezes the final study after the pilot-dependent choices are complete
- [ ] Frozen study executed, sealed and analyzed under the declared design
- [ ] Negative-results-preserving write-up and human publication decision

## M3 — Experimental depth

- [x] N=3/N=5 complete-graph threshold and composition sensitivity (Study 002)
- [x] pTFT include/exclude-self sensitivity with independent episode uncertainty
- [x] Exact finite-population pTFT means, variances and absorption benchmark
- [x] Versioned sparse graph semantics and complete-graph equivalence controls (#78 / #83)
- [x] Executed complete/ring/star controls with 18 exact predicted trajectories
- [x] Responsive EC grid with harmful/null controls and separate C1/C2/C3 diagnostics
- [x] Observation-grounded quality safeguards for responsive EC (#84)
- [x] Exact labeled-state sparse-graph pTFT benchmark (#85)
- [x] Independent four-component EC ablation: 192 behavioral episodes and 96 controls (#95)
- [x] Exact declared noisy-corpus model and versioned audit observation contract (#96)
- [x] Audit-enabled engine integration through the six ADR-0017 gates, specified by ADR-0018 (#103)
- [x] Separately declared audit-feedback experiment: 52 behavioral episodes, 24 controls, all P1–P8 and independent original-artifact audit (PR #107)
- [ ] Versioned audit-aware LLM prompts with unchanged legacy hashes; design approved and implementation in progress (#108)
- [ ] Deception-capable verification, with unchanged v0 controls
- [ ] Reputation/sanction institutions with responsive policies and integrity checks
- [ ] Concordia cognition adapter behind the observation firewall
- [ ] Serializable counterfactual policy-override specifications

Additional infrastructure should follow a concrete experimental need. No current
milestone changes Study 000/001 inputs or authorizes a freeze or paid run.
