"""Five-plane ScenarioSpec, NarrativeSkin, and the scenario compiler.

A scenario composes five causal planes (ADR-0003):

    world        - true state, payoffs, transitions, termination
    information  - evidence items, visibility, noise/stale/adversarial fixtures
    interaction  - pairwise / neighbourhood / commons structure, scheduling
    institution  - accountability + evidence topology (+ extension points)
    cognition    - which policy drives each agent (scripted / replay / llm)

The compiler validates plane combinations and produces a ResolvedScenario with
four content hashes (ADR-0004):

    mechanism_hash   - world+information+interaction+institution+agent roster.
                       Everything that defines the GAME. Skins cannot touch it.
    narrative_hash   - the skin only (names, prose, wording).
    evidence_corpus_hash - the information plane's evidence list.
    scenario_hash    - mechanism_hash + narrative_hash + cognition plane.

Numeric spec fields are ints or exact rational STRINGS ("1/10", "0.1" is also
accepted by Fraction) — never floats — so every spec is canonically hashable.
"""

from fractions import Fraction
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from collaborative_hill.domain.evidence import EvidenceSpec
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import (
    ECParams,
    ECWorldSpec,
    EvidenceCommonsMechanism,
)
from collaborative_hill.domain.world.nipd import NIPDMechanism, NIPDParams
from collaborative_hill.engine.hashing import content_hash

# --- world plane -------------------------------------------------------------


class NIPDWorld(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["nipd"] = "nipd"
    mode: Literal["pairwise", "neighbourhood"]
    params: NIPDParams = NIPDParams()
    rounds: int = 50


class ECWorld(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["evidence_commons"] = "evidence_commons"
    slots: dict[str, tuple[str, ...]]
    true_propositions: dict[str, str]
    params: ECParams = ECParams()


class InformationPlane(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence: tuple[EvidenceSpec, ...] = ()


class InteractionPlane(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    structure: Literal["pairwise", "neighbourhood", "commons"]
    scheduling: Literal["simultaneous"] = "simultaneous"
    graph: Literal["complete"] = "complete"  # extension point: named topologies
    communication: Literal["none", "messages"] = "none"


class PolicySpec(BaseModel):
    """Cognition assignment. ``params`` values are int/str/bool only (rationals
    as strings) so specs stay hashable; builders parse with Fraction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    params: dict[str, int | str | bool] = Field(default_factory=dict)


class AgentSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_id: str
    policy: PolicySpec


class CognitionPlane(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    agents: tuple[AgentSpec, ...]


class NarrativeSkin(BaseModel):
    """Names, prose, wording — and structurally nothing else.

    A skin has no numeric or rule-bearing fields, so it cannot change valid
    actions, payoffs, visibility, institutional rules, or metrics. Metamorphic
    tests additionally prove that swapping skins leaves mechanism_hash and the
    full event chain unchanged for scripted runs.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    skin_id: str
    version: int = 1
    title: str = ""
    preamble: str = ""
    agent_names: dict[str, str] = Field(default_factory=dict)
    action_wording: dict[str, str] = Field(default_factory=dict)
    slot_titles: dict[str, str] = Field(default_factory=dict)
    proposition_texts: dict[str, str] = Field(default_factory=dict)
    source_names: dict[str, str] = Field(default_factory=dict)
    evidence_content: dict[str, str] = Field(default_factory=dict)


class ScenarioSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    scenario_id: str
    description: str = ""
    world: NIPDWorld | ECWorld = Field(discriminator="kind")
    information: InformationPlane = InformationPlane()
    interaction: InteractionPlane
    institution: InstitutionConfig = InstitutionConfig()
    cognition: CognitionPlane

    @model_validator(mode="after")
    def _check_combination(self) -> "ScenarioSpec":
        ids = [a.agent_id for a in self.cognition.agents]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate agent ids in cognition plane")
        if isinstance(self.world, NIPDWorld):
            if self.interaction.structure != self.world.mode:
                raise ValueError(
                    f"interaction.structure {self.interaction.structure} must match "
                    f"nipd world mode {self.world.mode}"
                )
            if self.information.evidence:
                raise ValueError("NIPD scenarios carry no evidence corpus")
        else:
            if self.interaction.structure != "commons":
                raise ValueError("evidence_commons requires interaction.structure=commons")
            if not self.information.evidence:
                raise ValueError("evidence_commons requires a non-empty evidence corpus")
        return self


# --- compiler ------------------------------------------------------------------


class ResolvedScenario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    spec: ScenarioSpec
    skin: NarrativeSkin
    mechanism_hash: str
    narrative_hash: str
    evidence_corpus_hash: str
    scenario_hash: str

    def build_mechanism(self) -> Any:
        return build_mechanism(self.spec)


def mechanism_view(spec: ScenarioSpec) -> dict[str, Any]:
    """The exact projection covered by mechanism_hash: the game, not the players'
    minds and not the prose. Agent roster (ids) is structural; policies are not."""
    return {
        "domain": "chl.mechanism.v1",
        "world": spec.world.model_dump(mode="json"),
        "information": spec.information.model_dump(mode="json"),
        "interaction": spec.interaction.model_dump(mode="json"),
        "institution": spec.institution.model_dump(mode="json"),
        "agent_ids": [a.agent_id for a in spec.cognition.agents],
    }


def compile_scenario(spec: ScenarioSpec, skin: NarrativeSkin) -> ResolvedScenario:
    _validate_skin_references(spec, skin)
    build_mechanism(spec)  # raises on inconsistent world/information planes
    mech_hash = content_hash(mechanism_view(spec))
    narr_hash = content_hash({"domain": "chl.skin.v1", **skin.model_dump(mode="json")})
    corpus_hash = content_hash(
        {"domain": "chl.evidence.v1",
         "evidence": [e.model_dump(mode="json") for e in spec.information.evidence]}
    )
    scenario_hash = content_hash(
        {
            "domain": "chl.scenario.v1",
            "scenario_id": spec.scenario_id,
            "mechanism_hash": mech_hash,
            "narrative_hash": narr_hash,
            "cognition": spec.cognition.model_dump(mode="json"),
        }
    )
    return ResolvedScenario(
        spec=spec,
        skin=skin,
        mechanism_hash=mech_hash,
        narrative_hash=narr_hash,
        evidence_corpus_hash=corpus_hash,
        scenario_hash=scenario_hash,
    )


def _validate_skin_references(spec: ScenarioSpec, skin: NarrativeSkin) -> None:
    agent_ids = {a.agent_id for a in spec.cognition.agents}
    for aid in skin.agent_names:
        if aid not in agent_ids:
            raise ValueError(f"skin names unknown agent {aid}")
    evidence_ids = {e.evidence_id for e in spec.information.evidence}
    for eid in skin.evidence_content:
        if eid not in evidence_ids:
            raise ValueError(f"skin provides content for unknown evidence {eid}")
    if isinstance(spec.world, ECWorld):
        for sid in skin.slot_titles:
            if sid not in spec.world.slots:
                raise ValueError(f"skin titles unknown slot {sid}")
        props = {p for candidates in spec.world.slots.values() for p in candidates}
        for pid in skin.proposition_texts:
            if pid not in props:
                raise ValueError(f"skin text for unknown proposition {pid}")


def build_mechanism(spec: ScenarioSpec) -> Any:
    agent_ids = [a.agent_id for a in spec.cognition.agents]
    if isinstance(spec.world, NIPDWorld):
        return NIPDMechanism(
            agent_ids=agent_ids,
            mode=spec.world.mode,
            params=spec.world.params,
            rounds=spec.world.rounds,
        )
    ec_spec = ECWorldSpec(
        agent_ids=tuple(agent_ids),
        slots=spec.world.slots,
        true_propositions=spec.world.true_propositions,
        evidence=spec.information.evidence,
        params=spec.world.params,
    )
    return EvidenceCommonsMechanism(spec=ec_spec, institution=spec.institution)


def parse_rational(value: int | str, default: str = "0") -> Fraction:
    """Parse a spec-level rational (int or string like '1/10' or '0.1')."""
    if value is None:
        value = default
    return Fraction(value)
