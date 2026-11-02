"""Opt-in EC v3: scheduled public audit reports, unchanged task resolution.

Only prepare_round consults private truth, and only for targets due now. State
contains published findings, never future verdicts or private generator inputs.
The runner supplies isolated keyed RNGs and emits returned events before any
observations; see ADR-0018 for exact checkpoint and replay boundaries.
"""

import random
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from collaborative_hill.domain.audit import (
    AuditFinding,
    audit_seed_key,
    project_published_audit,
    sample_audit_finding,
)
from collaborative_hill.domain.institutions import AuditInstitutionConfig
from collaborative_hill.domain.world.evidence_commons import ECWorldSpec, EvidenceCommonsMechanism
from collaborative_hill.engine.events import ENGINE_ACTOR, EventType
from collaborative_hill.engine.seeds import SeedPath

EC_AUDIT_ENGINE_VERSION = 3
EC_AUDIT_OBSERVATION_SCHEMA_VERSION = 3


class AuditedEvidenceCommonsMechanism(EvidenceCommonsMechanism):
    """Auxiliary observation channel; legality, resolve and rewards stay inherited."""

    def __init__(self, *, spec: ECWorldSpec, institution: AuditInstitutionConfig) -> None:
        if not isinstance(institution, AuditInstitutionConfig):
            raise ValueError("audited EC requires an explicit audit institution")
        super().__init__(spec=spec, institution=institution)
        self.audit = institution.audit
        self.audit.validate_world(spec.slots, self.params.rounds)

    def initial_state(self) -> dict[str, Any]:
        return {**super().initial_state(), "audit_reports": []}

    def _published_state(self, state: dict[str, Any]) -> tuple[int, tuple[AuditFinding, ...]]:
        rnd, reports = state.get("round"), state.get("audit_reports")
        if type(rnd) is not int or rnd < 0:
            raise ValueError("audit state round must be a nonnegative integer")
        if not isinstance(reports, list) or any(not isinstance(item, dict) for item in reports):
            raise ValueError("audit_reports must be a list of public finding objects")
        return rnd, tuple(AuditFinding.model_validate(item) for item in reports)

    def prepare_round(
        self,
        state: dict[str, Any],
        rng_for_key: Callable[[SeedPath], random.Random],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        rnd, findings = self._published_state(state)
        earlier = {target.key() for target in self.audit.contract.schedule
                   if target.publish_round < rnd}
        through_now = {target.key() for target in self.audit.contract.schedule
                       if target.publish_round <= rnd}
        actual = [finding.key() for finding in findings]
        keys = set(actual)
        if len(actual) != len(keys) or keys not in (earlier, through_now):
            raise ValueError("published audit state must contain exactly the complete earlier "
                             "or complete current schedule prefix")
        new = deepcopy(state)
        if keys == through_now:
            return new, []

        due = sorted((target for target in self.audit.contract.schedule
                      if target.publish_round == rnd),
                     key=lambda target: (target.slot_id, target.proposition_id))
        events = []
        for target in due:
            finding = sample_audit_finding(
                self.audit, target,
                target_is_true=self.spec.true_propositions[target.slot_id] == target.proposition_id,
                availability_rng=rng_for_key(audit_seed_key(self.audit, target, "availability")),
                verdict_rng=rng_for_key(audit_seed_key(self.audit, target, "verdict")),
            )
            # Separate serialized copies keep event/observation callers from
            # mutating the checkpoint state through a shared nested dictionary.
            new["audit_reports"].append(finding.model_dump(mode="json"))
            events.append({
                "event_type": EventType.AUDIT_PUBLISHED.value, "actor": ENGINE_ACTOR,
                "payload": {
                    "contract_version": self.audit.contract.contract_version,
                    "audit_id": self.audit.contract.audit_id,
                    "contract_hash": self.audit.contract.contract_hash(),
                    "report": finding.model_dump(mode="json"),
                },
            })
        return new, events

    def observe(self, state: dict[str, Any], agent_id: str) -> dict[str, Any]:
        rnd, findings = self._published_state(state)
        envelope = project_published_audit(self.audit.contract, findings, rnd)
        return {**super().observe(state, agent_id),
                "observation_schema_version": EC_AUDIT_OBSERVATION_SCHEMA_VERSION,
                "audit": envelope.model_dump(mode="json")}
