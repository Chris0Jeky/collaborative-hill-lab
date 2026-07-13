# Related Work — Collaborative Hill Lab

**Status:** Foundation-phase discovery consolidation. **Access date for all web sources:**
2026-07-13. Consolidates `_discovery/related-work.md`.

**Confidence legend:** HIGH = confirmed from the primary artifact (arXiv abstract/PDF, repo
README, releases page); MED = confirmed from a single secondary/aggregator or a primary source
whose relevant detail was not read line-by-line; LOW = inferred / not directly verified.

**Method note.** Sources were confirmed from arXiv abstract pages, GitHub READMEs/releases, and
publisher pages, cross-checked against search snippets. No surveyed system was cloned or run;
architecture and reproducibility claims come from documentation, not from executing code. Where a
system's docs are silent on a property (e.g. Concordia determinism), this document says "silent"
rather than asserting absence. **Unverified identifiers are flagged inline and must be re-verified
before any formal citation.**

---

## 1. Concordia (Google DeepMind)

**What it is.** A generative agent-based-modelling library: LLM-driven "generative agents" acting in
an open-ended environment narrated by a Game Master.

**Primary sources.** Repo `google-deepmind/concordia`
(https://github.com/google-deepmind/concordia); PyPI `gdm-concordia`; latest release **v2.4.0,
2026-03-06** (releases page; recent tags v2.3.1/v2.3.0 2026-02-04, v2.2.0 2026-01-12, v2.1.0
2025-08-18). Tech report: *Generative agent-based modeling with actions grounded in physical,
social, or digital space using Concordia*, **arXiv:2312.03664** (Dec 2023). Design-pattern paper:
*Concordia Design Pattern*, **arXiv:2507.08892** (Jul 2025) — documents the Entity/Component/Engine
redesign (MED — id from README extraction).

**Architecture (HIGH from README).** Four core concepts: **Entities** (actors — player-character
Agents or system-controller Game Masters); **Components** (modular building blocks of an entity; all
behaviour — logic, chains of thought, memory ops — is a component); **Engine** (the simulation loop,
`Sequential` or `Simultaneous`, that solicits actions and delegates resolution); **Game Master (GM)**
(a tabletop-RPG-inspired entity that simulates the environment and translates agents' natural-language
intended actions into concrete outcomes, possibly issuing tool calls). Resolution happens inside a GM
component's `pre_act()` that parses free-text LLM output; checkpointing is via component
`get_state()/set_state()`.

**What it does / does not guarantee.** The README states **nothing** about determinism,
reproducibility, or ground-truth guarantees; there is no documented event ledger, content-addressed
store, seeded canonical replay, or branchable-counterfactual primitive. **Ground truth is whatever the
GM narrates** — a generative, not provenance-tracked, environment (HIGH that docs are silent; MED that
no such undocumented facility exists).

**Relation to CHL.** Concordia is CHL's closest *architectural* cousin (GM + entity-components maps
onto CHL's engine/runner), but it optimizes for *believable open-ended generation*, not *auditable
shared truth under incentives*. CHL deliberately inverts the GM: no LLM adjudicates world truth (see
`RESEARCH_CHARTER.md` §6.1). Concordia is a candidate **cognition/skin adapter** behind CHL's
observation firewall, pinned to a commit — never a scoring substrate
(`_discovery/architecture-stress.md` §5).

---

## 2. GovSim — *Cooperate or Collapse*

**What it is.** A common-pool-resource governance simulation for societies of LLM agents.

**Primary sources.** *Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM
Agents*, **arXiv:2404.16698**, **NeurIPS 2024** (poster). Authors: Giorgio Piatti, Zhijing Jin, Max
Kleiman-Weiner, Bernhard Schölkopf, Mrinmaya Sachan, Rada Mihalcea. Repo `giorgiopiatti/GovSim`. A
reproducibility study exists (OpenReview `ON8EMrNwww`) (MED).

**Architecture / environment (HIGH).** Three CPR scenarios — **fishery, pasture (sheep/grazing),
pollution (factory)** — over a shared resource that regenerates each round; agents balance individual
extraction against collective sustainability and communicate in natural language between rounds.

**Metrics / findings (HIGH/MED).** Survival time/rate (does the resource persist to the horizon),
total gain, equality/efficiency, communication ablations. Headline: only **2 of 45 instances** (15
LLMs × 3 scenarios) sustained the resource; best sustainability rate below 54%. "Universalization"
prompting and successful multi-agent communication significantly improved survival.

**What it does not guarantee.** Single dilemma family (CPR extraction); sustainability is the sole
normative axis; **no evidence/truth layer** — agents negotiate *quantities*, not *contested facts*;
determinism/replay are not design goals; outcomes are bound to specific LLM snapshots (MED, from
abstract framing).

**Relation to CHL.** CHL's strongest conceptual sibling: it operationalizes the Tragic-Valley collapse
phenomenon in LLM agents and shows institution-ish interventions shift the equilibrium. CHL
generalizes the contested object from *resource quantity* to *epistemic accuracy* and adds provenance
+ replay + branching that GovSim lacks.

---

## 3. SanctSim — *Corrupted by Reasoning*

**What it is.** A public-goods game with institutional choice (sanctioning vs sanction-free), for LLM
agents; the code artifact of the "Corrupted by Reasoning" paper.

**Primary sources.** *Corrupted by Reasoning: Reasoning Language Models Become Free-Riders in Public
Goods Games*, **arXiv:2506.23276** (v1 2025-06-29, v2 2025-07-24), OpenReview `kH6LOHGjEl`. Authors:
David Guzman Piedrahita, Yongjin Yang, Mrinmaya Sachan, Giorgia Ramponi, Bernhard Schölkopf, Zhijing
Jin. Repo **`davidguzmanp/SanctSim`** (https://github.com/davidguzmanp/SanctSim) — this repo, paired
with arXiv:2506.23276, is the "SanctSim" system referenced here; it is a code artifact, not a
separately titled publication (HIGH).

**Architecture / environment (HIGH).** A public-goods game with institutional choice adapted from the
Gürerk/Fehr sanctioning paradigm: each round agents choose between a **Sanctioning Institution (SI)**
(members may reward/punish based on contributions) and a **Sanction-Free Institution (SFI)**; repeated
over many rounds.

**Metrics / findings (HIGH).** Contribution levels, SI-vs-SFI sorting, costly-punishment uptake,
individual and collective payoff. Key result: **reasoning models (o1 series) opt out of costly peer
punishment and free-ride at higher rates**, depressing both individual and collective payoffs, while
some non-reasoning models sustain high cooperation. Four behavioural patterns identified (sustained
cooperation, fluctuation, gradual decline, rigid adherence); the failure mode is **institution-level,
not authority-level**.

**What it does not guarantee.** Scalar contributions, not contested evidence; an economic, not
epistemic, payoff; no provenance/replay layer; LLM-snapshot bound (MED — abstract-level reading).

**Relation to CHL.** Directly instantiates **peer punishment / sanctioning institutions**, one entry
in CHL's deferred institution menu (`institutions.py`), and reinforces the lineage motif that the
*structure* of accountability drives collapse vs cooperation. CHL's differentiators: pairwise-vs-
aggregate *targeting* as a first-class IV (not institution *choice*), plus an epistemic payoff.

---

## 4. Melting Pot 2.0 (Google DeepMind)

**What it is.** A MARL evaluation suite of gridworld social-dilemma substrates.

**Primary sources.** *Melting Pot 2.0*, **arXiv:2211.13746** (Oct 2023); original *Scalable Evaluation
of Multi-Agent Reinforcement Learning with Melting Pot*, **arXiv:2107.06857** (ICML 2021). Repo
`google-deepmind/meltingpot`. **>50 MARL substrates, 256+ test scenarios**; the protocol measures
**generalization to novel social partners** across cooperation/competition/deception/reciprocation/
trust axes.

**What it guarantees / does not.** **Deterministic, seeded, fully reproducible** pixel-based
substrates — the reproducibility bar CHL aims to match. But the agents are **RL, not LLM**; there is
no natural-language evidence, no epistemics, and no provenance layer; scenario *sets* are the
generalization instrument, not run *branching* (HIGH cites).

**Relation to CHL.** The reproducibility contrast is CHL's edge: CHL seeks Melting-Pot-grade
determinism *combined with* LLM-agent social dilemmas over evidence — a combination absent from the
LLM-social-sim lineage.

---

## 5. Generative Agents (Park et al.)

**What it is.** 25 LLM agents in a Sims-like sandbox ("Smallville") exhibiting emergent believable
social behaviour.

**Primary sources.** *Generative Agents: Interactive Simulacra of Human Behavior*, **UIST '23**
(doi:10.1145/3586183.3606763), **arXiv:2304.03442**. Authors: Joon Sung Park, Joseph C. O'Brien,
Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein. Repo
`joonspk-research/generative_agents`.

**Architecture (HIGH).** Observation + planning + reflection over a natural-language **memory stream**;
information spreads through the population as gossip.

**What it does not guarantee.** Optimizes **believability**, not truth or incentives; spread
information is not provenance-tracked or scored for accuracy; no mixed-incentive payoff; determinism
is not a goal (HIGH).

**Relation to CHL.** Antecedent for *information propagation through an agent population*, but with no
accuracy scoring, incentives, provenance, or replay — exactly the layers CHL adds.

---

## 6. Akata et al. — repeated games with LLMs

**What it is.** A behavioural study of LLMs playing finitely-repeated 2×2 games.

**Primary sources.** *Playing repeated games with large language models*, **Nature Human Behaviour
9:1380–1390 (2025)** (https://www.nature.com/articles/s41562-025-02172-y). Authors: Elif Akata, Lion
Schulz, Julian Coda-Forno, et al.

**Findings (HIGH).** LLMs play iterated PD and Battle-of-the-Sexes against each other, human-like
strategies, and humans; they are strong at self-interested PD-family play but **suboptimal at
coordination games**, with behaviour modulated by opponent information and a "social chain-of-thought."

**What it does not cover.** Pairwise 2-player only; **no population, institution, or evidence layer**;
model-bound experiments.

**Relation to CHL.** The direct LLM-era antecedent of CHL's PD lineage — it establishes that LLMs
carry PD-relevant behaviour — but stops at the 2-player game. CHL scales to N-agent populations, adds
the accountability-structure IV, and moves the object of play to contested evidence.

---

## 7. AgentBench (Liu et al.)

**What it is.** A benchmark of LLMs as single autonomous agents across 8 task environments.

**Primary sources.** *AgentBench: Evaluating LLMs as Agents*, **arXiv:2308.03688**, **ICLR 2024**.
Repo `THUDM/AgentBench`. Environments: OS, DB, knowledge graph, digital card game, etc.; single-agent
task competence.

**What it does not cover.** Not multi-agent, not cooperation, not social/epistemic — a single-agent
capability benchmark (HIGH).

**Relation to CHL.** The "AgentBench-class eval" reference point: CHL is a population/social eval,
orthogonal to single-agent capability benchmarks. Cited to place CHL on the map, not as a sibling.

---

## 8. Broader / adjacent landscape

- **Deliberative Illusion.** *The Deliberative Illusion: Diagnosing Factual Attrition and Stance
  Homogenization in Multi-Agent LLM Deliberation*, **arXiv:2606.03032** — **⚠ id in the 2604–2606
  range surfaced via search but not individually fetched; re-verify before formal citation.** The most
  CHL-adjacent finding: multi-agent deliberation *loses facts* and homogenizes stance — a
  truth-collapse (a "Tragic Valley of epistemics"). Diagnostic, not a manipulable-structure platform;
  CHL's differentiator over it is manipulable structure + reproducibility.
- **Prompt Infection.** *Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems*,
  **arXiv:2410.07283** (Springer LNCS 978-3-032-16092-8_28). Malicious prompts **self-replicate across
  interconnected agents like a virus**. CHL must cite it for the misinformation-propagation threat
  vector (an adversary injecting false "evidence" that spreads), not reinvent it. Related survey:
  *Prompt Injection Attacks in LLMs and AI Agent Systems*, MDPI Information 17(1):54 (2026); Google's
  Agent2Agent (A2A) protocol (2025) noted as expanding the inter-agent attack surface (MED).
- **LLM epistemic-commons / fact-finding tooling (MED).** *Multi-agent Systems for Misinformation
  Lifecycle* (arXiv:2505.17511); *LoCal: Logical and Causal Fact-Checking with LLM-Based Multi-Agents*
  (ACM Web Conf 2025, doi:10.1145/3696410.3714748); *Goal-Aware Identification and Rectification of
  Misinformation in Multi-Agent Systems* (arXiv:2506.00509). These build better fact-checkers; **none
  treats truth-building as a mixed-incentive social dilemma with a manipulable accountability
  structure** — CHL's open lane.
- **Cooperation-structure / institution levers (MED).** *Reputation as a Solution to Cooperation
  Collapse in LLM-based MASs* (arXiv:2505.05029); *Bosses, Kings, and the Commons: Cooperation Under
  Power Asymmetry in LLM Societies* (**arXiv:2605.29062 — ⚠ re-verify id**); *Evaluating Cooperation
  in LLM Social Groups through Elected Leadership* (**arXiv:2604.11721 — ⚠ re-verify id**);
  *NetworkGames: Personality-driven LLM Agents* (arXiv:2511.21783, cooperation on interaction networks
  — relevant to pairwise-vs-aggregate structure); *PAVE: A Cognitive Architecture for Legitimate
  Violation in Generative Agent Societies* (arXiv:2605.19351 — ⚠ re-verify id). These stake out
  reputation, power, leadership, and network-structure levers CHL's institution menu overlaps; CHL's
  contribution is *systematic comparison under a truth objective with replay*, not the individual
  levers.

**Unverified identifiers (do not formally cite until re-checked):** arXiv:2606.03032, 2605.29062,
2604.11721, 2605.19351 — surfaced by search in the 2604–2606 range but not individually fetched.
PDFs for Melting Pot, Generative Agents, Akata, and AgentBench were not opened; those cites rest on
arXiv-id/venue confirmation via search + aggregators (MED). No fabricated sources.

---

## 9. Source list (URL + access date 2026-07-13)

- Concordia: https://github.com/google-deepmind/concordia ,
  https://github.com/google-deepmind/concordia/releases ; arXiv:2312.03664 ; arXiv:2507.08892 ; v2.0
  blog https://www.cooperativeai.com/post/google-deepmind-releases-concordia-library-v2-0
- GovSim: arXiv:2404.16698 ; https://github.com/giorgiopiatti/GovSim ;
  https://neurips.cc/virtual/2024/poster/96895 ; OpenReview 0zWzJj6lO3, repro ON8EMrNwww
- SanctSim: arXiv:2506.23276 ; https://github.com/davidguzmanp/SanctSim ; OpenReview kH6LOHGjEl
- Melting Pot: arXiv:2211.13746 ; arXiv:2107.06857 ; https://github.com/google-deepmind/meltingpot
- Generative Agents: arXiv:2304.03442 ; UIST'23 doi:10.1145/3586183.3606763 ;
  https://github.com/joonspk-research/generative_agents
- Akata et al.: https://www.nature.com/articles/s41562-025-02172-y (Nat. Hum. Behav. 9:1380–1390, 2025)
- AgentBench: arXiv:2308.03688 ; https://github.com/THUDM/AgentBench
- Deliberative Illusion: arXiv:2606.03032 (⚠) ; Misinfo lifecycle arXiv:2505.17511 ; LoCal
  doi:10.1145/3696410.3714748 ; Goal-Aware Rectification arXiv:2506.00509
- Prompt Infection: arXiv:2410.07283 (Springer LNCS 978-3-032-16092-8_28) ; MDPI Information 17(1):54
  (2026) ; Reputation-collapse arXiv:2505.05029 ; Power-asymmetry arXiv:2605.29062 (⚠) ;
  Elected-leadership arXiv:2604.11721 (⚠) ; NetworkGames arXiv:2511.21783 ; PAVE arXiv:2605.19351 (⚠)
