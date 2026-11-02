# Audit feedback under a declared synthetic law

This experiment completes the first opt-in audit-engine integration from
[issue #103](https://github.com/Chris0Jeky/collaborative-hill-lab/issues/103).
It asks how an observation-driven negative-veto policy responds to audit timing,
accuracy and unavailable reports when three differently labeled sources share
one perfectly correlated error. It is exploratory, scripted and unfrozen.

## What was fixed before execution

The [design](DESIGN.md) declares the 76 cases, literal action traces and task
outcomes, eight predictions, exact mixture equations and separate software
integrity fixtures. Both that design and the complete reviewed source were
published before the original execution. [PUBLISHED_SOURCE.json](PUBLISHED_SOURCE.json)
maps the actual local execution commit to the identical public Git tree;
[SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json) retains the original commit,
cleanliness flag, dependency lock, environment and 65 source-file digests.

The engine's [ADR-0018](../../docs/adr/0018-opt-in-evidence-commons-audits.md)
fixes exact generation and seed semantics. It does not alter the earlier
noisy-corpus experiment or its standalone audit contract.

## Retained evidence

The original batch contains 52 behavioral episodes and 24 fixed-action controls.
All 76 chains replay; four additional branch fixtures are software checks,
separate from that scientific count. All eight predictions hold, including
60 same-action comparisons, 42 truth controls and 720 exact expectation rows.
The complete outcomes, failures/zero effects, actions and typed settings are in
[RESULTS.json](RESULTS.json); [RESULTS.md](RESULTS.md) is generated from those
records. The original raw evidence is retained separately, and verification
reruns do not replace it.

Each audited episode uses an endpoint configuration that generates its declared
conditional verdict. Intermediate accuracy and unavailability values are exact
reweightings of these trajectories. They are not empirical samples at those
parameters. The separate policy uses only released findings and is insensitive
to the opaque contract identity; the mixture argument does not automatically
apply to another policy that reads additional information.

## Main result and its limits

For publication before proposals or verification, the signed-quality change is

```text
12 (1 - unavailable_probability) (audit_accuracy + source_error - 1).
```

With source error `1/10`, no unavailability and early publication, audit accuracy
`3/4` raises accuracy among accepted claims from `9/10` to `27/28`. Acceptance
falls from `1` to `7/10`, and signed quality falls from `48/5` to `39/5`. Audit
accuracy `9/10` yields a zero quality contrast; a perfect synthetic audit raises
quality to `54/5`. These are exact expectations in the declared finite model.

Timing also matters. Negative reports before proposals suppress proposals;
reports before verification leave unsupported claims. In this fixture, a report
at round 5 arrives after the selected claim already has two supports: it saves
six units of redundant verification effort without changing acceptance or
quality. Round 6 has no task effect. Those fixture-specific savings do not show
that inaccurate late audits improve inference.

Audit service cost is zero by assumption. No configured accuracy is empirically
calibrated. The experiment does not learn reliability, optimize policies, model
endogenous target selection or choose final utility weights. Conditional audit
accuracy is undefined when every finding is unavailable; selective accuracy is
undefined when no claim is accepted. Both use JSON null.

The experiment uses the separate scripted `ec_audit_veto_contributor` policy.
The legacy LLM prompt renderer omits this envelope; these results do not establish
that an LLM observes or responds to audits. See [audit usage](../../docs/AUDIT_USAGE.md)
for the supported configuration and version boundaries.

## Reproduce or inspect

```bash
# Fresh original-style execution; source must be committed and clean.
python experiments/audit-feedback/audit_feedback.py --out artifacts/audit-feedback-new

# Temporary regeneration, 80 chain replays, exact comparisons and byte checks.
make check-audit-feedback
```

`--out` refuses an existing destination. If execution integrity fails, the
generated files remain in place with a failure record covering every declared
cell; incomplete prediction values remain null. A failed prediction is retained
and exits nonzero. Markdown distinguishes measured traces from expected ones and
does not print success claims when their supporting checks fail.

The collector validates the exact run set, scenario/configuration identities,
literal actions and task outcomes, publication order, every checkpoint and
chain, original source claims when supplied, and the declared branch policy
overrides. Replaying recorded actions proves deterministic execution of those
actions; it does not infer the identity of arbitrary policy code from a label.
