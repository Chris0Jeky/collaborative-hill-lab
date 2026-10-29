# Research Charter — Collaborative Hill Lab

**Status:** Foundation phase (T1 sandbox). **Date:** 2026-07-13.
**Implementation scope updated:** 2026-10-29 for Study 002, the incentive atlas and
the versioned seed/analysis contracts; the human-owned decisions in §8 are unchanged.
**Owner of scientific claims:** Chris (human). This charter is the standing scientific
contract; downstream design docs and studies inherit its definitions and operating
principles. It consolidates the Phase-0 discovery reports in `docs/research/_discovery/`
and is subordinate to `CLAUDE.md`/`AGENTS.md` on repo rules.

---

## 1. Mission

Build a reproducible laboratory for one question: **whether populations of LLM agents can
build shared truth under mixed incentives, and which interaction, information, and
institutional structures move them from a Tragic Valley of free-riding, misinformation, and
coordination failure to a Collaborative Hill of accurate, sustainable cooperation.**

The motivating legacy hypothesis is that targeted accountability can sustain
cooperation where diffuse responses fail. Study 000/002 show that its N-IPD
comparison also changes the reciprocity rule; the pattern is not a structure-only
effect. The lab tests that boundary before extending the question to LLM agents
reasoning over evidence, tools and conflicting information. The first environment is the
**Evidence Commons**. The lab is simultaneously a research platform, a benchmark, and an
agent-systems testbed; its distinguishing commitment is that every result is
hash-verifiably reproducible and every experimental structure is a first-class,
manipulable variable rather than an emergent accident of prompt wording.

---

## 2. Core research question (verbatim from `CLAUDE.md`)

> which interaction, information, and institutional structures move agent populations from
> the **Tragic Valley** (free-riding, misinformation, coordination failure) to the
> **Collaborative Hill** (accurate cooperation)

The load-bearing independent variable carried from the lineage is **the structure of
accountability**: whether an agent's cooperation or defection can be *targeted* back to it
by the agents it interacts with (pairwise/attributable) or is *diffused* into an aggregate
signal that obscures who contributed and who defected (neighbourhood/aggregate).

---

## 3. Definitions

**Tragic Valley.** A descriptive label for a low-cooperation outcome regime:
free-riding, unchallenged misinformation or degraded collective output. A claimed
welfare gap must be checked for the configured utilities; current Study 001 weights
fail collective stakes, and collective gains alone would not imply every agent benefits.
In the ideal N-IPD include-self pTFT model with `m` reciprocators, one fixed AllD
agent, a complete graph and zero exploration, expected cooperation follows
`E[c_t] = (m/(m+1)) E[c_(t−1)]`. This geometric decay is a property of that specified
rule. Quorum TFT can sustain cooperation on the same neighbourhood structure.
The metaphor is not a result about a particular Evidence Commons dataset or people.

**Collaborative Hill.** A descriptive label for sustained cooperation and useful
collective output. A concrete N-IPD example is zero-exploration targeted TFT against
one fixed AllD: reciprocal edges stay `(C,C)` while the defector is quarantined.
For N=3, after the initial round, each TFT earns `R + P` and AllD earns `2P` per
round. Linked TFT on that same pairwise structure collapses, so pairwise interaction
alone is insufficient. In Evidence Commons, accurate sustained cooperation under
responsive institutions is a research target, not an established effect of attribution.

**Evidence Commons.** The lab's first environment: an evidence-grounded commons in which
agents jointly assemble a briefing by proposing, verifying, challenging, and depending on
shared *claims* citing shared *evidence items*, under mixed incentives (contribution costs
effort; briefing quality pays out collectively; free-riding is individually tempting). Its
defining feature is that **verification checks provenance, not truth**: a well-cited piece of
misinformation passes verification, and that gap between provenance and veracity is precisely
the epistemics under study. Ground truth (each slot's true proposition, each item's
truth-alignment) is held by the world and never observable to agents. Implemented in
`src/collaborative_hill/domain/world/evidence_commons.py`; the institution plane
(`institutions.py`) crosses accountability ∈ {aggregate, attributable} with evidence-topology
∈ {private, shared_ledger} for the Study 001 2×2.

---

## 4. Intellectual lineage

The lab descends from Chris's N-person Prisoner's Dilemma work with Tcaci & Huyck
(*Navigating the N-Person Prisoner's Dilemma: From the Tragic Valley to the Collaborative
Hill*; the results source is the LaTeX draft `prisoners.tex`, a work-in-progress with visible
`undone` markers — see `LEGACY_AUDIT.md`). Its targeted-versus-pooled comparison
motivates a hypothesis about accountability. The legacy audit found implementation
defects and a change in policy semantics between conditions; it does not establish
a substrate-independent equilibrium theorem. Study 000 re-derives specified
algorithmic claims in the new kernel and includes policy controls; Study 002
extends those controls across thresholds, denominator conventions and composition.

The lab then asks whether related institutional interventions help **LLM agents
reasoning over evidence**, where cooperation concerns accurate shared output rather
than an abstract action. That transfer requires new evidence. Evidence Commons
provides an accountability axis and explicit information rules for testing it;
the scripted contributor/freerider controls do not themselves demonstrate a response
to attribution. The implementation is from scratch (Option C in `LEGACY_AUDIT.md`),
and hand-derived predictions, rather than the defective legacy artifacts, supply
the current numerical oracles.

---

## 5. The five-plane model

Every experiment is specified as a composition of five orthogonal planes. Separating them is
what makes a "structure" a manipulable variable rather than a hidden confound. (Architecture
rationale: `_discovery/architecture-stress.md` §4.)

**World plane.** The ground-truth substrate and its deterministic dynamics: the state that is
*true* independent of any agent's belief — the N-IPD payoff engine, or the Evidence Commons'
true propositions, evidence truth-alignment, budgets, and scoring. World state is written only
by the world-update step, is integer/`Fraction`-exact so it can be hashed, and is never
serialized to an agent. It is adjudicated exclusively by typed code, never by a model.

**Information plane.** What is *observable*, to whom, and when: the allow-list projection from
world state into per-agent observations. It is the firewall that makes the pairwise-vs-diffuse
contrast real — in N-IPD pairwise mode an agent sees each opponent's move *against it*, while in
neighbourhood mode it sees only the *count* of other cooperators. Truth fields physically do not
exist on observation objects, so they cannot leak even under naive serialization
(`_discovery/security-adversarial.md` §2). The information policy is mechanism, keyed on field
identities, never on narrative framing.

**Interaction plane.** Who acts with whom, in what topology, and in what order: pairwise
all-play-all bilateral games vs a single aggregate neighbourhood vote; sequential vs
simultaneous resolution; deterministic, integer-keyed turn order. This plane owns the structural
IV carried from the lineage.

**Institution plane.** The rules that constrain actions before resolution and react to outcomes
after: accountability (attributable vs aggregate credit and visibility), evidence topology, and
the deferred extension menu (reputation, sanctions, commitments, audits, approval gates —
`institutions.py`). Institutions read world ground truth through a read-only view and emit
institutional events without changing world truth. In v0, C3 checks that accountability
preserves briefing, quality and total utility for identical enumerated profiles within
each evidence topology. Evidence sharing changes available information. A new institution
requires its own invariance claim and tests; C3 is not a blanket guarantee for all extensions.

**Cognition plane.** The agents themselves: scripted policies (TFT variants, AllC, AllD,
free-rider, honest contributor) and LLM policies behind a provider adapter. Cognition sees
**only** observation objects — never world/institution internals or scored variables
(`act(Observation) -> ActionProposal` and nothing else). LLM sampling is explicitly *outside* the
deterministic hash chain: replay replays the recorded typed action, it does not re-query the
model (`_discovery/architecture-stress.md` §1). This plane is the only source of nondeterminism,
and it is quarantined behind the cognition firewall.

---

## 6. Locked operating principles

These are non-negotiable for the foundation phase; changing one requires an ADR.

1. **Models propose, typed code disposes.** Every state transition, payoff, acceptance, and
   verification outcome is computed by deterministic typed code. A model's free text is parsed
   into a typed action and never read back to decide an outcome. No LLM adjudicates world truth
   (contrast Concordia's GameMaster — `_discovery/architecture-stress.md` §5).
2. **World-truth / evidence / belief are physically separated.** Ground truth, the evidence
   record, and an agent's observation are distinct types; the observation type has no truth
   attribute to leak. One `observe`/`project_observation` chokepoint produces agent-facing views by
   explicit allow-list.
3. **Mechanism vs narrative.** The numbers (payoffs, thresholds, action schemas, information policy,
   seeds) live in the mechanism and are hashed; the prose "skin" is a pure render of mechanism state
   and is never read back into mechanics. Changing the skin preserves mechanism identity and
   fixed-action world transitions. Event-chain equality additionally holds run identity and
   narrative-bearing start metadata fixed; ordinary study runs can record distinct narrative identities.
4. **Event-sourced reproducibility.** Runs are append-only, hash-chained event ledgers over
   canonical JSON with integer/`Fraction`-exact scored quantities (no floats in hashed payloads).
   Seeds are derived by *identity*, not draw order, so adding an agent does not perturb others'
   streams. A run verifies by recomputing the chain head; branches share the parent prefix
   byte-for-byte (`_discovery/architecture-stress.md` §§1–2).
5. **Synthetic data only in the foundation phase.** The evidence corpus is synthetic and may contain
   adversarial prompt-injection fixtures *by design*, held as inert data. No real human-subject or
   participant data enters at T1; if it ever does, the `sensitive_data` overlay is flipped first
   (`CLAUDE.md`).
6. **No hidden chain-of-thought storage in the mechanism.** Raw prompts/completions and model
   metadata live in a separate, content-addressed transcript store referenced from *unhashed*
   metadata — never in the hashed mechanism chain, never routed into another agent's context. Audit
   is possible without coupling mechanism identity to prompt wording.
7. **AI-agent claims only.** Every result is a statement about the behaviour of *these models under
   these structures*, reported as action/payoff distributions. The lab makes **no** predictions about
   human behaviour and no mentalistic claim ("trust", "intent") outside an explicitly labelled
   interpretation section gated by a pre-registered claim boundary
   (`_discovery/methodology-stats.md` §5).

---

## 7. Scope and non-goals

**In scope (foundation phase):** the deterministic kernel (seeds, canonical JSON, event ledger,
content-addressed stores, checkpoints, branching); the five-plane domain (ScenarioSpec, mechanism,
skin, actions, evidence, claims, institutions); the engine (runner, replay, observation policy,
validators); scripted + LLM-adapter agents with a fake provider; metrics/manifests/study lifecycle;
Study 000 (legacy N-IPD reproduction / deconfounding) and Study 001 (Evidence Commons 2×2, draft).
The authorized 2026-10-29 extension adds Study 002's N=3/N=5 complete-graph sensitivity
experiment, a post hoc exact finite-population pTFT benchmark, the finite-strategy
incentive atlas, sealed factorial analysis and persistent verification. A further authorized
engineering slice adds observation-responsive EC controls, explicitly versioned local
graph N-IPD and configurable provider transport with mocked HTTP validation. These remain
exploratory scripted research and provider engineering, not a live LLM finding. The new
transport does not select a live model, budget or confirmatory design.

**Explicit non-goals now:** RL / Q-learning agents (the legacy QL claims are out of foundation
scope); large-N or general-network conclusions beyond the small declared graph controls;
real users or human-subject data; agent-controlled network/shell/filesystem tools inside an
episode; cryptographic authenticity/signing of ledgers
(integrity, not authenticity, is the T1 concern); production deployment or any external consumer.
Institutional levers beyond the Study-001 2×2 (reputation, sanctions, commitments) are *designed
but not built* until a study needs them (second-occurrence rule).

---

## 8. Human-owned decisions

The following are reserved to Chris and are never settled by an agent:

- The scientific claims and their framing (what "Tragic Valley"/"Collaborative Hill" assert).
- Final payoff/scoring weights and institution parameters (the ECParams defaults are provisional and
  marked HUMAN-OWNED in code; only the *dilemma property* is machine-checked, not the specific
  magnitudes).
- Hypotheses, primary outcomes, and the pre-registration for any confirmatory study; the
  exploratory/confirmatory split; the claim boundary on any positive result.
- Promotion of the repo tier (T1 → T2) and any change to the operating principles above.
- Which models/providers are in scope for a study, and acceptance that a study's cost ceiling binds.

These surface in the repo's human-action file and are walked via the `guided-walkthrough` skill when
they accumulate.

---

## 9. Success criteria for the foundation phase

The foundation is "done" when all of the following hold and are demonstrated by a passing check, not
asserted:

1. **Deterministic replay is hash-verified.** A run replays to a byte-identical event-chain head; a
   branch shares its parent's prefix byte-for-byte; the four trust-root singletons (`canon`,
   `derive_seed`, checkpoint-completeness, skin-invariance) have passing golden/property tests
   (`_discovery/architecture-stress.md` §7).
2. **The payoff oracle matches the hand-derived ground truth.** N=3 pairwise and neighbourhood
   payoff tables, the social-dilemma inequalities, and the 2TFT+1AllD mechanism (quarantine vs
   geometric collapse) are asserted against literal hand-derived values — never derived from the code
   under test (`_discovery/mechanism-math-review.md` §§2,6).
3. **The truth/observation boundary holds.** Canary tests find no truth field in any observation,
   prompt, or shared transcript; the capability chokepoint is the sole mutation path; citations
   outside an agent's visible set earn zero credit (`_discovery/security-adversarial.md` §§2–3).
4. **Study 000 exposes the structure/strategy confound.** Named TFT variants
   (per-opponent, linked, probabilistic and threshold) have explicit decision rules.
   The observed legacy comparison depends on both structure and policy; it does not
   identify a structure-only causal effect. Study 002 checks threshold, denominator and
   composition sensitivity without erasing those policy differences
   (`LEGACY_AUDIT.md` and `../../studies/002-nipd-sensitivity/README.md`).
5. **Methodology rails are in place.** Analysis uses episode-level outcomes from
   independently seeded episodes or declared paired blocks, with explicit seed protocols
   and recorded model metadata. Original studies use independent streams;
   declared `paired-policy-v2` drafts pair kernel policy streams within blocks but do not
   pair LLM-provider sampling. Paired resampling uses complete `(scenario_block, replicate)`
   blocks; cells within a block are not independent replicates. Effect sizes receive
   intervals where the design supports them; exact deterministic controls and zero-variance
   samples are handled explicitly.
   Exploratory/confirmatory scope remains part of the study lifecycle (ADR-0008 and the
   draft SAP).
6. **Study 001 is a runnable draft** whose enumerated certificate finds free-riding temptation
   (C1) but fails collective stakes (C2) at the configured parameters: the social dilemma is
   not certified. Accountability intervention integrity (C3) passes for identical profiles.

Honest boundary: the foundation phase certifies the *instrument*, not the *finding*. Numeric
reproduction of the legacy headline percentages and any confirmatory LLM result are downstream of a
Study-000/Study-001 *run* and are not claimed here.
