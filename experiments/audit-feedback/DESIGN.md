# Audit feedback: pre-execution design

Status: exploratory, unfrozen, exact conditional-outcome enumeration for issue
#103. This design is committed and published before any audit-enabled episode or
research execution. It is not a live-model pilot, a confirmatory study or a
selection of final utility weights. The historical StudySpecs, policies and
experiment records remain unchanged. No provider call or freeze is involved.

The contract foundation is [ADR-0017](../../docs/adr/0017-noisy-corpus-and-audit-contract.md).
The integration must explicitly select EC engine version 3 and observation schema
version 3 while preserving engine version 2 for every existing no-audit scenario.
The original standalone audit prototype and noisy-corpus evidence are retained.

## Question and scope

When does a published audit change an observation-driven policy's behavior, and
when does that response improve signed quality, coverage or utility under an
explicitly synthetic accuracy model? We separate publication timing from report
accuracy and distinguish an informational channel from an automatic acceptance
rule. In particular, a negative report cannot retract previously earned support
unless some separately specified legal action does so.

The finite source worlds use unanimously agreeing reports with distinct source
labels. They are perfectly correlated source reports, not independent
corroboration. This is the earlier skeptical rule's blind spot. The audit adds a
declared truth-correlated public signal with errors independent of source errors;
that independence and its accuracy are modeling assumptions, not measurements.

The main experiment has 52 behavioral episodes and 24 action-fixed controls,
76 sealed runs in total. Extra software-integrity fixtures are identified
separately and do not add scientific samples. Exact mixture rows reweight the
finite response table; they do not add episodes, independent replicates,
confidence intervals or significance tests.

## Policy contract and alternatives

The new registered policy is:

```text
ec_audit_veto_contributor[min_sources=2,peer_threshold=0,warmup=0,share=True]@1
```

Its constructor accepts the same four parameters and bounds as the existing
skeptical rule: `min_sources`, `peer_threshold`, `warmup_rounds` and
`share_evidence`. Its general defaults remain 2, `1/2`, 3 and true. This experiment
sets the quorum and warmup to zero so peer-participation gating cannot confound
the audit response.

After validating any present audit envelope, the policy obtains the unchanged
version-1 skeptical rule's proposed typed action from the current observation.
If that action proposes or verifies a claim,
it looks up the corresponding `(slot_id, proposition_id)` in the published audit
reports. A `negative` report replaces that selected action with `Withhold`.
Otherwise it returns the original proposal. Inspection, sharing, challenges and
existing no-op choices are unchanged. It does not try another candidate after a
veto, fabricate citations, treat a positive audit as evidence, reverse a negative
audit on the basis of its configured accuracy, or automatically challenge a claim.

An absent audit field, no published matching report, `positive` or `unavailable`
does not veto. This supplies an exact action bridge to the existing skeptical
rule. A present malformed envelope is an error, not an absent audit. The policy
uses the shared strict public schema; unknown versions, malformed records,
duplicate targets, future reports and targets outside the observation's candidate
set must not silently become decisions. The schema's `contract_hash` is opaque:
it is validated as an identity but never used to choose an action.

The rule has no persistent action/verdict history and consumes no random draws.
A fresh policy object at a branch therefore behaves identically given the same
observation. It receives no world truth, audit error/missingness bits, generator,
future findings, internal state or hidden reliability estimate. Its only audit
input is the version-1 public envelope already specified by ADR-0017.

A strict positive gate was considered but would also introduce mandatory waiting
and make unavailable audits suppress all participation. Reranking candidates or
attempting corrective challenges would require additional choice/citation rules.
The selected negative veto isolates a narrower response and makes the
unavailable case an exact behavioral control. It is not claimed to be optimal.

## Runtime audit law and interface

The required audit institution supplies this structure:

```text
audit:
  contract: the unchanged AuditConfig schema for ec-audit-observation@1
  generation:
    generator_version: ec-audit-generator@1
    unavailable_probability: a canonical rational string in [0,1]
    draw_dependence: independent-per-target
    unavailable_dependence: independent-of-truth-source-errors-and-correctness
```

Available audit correctness has the contract's exact probability `a`. An
independent unavailability draw has probability `u`. Per-target draw identities
must include the generator/channel version, audit ID, slot and proposition, with
separate missingness and correctness scopes. No global RNG or persisted/shared draw
cursor is allowed. Additional targets or an unavailable result must not shift existing
targets' outcomes. Multiple-target independence is explicit in the generator,
not inferred from the original observation contract.

The engine publishes a finding once at the start of its scheduled round, before
any agent receives that round's observation. Every agent receives the same public
envelope, and published reports persist. Only released reports enter episode
state/checkpoints; future verdicts and generation bits are not persisted there.
Replays and branches reconstruct the declared outcomes from their sealed
configuration and seed identity without rerolling or provider calls.

The channel adds no audit effort cost and changes no legal action, citation
validity, support adjudication, acceptance rule, credit or reward formula. These
are version-3 integration requirements, not conclusions inferred from a positive
scientific result. Any priced audit, sanction or endogenous targeting rule needs
a separate design. Configured accuracy is synthetic accuracy conditional on
availability, not a claim about deployed verification.

## Fixed episode inputs

- Three agents: `a1`, `a2`, `a3`; one slot `s1`; candidates `p` and `q`.
- Hidden truth `T` is either `p` or `q`.
- Three fresh version-1 evidence items `e1`, `e2`, `e3`, with distinct labels
  `src-1`, `src-2`, `src-3`, all support the same candidate `R` in `{p,q}`.
  Their initial holders are `a1`, `a2`, `a3`, respectively.
- Shared-ledger topology exposes all item identities to all agents at round 0;
  inspection is still required. All agents are active, with inspect budget 3 and
  verify budget 2. There are 8 simultaneous rounds, numbered 0 through 7.
- Aggregate accountability is held fixed. Inspect/share/propose/challenge cost
  1, verification costs 2, and accepted correct/wrong quality is `+12/-12`.
  Accepted proposer credit is `+3/-3`; accepted verifier credit is `+2/-2`.
  These are existing placeholders and remain unchanged.
- Every audited world schedules exactly one target `(s1,R)` at round
  `tau in {3,4,5,6}`. The target is fixed from the corpus template before the
  episode, never selected from agent actions or claims. It does not depend on T.
- Audit ID is `audit-1`. The policy sees no future schedule or finding through
  any extra observation field. The contract/generator identity is hash-bound.
- Seed is 20261102 and the protocol is `paired-policy-v2`. Every run in a given R
  world uses mechanism root `(20261102,"audit-feedback",R)`, policy root
  `(20261102,"audit-feedback","policy",R)` and scenario block `audit-feedback-R`
  with R replaced by its candidate ID. T, V and publication timing do not change
  these roots. The experiment never searches for seeds producing desired reports.

The current version-1 skeptical policy with `min_sources=2`, zero quorum/warmup
and sharing enabled is the unaudited behavioral baseline. It sees all three
agreeing fresh source labels and passes its evidence screen regardless of T.

## Complete grid and deterministic endpoint execution

The audit-policy grid is the full product:

```text
T in {p,q}
R in {p,q}
published finding V in {positive,negative,unavailable}
publication round tau in {3,4,5,6}
```

This is exactly 48 audited behavioral episodes. There are also four unaudited
version-1 behavioral baselines, one for every `(T,R)` pair.

Each conditional finding is produced by the real integrated generator at a
deterministic endpoint, never by injecting a finding or replacing the generator:

| Requested conditional finding | Endpoint accuracy | Endpoint unavailability |
|---|---|---|
| positive and `R=T` | `1` | `0` |
| positive and `R!=T` | `0` | `0` |
| negative and `R=T` | `0` | `0` |
| negative and `R!=T` | `1` | `0` |
| unavailable, either truth relation | `1` | `1` |

The endpoint configuration is retained verbatim in each run's provenance. These
are conditional response cases, not samples from a single intermediate-accuracy
configuration. Changing accuracy changes the public contract hash; the policy's
action rule deliberately ignores that opaque value. The exact mixture analysis
below is justified only because probability settings influence this policy through
the released verdict, not through the hash or any extra probability field.
Schema/hash-insensitivity checks and the fixed timing trace test that boundary.

Nondegenerate sampler tests are required separately. Endpoint episodes alone
cannot verify the distribution of a nondegenerate generator.

## Hand-derived action and task oracle

Let `I1,I2,I3` denote inspecting `e1,e2,e3`, and `P` denote proposing R with
citations `(e1,e2,e3)`. All agents submit these actions simultaneously. Round-3
proposals create `c1,c2,c3` in sorted agent order. Define `V1` as the round of
verifications `(a1:c2,a2:c1,a3:c1)` and `V2` as
`(a1:c3,a2:c3,a3:c2)`. `W` is all-agent Withhold.

The four complete eight-round schedules are literal expectations:

```text
A = I1 I2 I3 P V1 V2 W W
B = I1 I2 I3 W W  W  W W
C = I1 I2 I3 P W  W  W W
D = I1 I2 I3 P V1 W  W W
```

The unaudited rule always follows A. The audit rule follows A for positive or
unavailable reports at every tau. A negative report selects B at tau=3, C at
tau=4, D at tau=5, and A at tau=6. All agents inspect the same three items first;
audit reports are not a reason to stop inspection or bypass provenance.

| Report/timing | Trace | Accepted claim | Total effort | Contribution fraction | Total utility if `R=T` | Total utility if `R!=T` |
|---|---|---|---|---|---|---|
| positive or unavailable, any tau | A | c1, support 2 | 24 | `3/4` | `-5` | `-43` |
| negative, tau=3 | B | none | 9 | `3/8` | `-9` | `-9` |
| negative, tau=4 | C | none | 12 | `1/2` | `-12` | `-12` |
| negative, tau=5 | D | c1, support 2 | 18 | `5/8` | `1` | `-37` |
| negative, tau=6 | A | c1, support 2 | 24 | `3/4` | `-5` | `-43` |

Accepted quality is `+12` when R is true and `-12` otherwise; total credit is
`+7/-7`. Nonacceptance has zero quality and zero credit. In aggregate each agent
gets one third of the displayed total utility. Each agent's effort is 8, 3, 4
or 6 under A, B, C or D. All inspect budgets end at zero; verify budgets are
0, 2, 2 or 1, respectively.

D already gives c1 two verifications, c2 one and c3 none. The second verification
round in A brings c2/c3 to two each but cannot displace earliest c1. Therefore a
negative audit at tau=5 changes effort and utility while leaving the winner,
quality and credit unchanged. A negative audit at tau=6 changes no task outcome.
These are fixture-specific timing predictions, not a general retraction theorem.

## Action-fixed C3 controls without redundant episodes

For each of the four `(T,R)` worlds, retain one unaudited episode for each literal
schedule A, B, C and D. The four A runs are the behavioral baselines above; the
12 additional B/C/D runs use predetermined typed schedules. Every audited
behavioral run is matched to its corresponding unaudited schedule and world.
Shared controls are explicitly referenced, never counted as independent repeats.

A second set of 12 action-fixed audited controls forces the full A schedule in
negative-report worlds at tau=3, 4 or 5, for all four `(T,R)` pairs. This is
essential: a mechanism that wrongly treats a negative audit as an automatic veto
could pass a comparison in which the policy already withheld the action. The
forced A controls must still accept c1, including a false c1, with the unchanged
`+12/-12` quality and effort 24. At tau=6 the audited behavioral trace is already
A; positive/unavailable behavioral traces also supply A without extra runs.

Thus there are 48 audited behavioral runs, four unaudited behavioral baselines,
12 unaudited B/C/D controls and 12 audited full-A controls: 76 runs in total.
There are 60 explicit audit-on/off C3 comparisons using these shared controls.
Each comparison fixes all accepted typed actions and requires identical briefing,
budgets, effort, quality, individual/total credit and utility. Public audit
observations/events and full chain hashes may differ intentionally.

## Declared exact mixture law

The synthetic truth mixture assigns `P(T=p)=P(T=q)=1/2`. Conditional on truth,
the common source report has `P(R=T)=1-e` and `P(R!=T)=e`. All three reports share
that same error; distinct labels add no independence. Unavailability has
probability u independently of truth, source error and audit correctness. Given
availability, the audit is correct with probability a independently of source
error. There is only one target in each research world, so no empirical claim
about cross-target dependence follows.

For each `(T,R)` world, multiply its source mass by:

| Finding | `R=T` | `R!=T` |
|---|---|---|
| positive | `(1-u)a` | `(1-u)(1-a)` |
| negative | `(1-u)(1-a)` | `(1-u)a` |
| unavailable | `u` | `u` |

The declared grid is `e in {0,1/10,1/2,1}`, `a in {0,1/2,3/4,9/10,1}`,
`u in {0,1/2,1}`, and the four publication times. Every law's masses sum to one.
Report all 240 law/timing combinations under the equal truth mixture and
conditional on each truth: 720 exact expectation records. Preserve all endpoint
cells even when a law gives them zero mass. The weighting parameters are separate
from each executed endpoint configuration and are never substituted into its
manifest or source provenance.

Let `C=P(correct accepted)`, `W=P(wrong accepted)`, `A=C+W`, `D=C-W`, and
`N=P(negative)=(1-u)[(1-e)(1-a)+ea]`. Selective accuracy is `C/A` when A is
positive and JSON null otherwise; it is not an average with abstentions coded
as zero. Expected signed quality is `12D` and expected total credit is `7D`.

For tau=3 or 4:

```text
C = (1-e)[u+(1-u)a]
W = e[u+(1-u)(1-a)]
A = 1-N
D = u(1-2e)+(1-u)(a-e)
effort(tau=3) = 9+15A
effort(tau=4) = 12+12A
contribution(tau=3) = 3(1+A)/8
contribution(tau=4) = (2+A)/4
total utility = 19D-effort
```

The unaudited baseline has `C=1-e`, `W=e`, `A=1`, quality `12(1-2e)`, effort
24, contribution `3/4`, and total utility `19(1-2e)-24`. Hence the early-audit
quality contrast is exactly `12(1-u)(a+e-1)`: positive if `a>1-e`, zero at
`a=1-e` or u=1, negative if `a<1-e` and u<1.

At tau=5, C/W/A, quality and credit remain the baseline values, while effort is
`24-6N`, contribution is `3/4-N/8`, and total utility is the baseline plus `6N`.
At tau=6 every task outcome is exactly baseline. In particular, tau=5 can save
effort even with an inaccurate audit: that is a response to a redundant action
in this fixture, not evidence that the information was accurate.

Hand-calculated checkpoints for e=`1/10`, u=`0`, tau=3:

| a | Acceptance A | Selective accuracy | Signed quality | Total utility |
|---|---|---|---|---|
| `0` | `1/10` | `0` | `-6/5` | `-62/5` |
| `1/2` | `1/2` | `9/10` | `24/5` | `-89/10` |
| `3/4` | `7/10` | `27/28` | `39/5` | `-143/20` |
| `9/10` | `41/50` | `81/82` | `48/5` | `-61/10` |
| `1` | `9/10` | `1` | `54/5` | `-27/5` |
| unaudited baseline | `1` | `9/10` | `48/5` | `-44/5` |

The a=`3/4` row improves accuracy among accepted claims while reducing coverage
and signed quality. The a=`9/10` row has zero signed-quality contrast despite
higher selective accuracy. At u=1 every audit-policy row equals baseline.
At e=0,a=0,u=0 or e=1,a=1,u=0 with early publication, acceptance is zero and
selective accuracy is null, not zero or one.

## Predictions committed before execution

- **P1:** All 48 audited behavioral schedules and four unaudited baselines match
  the literal A/B/C/D table, including claim IDs, citations and per-agent actions.
- **P2:** Every run's final briefing, budgets, effort, credit, utility and
  contribution fraction matches the independent literal task oracle.
- **P3:** All 60 same-action audit-on/off comparisons pass C3, including forced
  verification after an early negative audit. Audit publication alone never
  invalidates a citation or changes acceptance/scoring.
- **P4:** Each audited run publishes exactly one scheduled finding before every
  observation at its publication round, with no earlier report. Every agent
  receives the same persistent public finding; no raw hidden fields or
  generation bits appear in observations, public events or checkpoints.
- **P5:** For truth-flip pairs with R, timing, endpoint accuracy, availability and
  seeds held fixed, observations/actions are identical before the first differing
  published report. Under fixed actions, later observation differences are confined
  to the declared audit envelope. In behavioral pairs, later ordinary history may
  differ as a consequence of legitimate policy responses; that is not a hidden leak.
- **P6:** Every declared law sums to one, has the declared source-error and
  availability marginals and joint available-correct mass `(1-u)a`, and matches
  the independent closed forms. Conditional audit accuracy equals a only when
  u<1; it is undefined/null when u=1, not an imputed empirical accuracy.
  Truth-conditional expectations equal the mixed row.
- **P7:** The signed-quality threshold, selective-accuracy/coverage tradeoff,
  all-unavailable control, late-publication null and tau=5 effort-only response
  agree with the formulas and hand-calculated checkpoints above.
- **P8:** All 76 sealed original runs replay exactly. Required branch fixtures
  preserve byte-identical prefixes and audit publication/seed identity; software
  verification reruns do not replace original evidence or increase the sample.

Predictions are not edited after execution. A mismatch retains its cell, original
trace and explicit failed prediction. Checks exit nonzero on failure; the readout
must not silently omit a negative, zero, unavailable, failed or zero-mass case.

## Separate software-integrity fixtures

These are engineering checks, not additional research observations:

1. Hand-constructed policy observations cover negative proposal/verification vetoes;
   missing/empty/positive/unavailable and other-target bridges; unchanged inspection,
   sharing, evidence challenges and quorum; unknown/malformed/future/duplicate
   reports; unread/stale citations; nonmutation; and a freshly rebuilt policy.
   Expected typed actions are literal, not obtained by running the new policy.
2. Nondegenerate exact generator oracles use a=`3/4`, u=`1/2`. An independent
   product of two availability buckets and four correctness buckets has exactly
   four unavailable, three available-correct and one available-wrong outcomes.
   Tests also cover probability boundaries, separate draw scopes and invariance
   when another scheduled target is added or its independently keyed availability
   outcome changes. The runtime has one global u, not per-target probability knobs.
3. Strict scenario/configuration checks cover candidate IDs, duplicate targets,
   bool/float/coercion boundaries, noncanonical probabilities and publication
   before round 0 or at/after the horizon. The first and last legal publication
   rounds are tested. Audit settings alter the intended hashes; skins and all
   historical no-audit hashes retain their existing contracts.
4. A truthful negative fixture with T=q,R=p,tau=4 supplies branch checkpoints
   before publication and after publication, plus a nested branch. Fresh audit
   policy instances preserve the parent's response, no already-public finding
   is rerolled/republished, and all resulting sealed segments replay. Overriding
   all three policies with the existing skeptic before publication yields full
   A and wrong quality -12 despite the negative audit. Such branch fixtures are
   verification, not additions to the 76-run scientific grid.
5. Fixed-action truth flips enforce the audit-only observation projection; normal
   behavioral truth flips check the first permitted divergence. Every ledger and
   checkpoint is scanned for hidden truth fields and unreleased findings.
6. Unchanged v1 action/ID and historical hash tests remain required. Source
   comparison verifies existing policy functions were not edited by the additive
   registration. Existing research readout bytes and all four unfrozen StudySpecs
   remain unchanged.

## Reproduction, provenance and limits

Implementation will separate the policy, literal schedules/closed-form oracle,
episode generation and readout verification. Pure policy tests are written and
observed failing against the old factory before implementation. The complete
generator/check source is committed and published before original research
execution. Execution requires clean committed source and a fresh artifact root.

The generator retains all 76 run identities, completed seals, terminal hashes,
prediction checks and exact mixture weights. Its source record binds the actual
clean execution commit, dependency lock and transitive source inputs. A public
mapping may associate an identical published tree without rewriting the original
execution identity. Readouts use integers and canonical Fraction strings.

`audit_feedback.py --check` will regenerate runs in a fresh temporary directory,
replay them and compare retained JSON/Markdown readouts byte for byte. Original
raw runs receive their own integrity audit and are retained separately. Review
and later regression runs are labeled reproductions.

The conclusions are limited to this single-slot, all-active, shared-ledger,
unanimous-source fixture and this deliberately narrow veto rule. Neither the
source error rate nor audit accuracy, independence, missingness or free channel
cost is empirically calibrated. There is no policy optimization, active audit
selection, learning, equilibrium certification, LLM/human result or general audit
benefit claim. The policy cannot produce an unsupported correct claim or retract
already earned support merely because a negative report appears. Future costs,
dependence models and richer policies require separately versioned designs.
