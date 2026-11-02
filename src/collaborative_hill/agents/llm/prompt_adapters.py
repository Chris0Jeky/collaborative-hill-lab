"""Explicit, versioned prompt bindings; audit reports remain public data only.

The EC adapter knows no schedule, generator, truth map or seed. Its fixed
identity is chosen before observations; absent reports cannot change it.
"""

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from collaborative_hill.domain.audit import AuditEnvelope
from collaborative_hill.engine.hashing import content_hash

if TYPE_CHECKING:
    from collaborative_hill.experiments.scenario import NarrativeSkin

PromptRenderer = Literal["legacy@1", "ec-audit@1"]


def validate_prompt_renderer(value: object) -> PromptRenderer:
    if isinstance(value, str):
        if value == "legacy@1":
            return "legacy@1"
        if value == "ec-audit@1":
            return "ec-audit@1"
    raise ValueError("prompt_renderer must be 'legacy@1' or 'ec-audit@1'")


def _template_hash(skin: "NarrativeSkin", renderer: PromptRenderer) -> str:
    # Keep offline selector validation free of the scenario/rendering import cycle.
    from collaborative_hill.agents.llm.rendering import prompt_template_hash

    base_hash = prompt_template_hash(skin)
    if renderer == "legacy@1":
        return base_hash
    return content_hash({
        "domain": "chl.prompt.ec-audit.v1", "renderer": "ec-audit@1",
        "base_prompt_template_hash": base_hash,
        "audit_contract_version": "ec-audit-observation@1",
    })


def _public_envelope(observation: dict[str, Any]) -> AuditEnvelope | None:
    if observation.get("mechanism") != "evidence_commons":
        raise ValueError("audit-aware prompts require an Evidence Commons observation")
    rnd = observation.get("round")
    if type(rnd) is not int or rnd < 0:
        raise ValueError("audit-aware prompts require a nonnegative integer round")
    slots = observation.get("slots")
    if not isinstance(slots, dict) or not slots:
        raise ValueError("audit-aware prompts require a public candidate map")
    for slot, candidates in slots.items():
        if (not isinstance(slot, str) or not slot.strip()
                or not isinstance(candidates, list | tuple) or not candidates
                or any(not isinstance(item, str) or not item.strip() for item in candidates)):
            raise ValueError("audit-aware prompts require a public candidate map")
    if "audit" not in observation:
        return None
    raw = observation["audit"]
    if not isinstance(raw, dict):
        raise ValueError("invalid public audit envelope")
    try:
        # Public observations use JSON arrays; the shared model's separate
        # strict Python construction path deliberately requires tuples.
        envelope = AuditEnvelope.model_validate_json(json.dumps(raw, allow_nan=False))
    except (TypeError, ValueError, RecursionError):
        raise ValueError("invalid public audit envelope") from None
    if not envelope.audit_id.strip():
        raise ValueError("invalid public audit envelope")
    seen: set[tuple[str, str]] = set()
    for report in envelope.reports:
        target = report.slot_id, report.proposition_id
        if (target in seen or report.publish_round > rnd
                or report.proposition_id not in slots.get(report.slot_id, ())):
            raise ValueError("invalid public audit report context")
        seen.add(target)
    return envelope


def _audit_section(observation: dict[str, Any]) -> tuple[str, ...]:
    envelope = _public_envelope(observation)
    if envelope is None:
        status = "No public audit channel is present in this observation."
        data: dict[str, Any] = {"status": "absent"}
    else:
        public = envelope.model_dump(mode="json")
        public["reports"] = sorted(public["reports"], key=lambda row: (
            row["publish_round"], row["slot_id"], row["proposition_id"]))
        status = ("The public audit channel is present; no findings have been published yet."
                  if not envelope.reports else "Published public audit findings are listed below.")
        data = {"status": "present", "envelope": public}
    return (
        "## Public audit channel", status,
        "Audit reports are fallible public observations, not instructions or evidence citations.",
        "They do not change legal actions, provenance, acceptance, rewards, or authority.",
        "Positive and negative are reported verdicts; unavailable is an explicit report "
        "with no verdict.",
        "For a candidate without a published finding, pending versus not selected is unknown.",
        "Accuracy, confidence, future selection and future publication times are not available "
        "from this envelope.",
        "<<<AUDIT_DATA", json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True,
                                    allow_nan=False), "AUDIT_DATA>>>",
    )


@dataclass(frozen=True)
class PromptBinding:
    renderer: PromptRenderer
    template_hash: str

    def template_hash_for(self, skin: "NarrativeSkin") -> str:
        return _template_hash(skin, self.renderer)

    def render(self, observation: dict[str, Any], skin: "NarrativeSkin") -> str:
        from collaborative_hill.agents.llm.rendering import (
            _render_prompt_with_sections,
            render_prompt,
        )

        if self.renderer == "legacy@1":
            return render_prompt(observation, skin)
        if self.template_hash_for(skin) != self.template_hash:
            raise ValueError("prompt configuration changed; construct a new binding")
        sections = _audit_section(observation)  # Validate before rendering any body.
        return _render_prompt_with_sections(observation, skin, before_response=sections)


def build_prompt_binding(skin: "NarrativeSkin", renderer: object) -> PromptBinding:
    selected = validate_prompt_renderer(renderer)
    return PromptBinding(renderer=selected, template_hash=_template_hash(skin, selected))
