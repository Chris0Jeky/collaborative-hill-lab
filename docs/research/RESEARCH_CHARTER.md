# Research Charter — Collaborative Hill Lab

**Status:** Foundation phase (T1 sandbox). **Date:** 2026-07-13.
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

The lab carries Chris's N-person Prisoner's Dilemma finding — *targeted pairwise
accountability breeds reciprocity; diffuse aggregate punishment breeds the valley* — from
classical and reinforcement-learning agents to LLM agents that must reason over evidence,
tools, and conflicting information toward a shared output. The first environment is the
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

**Tragic Valley.** The region of a population's structural parameter space in which
cooperation collapses to a low fixed point: agents free-ride, misinformation persists
unchallenged, and collective output degrades even though every agent would be better off
under mutual cooperation. In the N-IPD micro-mechanism this is the geometric decay of
cooperation under diffuse (neighbourhood) accountability, where a single defector poisons
the shared signal that all reciprocators depend on (mechanism review §3.3: expected
cooperation ratio contracts as `q_r = (m/(m+1))·q_{r-1} → 0` for `m` reciprocators plus one
defector). In the Evidence Commons it is the regime where free-riding dominates and the
sealed briefing carries wrong or unsupported claims. The term is Tcaci & Huyck's metaphor
for a low-cooperation region of parameter space, adopted here as a defined outcome regime,
not a claim about any specific dataset.

**Collaborative Hill.** The complementary region in which cooperation is sustained at a high
fixed point: reciprocators can identify and reward each other and quarantine defectors, so
accurate collective output persists. In the N-IPD this is the pairwise regime where the
TFT–TFT relationship is an absorbing `(C,C)` state and a lone defector is confined to its own
edges (mechanism review §3.2: each reciprocator earns `R + P` per round while the defector
is quarantined to `2P`). In the Evidence Commons it is the regime where attributable peer
review sustains truthful, well-provenanced claims.

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
`undone` markers — see `LEGACY_AUDIT.md`). That work established, in classical and RL agents,
that **the geometry of retaliation determines the equilibrium**: reciprocity conditioned on a
*per-partner* signal (pairwise TFT) sustains cooperation, while reciprocity conditioned on a
*pooled scalar* signal (probabilistic/neighbourhood TFT) collapses to universal defection.
This is a statement about *structure*, independent of the substrate.

The lab transfers that structural claim to a qualitatively harder substrate — **LLM agents
reasoning over evidence** — where the object of cooperation is not an abstract "cooperate"
token but the construction of *accurate shared truth* under conflicting information. The
transfer is deliberate and bounded: the N-IPD is retained as a micro-mechanism
(`world/nipd.py`) so the lineage result can be re-derived and metamorphically checked in the
new kernel, and the Evidence Commons generalizes the same accountability axis (targeted vs
diffuse) from an abstract payoff to an epistemic one. The lab does **not** inherit any legacy
code; it is a from-scratch reimplementation (Option C — see `LEGACY_AUDIT.md` §"What Study 000
does"), keeping legacy only as an external oracle for cross-checks.

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
institutional events; they never mutate world truth and never change the legal action set or the
payoff totals for identical behaviour — they change *who is seen* and *who is credited*.

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
   and is never read back into mechanics. Permuting the skin must not change any mechanism or event
   hash of a fixed-action replay.
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

**Explicit non-goals now:** RL / Q-learning agents (the legacy QL claims are out of foundation
scope); large-N and network-topology sweeps beyond N=3; real users or human-subject data; live
network/shell/filesystem tools inside an episode; cryptographic authenticity/signing of ledgers
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
4. **Study 000 deconfounds structure from strategy.** Named TFT variants (per-opponent vs
   probabilistic vs threshold) are held explicitly distinct, so the Hill-vs-Valley contrast is
   attributable to interaction structure and not to a silently-swapped decision rule
   (`LEGACY_AUDIT.md` §"TFT-semantics confound").
5. **Methodology rails are in place.** Episode-level unit of analysis, CRN-paired scenario seeds, full
   seed/model provenance in a run manifest, effect sizes with intervals, and an
   exploratory/confirmatory split are wired into the study lifecycle
   (`_discovery/methodology-stats.md` §2).
6. **Study 001 is a runnable draft** whose mechanism certificate proves the Evidence Commons is a
   social dilemma by enumeration at the configured parameters, with the 2×2 institution design
   changing only attribution/visibility and not the task.

Honest boundary: the foundation phase certifies the *instrument*, not the *finding*. Numeric
reproduction of the legacy headline percentages and any confirmatory LLM result are downstream of a
Study-000/Study-001 *run* and are not claimed here.
