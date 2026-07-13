"""Evidence model: what the environment knows vs what agents may see.

An :class:`EvidenceSpec` lives in the InformationPlane of a scenario. Its
``truth_status`` is environment-only: it NEVER appears in observations (leak
tests enforce this with canary values). What an agent learns by inspecting an
item is its *structured facts* — which proposition it bears on and with which
stance — plus its freshness and source. Whether those facts track world truth
is exactly what agents must figure out from provenance and cross-checking.

Prose content for evidence belongs to narrative skins (keyed by evidence id),
so adversarial text (prompt-injection fixtures) is inert data by construction:
the mechanism only ever reads the typed fields defined here.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Stance = Literal["supports", "contradicts"]
Freshness = Literal["fresh", "stale"]


class EvidenceSpec(BaseModel):
    """One synthetic evidence item as defined by a scenario (mechanism-level)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str
    source_id: str
    version: int = 1
    slot_id: str
    proposition_id: str
    stance: Stance
    freshness: Freshness = "fresh"
    # Environment-only: does this item's stance point at the slot's true
    # proposition? Redundant with world truth but recorded for audit clarity.
    truth_aligned: bool
    # Marks the prompt-injection fixture. The malicious TEXT lives in skins;
    # this flag is mechanism-level so both skins carry the same fixture.
    adversarial: bool = False
    initial_holders: tuple[str, ...] = ()

    def observable_facts(self) -> dict[str, object]:
        """The projection an agent receives upon inspection. No truth fields."""
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "version": self.version,
            "slot_id": self.slot_id,
            "proposition_id": self.proposition_id,
            "stance": self.stance,
            "freshness": self.freshness,
        }
