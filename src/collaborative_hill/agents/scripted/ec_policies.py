"""Scripted Evidence Commons personas. Purely observation-driven (no internal
memory), so a rebuilt instance mid-branch behaves identically to the original.

- ``ec_contributor``: inspect -> (share under private topology) -> propose from
  fresh supporting inspected evidence -> verify others' claims -> withhold.
- ``ec_freerider``:  withholds every round; collects the collective reward.
- ``ec_verifier``:   inspect -> challenge provenance-broken claims it can refute
  -> verify others' claims -> withhold. Never proposes.
- ``ec_misinformer``: like a contributor but cites ANY supporting evidence
  including stale, never shares, never verifies. Given a corpus where its
  holdings support false propositions, it propagates misinformation without
  ever reading world truth (behaviour emerges from corpus + rule).

All choices iterate sorted ids, so behaviour is deterministic.
"""

from typing import Any

from collaborative_hill.domain.actions import (
    ActionProposal,
    ChallengeClaimAction,
    InspectEvidenceAction,
    ProposeClaimAction,
    ShareEvidenceAction,
    VerifyClaimAction,
    WithholdAction,
)


def _inspected(observation: dict[str, Any]) -> list[dict[str, Any]]:
    return [e for e in observation["evidence"] if "facts" in e]


def _uninspected_ids(observation: dict[str, Any]) -> list[str]:
    return sorted(e["evidence_id"] for e in observation["evidence"] if "facts" not in e)


def _slots_with_my_claim(observation: dict[str, Any]) -> set[str]:
    return {c["slot_id"] for c in observation["claims"] if c["proposed_by_me"]}


def _claimed_propositions(observation: dict[str, Any]) -> set[tuple[str, str]]:
    return {(c["slot_id"], c["proposition_id"]) for c in observation["claims"]}


class ECContributorPolicy:
    def __init__(self, share_evidence: bool = True) -> None:
        self.share_evidence = share_evidence
        self.policy_id = f"ec_contributor[share={share_evidence}]@1"

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        del rng
        if observation["my_budgets"]["inspect"] > 0:
            pending = _uninspected_ids(observation)
            if pending:
                return ActionProposal(action=InspectEvidenceAction(evidence_id=pending[0]),
                                      justification="inspecting unread evidence")
        fresh_support = [
            e for e in _inspected(observation)
            if e["facts"]["stance"] == "supports" and e["facts"]["freshness"] == "fresh"
        ]
        if self.share_evidence and observation["evidence_topology"] == "private":
            unshared = [e for e in fresh_support if not e["public"]]
            if unshared:
                eid = sorted(e["evidence_id"] for e in unshared)[0]
                return ActionProposal(
                    action=ShareEvidenceAction(evidence_id=eid),
                    justification="sharing supporting evidence so it can be verified")
        my_slots = _slots_with_my_claim(observation)
        already = _claimed_propositions(observation)
        for e in sorted(fresh_support, key=lambda x: x["evidence_id"]):
            slot = e["facts"]["slot_id"]
            prop = e["facts"]["proposition_id"]
            if slot in my_slots or (slot, prop) in already:
                continue
            citations = tuple(sorted(
                x["evidence_id"] for x in fresh_support
                if x["facts"]["slot_id"] == slot and x["facts"]["proposition_id"] == prop
            ))
            return ActionProposal(
                action=ProposeClaimAction(slot_id=slot, proposition_id=prop,
                                          evidence_ids=citations),
                justification="proposing a claim my fresh evidence supports",
            )
        if observation["my_budgets"]["verify"] > 0:
            for c in observation["claims"]:
                if not c["proposed_by_me"] and not c["verified_by_me"]:
                    return ActionProposal(action=VerifyClaimAction(claim_id=c["claim_id"]),
                                          justification="verifying an unchecked claim")
        return ActionProposal(action=WithholdAction(), justification="nothing productive left")


class ECFreeriderPolicy:
    policy_id = "ec_freerider@1"

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        del observation, rng
        return ActionProposal(action=WithholdAction(),
                              justification="conserving effort")


class ECVerifierPolicy:
    policy_id = "ec_verifier@1"

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        del rng
        if observation["my_budgets"]["inspect"] > 0:
            pending = _uninspected_ids(observation)
            if pending:
                return ActionProposal(action=InspectEvidenceAction(evidence_id=pending[0]),
                                      justification="inspecting unread evidence")
        contradictions = {
            (e["facts"]["slot_id"], e["facts"]["proposition_id"]): e["evidence_id"]
            for e in _inspected(observation)
            if e["facts"]["stance"] == "contradicts" and e["facts"]["freshness"] == "fresh"
        }
        for c in observation["claims"]:
            key = (c["slot_id"], c["proposition_id"])
            if key in contradictions and not c["challenged_by_me"] and not c["proposed_by_me"]:
                return ActionProposal(
                    action=ChallengeClaimAction(claim_id=c["claim_id"],
                                                evidence_ids=(contradictions[key],)),
                    justification="my evidence contradicts this claim",
                )
        if observation["my_budgets"]["verify"] > 0:
            for c in observation["claims"]:
                if not c["proposed_by_me"] and not c["verified_by_me"]:
                    return ActionProposal(action=VerifyClaimAction(claim_id=c["claim_id"]),
                                          justification="verifying an unchecked claim")
        return ActionProposal(action=WithholdAction(), justification="nothing to check")


class ECMisinformerPolicy:
    policy_id = "ec_misinformer@1"

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        del rng
        if observation["my_budgets"]["inspect"] > 0:
            pending = _uninspected_ids(observation)
            if pending:
                return ActionProposal(action=InspectEvidenceAction(evidence_id=pending[0]),
                                      justification="inspecting unread evidence")
        supporting = [
            e for e in _inspected(observation) if e["facts"]["stance"] == "supports"
        ]  # stale allowed — that is the point
        my_slots = _slots_with_my_claim(observation)
        already = _claimed_propositions(observation)
        for e in sorted(supporting, key=lambda x: x["evidence_id"]):
            slot = e["facts"]["slot_id"]
            prop = e["facts"]["proposition_id"]
            if slot in my_slots or (slot, prop) in already:
                continue
            citations = tuple(sorted(
                x["evidence_id"] for x in supporting
                if x["facts"]["slot_id"] == slot and x["facts"]["proposition_id"] == prop
            ))
            return ActionProposal(
                action=ProposeClaimAction(slot_id=slot, proposition_id=prop,
                                          evidence_ids=citations),
                justification="proposing a claim my evidence supports",
            )
        return ActionProposal(action=WithholdAction(), justification="waiting")


def build_ec_policy(name: str, params: dict[str, Any]) -> Any:
    if name == "ec_contributor":
        share = params.get("share_evidence", True)
        return ECContributorPolicy(share_evidence=bool(share))
    if name == "ec_freerider":
        return ECFreeriderPolicy()
    if name == "ec_verifier":
        return ECVerifierPolicy()
    if name == "ec_misinformer":
        return ECMisinformerPolicy()
    raise ValueError(f"unknown scripted EC policy: {name}")
