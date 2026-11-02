"""Strict public audit data and the explicitly synthetic generation law.

ADR-0018 integrates ADR-0017's public contract without importing or rewriting
its historical experimental prototype. Only the trusted mechanism supplies
``target_is_true`` to the pure sampler; no policy receives that input or an RNG
factory. Public findings contain no private truth or internal draw fields.
"""

import random
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from collaborative_hill.engine.hashing import content_hash
from collaborative_hill.engine.seeds import SeedPath, derive_seed

CONTRACT_VERSION: Literal["ec-audit-observation@1"] = "ec-audit-observation@1"
GENERATOR_VERSION: Literal["ec-audit-generator@1"] = "ec-audit-generator@1"
NonnegativeInt = Annotated[StrictInt, Field(ge=0)]
AuditPurpose = Literal["availability", "verdict"]


def exact_probability(value: str) -> Fraction:
    """Canonical exact probability; bools, floats and alternate spellings fail."""
    if not isinstance(value, str):
        raise ValueError("probability must be a canonical rational string")
    try:
        probability = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("probability must be a canonical rational string") from exc
    if not 0 <= probability <= 1 or str(probability) != value:
        raise ValueError("probability must be canonical and between zero and one")
    return probability


class StrictAuditModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class AuditTarget(StrictAuditModel):
    slot_id: StrictStr
    proposition_id: StrictStr
    publish_round: NonnegativeInt

    @field_validator("slot_id", "proposition_id")
    @classmethod
    def nonblank_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identifiers must not be blank")
        return value

    def key(self) -> tuple[str, str, int]:
        return self.slot_id, self.proposition_id, self.publish_round


class AuditFinding(AuditTarget):
    verdict: Literal["positive", "negative", "unavailable"]


class AuditConfig(StrictAuditModel):
    """Unchanged ec-audit-observation@1 public configuration and hash shape."""

    contract_version: Literal["ec-audit-observation@1"]
    audit_id: StrictStr
    accuracy: StrictStr
    accuracy_semantics: Literal["symmetric-conditional-on-availability"]
    oracle_kind: Literal["synthetic-trusted-oracle"]
    dependence: Literal["independent-of-source-errors"]
    visibility: Literal["public"]
    selection: Literal["fixed-ex-ante-targets"]
    unavailable_semantics: Literal["explicit-no-verdict"]
    schedule: tuple[AuditTarget, ...] = Field(min_length=1)

    @field_validator("audit_id")
    @classmethod
    def nonblank_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identifiers must not be blank")
        return value

    @field_validator("accuracy")
    @classmethod
    def exact_accuracy(cls, value: str) -> str:
        exact_probability(value)
        return value

    @model_validator(mode="after")
    def unique_targets(self) -> Self:
        targets = [(target.slot_id, target.proposition_id) for target in self.schedule]
        if len(set(targets)) != len(targets):
            raise ValueError("each slot/proposition may be scheduled only once")
        return self

    def contract_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))


class AuditEnvelope(StrictAuditModel):
    contract_version: Literal["ec-audit-observation@1"]
    audit_id: StrictStr
    contract_hash: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    reports: tuple[AuditFinding, ...]


class AuditGenerationConfig(StrictAuditModel):
    generator_version: Literal["ec-audit-generator@1"]
    unavailable_probability: StrictStr
    draw_dependence: Literal["independent-per-target"]
    unavailable_dependence: Literal["independent-of-truth-source-errors-and-correctness"]

    @field_validator("unavailable_probability")
    @classmethod
    def exact_unavailability(cls, value: str) -> str:
        exact_probability(value)
        return value


class AuditMechanismConfig(StrictAuditModel):
    contract: AuditConfig
    generation: AuditGenerationConfig

    @model_validator(mode="after")
    def valid_seed_components(self) -> Self:
        for target in self.contract.schedule:
            derive_seed(self.generation.generator_version, self.contract.contract_version,
                        self.contract.audit_id, target.slot_id, target.proposition_id)
        return self

    def validate_world(self, slots: Mapping[str, Sequence[str]], rounds: int) -> None:
        """Bind public targets and times to the actual EC candidate set/horizon."""
        if type(rounds) is not int or rounds <= 0:
            raise ValueError("audits require a positive integer world horizon")
        for target in self.contract.schedule:
            if target.slot_id not in slots:
                raise ValueError(f"audit target has unknown slot: {target.slot_id}")
            if target.proposition_id not in slots[target.slot_id]:
                raise ValueError("audit target proposition is not a candidate of its slot")
            if target.publish_round >= rounds:
                raise ValueError("audit publish_round must be less than the world horizon")


def audit_seed_key(config: AuditMechanismConfig, target: AuditTarget,
                   purpose: AuditPurpose) -> SeedPath:
    """Relative key; the runner adds the preserved mechanism-root opening scope."""
    if purpose not in ("availability", "verdict"):
        raise ValueError("unknown audit draw purpose")
    if target not in config.contract.schedule:
        raise ValueError("audit target must be scheduled")
    return (config.generation.generator_version, config.contract.contract_version,
            config.contract.audit_id, target.slot_id, target.proposition_id, purpose)


def sample_audit_finding(
    config: AuditMechanismConfig,
    target: AuditTarget,
    *,
    target_is_true: bool,
    availability_rng: random.Random,
    verdict_rng: random.Random,
) -> AuditFinding:
    """Sample the declared synthetic law from separate exact integer draws.

    Availability and correctness are independent model assumptions, not measured
    calibration. This function receives neither a world map nor source errors.
    """
    if type(target_is_true) is not bool:
        raise ValueError("target_is_true must be bool")
    if target not in config.contract.schedule:
        raise ValueError("audit target must be scheduled")
    unavailable = exact_probability(config.generation.unavailable_probability)
    if availability_rng.randrange(unavailable.denominator) < unavailable.numerator:
        verdict: Literal["positive", "negative", "unavailable"] = "unavailable"
    else:
        accuracy = exact_probability(config.contract.accuracy)
        correct = verdict_rng.randrange(accuracy.denominator) < accuracy.numerator
        verdict = "positive" if target_is_true == correct else "negative"
    return AuditFinding(slot_id=target.slot_id, proposition_id=target.proposition_id,
                        publish_round=target.publish_round, verdict=verdict)


def project_published_audit(config: AuditConfig, findings: tuple[AuditFinding, ...],
                            observed_round: object) -> AuditEnvelope:
    """Project exactly the due prefix; unlike the prototype, need no future verdicts."""
    if type(observed_round) is not int or observed_round < 0:
        raise ValueError("observed round must be a nonnegative integer")
    expected = {target.key() for target in config.schedule
                if target.publish_round <= observed_round}
    actual = [finding.key() for finding in findings]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("published findings must cover exactly the due schedule prefix")
    ordered = tuple(sorted(findings, key=lambda item: (item.publish_round,
                                                      item.slot_id, item.proposition_id)))
    return AuditEnvelope(contract_version=CONTRACT_VERSION, audit_id=config.audit_id,
                         contract_hash=config.contract_hash(), reports=ordered)
