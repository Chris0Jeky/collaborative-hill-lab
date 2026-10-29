# Claims and Limitations — Collaborative Hill Lab

The scope contract for what the platform's outputs do and do not license. Each study
states its own claim boundary; a confirmatory preregistration must restate it. This
document is the standing cross-study boundary, updated 2026-10-29. It reflects the implemented
N-IPD engine and **Evidence Commons v0 system**
(`domain/world/evidence_commons.py`, `domain/institutions.py`, `engine/*`, `metrics/*`).

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

5. **Cognition or intent.** Outcomes are token statistics realised as typed actions. Mentalistic
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
   (`ec_contributor`, `ec_freerider`, `ec_verifier`, `ec_misinformer`, and the NIPD family)
   are hand-specified reactive strategies, not trained or adaptive agents. They calibrate the
   environment and bound the LLM readings; they are not claimed to be optimal or representative.

4. **Small N and declared composition.** Current Evidence Commons fixtures use N=3;
   the N-IPD studies cover N=3 and N=5 complete graphs. Findings are specific to the
   declared population and policy mixture. These unfrozen exploratory designs are not
   confirmatory preregistrations. Increasing N while retaining one defector also changes
   its population fraction; Study 002 includes a two-defector control to expose that issue.

5. **Single-episode credit model.** Credit and scoring are computed within one episode at
   seal (`final_rewards`). There is no cross-episode reputation, memory, or carryover — an
   agent starts each episode fresh. Repeated-game reputation dynamics are not modelled.

6. **LLM cognition is non-reproducible; replay covers actions, not minds.** Provider sampling
   is a second RNG outside our control, and temp-0 is not guaranteed deterministic
   (batching/MoE/float non-associativity). Replay (`agents/replay.py`) reproduces the
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

9. **No sanctions, reputation, commitments, audits, or human-gates yet.** `InstitutionConfig`
   implements exactly two axes (accountability × evidence_topology). Sanctions, reputation
   scores, commitments, and approval gates are documented extension points, deliberately
   unimplemented under the second-occurrence rule. Claims about those mechanisms are out of
   scope until they exist with their own ADRs.

10. **Two-axis institution space.** The intervention space is the implemented 2×2. Richer
    institutional designs are future work; current claims are confined to these four cells.

11. **Synthetic evidence only.** The evidence corpus is a finite, environment-authored set of
    typed items (`EvidenceSpec`); adversarial content is an inert data fixture. No real
    documents, no retrieval, no open-world evidence. Findings are about the modelled commons,
    not real information ecosystems.

12. **Costs/tokens reported only when measured.** Operational metrics never fabricate token
    or cost figures; a `None` means unmeasured. Cost-conditioned claims are only as good as the
    measurement the manifest actually recorded.

13. **Analysis identity checks are necessary, not sufficient.** `chl analyze` rejects
    known non-treatment confounds and conflicting retries. It retains descriptive values
    but withholds paired inference when coupling or complete blocks cannot be verified.
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
    independent ledger verification requires those artifacts.

---

## 4. Standing rule

Any result statement that survives review must name its **model(s), environment, N,
institution cell, and scale**, state the unit and design, and distinguish measured values
from analytical predictions. Report an effect size and uncertainty interval where the
design supports one; report exact deterministic values or explicitly withheld inference
where it does not. A zero empirical variance is not population certainty. Stay inside §1
while avoiding every item in §2, and label exploratory and post hoc analyses as such.
