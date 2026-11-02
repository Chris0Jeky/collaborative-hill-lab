"""Standalone audit observation contract; NOT an enabled EC engine channel.

See ADR-0017. This validates a declared synthetic accuracy and supplied findings;
it neither samples findings nor attests their accuracy. No policy receives truth.
"""

from copy import deepcopy
from fractions import Fraction
from typing import Annotated, Any, Literal, Self

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

CONTRACT_VERSION: Literal["ec-audit-observation@1"] = "ec-audit-observation@1"
HIDDEN_FIELDS = frozenset({"true_propositions", "truth_aligned"})
NonnegativeInt = Annotated[StrictInt, Field(ge=0)]


def exact_probability(value: str) -> Fraction:
    """Accept canonical rational strings only; never coerce bools or floats."""
    if not isinstance(value, str):
        raise ValueError("probability must be a canonical rational string")
    try:
        probability = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("probability must be a canonical rational string") from exc
    if not 0 <= probability <= 1 or str(probability) != value:
        raise ValueError("probability must be canonical and between zero and one")
    return probability


class StrictContractModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class AuditTarget(StrictContractModel):
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


class AuditConfig(StrictContractModel):
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


class AuditEnvelope(StrictContractModel):
    contract_version: Literal["ec-audit-observation@1"]
    audit_id: StrictStr
    contract_hash: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    reports: tuple[AuditFinding, ...]


def project_audit(config: AuditConfig, findings: tuple[AuditFinding, ...],
                  observed_round: object) -> AuditEnvelope:
    """Publish scheduled findings only when due, retaining earlier public reports."""
    if type(observed_round) is not int or observed_round < 0:
        raise ValueError("observed round must be a nonnegative integer")
    expected = {target.key() for target in config.schedule}
    actual = [finding.key() for finding in findings]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("findings must cover every scheduled target exactly once")
    due = tuple(sorted(
        (finding for finding in findings if finding.publish_round <= observed_round),
        key=lambda finding: (finding.publish_round, finding.slot_id, finding.proposition_id),
    ))
    return AuditEnvelope(contract_version=CONTRACT_VERSION, audit_id=config.audit_id,
                         contract_hash=config.contract_hash(), reports=due)


def has_hidden_fields(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(HIDDEN_FIELDS.intersection(value)) or any(
            has_hidden_fields(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(has_hidden_fields(item) for item in value)
    return False


def with_audit(observation: dict[str, Any], config: AuditConfig,
               findings: tuple[AuditFinding, ...]) -> dict[str, Any]:
    """Pure prototype augmentation; not called by the engine or any policy."""
    if observation.get("mechanism") != "evidence_commons":
        raise ValueError("audit prototype expects an Evidence Commons observation")
    if "audit" in observation or has_hidden_fields(observation):
        raise ValueError("base observation contains an audit collision or hidden fields")
    envelope = project_audit(config, findings, observation.get("round"))
    result = deepcopy(observation)
    result["audit"] = envelope.model_dump(mode="json")
    return result
