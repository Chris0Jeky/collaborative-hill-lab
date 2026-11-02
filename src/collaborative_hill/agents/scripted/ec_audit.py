"""Versioned negative-audit veto over the unchanged skeptical EC rule.

The wrapper is observation-driven and has no action/verdict memory. A published
negative report can suppress the selected proposal or verification; every other
choice is the original rule's choice. Audits never supply citations or silently
change provenance, acceptance or rewards. See experiments/audit-feedback/DESIGN.md.
"""

import json
from fractions import Fraction
from typing import Any, cast

from collaborative_hill.agents.scripted.ec_policies import ECSkepticalContributorPolicy
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import (
    ActionProposal,
    ProposeClaimAction,
    VerifyClaimAction,
    WithholdAction,
)
from collaborative_hill.domain.audit import AuditEnvelope


def _negative_targets(observation: dict[str, Any]) -> set[tuple[str, str]]:
    """Validate every present envelope before any action, including a no-op."""
    if "audit" not in observation:
        return set()
    raw = observation["audit"]
    if not isinstance(raw, dict):
        raise ValueError("audit must be a public envelope object")
    try:
        # Real public observations use JSON lists; the shared model deliberately
        # requires tuples only at its strict Python-object construction boundary.
        envelope = AuditEnvelope.model_validate_json(json.dumps(raw, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid public audit envelope") from exc
    if not envelope.audit_id.strip():
        raise ValueError("audit identity must not be blank")
    observed_round = observation.get("round")
    if type(observed_round) is not int or observed_round < 0:
        raise ValueError("audit requires a nonnegative integer observation round")
    slots = observation.get("slots")
    if not isinstance(slots, dict):
        raise ValueError("audit requires the observation's candidate map")

    seen: set[tuple[str, str]] = set()
    negative: set[tuple[str, str]] = set()
    for report in envelope.reports:
        target = report.slot_id, report.proposition_id
        if target in seen:
            raise ValueError("audit reports repeat a target")
        seen.add(target)
        candidates = slots.get(report.slot_id)
        if (not isinstance(candidates, list | tuple)
                or report.proposition_id not in candidates):
            raise ValueError("audit report target is outside the observation's candidates")
        if report.publish_round > observed_round:
            raise ValueError("audit report is not yet public at this observation round")
        if report.verdict == "negative":
            negative.add(target)
    return negative


class ECAuditVetoContributorPolicy:
    """Veto only the selected claim action when its public audit is negative."""

    def __init__(self, min_sources: int | str = 2,
                 peer_threshold: Fraction | str | int = "1/2",
                 warmup_rounds: int | str = 3, share_evidence: bool | str = True) -> None:
        parsed = coerce_policy_params("ec_audit_veto_contributor", {
            "min_sources": min_sources, "peer_threshold": peer_threshold,
            "warmup_rounds": warmup_rounds, "share_evidence": share_evidence,
        })
        self._skeptical = ECSkepticalContributorPolicy(
            min_sources=cast(int, parsed["min_sources"]),
            peer_threshold=cast(Fraction, parsed["peer_threshold"]),
            warmup_rounds=cast(int, parsed["warmup_rounds"]),
            share_evidence=cast(bool, parsed["share_evidence"]),
        )
        self.policy_id = (
            f"ec_audit_veto_contributor[min_sources={self._skeptical.min_sources},"
            f"peer_threshold={self._skeptical.peer_threshold},"
            f"warmup={self._skeptical.warmup_rounds},"
            f"share={self._skeptical.share_evidence}]@1"
        )

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        negative = _negative_targets(observation)
        proposal = self._skeptical.propose(observation, rng)
        action = proposal.action
        if isinstance(action, ProposeClaimAction):
            veto = (action.slot_id, action.proposition_id) in negative
        elif isinstance(action, VerifyClaimAction):
            veto = any(
                claim["claim_id"] == action.claim_id
                and (claim["slot_id"], claim["proposition_id"]) in negative
                for claim in observation["claims"]
            )
        else:
            veto = False
        if veto:
            return ActionProposal(
                action=WithholdAction(),
                justification="published audit is negative for the selected candidate",
            )
        return proposal
