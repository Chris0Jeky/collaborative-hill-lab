# ADR-0019 — Opt-in audit-aware LLM prompts

Status: **design draft for technical review** (2026-11-02). Implementation is a
separate follow-up to ADR-0018 / PR #107. This document changes no scientific
design, original result, mechanism, audit law or scripted policy.

## Context and decision

EC v3 supplies the public `ec-audit-observation@1` envelope. The existing LLM
renderer selects particular EC fields and omits that envelope. Its renderer
version, prompt-template hash and policy ID are already recorded in provenance;
changing the default rendering would silently change an established policy.

Select a separately versioned prompt adapter explicitly at policy construction:

```python
class LLMPolicy:
    def __init__(
        self, agent_id: str, provider: CompletionProvider, skin: NarrativeSkin,
        max_retries: int | None = None, sampling: dict[str, Any] | None = None,
        *, prompt_renderer: PromptRenderer = "legacy@1",
    ) -> None: ...
```

The only accepted values are the exact strings `legacy@1` and `ec-audit@1`.
The default retains the current renderer, template hash, policy ID and manifest
shape. The audit-aware adapter displays validated public audit data without
imposing the scripted negative-veto rule on the model.

Approaches considered:

- **Explicit policy-owned selector (chosen direction).** One optional flat
  parameter serves both existing fake and compatible provider factories, and
  binds the prompt implementation before any observations or requests.
- **Separate policy names/classes.** These could preserve defaults, but duplicate
  factory/authorization registration for a change that belongs to prompting.
- **Automatic dispatch when an observation contains `audit`.** Rejected: prompt
  semantics would change after construction without a fixed recorded identity.

The `ec-audit@1` adapter accepts EC observations with or without an audit channel.
It rejects non-EC observations before a provider call. Scenario validation also
rejects an explicit audit-aware LLM selection on a non-EC world. This permits
deliberate audit-off controls using the same adapter.

## 1. Fixed identity and preserved legacy behavior

Use a small frozen prompt binding containing the selected renderer and its
construction-time template hash. The binding is immutable for both modes;
read-only policy template identity is required for `ec-audit@1` only.
The adapter is never reselected from an observation. Keep the original
`render_prompt(observation, skin)` and `prompt_template_hash(skin)` default
outputs exactly unchanged, including whitespace and JSON ordering.

For `legacy@1`, retain the exact existing template-hash algorithm and policy-ID
format, including the existing compatible-provider identity suffix. Do not add
new keys to default policy audit metadata or manifests.
Preserve legacy public attribute assignment and drift behavior too: callers may
assign `prompt_template_hash`, `max_retries`, `sampling` and `skin` as before;
the existing compatible-provider pre-call check still raises `ProviderError`
for configuration drift, rather than replacing those checks with assignment-time
errors. Legacy fake-policy mutability is not silently tightened. The new renderer
selector has no prior mutable API, and the frozen audit binding remains the
authority for opt-in template identity even if a compatibility mirror is tampered
with; audit-mode drift must be refused before a call.

For `ec-audit@1`, define the template hash as `content_hash` of exactly:

```json
{
  "domain": "chl.prompt.ec-audit.v1",
  "renderer": "ec-audit@1",
  "base_prompt_template_hash": "<existing v1 hash for this skin>",
  "audit_contract_version": "ec-audit-observation@1"
}
```

Its policy ID uses the explicit new form:

```text
llm[<model_id>,skin=<skin_id>,renderer=ec-audit@1,tpl=<hash12>]@2
```

For a compatible provider, append the existing `provider=<identity16>` component
inside the brackets using the unchanged provider-metadata hash algorithm.
The template identity does not include current reports, the observation round,
the audit ID or the audit contract hash: those are observation content. A prompt
text digest continues to identify each concrete request in the transcript.

Before every audit-aware proposal, recompute the selected template identity
from the current skin and compare it with the frozen construction snapshot.
Refuse skin/template/renderer drift before `provider.complete`, including fake
providers. Compatible-provider configuration checks continue to compare their
existing transport/sampling/retry metadata and use the selected template hash.
Failure raises a sanitized `ProviderError` with `attempts=()` and makes no call;
usage counters and transcripts remain unchanged. Mutating nested skin mappings
must not evade this check. Legacy fake-policy behavior otherwise stays unchanged.

## 2. Public validation before rendering or requests

The new adapter receives only the supplied observation and skin. It never reads
the mechanism, world truth, generation settings, audit schedule or seed streams.
It validates before constructing a provider prompt:

1. `mechanism` is `evidence_commons`; `round` is an exact nonnegative `int`
   (no bool, float or string coercion).
2. `slots` is a public candidate map with nonblank string slot IDs and nonempty
   list/tuple candidate collections containing nonblank strings.
3. An absent `audit` key is legitimate. A present null/scalar value is invalid.
4. A present object is parsed as the shared strict `AuditEnvelope`, using the
   explicit JSON validation path for JSON-array report lists. Reject unsupported
   versions, malformed hashes, blank audit IDs, extra fields, invalid verdicts,
   scalar coercions and values that cannot be represented as standard JSON.
5. Each report targets a declared candidate of its slot, has
   `publish_round <= observation.round`, and appears at most once per
   `(slot_id, proposition_id)`, regardless of timestamp or verdict.

After validation, project only `contract_version`, `audit_id`, `contract_hash`
and the four public finding fields. Sort reports by publication round, slot and
proposition. Do not serialize the entire input observation into the new section.
Do not silently drop an invalid report, repair it or fall back to v1 rendering.
Malformed observations raise a stable `ValueError` without interpolating raw
payloads; no provider call, attempt, retry or transcript entry is recorded.

This validates syntax and observable context. The adapter cannot recompute the
contract hash or certify completeness/authenticity without the public contract
and ledger; it must not claim that it has done so.

## 3. Prompt meaning and data boundaries

Insert a deterministic public-audit section before the existing response-format
instructions. A small internal rendering helper may share the existing EC body;
v1 public functions and their exact outputs remain covered by literal fixtures.
Within the new audit section, envelope identifiers and findings appear only in
JSON-quoted data, with control characters escaped, inside a clearly delimited
data block. No envelope payload is interpolated into instruction prose or a
section delimiter. This guarantee is scoped to the new section: the preserved
v1 EC body also displays slot/proposition IDs using its existing formatting.
It is not a claim that any model will resist prompt injection.

The section distinguishes these observable cases:

| Observation | Meaning rendered |
|---|---|
| No `audit` key | No public audit channel is present in this observation |
| Valid envelope, zero reports | Channel present; no findings have been published yet |
| Published `unavailable` | This target has an explicit report with no verdict |
| Published `positive` / `negative` | This target has the corresponding fallible public verdict |
| Candidate absent from a present envelope's reports | No published finding; pending versus not selected is unknown |

The envelope contains no schedule. Do not infer future selection, publication
time, coverage, accuracy, source independence or confidence from its hash or
absence of a finding. Positive and negative reports are data; neither changes
legality, provenance, acceptance, task rewards or authority. The prompt explains
that audits are not evidence citations. It issues no rule to propose, verify,
withhold, retract or change a claim because of a verdict. The existing typed
action gate remains authoritative for what the model can do.

## 4. Factory, scenario and manifest plumbing

Both existing policy names accept the same optional parameter:

```json
{"name": "llm_fake", "params": {"prompt_renderer": "ec-audit@1", "script": "[...]"}}
```

The compatible variant uses `name="llm_openai_compatible"` with its existing
required endpoint, model and token-limit settings plus the same selector.
Unknown renderer names and non-string selectors fail during offline parameter
validation, before credentials, requests or output-directory creation.

The selector belongs to the policy layer. Do not add it to
`OpenAICompatibleConfig`, sampling, HTTP payloads or transport audit metadata.
`validate_provider_params` validates this recognized policy key while passing
only existing transport keys to the unchanged config model.
`build_openai_compatible_policy` passes the validated selector to `LLMPolicy`;
the `llm_fake` branch of `build_policies` does the same. Existing credential and
`allow_provider_requests` gates remain unchanged. An explicit scripted override
still bypasses unused provider construction.

The small shared API is `PromptRenderer = Literal["legacy@1", "ec-audit@1"]`,
`validate_prompt_renderer(value: object) -> PromptRenderer`, and
`build_prompt_binding(skin: NarrativeSkin, renderer: object) -> PromptBinding`.
The frozen binding exposes `renderer`, `template_hash`,
`template_hash_for(skin) -> str` and `render(observation, skin) -> str`.
The compatible factory's existing signature stays unchanged; its flat `params`
mapping carries the selector. Non-EC selection is also checked in
`build_policies`, before constructing an effective selected provider, so a
caller passing copied model objects cannot bypass the scenario check. A valid
explicit override retains its existing bypass behavior.

The selected parameter is already stored in the resolved cognition plane and
changes the scenario/study hash when added. It does not change mechanism,
narrative or evidence-corpus hashes. Existing `policies` and
`prompt_template_hashes` manifest fields record the new identity, so no manifest
schema/default-field change is needed. Explicit `legacy@1` and omitted default
produce the same policy/template identity; their raw scenario specifications
may have different hashes because one contains an extra explicit parameter.

## 5. Minimal file map and verification gates

| File | Responsibility |
|---|---|
| `agents/llm/prompt_adapters.py` (new) | Exact selector validation, frozen binding, audit-envelope/context validation, deterministic audit section and new hash |
| `agents/llm/rendering.py` | Small internal body-sharing seam; unchanged public v1 outputs/hash algorithm |
| `agents/llm/policy.py` | Construction-time binding, read-only identity, selected rendering and pre-call drift guard |
| `agents/llm/configuration.py` | Accept/validate the policy-owned selector; keep transport config unchanged |
| `experiments/scenario.py` | Validate fake/live selector offline and reject EC-only selection on other worlds |
| `experiments/study.py` | Forward the selector through the existing fake factory; live factory already owns its forwarding |
| New focused unit/integration tests | Literal compatibility, public rendering, malformed input, provenance and fake-provider replay cases |

Before editing implementation, capture literal v1 prompts, template hashes,
policy IDs, manifest metadata and representative fake-provider event chains
from the pre-change source. Cover EC and NIPD, plain and nontrivial skins,
compatible-provider identity with mocked transport, and invalid-output retries.
Expected fixtures must not be generated by the new implementation under test.

Then use failing-first focused tests for: exact old outputs; new IDs/hashes fixed
before any observations; absent/empty/unavailable/positive/negative distinctions;
strict unknown/future/duplicate/out-of-candidate rejection; sanitized errors;
JSON-escaped malicious-looking IDs; nested-skin and renderer/template drift;
matching fake/live-factory selection; selected versus default hash separation;
and unchanged authorization/credential preflight.

Use fake providers and intercepted compatible-provider requests only. Capture
the actual prompt at that boundary and assert malformed/drift cases make zero
calls. A small sealed fake EC v3 episode must show published reports in the
captured prompt, matching transcript prompt digests and manifest template IDs,
with no fabricated usage. Verify offline replay and a continuation using the
same configured adapter; replay must not invoke a provider. Full existing tests,
static checks and relevant historical artifact checks run on the final head.

No original scientific batch, live model selection, network provider request, paid run,
study freeze or final weight choice is part of this follow-up. The adapter makes
reports available to a model; fake tests establish plumbing, not model quality
or a benefit from audits.
