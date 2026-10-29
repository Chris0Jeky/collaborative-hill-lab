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
- ``ec_conditional_contributor``: the unchanged contributor's action rule,
  gated after a finite warmup by a conservative visible peer-contributor quorum.
  A zero quorum is an exact response-free action control (ADR-0012).

All choices iterate sorted ids, so behaviour is deterministic.
"""

from fractions import Fraction
from typing import Any, cast

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


def visible_peer_contributor_count(observation: dict[str, Any]) -> int:
    """Lower bound on distinct peers who have proposed or verified a claim.

    Named identities can be deduplicated across all claims. Without identities,
    each claim certifies its nonself proposer plus nonself verifiers: these roles
    are disjoint because EC forbids self-verification. Across anonymous claims
    the same peers may recur, so only the maximum per-claim bound is warranted.
    Inspection, sharing, challenges and outcome quality are not this signal.
    """
    identified: set[str] = set()
    lower_bound = 0
    for claim in observation["claims"]:
        if "proposer" in claim:
            identified.add(claim["proposer"])
        identified.update(claim.get("verifiers", ()))
        peers_in_claim = (int(not claim["proposed_by_me"])
                          + claim["n_verifications"] - int(claim["verified_by_me"]))
        lower_bound = max(lower_bound, peers_in_claim)
    identified.discard(observation["self_id"])
    return max(len(identified), lower_bound)


class ECConditionalContributorPolicy:
    """Contribution quorum over permitted cumulative claim history, version 1.

    Decisions at t < warmup_rounds use ECContributorPolicy. Later decisions do
    so iff the visible peer count is at least peer_threshold * (N - 1).
    Otherwise the action is Withhold. Re-evaluating every observation permits
    later recovery; no action history or latent state is stored on the policy.
    """

    def __init__(self, peer_threshold: Fraction | str | int = "1/2",
                 warmup_rounds: int | str = 3, share_evidence: bool | str = True) -> None:
        parsed = coerce_policy_params("ec_conditional_contributor", {
            "peer_threshold": peer_threshold, "warmup_rounds": warmup_rounds,
            "share_evidence": share_evidence,
        })
        self.peer_threshold = cast(Fraction, parsed["peer_threshold"])
        self.warmup_rounds = cast(int, parsed["warmup_rounds"])
        self.share_evidence = cast(bool, parsed["share_evidence"])
        self._contributor = ECContributorPolicy(share_evidence=self.share_evidence)
        self.policy_id = (
            f"ec_conditional_contributor[peer_threshold={self.peer_threshold},"
            f"warmup={self.warmup_rounds},share={self.share_evidence}]@1"
        )

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        if observation["round"] >= self.warmup_rounds:
            required = self.peer_threshold * (observation["n_agents"] - 1)
            if visible_peer_contributor_count(observation) < required:
                return ActionProposal(
                    action=WithholdAction(),
                    justification="visible peer contribution history is below my quorum",
                )
        return self._contributor.propose(observation, rng)


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
    if name == "ec_conditional_contributor":
        parsed = coerce_policy_params(name, params)
        return ECConditionalContributorPolicy(
            peer_threshold=cast(Fraction, parsed.get("peer_threshold", Fraction(1, 2))),
            warmup_rounds=cast(int, parsed.get("warmup_rounds", 3)),
            share_evidence=cast(bool, parsed.get("share_evidence", True)),
        )
    raise ValueError(f"unknown scripted EC policy: {name}")
