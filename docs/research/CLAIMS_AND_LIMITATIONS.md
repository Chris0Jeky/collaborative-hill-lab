# Claims and Limitations — Collaborative Hill Lab

The scope contract for what the platform's outputs do and do not license. Every study's
preregistration restates its own claim boundary (field 15); this document is the standing,
cross-study boundary. It reflects the **implemented v0 system**
(`domain/world/evidence_commons.py`, `domain/institutions.py`, `engine/*`, `metrics/*`).

---

## 1. What the platform CAN claim

1. **Properties of agent populations under configured mechanisms.** For a specified model (or
   scripted policy set), environment, and institution, the lab measures behavioural and
   epistemic outcomes — briefing quality (`accepted_correct − accepted_incorrect`),
   contribution/verification rates, free-rider advantage, payoff inequality — with episode-level
   uncertainty. Claims take the form: "under model M, in Evidence Commons at N=3, mechanism A
   (`attributable`) produced higher briefing quality than mechanism B (`aggregate`), effect
   size E with 95% CI, at this scale."

2. **Reproducible, content-addressed comparisons.** Every run is pinned by a hash chain and a
   manifest (`experiments/manifests.py`): scenario/mechanism/narrative/evidence hashes, code
   commit, dependency lock, seeds, provider and prompt-template hashes. Two people on two
   machines can reproduce a scripted run **byte-for-byte** (identical `final_event_hash`) and
   can audit exactly which model/version/config produced an LLM run.

3. **Mechanism-attributable effects.** Because institution changes are proven to alter only
   *who is seen* and *who is credited* — never the task, legal actions, or payoff totals for
   identical behaviour (the mechanism certificate, `studies/001`, checks this by enumeration;
   `mechanism_hash` excludes the institution's presentation) — a measured difference between
   institutions is attributable to the institution, not to a confounded task change.

4. **Mechanism-invariance of narrative skins (scripted).** For scripted agents, skins are
   proven pure-presentation: swapping a `NarrativeSkin` leaves `mechanism_hash` and the entire
   event chain identical. So any scripted result is demonstrably not a prose artifact.

5. **Comparative, not absolute, readings.** The lab compares mechanisms and models against
   each other and against analytical/scripted baselines whose behaviour is known in closed
   form (the hand-derived payoff tables; the enumerated dilemma certificate).

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

4. **Small N.** Groups are N=3–5 agents. Findings are scale-specific; nothing is claimed
   about large populations, and N is a pre-registered factor, not a free knob.

5. **Single-episode credit model.** Credit and scoring are computed within one episode at
   seal (`final_rewards`). There is no cross-episode reputation, memory, or carryover — an
   agent starts each episode fresh. Repeated-game reputation dynamics are not modelled.

6. **LLM cognition is non-reproducible; replay covers actions, not minds.** Provider sampling
   is a second RNG outside our control, and temp-0 is not guaranteed deterministic
   (batching/MoE/float non-associativity). Replay (`agents/replay.py`) reproduces the
   *recorded actions* and re-derives the identical sealed ledger, but it does **not**
   reproduce the model's internal computation. An LLM run is reproducible as a *record*, not
   as a *cognitive process*.

7. **Narrative-skin invariance is proven for scripted agents only.** The skin-is-presentation
   invariant is a *proof* for scripted runs (identical event chain across skins). For LLM
   agents, skins are the surface the model reads and behaviour may vary; LLM skin-invariance
   is a **measurement target, not yet a result**. Until measured, "the effect is a mechanism
   effect, not a prompt artifact" is asserted only for scripted agents.

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

---

## 4. Standing rule

Any result statement that survives review must name its **model(s), environment, N,
institution cell, and scale**, attach an **effect size with an uncertainty interval**, and
stay inside §1 while avoiding every item in §2. When in doubt, downgrade to the comparative,
mechanism-linked, scale-qualified form.
</content>
