# Claims and Limitations — Collaborative Hill Lab

The scope contract for what the platform's outputs do and do not license. Each study
states its own claim boundary; a confirmatory preregistration must restate it. This
document is the standing cross-study boundary, updated 2026-10-29. It reflects legacy
N-IPD, the separately versioned local graph world, **Evidence Commons v0**, its
observation-responsive policy baseline, and optional provider transport. All current
measured scientific results use scripted agents and synthetic inputs; transport tests use
mocked responses. No live provider pilot is claimed.

---

## 1. What the platform CAN claim

1. **Properties of agent populations under configured mechanisms.** For a specified model (or
   scripted policy set), environment, and institution, the lab measures behavioural and
   epistemic outcomes — briefing quality (`accepted_correct − accepted_incorrect`),
   contribution/verification rates, free-rider advantage, payoff inequality — with episode-level
   uncertainty where estimable, or exact deterministic checks. A future measured claim
   could take the form: "under model M, in Evidence Commons at N=3, mechanism A
   (`attributable`) produced higher briefing quality than mechanism B (`aggregate`), effect
   size E with 95% CI, at this scale."

2. **Reproducible, content-addressed comparisons.** Sealed events and manifests record
   scenario/mechanism/narrative/evidence identities, seed paths and available code, dependency
   and provider metadata. Given the same inputs, code, seed protocol, run identity and start
   metadata, the deterministic replay checks reproduce the event chain. Metadata supports
   audit but does not authenticate executable code or a provider's internal sampling.
   Unavailable provenance remains unavailable; a source label alone is not a full source snapshot.

3. **Controlled institutional comparisons.** The Study 001 C3 enumeration checks that
   changing aggregate to attributable accountability preserves briefing, quality and total
   utility for identical tested contributor/freerider profiles, within each evidence topology.
   This is a bounded same-behavior integrity check, not proof of a behavioral causal effect
   or an invariance claim across evidence topologies or arbitrary policies. Institution
   configuration **is included** in `mechanism_hash`; narrative skin is excluded. Causal
   interpretation additionally needs comparable non-treatment settings and a valid design.
   See [the analysis contract](ANALYSIS_INPUT_VALIDATION.md),
   [mechanism projection](../../src/collaborative_hill/experiments/scenario.py) and
   [certificate](../../studies/001-evidence-commons/certificate.py).

4. **Mechanism-invariance of narrative skins (scripted).** Swapping a `NarrativeSkin`
   preserves the mechanism identity and scripted world transitions. The metamorphic test
   also proves identical event chains when run identity is held fixed and narrative-bearing
   start metadata is omitted. A full study run may record different narrative identities in
   its start metadata, so it need not have the same chain head. This check does not establish
   skin-invariant LLM behavior. See [the exact test contract](../../tests/metamorphic/test_skin_isolation.py).

5. **Comparative, not absolute, readings.** The lab compares mechanisms and models against
   each other and against analytical/scripted baselines whose behaviour is known in closed
   form (the hand-derived payoff tables; the enumerated incentive checks, which do not
   certify a social dilemma for Study 001's current parameters because C2 fails).

6. **A bounded observation-responsive institutional effect.** The separate
   [responsive EC experiment](../../experiments/responsive-commons/RESULTS.md) fixes N=3,
   12 rounds, two corpora, two institutional axes, five active-policy rules and all eight
   labeled active/freerider profiles. Its 320 deterministic episodes yield 160 matched
   attributable-minus-aggregate quality contrasts: 2 positive, 2 negative and 156 zero. All 160
   controlled action replays preserve briefing, effort, quality and total utility.
   The effect is specific to visible contribution history and this finite design;
   the counts are not population probabilities. C1/C2 diagnostics over the two designated
   strategies are separate from adaptive behavior and fixed-action C3 integrity.

7. **Explicit graph contracts and controls.** The new `nipd_graph` world exposes only local
   interactions, uses canonical undirected adjacency and requires sum/mean payoff
   aggregation. Hand-derived ring/star/isolate tests and legacy complete-graph controls
   check those semantics. The [18-condition design](../../experiments/graph-topology/README.md)
   holds N, defector count, horizon and mean payoff fixed while separating topology,
   reciprocity rule and defector placement. The [recorded results](../../experiments/graph-topology/RESULTS.md)
   match all 18 pre-execution cooperation curves, with every sealed episode replayed.
   Those exact finite controls establish no universal topology benefit or independent
   replication from symmetry-equivalent seats.

---

## 2. What the platform CANNOT claim

1. **Human behaviour.** Agents are LLMs and scripts. No result predicts, models, or
   generalises to human cooperation, human institutions, or human epistemics.

2. **Policy recommendations.** Nothing here licenses real-world institutional or governance
   recommendations. The mapping from a synthetic commons to any real organisation is
   unvalidated and out of scope.

3. **Provider-general conclusions from one model.** A single model's behaviour is that
   model's behaviour. Cross-provider or "LLMs in general" statements require multiple models
   run under the same design and are out of scope for any single-model study.

4. **Absolute alignment / trustworthiness / honesty.** The lab measures behaviour under
   configured incentives, not a model's disposition. "Model M cooperated more under
   attributable accountability" is **not** "model M is aligned/honest/trustworthy." Absolute
   safety or alignment claims are outside the platform's evidentiary reach.

5. **Cognition or intent.** Outcomes are typed actions, payoffs and environment metrics. Mentalistic
   language ("trust," "reciprocity," "intent") is interpretation, permitted only in a labelled
   section and only after an effect is shown mechanism-linked (survives re-skinning for LLM
   agents). Replay reproduces *actions*, not *minds* (§3.6).

---

## 3. Current known limitations (v0, honest enumeration)

1. **Verification is engine-adjudicated provenance-checking — agents cannot lie in
   verification.** `_adjudicate_verification` is deterministic typed code: a verification is
   `supported` iff a cited item is accessible, fresh, supporting, and matches the claim's
   slot/proposition. The *verifier agent does not report an outcome*; the engine computes it.
   So an agent cannot submit a dishonest verification — **deception in verification is not
   modelled in v0** and is explicit future work. What v0 *does* capture is
   provenance-vs-truth divergence: well-cited misinformation passes verification (provenance
   holds) yet scores as incorrect (truth fails).

2. **Acceptance is a mechanical net-support rule.** A claim is accepted iff
   `net_support = supported_verifications − valid_challenges ≥ 1`, highest wins, ties to
   earliest (`final_briefing`). There is no deliberation, negotiation, or judgement in
   acceptance. `ApproveClaimAction` exists in the action union but is **not legal in v0** (a
   documented v1 extension point).

3. **Scripted personas are not learned strategies.** The scripted policies
   (`ec_contributor`, `ec_freerider`, `ec_verifier`, `ec_misinformer`,
   `ec_conditional_contributor`, and the global/local N-IPD families) are hand-specified
   observation-driven rules without learned parameters or hidden policy state. The legacy
   contributor/freerider pair ignores attribution and monetary weights. The conditional
   contributor can change behavior when identities make more distinct contributors visible,
   but does not respond to utility coefficients, truth or evidence quality. Its cumulative
   signal counts proposals and verification attempts, not current willingness or accuracy.
   These controls are not claimed to be optimal, representative or performance bounds.

4. **Small N and declared composition.** Current Evidence Commons fixtures use N=3;
   the N-IPD studies cover N=3 and N=5 complete graphs, and the graph controls use N=5
   complete/ring/star layouts. Findings are specific to the
   declared population and policy mixture. These unfrozen exploratory designs are not
   confirmatory preregistrations. Increasing N while retaining one defector also changes
   its population fraction; Study 002 includes a two-defector control to expose that issue.

5. **Single-episode credit model.** Credit and scoring are computed within one episode at
   seal (`final_rewards`). There is no cross-episode reputation, memory, or carryover — an
   agent starts each episode fresh. Repeated-game reputation dynamics are not modelled.

6. **LLM cognition is not reproduced by the engine; replay covers recorded actions.**
   Provider seed and temperature settings do not establish kernel-controlled randomness.
   No live endpoint, billing behavior or provider determinism has been verified.
   Replay (`agents/replay.py`) reproduces the
   *recorded actions* and re-derives the identical sealed ledger, but it does **not**
   reproduce the model's internal computation. An LLM run is reproducible as a *record*, not
   as a *cognitive process*.

7. **Narrative-skin behavior is checked for scripted agents only.** The metamorphic
   guarantees have the identity/metadata qualifications in §1.4. LLM agents read the skin
   and may change their decisions; LLM skin robustness is a measurement target, not a result.

8. **PD-literature contamination risk for LLM agents.** Models likely recognise the
   Prisoner's Dilemma, tragedy-of-the-commons, TFT, and Axelrod from training data and may
   role-play the textbook answer rather than reason from the presented payoffs. Neutral skins
   and (future) scrambled-incentive controls mitigate this, but for LLM agents recall-vs-
   reasoning is an unresolved confound. Scripted baselines are immune (no cognition).

9. **No sanctions, reputation, commitments or approval institutions inside episodes.** `InstitutionConfig`
   implements exactly two axes (accountability × evidence_topology). Sanctions, reputation
   scores, commitments, and approval gates are documented extension points, deliberately
   unimplemented. Claims about those mechanisms are out of
   scope until they exist with their own ADRs.

10. **Two-axis institution space.** The intervention space is the implemented 2×2. Richer
    institutional designs are future work; current claims are confined to these four cells.

11. **Synthetic evidence only.** The evidence corpus is a finite, environment-authored set of
    typed items (`EvidenceSpec`); adversarial content is an inert data fixture. No real
    documents, no retrieval, no open-world evidence. Findings are about the modelled commons,
    not real information ecosystems.

12. **Costs/tokens reported only when measured.** Operational metrics never fabricate token
    or cost figures; a `None` means unmeasured. Each request dimension needs complete
    coverage before its total is reported. Partial measured sums, unknown 429/timeout
    usage and refusal/format-repair consumption remain visible. A completion-token cap is
    not a dollar ceiling or remote cancellation. The transport supplies no price table;
    child usage describes only its continuation. See [provider usage](../PROVIDER_USAGE.md).

13. **Analysis identity checks are necessary, not sufficient.** `chl analyze` rejects
    known non-treatment confounds and conflicting retries, including changed recorded
    transport settings or known reported-model sets within a comparison block. Missing
    model versions remain unknown; pre-response failures stay in attrition. It retains
    descriptive values but withholds paired inference when coupling or complete blocks
    cannot be verified.
    It cannot infer an entire missing run from absent artifacts, authenticate
    policy code from its label, or create paired provider randomness. Current analysis
    remains `sap_status: draft`; zero observed variance suppresses intervals and p-values.

14. **Exact N-IPD mathematics has explicit model assumptions.** Study 002's exact
    finite-state benchmark is post hoc and assumes independent rational Bernoulli decisions,
    a complete graph, fixed AllD agents and zero exploration. The simulator still uses
    finite-precision PRNG draws and binary-floating-point ratios. Exact model variances
    include cross-round dependence; agents, rounds and votes are not extra replicates.
    Model expectations and Monte Carlo errors do not replace the original empirical
    intervals, including the reported finite-sample discrepancy.

15. **Consistency is not authenticity.** Hash verification detects changes relative to a
    retained terminal commitment. It cannot authenticate a history against a writer who
    replaces the entire record and all commitments. Checked-in Study 002 summaries retain
    per-episode terminal hashes, but its original raw ledgers are generated artifacts;
    independent ledger verification requires those artifacts. The responsive EC and graph
    readouts likewise distinguish original execution/source commitments from later
    regeneration. Repeating current source is a new run, even if outcomes agree exactly.

16. **Graph statistics depend on their units.** Pairwise cooperation is a fraction of
    directed edge votes; neighbourhood cooperation is a fraction of positive-degree
    agents' broadcast votes. Isolates have zero reward and add no eligible votes; entirely
    edgeless worlds are rejected. Pairwise rates weight agents by degree, while sum/mean
    payoff aggregation is a separate explicit choice. On a star, moving AllD between hub
    and leaf changes exposure and first-round vote weights before any response occurs.
    Cross-policy comparisons can also change observation and action rules. Global
    cooperator count is insufficient for general sparse-graph pTFT dynamics, so the Study
    002 complete-population Markov benchmark is not a sparse-network oracle.

---

## 4. Standing rule

Any result statement that survives review must name its **model(s), environment, N,
institution cell, and scale**, state the unit and design, and distinguish measured values
from analytical predictions. Report an effect size and uncertainty interval where the
design supports one; report exact deterministic values or explicitly withheld inference
where it does not. A zero empirical variance is not population certainty. Stay inside §1
while avoiding every item in §2, and label exploratory and post hoc analyses as such.
