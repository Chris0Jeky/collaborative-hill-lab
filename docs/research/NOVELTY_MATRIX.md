# Novelty Matrix — Collaborative Hill Lab

**Status:** Foundation-phase discovery consolidation. **Date:** 2026-07-13.
Consolidates `_discovery/related-work.md` §§5–6. Cells reflect documented behaviour of each
system; the **CHL row is planned/claimed** and must be re-checked against the code as it is built.
Full citations and confidence tags are in `RELATED_WORK.md`. "—" = not present / not a design
concern.

---

## The matrix

Ten columns: research question · environment · interaction structure · information structure ·
institutional interventions · evidence provenance · reproducibility · branchable counterfactuals ·
metrics · major limitations.

| System | Research question | Environment | Interaction structure | Information structure | Institutional interventions | Evidence provenance | Reproducibility | Branchable counterfactuals | Metrics | Major limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| **Concordia** (arXiv:2312.03664; v2.4.0 2026-03-06) | Can we build believable, grounded generative ABMs? | Open, GM-narrated physical/social/digital space | GM-mediated; any topology the modeler scripts | Natural-language memory + GM narration | Modeler-scripted; no taxonomy | — (GM narrates ground truth; no provenance layer) | **Silent** in docs; LLM+GM adjudication non-deterministic | — (no native branching primitive) | None built-in; modeler-defined | Not truth/incentive-focused; no auditable provenance or seeded replay |
| **GovSim** (arXiv:2404.16698, NeurIPS'24) | Do LLM societies sustainably govern a commons? | CPR: fishery / pasture / pollution, regenerating resource | Round-based, all-to-all NL communication | Shared public dialogue | Universalization prompt; communication on/off | — | Code released; LLM-snapshot bound, not seeded-canonical | — | Survival time/rate, gain, efficiency | One dilemma family; resource-only, no contested facts; no replay/branching |
| **SanctSim** (arXiv:2506.23276) | Do reasoning LLMs sustain cooperation under sanctioning institutions? | Public-goods game with institutional choice (SI vs SFI) | Repeated; agents sort into institutions, punish/reward peers | Contribution history observable | **SI vs SFI**, costly peer punishment/reward | — | Code (SanctSim repo); LLM-snapshot bound | — | Contribution, payoff, punishment uptake, institution sorting | Scalar contributions not evidence; economic not epistemic payoff; no provenance/replay |
| **Melting Pot 2.0** (arXiv:2211.13746) | Do MARL agents generalize to novel social partners? | 50+ gridworld substrates, 256+ scenarios | Spatial gridworld; mixed cooperation/competition | Pixel observations | Substrate rules (e.g. zapping/tagging) | — | **Deterministic, seeded, fully reproducible** substrates | — (scenario sets, not run branching) | Focal per-capita return, generalization scores | RL not LLM; no NL evidence/epistemics; no provenance |
| **Generative Agents** (UIST'23, arXiv:2304.03442) | Can LLM agents produce believable emergent social behaviour? | Smallville sandbox (Sims-like) | Spatial proximity + NL conversation | Memory stream (obs/plan/reflect); gossip spreads | User intervention (ad hoc) | — (no accuracy tracking of spread info) | Not a goal; LLM-bound | — | Believability (human eval) | Believability not truth; no incentives, provenance, replay, or scoring |
| **Akata et al.** (Nat. Hum. Behav. 2025) | How do LLMs behave in repeated 2×2 games? | Iterated PD, Battle of the Sexes, etc. | **Pairwise, 2-player** repeated | Opponent-info + social CoT | — (game payoff only) | — | Model-bound experiments | — | Game score, cooperation rate, coordination success | 2-player only; no population/institution/evidence layer |
| **Collaborative Hill Lab** (planned) | Which interaction/information/institutional structures move LLM-agent populations from the Tragic Valley to the Collaborative Hill in *building shared truth*? | **Evidence Commons** (contested claims + evidence under mixed incentives); N-IPD micro-mechanism | **Pairwise-targeted vs aggregate/neighbourhood accountability as a first-class manipulable** (carries the N-person PD finding) | Configurable observation policy (five-plane; allow-list projection); private vs shared-ledger topology | Taxonomy incl. attributable vs aggregate accountability now; reputation/sanctions/commitments designed, deferred | **First-class provenance-tracked claims/evidence**; verification checks provenance, not truth | **Seeds derived by identity + canonical JSON + hash-chained event ledger + content-addressed stores → bit-exact replay** | **Native branchable counterfactuals** (prefix byte-identical) off any checkpoint | Epistemic accuracy (briefing correctness) + cooperation + collapse metrics (Tragic-Valley/Collaborative-Hill) | Planned/unbuilt; no study run yet; claims unproven; LLM-snapshot sensitivity still applies |

---

## Honest novelty assessment

### Defensible lanes (survive scrutiny)

1. **Epistemic payoff as the social dilemma (clearest novelty, MED-HIGH).** GovSim and SanctSim make
   agents fight over *quantities* (fish, contributions). No surveyed *incentive-structure* system makes
   the contested object **truth itself**, with provenance-tracked evidence, under a manipulable
   accountability structure. The fact-checking multi-agent papers (arXiv:2505.17511, LoCal,
   arXiv:2506.00509) build tools; they do not treat accountability structure as an IV.
2. **Reproducibility + branching stack as a first-class scientific instrument (HIGH).** Seeded
   canonical replay + hash-chained event ledger + content-addressed stores + **branchable
   counterfactuals** is essentially absent from the LLM-social-sim lineage: Concordia is *silent* on
   determinism; GovSim/SanctSim release code but are LLM-snapshot bound with no seeded-replay/branching
   primitive; Melting Pot has determinism but is RL, not LLM/epistemic. Combining LLM-agent social
   dilemmas *with* Melting-Pot-grade reproducibility and branching is the novel union. None of the
   surveyed LLM systems document branchable counterfactuals.
3. **Pairwise-vs-aggregate accountability as the primary manipulated variable, carried into LLMs
   (MED-HIGH).** Akata is pairwise-only (no population); SanctSim manipulates institution *choice*, not
   pairwise-vs-diffuse *targeting*; GovSim is all-to-all. Carrying Chris's specific RL/classical
   N-person-PD finding (targeted pairwise reciprocity vs diffuse punishment) into LLM populations over
   evidence is an untaken combination.

### Where overlap is real — do NOT overclaim

- **The collapse phenomenon ("Tragic Valley") is NOT novel.** GovSim and SanctSim already demonstrate
  LLM-cooperation collapse under a social dilemma; *Deliberative Illusion* (arXiv:2606.03032, id
  unverified) shows the epistemic version (fact loss in deliberation). CHL cannot claim first
  demonstration of LLM-cooperation or LLM-epistemic collapse. Its novelty is the *epistemic domain +
  reproducibility + accountability-structure IV combined*, not the phenomenon.
- **The GM / entity-component architecture is Concordia's,** not CHL's; CHL reuses a known pattern (and
  inverts the GM so no LLM adjudicates truth).
- **"Universalization / communication / reputation / sanctioning improve cooperation" are already
  published levers** (GovSim, arXiv:2505.05029, SanctSim). CHL's institution menu overlaps these; the
  contribution is *systematic comparison under a truth objective with replay*, not the individual
  levers.
- **Multi-agent misinformation propagation is staked out** by Prompt Infection (arXiv:2410.07283) on
  the security side; CHL must cite it, not reinvent it.

### What would falsify our novelty claims

- **Reproducibility/branching lane** is falsified if any surveyed LLM-social system already ships
  seeded canonical replay *and* run-state branching. Trigger to re-check: Concordia v2.4.0 added
  "dynamic state editing" and state snapshotting — **verify whether that enables branchable
  counterfactuals before claiming uniqueness.** If Concordia (or a GovSim/SanctSim successor) documents
  a hash-verified replay + branch primitive, claim 2 collapses to "one of few," not "novel."
- **Epistemic-dilemma lane** is falsified if a paper is found that manipulates an accountability/
  interaction structure as an IV *over contested truth with provenance*, not just as a diagnostic. The
  *Deliberative Illusion* line (arXiv:2606.03032) is converging on this territory fast; if it (or a
  successor) adds a manipulable structure knob, claim 1 weakens to "independent concurrent work."
- **Accountability-targeting lane** is falsified if an LLM-population study is found that varies
  *pairwise-targeted vs diffuse-aggregate* retaliation directly (not institution choice, not
  all-to-all). NetworkGames (arXiv:2511.21783) varies interaction *networks* and is the nearest threat;
  read it in full before claiming the targeting IV is untaken.

### Open verification items

- Re-verify the 2604–2606-range arXiv ids (2606.03032, 2605.29062, 2604.11721, 2605.19351) before any
  formal citation — surfaced by search, not individually fetched.
- Fetch full PDFs for Melting Pot, Generative Agents, Akata, and AgentBench to confirm the
  reproducibility/metrics cells (currently MED, from abstract/README + aggregators).
- Confirm Concordia's determinism and state-snapshot/branching status against a pinned commit, not just
  the README (directly gates novelty claim 2).
- Read NetworkGames (arXiv:2511.21783) and SanctSim in full to confirm neither already implements the
  pairwise-vs-aggregate targeting IV (gates novelty claim 3).
- Re-confirm every CHL-row cell against the built code before publishing the matrix — the row is
  currently *claimed*, and each guarantee (bit-exact replay, prefix-identical branching, truth
  firewall) must be demonstrated by a passing test per `RESEARCH_CHARTER.md` §9, not asserted.
