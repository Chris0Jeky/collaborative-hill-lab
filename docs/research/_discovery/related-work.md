# Related Work — Discovery Survey

**Role:** Related-work researcher (web). **Access date for all sources:** 2026-07-13.
**Scope:** Primary sources for systems adjacent to Collaborative Hill Lab (CHL) — LLM-agent
populations building shared truth under mixed incentives; Evidence Commons; pairwise vs
aggregate accountability; provenance-tracked claims; reproducible event-sourced runs;
branchable counterfactuals.

**Confidence legend:** HIGH = confirmed from the primary artifact (arXiv abstract/PDF, repo
README, releases page). MED = confirmed from a single secondary/aggregator or from a primary
source whose relevant detail I did not read line-by-line. LOW = inferred / not directly verified.

**Method note:** Fetched arXiv abstract pages, GitHub README/releases, and cross-checked with
web search snippets. I did NOT clone or run any of these systems; architecture claims about
determinism/reproducibility come from documentation, not from executing the code. Where a
system's docs are silent on a property (e.g. Concordia determinism), I say "silent" rather
than asserting absence.

---

## 1. Google DeepMind Concordia

- **Repo:** `google-deepmind/concordia` — https://github.com/google-deepmind/concordia (HIGH)
- **PyPI package:** `gdm-concordia` (HIGH)
- **Latest release:** **v2.4.0, 2026-03-06** (HIGH — from the releases page). Recent tags:
  v2.3.1 (2026-02-04), v2.3.0 (2026-02-04), v2.2.0 (2026-01-12), v2.1.0 (2025-08-18). A
  "v2.0" line was announced mid-2025 (cooperativeai.com blog "Google DeepMind Releases
  Concordia Library v2.0"). v2.4.0 notes mention an **asynchronous simulation engine**,
  **dynamic state editing** in the visual interface, migration to newer Google AI packages,
  and multi-modal / image-generation support. (HIGH for tags/dates; MED for feature list.)
- **Tech report:** "Generative agent-based modeling with actions grounded in physical, social,
  or digital space using Concordia" — **arXiv:2312.03664** (Dec 2023; v2 on arXiv HTML). (HIGH)
  Authors incl. Vezhnevets, Agapiou, Duéñez-Guzmán et al. (DeepMind). A second, newer paper —
  **"Concordia Design Pattern," arXiv:2507.08892** (Jul 2025) — documents the redesigned
  Entity/Component/Engine architecture. (MED — id from README extraction.)
- **Architecture (v2, HIGH from README):** Three core concepts.
  - **Entities** — actors: player characters (Agents) or system controllers (Game Masters).
  - **Components** — modular building blocks of an Entity; all behavior (logic, chains of
    thought, memory operations) implemented as components.
  - **Engine** — the simulation loop; solicits actions from entities and delegates resolution
    to the Game Master (GM).
  - **Game Master (GM)** — inspired by tabletop RPGs; simulates the environment, translates
    agents' natural-language intended actions into concrete outcomes, may issue API calls to
    external tools/apps in digital environments.
- **What it guarantees re: determinism / ground truth (HIGH — by absence):** The README states
  **nothing** about determinism, reproducibility, or ground-truth guarantees. The GM
  adjudicates outcomes via LLM calls in natural language; there is no documented event ledger,
  content-addressed store, seeded canonical replay, or branchable-counterfactual primitive.
  Ground truth is whatever the GM narrates — it is a *generative* environment, not a
  provenance-tracked one. This is the central seam CHL differentiates on. (HIGH that docs are
  silent; MED that no such facility exists undocumented.)
- **Relevance to CHL:** Closest architectural cousin (GM + entity-components is a natural fit
  for CHL's engine/runner). But Concordia optimizes for *believable open-ended generation*,
  not *auditable shared truth under incentives*. No native evidence-provenance, no institutional
  intervention taxonomy, no mixed-incentive scoring.

---

## 2. GovSim — "Cooperate or Collapse"

- **Paper:** "Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM
  Agents" — **arXiv:2404.16698**, **NeurIPS 2024** (poster; neurips.cc/virtual/2024/poster/96895).
  (HIGH)
- **Authors:** Giorgio Piatti, Zhijing Jin, Max Kleiman-Weiner, Bernhard Schölkopf, Mrinmaya
  Sachan, Rada Mihalcea. (HIGH)
- **Repo:** `giorgiopiatti/GovSim` — https://github.com/giorgiopiatti/GovSim (HIGH). OpenReview:
  forum id `0zWzJj6lO3`. A reproducibility study exists (OpenReview `ON8EMrNwww`,
  "Understanding multi-agent LLM cooperation in the GovSim framework"). (MED)
- **Environment design (HIGH):** Common-pool-resource governance. **Three scenarios: fishery,
  pasture (sheep/grazing), pollution (factory).** Shared resource regenerates over time; agents
  must balance individual extraction against collective sustainability — a tragedy-of-the-commons
  social dilemma. Agents communicate in natural language between rounds.
- **Metrics (HIGH/MED):** **Survival time / survival rate** (does the resource persist to the
  horizon), total gain, equality/efficiency, and communication ablations. Headline result: only
  **2 of 45 instances** (15 LLMs × 3 scenarios) sustained the resource; **best sustainability
  rate below 54%**. "Universalization" prompting (Kantian "what if everyone did this") and
  successful multi-agent communication significantly improved survival. (HIGH)
- **Limitations (MED — from abstract framing, not a read limitations section):** Single dilemma
  family (CPR extraction); sustainability is the sole normative axis; no evidence/truth layer —
  agents negotiate *quantities*, not *contested facts*; determinism/replay not a design goal;
  outcomes bound to specific LLM snapshots.
- **Relevance to CHL:** Strongest conceptual sibling — it operationalizes the
  Tragic-Valley/collapse phenomenon in LLM agents and shows institutional-ish interventions
  (universalization, communication) shift the equilibrium. CHL generalizes the axis from
  *resource sustainability* to *epistemic accuracy* (shared truth), and adds provenance +
  replay + branchable counterfactuals that GovSim lacks.

---

## 3. SanctSim — "Corrupted by Reasoning"

- **Paper:** "Corrupted by Reasoning: Reasoning Language Models Become Free-Riders in Public
  Goods Games" — **arXiv:2506.23276** (v1 2025-06-29; v2 2025-07-24). OpenReview `kH6LOHGjEl`.
  (HIGH)
- **Authors:** David Guzman Piedrahita, Yongjin Yang, Mrinmaya Sachan, Giorgia Ramponi,
  Bernhard Schölkopf, Zhijing Jin. (HIGH)
- **Repo:** **`davidguzmanp/SanctSim`** — https://github.com/davidguzmanp/SanctSim (HIGH — this
  is the exact "SanctSim" system the task refers to; it is the code artifact of the
  "Corrupted by Reasoning" paper, not a separately named publication).
- **Environment design (HIGH):** A **public goods game with institutional choice**, adapted from
  behavioral economics (the classic Gürerk/Fehr "sanctioning vs sanction-free institution"
  paradigm). Each round agents choose between a **Sanctioning Institution (SI)** — members may
  reward/punish others based on contributions — and a **Sanction-Free Institution (SFI)** with
  no such mechanism. Repeated interaction over many rounds.
- **Metrics / findings (HIGH):** Cooperation/contribution levels, sorting into SI vs SFI,
  costly-punishment uptake, individual & collective payoff. Key result: **reasoning models (o1
  series) opt out of costly peer punishment and free-ride at higher rates, depressing both
  individual and collective payoffs**, while some non-reasoning models sustain high cooperation.
  Four behavioral patterns identified: sustained high cooperation, fluctuation, gradual decline,
  rigid strategy adherence. Failure mode is **institution-level, not authority-level**. (HIGH)
- **Limitations (MED):** Abstract-only reading — quantitative metrics and explicit limitations
  not fully extracted. Scalar contributions, not contested evidence; no provenance/replay layer.
- **Relevance to CHL:** Directly instantiates **peer punishment / sanctioning institutions** —
  one of CHL's "institutional interventions." Reinforces Chris's thesis motif that the
  *structure* of accountability (here institutional choice) drives collapse vs cooperation. CHL's
  novelty over it: pairwise-vs-aggregate accountability as a first-class manipulable, plus an
  epistemic (truth) payoff rather than a pure economic one.

---

## 4. Broader landscape (exact cites)

- **Melting Pot 2.0 (DeepMind).** "Melting Pot 2.0" tech report — **arXiv:2211.13746** (Oct
  2023); original: "Scalable Evaluation of Multi-Agent Reinforcement Learning with Melting Pot,"
  **arXiv:2107.06857** (ICML 2021). Repo `google-deepmind/meltingpot`. **>50 MARL substrates,
  256+ test scenarios**; evaluation protocol measures **generalization to novel social partners**
  across cooperation/competition/deception/reciprocation/trust. RL (not LLM) agents; pixel-based
  gridworld substrates; fully deterministic/reproducible substrates but no LLM epistemics, no
  provenance, no natural-language evidence. (HIGH cites; the reproducibility contrast is CHL's edge.)
- **Generative Agents (Park et al.).** "Generative Agents: Interactive Simulacra of Human
  Behavior," **UIST '23**; **arXiv:2304.03442**. Authors: Joon Sung Park, Joseph C. O'Brien,
  Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein. Repo
  `joonspk-research/generative_agents`. 25 agents in "Smallville"; architecture =
  **observation + planning + reflection over a natural-language memory stream**. Believability,
  not truth/incentives; information spreads (gossip) but is not provenance-tracked or scored for
  accuracy; no mixed-incentive payoff; determinism not a goal. (HIGH)
- **Playing Repeated Games with LLMs (Akata et al.).** **Nature Human Behaviour 9:1380–1390
  (2025)**, https://www.nature.com/articles/s41562-025-02172-y. Authors: Elif Akata, Lion
  Schulz, Julian Coda-Forno, et al. LLMs play finitely-repeated 2×2 games (iterated PD, Battle
  of the Sexes) vs each other / human-like strategies / humans. Finding: LLMs strong at
  self-interested PD-family, **suboptimal at coordination games**; behavior modulated by
  opponent info and a **"social chain-of-thought."** Pairwise 2-player, no population/institution
  layer, no evidence. Direct antecedent for CHL's PD lineage. (HIGH)
- **AgentBench (Liu et al.).** "AgentBench: Evaluating LLMs as Agents," **arXiv:2308.03688**,
  **ICLR 2024**. Repo `THUDM/AgentBench`. 8 environments (OS, DB, KG, digital card game, etc.),
  single-agent task competence — **not** multi-agent cooperation. Included as the "AgentBench-class
  eval" reference point: CHL is a population/social eval, orthogonal to single-agent capability
  benchmarks. (HIGH)
- **Adjacent 2025–2026 LLM cooperation/power work (MED cites, snippet-level):**
  - "Bosses, Kings, and the Commons: Cooperation Under Power Asymmetry in LLM Societies,"
    arXiv:2605.29062 — power asymmetry over a GovSim-like commons.
  - "Evaluating Cooperation in LLM Social Groups through Elected Leadership," arXiv:2604.11721.
  - "Reputation as a Solution to Cooperation Collapse in LLM-based MASs," arXiv:2505.05029 —
    reputation as an institutional lever (relevant to CHL's information structure).
  - "PAVE: A Cognitive Architecture for Legitimate Violation in Generative Agent Societies,"
    arXiv:2605.19351. "NetworkGames: … Personality-driven LLM Agents," arXiv:2511.21783 —
    cooperation on interaction *networks* (relevant to pairwise-vs-aggregate structure).
- **LLM epistemic commons / collaborative fact-finding (2025–2026, MED):**
  - "Multi-agent Systems for Misinformation Lifecycle: Detection, Correction and Source
    Identification," arXiv:2505.17511.
  - "LoCal: Logical and Causal Fact-Checking with LLM-Based Multi-Agents," ACM Web Conf 2025,
    doi:10.1145/3696410.3714748.
  - "The Deliberative Illusion: Diagnosing Factual Attrition and Stance Homogenization in
    Multi-Agent LLM Deliberation," arXiv:2606.03032 — **most CHL-adjacent**: multi-agent
    deliberation *loses* facts and homogenizes stance (a truth-collapse phenomenon; directly a
    Tragic-Valley-of-epistemics result).
  - "Goal-Aware Identification and Rectification of Misinformation in Multi-Agent Systems,"
    arXiv:2506.00509. These are *tool/architecture* papers (build a better fact-checker), NOT
    incentive-structure experiments — none treat truth-building as a mixed-incentive social
    dilemma with manipulable accountability structure. This is CHL's open lane.
- **Multi-agent prompt-injection / inter-agent security (MED):**
  - **"Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems,"
    arXiv:2410.07283** (Springer LNCS 978-3-032-16092-8_28) — malicious prompts **self-replicate
    across interconnected agents like a virus**; introduces data propagation + self-replication.
    Relevant to CHL's threat model: an adversary injecting false "evidence" that propagates
    through the agent population — a misinformation-dynamics attack vector CHL should be able to
    stage and measure.
  - Survey: "Prompt Injection Attacks in LLMs and AI Agent Systems," MDPI Information 17(1):54
    (2026). Google's **Agent2Agent (A2A) protocol** (2025) noted as expanding inter-agent attack
    surface.

---

## 5. Novelty matrix

Columns: RQ | Environment | Interaction structure | Information structure | Institutional
interventions | Evidence provenance | Reproducibility | Branchable counterfactuals | Metrics |
Major limitations. "—" = not present / not a design concern. Cells reflect documented behavior;
CHL row is *planned/claimed* and must be re-checked as it is built.

| System | Research question | Environment | Interaction structure | Information structure | Institutional interventions | Evidence provenance | Reproducibility | Branchable counterfactuals | Metrics | Major limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| **Concordia** (arXiv:2312.03664; v2.4.0 2026-03-06) | Can we build believable grounded generative ABMs? | Open, GM-narrated physical/social/digital space | GM-mediated; any topology the modeler scripts | Natural-language memory + GM narration | Modeler-scripted (no taxonomy) | — (GM narrates ground truth; no provenance) | **Silent** in docs; LLM+GM adjudication non-deterministic | — (no native branching primitive) | None built-in; modeler-defined | Not truth/incentive-focused; no auditable provenance or seeded replay |
| **GovSim** (arXiv:2404.16698, NeurIPS'24) | Do LLM societies sustainably govern a commons? | CPR: fishery/pasture/pollution, regenerating resource | Round-based, all-to-all NL communication | Shared public dialogue | Universalization prompt; communication on/off | — | Code released; LLM-snapshot bound, not seeded-canonical | — | Survival time/rate, gain, efficiency | One dilemma family; resource-only, no contested facts; no replay/branching |
| **SanctSim** (arXiv:2506.23276) | Do reasoning LLMs sustain cooperation under sanctioning institutions? | Public-goods game w/ institutional choice (SI vs SFI) | Repeated; agents sort into institutions, punish/reward peers | Contribution history observable | **SI vs SFI**, costly peer punishment/reward | — | Code (SanctSim repo); LLM-snapshot bound | — | Contribution, payoff, punishment uptake, institution sorting | Scalar contributions not evidence; economic not epistemic payoff; no provenance/replay |
| **Melting Pot 2.0** (arXiv:2211.13746) | Do MARL agents generalize to novel social partners? | 50+ gridworld substrates, 256+ scenarios | Spatial gridworld; mixed cooperation/competition | Pixel observations | Substrate rules (e.g. zapping/tagging) | — | **Deterministic, seeded, fully reproducible** substrates | — (scenario sets, not run branching) | Focal per-capita return, generalization scores | RL not LLM; no NL evidence/epistemics; no provenance |
| **Generative Agents** (UIST'23, arXiv:2304.03442) | Can LLM agents produce believable emergent social behavior? | Smallville sandbox (Sims-like) | Spatial proximity + NL conversation | Memory stream (obs/plan/reflect); gossip spreads | User intervention (ad hoc) | — (no accuracy tracking of spread info) | Not a goal; LLM-bound | — | Believability (human eval) | Believability not truth; no incentives, provenance, replay, or scoring |
| **Akata et al.** (Nat. Hum. Behav. 2025) | How do LLMs behave in repeated 2×2 games? | Iterated PD, Battle of the Sexes, etc. | **Pairwise, 2-player** repeated | Opponent-info + social CoT | — (game payoff only) | — | Model-bound experiments | — | Game score, cooperation rate, coordination success | 2-player only; no population/institution/evidence layer |
| **AgentBench** (arXiv:2308.03688, ICLR'24) | How capable are LLMs as single autonomous agents? | 8 task envs (OS/DB/KG/…) | **Single-agent** (no peers) | Task-local observations | — | — | Static benchmark, versioned | — | Task success per env | Single-agent capability, not cooperation/social/truth |
| **Deliberative Illusion** (arXiv:2606.03032) | Does multi-agent deliberation preserve facts? | Multi-agent LLM deliberation/debate | All-to-all debate rounds | Shared discussion | Debate protocol | — (measures factual attrition, no ledger) | Not designed for replay | — | Factual attrition, stance homogenization | Diagnostic study, not a manipulable-structure platform |
| **Prompt Infection** (arXiv:2410.07283) | Can injected prompts self-propagate across agents? | Multi-agent LLM system (tool-using) | Message-passing agent network | Inter-agent messages (attack channel) | — (adversarial, not governance) | — | Attack demonstration | — | Infection/propagation success | Security threat model, not cooperation/truth science |
| **Collaborative Hill Lab** (planned) | Which interaction/information/institutional structures move LLM-agent populations from the Tragic Valley to the Collaborative Hill in *building shared truth*? | **Evidence Commons** (contested claims + evidence under mixed incentives) | **Pairwise-targeted vs aggregate/neighbourhood accountability as a first-class manipulable** (carries the N-person PD finding) | Configurable observation policy (five-plane ScenarioSpec) | Taxonomy incl. pairwise reciprocity, diffuse punishment, sanctioning, reputation | **First-class provenance-tracked claims/evidence** | **Seeds + canonical JSON + event ledger + content-addressed stores → exact replay** | **Native branchable counterfactuals** off any run state | Epistemic accuracy + cooperation + collapse metrics (Tragic-Valley/Collaborative-Hill) | Planned/unbuilt; no code yet; claims unproven; LLM-snapshot sensitivity still applies |

---

## 6. Novelty assessment (honest)

**What is genuinely open / CHL-defensible (survives scrutiny):**
1. **Epistemic payoff as the social dilemma.** GovSim/SanctSim make agents fight over
   *quantities* (fish, contributions). No surveyed *incentive-structure* system makes the
   contested object **truth itself** with provenance-tracked evidence. The fact-checking
   multi-agent papers build tools; they do not manipulate accountability structure as an IV.
   "Deliberative Illusion" (2606.03032) shows the *phenomenon* (fact loss in deliberation) but
   is diagnostic, not a manipulable platform. **This is CHL's clearest novelty.** (MED-HIGH)
2. **Reproducibility stack as a first-class scientific instrument.** Seeded canonical replay +
   event ledger + content-addressed stores + **branchable counterfactuals** is essentially
   absent from the LLM-social-sim lineage (Concordia is *silent* on determinism; GovSim/SanctSim
   release code but are LLM-snapshot bound with no seeded-replay/branching primitive). Melting
   Pot has determinism but is RL, not LLM/epistemic. CHL combining LLM-agent social dilemmas
   *with* Melting-Pot-grade reproducibility + branching is novel. (HIGH — none of the surveyed
   LLM systems document branchable counterfactuals.)
3. **Pairwise-vs-aggregate accountability as the primary manipulated variable, ported to LLMs.**
   Akata is pairwise-only (no population); SanctSim manipulates institution *choice* not
   pairwise-vs-diffuse *targeting*; GovSim is all-to-all. Carrying Chris's specific
   RL/classical N-person-PD finding (targeted pairwise reciprocity vs diffuse punishment) into
   LLM populations over evidence is an untaken combination. (MED-HIGH)

**Where overlap is real — do NOT overclaim:**
- The *collapse phenomenon* ("Tragic Valley") is already demonstrated in LLM agents by GovSim
  and SanctSim; CHL cannot claim to be first to show LLM-cooperation collapse. Novelty is the
  *epistemic domain + reproducibility + accountability-structure IV*, not the phenomenon.
- GM/entity-component **architecture** is Concordia's, not new; CHL reuses a known pattern.
- "Universalization / communication / reputation / sanctioning improve cooperation" are already
  published levers (GovSim, arXiv:2505.05029, SanctSim). CHL's institutional-intervention menu
  overlaps these; the contribution is *systematic comparison under a truth objective with
  replay*, not the individual levers.
- Multi-agent misinformation propagation is staked out by Prompt Infection (2410.07283) on the
  security side; CHL's misinformation-dynamics angle must cite it, not reinvent it.

**Risks to the novelty claim:** (a) Concordia may add reproducibility features in a future
release (v2.4 already added "dynamic state editing" — check whether state snapshotting enables
branching before claiming uniqueness). (b) The 2606.03032 "Deliberative Illusion" line is
converging on the same epistemic-collapse territory fast; CHL's differentiator must stay the
*manipulable structure + reproducibility*, not merely "facts are lost in deliberation."

---

## 7. Source list (URL + access date 2026-07-13)

- Concordia repo/README/releases: https://github.com/google-deepmind/concordia ,
  https://github.com/google-deepmind/concordia/releases ; tech report arXiv:2312.03664
  (https://arxiv.org/abs/2312.03664), design pattern arXiv:2507.08892; v2.0 blog
  https://www.cooperativeai.com/post/google-deepmind-releases-concordia-library-v2-0
- GovSim: arXiv:2404.16698 (https://arxiv.org/abs/2404.16698); repo
  https://github.com/giorgiopiatti/GovSim ; NeurIPS poster
  https://neurips.cc/virtual/2024/poster/96895 ; OpenReview 0zWzJj6lO3, repro ON8EMrNwww
- SanctSim / Corrupted by Reasoning: arXiv:2506.23276 (https://arxiv.org/abs/2506.23276); repo
  https://github.com/davidguzmanp/SanctSim ; OpenReview kH6LOHGjEl
- Melting Pot: arXiv:2211.13746, arXiv:2107.06857; https://github.com/google-deepmind/meltingpot
- Generative Agents: arXiv:2304.03442; UIST'23 doi:10.1145/3586183.3606763;
  https://github.com/joonspk-research/generative_agents
- Akata et al.: https://www.nature.com/articles/s41562-025-02172-y (Nat. Hum. Behav. 9:1380–1390, 2025)
- AgentBench: arXiv:2308.03688; https://github.com/THUDM/AgentBench
- Deliberative Illusion: arXiv:2606.03032 ; Misinfo lifecycle: arXiv:2505.17511 ; LoCal
  doi:10.1145/3696410.3714748 ; Goal-Aware Rectification arXiv:2506.00509
- Prompt Infection: arXiv:2410.07283 (Springer LNCS 978-3-032-16092-8_28); MDPI Information
  17(1):54 (2026); Reputation-collapse arXiv:2505.05029; Power-asymmetry arXiv:2605.29062;
  Elected-leadership arXiv:2604.11721; NetworkGames arXiv:2511.21783

**Unreachable / not fully verified:** I did not open PDFs for Melting Pot, Generative Agents,
Akata, AgentBench, or the 2025-26 adjacent papers — cites are from arXiv-id/venue confirmation
via search + aggregators (MED). arXiv ids in the 2604–2606 range are surfaced by search but not
individually fetched; treat as MED and re-verify before formal citation. No fabricated sources.
