"""Independent skeptical-rule switches, an additive research policy (ADR-0016).

The original conditional/skeptical v1 implementations remain authoritative for
their existing identifiers. This variant only reads the same observations.
"""

from fractions import Fraction
from typing import Any, cast

from collaborative_hill.agents.scripted.ec_policies import (
    ECSkepticalContributorPolicy,
    _claimed_propositions,
    _inspected,
    _slots_with_my_claim,
    _uninspected_ids,
    visible_peer_contributor_count,
)
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import (
    ActionProposal,
    ChallengeClaimAction,
    InspectEvidenceAction,
    ProposeClaimAction,
    ShareEvidenceAction,
    VerifyClaimAction,
    WithholdAction,
)


class ECAblationContributorPolicy:
    """SHCR component switches with no latent memory or truth/utility input."""

    def __init__(self, evidence_screen: bool | str = True,
                 share_contradictions: bool | str = True,
                 challenge_claims: bool | str = True,
                 require_read_citation: bool | str = True,
                 min_sources: int | str = 2,
                 peer_threshold: Fraction | str | int = "1/2",
                 warmup_rounds: int | str = 3, share_evidence: bool | str = True) -> None:
        parsed = coerce_policy_params("ec_ablation_contributor", {
            "evidence_screen": evidence_screen, "share_contradictions": share_contradictions,
            "challenge_claims": challenge_claims, "require_read_citation": require_read_citation,
            "min_sources": min_sources, "peer_threshold": peer_threshold,
            "warmup_rounds": warmup_rounds, "share_evidence": share_evidence,
        })
        self.evidence_screen = cast(bool, parsed["evidence_screen"])
        self.share_contradictions = cast(bool, parsed["share_contradictions"])
        self.challenge_claims = cast(bool, parsed["challenge_claims"])
        self.require_read_citation = cast(bool, parsed["require_read_citation"])
        self.min_sources = cast(int, parsed["min_sources"])
        self.peer_threshold = cast(Fraction, parsed["peer_threshold"])
        self.warmup_rounds = cast(int, parsed["warmup_rounds"])
        self.share_evidence = cast(bool, parsed["share_evidence"])
        self._screen = ECSkepticalContributorPolicy(
            min_sources=self.min_sources, peer_threshold=self.peer_threshold,
            warmup_rounds=self.warmup_rounds, share_evidence=self.share_evidence)
        self.policy_id = (
            f"ec_ablation_contributor[screen={self.evidence_screen},"
            f"share_contradictions={self.share_contradictions},challenge={self.challenge_claims},"
            f"read_citation={self.require_read_citation},min_sources={self.min_sources},"
            f"peer_threshold={self.peer_threshold},warmup={self.warmup_rounds},"
            f"share={self.share_evidence}]@1")

    def _passes(self, observation: dict[str, Any], slot: str, proposition: str) -> bool:
        return (not self.evidence_screen
                or self._screen.passes_screen(observation, slot, proposition))

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        del rng
        if observation["round"] >= self.warmup_rounds:
            required = self.peer_threshold * (observation["n_agents"] - 1)
            if visible_peer_contributor_count(observation) < required:
                return ActionProposal(action=WithholdAction(),
                                      justification="visible peer contribution is below my quorum")
        if observation["my_budgets"]["inspect"] > 0:
            pending = _uninspected_ids(observation)
            if pending:
                return ActionProposal(action=InspectEvidenceAction(evidence_id=pending[0]),
                                      justification="inspecting unread evidence")
        fresh = sorted((e for e in _inspected(observation) if e["facts"]["freshness"] == "fresh"),
                       key=lambda e: e["evidence_id"])
        if self.share_evidence and observation["evidence_topology"] == "private":
            for item in fresh:
                if (not item["public"] and (item["facts"]["stance"] == "supports"
                                            or self.share_contradictions)):
                    return ActionProposal(
                        action=ShareEvidenceAction(evidence_id=item["evidence_id"]),
                        justification="sharing evidence allowed by my components")
        return self._act_on_claims(observation, fresh)

    def _act_on_claims(self, observation: dict[str, Any],
                       fresh: list[dict[str, Any]]) -> ActionProposal:
        def cited(stance: str, slot: str, proposition: str) -> tuple[str, ...]:
            return tuple(e["evidence_id"] for e in fresh if e["facts"]["stance"] == stance
                         and e["facts"]["slot_id"] == slot
                         and e["facts"]["proposition_id"] == proposition)

        if self.challenge_claims:
            for claim in observation["claims"]:
                if claim["proposed_by_me"] or claim["challenged_by_me"]:
                    continue
                against = cited("contradicts", claim["slot_id"], claim["proposition_id"])
                if against:
                    return ActionProposal(action=ChallengeClaimAction(
                        claim_id=claim["claim_id"], evidence_ids=against),
                        justification="my fresh evidence contradicts this peer claim")
        my_slots = _slots_with_my_claim(observation)
        already = _claimed_propositions(observation)
        for item in fresh:
            slot, proposition = item["facts"]["slot_id"], item["facts"]["proposition_id"]
            if (item["facts"]["stance"] != "supports" or slot in my_slots
                    or (slot, proposition) in already or not self._passes(observation, slot,
                                                                           proposition)):
                continue
            return ActionProposal(action=ProposeClaimAction(
                slot_id=slot, proposition_id=proposition,
                evidence_ids=cited("supports", slot, proposition)),
                justification="proposing a claim allowed by my components")
        if observation["my_budgets"]["verify"] > 0:
            for claim in observation["claims"]:
                if (claim["proposed_by_me"] or claim["verified_by_me"]
                        or not self._passes(observation, claim["slot_id"],
                                            claim["proposition_id"])):
                    continue
                read_support = cited("supports", claim["slot_id"], claim["proposition_id"])
                if (self.require_read_citation
                        and not set(claim["evidence_ids"]) & set(read_support)):
                    continue
                return ActionProposal(action=VerifyClaimAction(claim_id=claim["claim_id"]),
                                      justification="verifying a claim allowed by my components")
        return ActionProposal(action=WithholdAction(), justification="no permitted contribution")
