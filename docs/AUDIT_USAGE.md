# Opt-in Evidence Commons audits

Audits add a scheduled public observation channel to Evidence Commons. The
separate EC v3 mechanism publishes findings before agents observe a round. The
existing EC v2 mechanism, institution fields, policies, scenario hashes and
sealed runs retain their prior behavior when the `audit` setting is absent.

The mechanism is a synthetic experiment instrument. Configured accuracy and
unavailability are exact model assumptions; they are not measured calibration
of an external auditor. [ADR-0018](adr/0018-opt-in-evidence-commons-audits.md)
specifies the law, stream identities and lifecycle contract.

## Configure a public audit

Add this object to an Evidence Commons scenario's `institution`. Replace the
target IDs with a candidate that belongs to the scenario's declared slot and
choose a publication round strictly below its total round count.

```json
{
  "accountability": "attributable",
  "evidence_topology": "shared_ledger",
  "audit": {
    "contract": {
      "contract_version": "ec-audit-observation@1",
      "audit_id": "audit-1",
      "accuracy": "3/4",
      "accuracy_semantics": "symmetric-conditional-on-availability",
      "oracle_kind": "synthetic-trusted-oracle",
      "dependence": "independent-of-source-errors",
      "visibility": "public",
      "selection": "fixed-ex-ante-targets",
      "unavailable_semantics": "explicit-no-verdict",
      "schedule": [
        {"slot_id": "s1", "proposition_id": "p", "publish_round": 3}
      ]
    },
    "generation": {
      "generator_version": "ec-audit-generator@1",
      "unavailable_probability": "1/2",
      "draw_dependence": "independent-per-target",
      "unavailable_dependence": "independent-of-truth-source-errors-and-correctness"
    }
  }
}
```

All audit fields shown above are required. Probabilities use canonical rational
strings: `"0"`, `"1/2"`, `"3/4"`, or `"1"`, for example. Floats, unreduced fractions,
Boolean rounds, empty schedules, repeated slot/candidate targets, unknown
candidates and publication outside the run horizon are rejected. An explicit
`"audit": null` is invalid; omit the key to use the legacy mechanism. Audits are
not supported by either N-IPD mechanism.

With accuracy `a` and unavailable probability `u`, a true target produces
positive, negative and unavailable findings with probabilities `(1-u)a`,
`(1-u)(1-a)` and `u`. A false target exchanges the positive and negative
probabilities. Availability and correctness use separate, exactly sampled
integer draws. Draws for different targets are independent conditional on the
configured world; verdicts can still be related through related truths.

## Choose an audit-responsive policy

The separately versioned `ec_audit_veto_contributor` wraps the existing
`ec_skeptical_contributor` rule. Use it in a cognition-plane agent policy:

```json
{
  "name": "ec_audit_veto_contributor",
  "params": {
    "min_sources": 2,
    "peer_threshold": "1/2",
    "warmup_rounds": 3,
    "share_evidence": true
  }
}
```

These are its defaults. A published negative finding for the selected
slot/candidate turns a proposal or verification into an explicit withhold.
Positive, unavailable, pending or absent findings preserve the skeptical
baseline's choice. The policy does not rerank alternatives, invert an inaccurate
audit, create a citation, retract an existing claim or challenge from an audit
alone. It validates every present envelope before choosing any action.

Existing scripted policies retain their original behavior. The original
audit-feedback experiment measures the scripted veto policy above.

## Show public findings to an LLM policy

Add `"prompt_renderer": "ec-audit@1"` to an existing `llm_fake` or
`llm_openai_compatible` policy's flat `params`, retaining its required script or
provider settings. Direct Python callers select
`LLMPolicy(..., prompt_renderer="ec-audit@1")`. This selector works only with
Evidence Commons, including an EC audit-off control. The default `legacy@1`
continues to omit the audit envelope and preserves its exact prompt/template
identity. [ADR-0019](adr/0019-opt-in-audit-aware-llm-prompts.md) defines the new
binding; [provider usage](PROVIDER_USAGE.md#opt-in-audit-aware-evidence-commons-prompts)
documents configuration and execution boundaries.

The adapter validates the public envelope and current candidate/round context
before a request, sorts released reports, and includes only their allowlisted
public fields. An absent channel, an empty published-report list, an explicit
unavailable report and a positive/negative verdict remain distinct. A candidate
without a finding may be pending or unselected; the envelope supplies no schedule,
accuracy or confidence. Reports do not create evidence citations, grant authority
or force a particular action.

The renderer and template identity are fixed at construction. Nested skin or
template drift is rejected before fake or compatible-provider calls; construct
a new policy for a new configuration. The selector is a policy setting, not an
HTTP or sampling field. Its distinct policy/template identity is retained in
manifests and actual prompt digests in transcripts. Continuation usage covers
only the new requests, and replay remains offline.

Validation uses fake providers and intercepted HTTP. It establishes the prompt
supplied to the provider, with no measured live-model behavior or audit benefit.
JSON escaping protects the added data section's formatting; it does not establish
model resistance to instructions in prose or change the legacy prompt body.

## Publication, branching and replay

At round `t`, the mechanism publishes the complete due batch in canonical target
order. Each `AuditPublished` event precedes every `ObservationIssued` event for
that round. All agents receive the same released envelope. Pending targets have
no report; explicit `unavailable` means a report was published without a verdict.
Neither hidden truth fields nor future findings are placed in observations or
the event ledger.

An ordinary checkpoint at round `t` records the state before that round opens.
A continuation publishes its due findings once before observing. Already
prepared states are idempotent; missing historical reports, partial batches,
duplicates and premature reports are rejected. Nested branches replay from
their own sealed artifacts without calling providers or loading ancestor paths.

Each target's availability and verdict have separate keys under the mechanism
seed root. Under the **same mechanism root**, adding or reordering targets,
moving publication time, changing the policy root, or choosing a different
branch ID does not reroll that target. Different study conditions normally
have different mechanism roots. Paired policy seeds alone do not promise
common audit draws across conditions.

Audit settings are bound into the audited scenario and mechanism hashes.
Contract identity covers the public contract; the mechanism hash also binds
generation settings. Narrative and evidence-corpus identities do not change
merely because audit settings change. Replay and branching validate that a
manifest's institution matches its hash-checked resolved scenario before
creating output.

## Scientific interpretation

The audit channel changes information and can change behavior. It does not
change task legality, provenance, acceptance rules, budgets, effort charges or
reward formulas for the same accepted actions. An audit is not verification
authority or evidence accepted by the underlying task.

The [audit-feedback design](../experiments/audit-feedback/DESIGN.md) separates
conditional response trajectories from exact mixtures over stated error laws.
Its placeholder weights and perfectly correlated source errors are deliberate
fixture choices. Accuracy among accepted claims, acceptance coverage, signed
quality, effort and utility answer different questions and are reported
separately. If every report is unavailable, conditional audit accuracy is
undefined; a null finding is not assigned invented accuracy.
