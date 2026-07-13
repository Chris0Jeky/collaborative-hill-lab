"""Typed action protocol: a closed, discriminated union.

Agents — scripted or LLM — may only propose values of :data:`Action`. There is
no free-text world mutation anywhere: an LLM adapter that fails to produce a
valid member of this union yields an ``ActionRejected`` event and the
configured fallback (fail the run, or an explicit ``AbstainAction``), never a
silently repaired action (ADR-0007).

Design note: Evidence Commons propositions are a *finite, environment-defined
space* — agents reference propositions and evidence by id. Natural language
belongs to narrative skins only, so no scientific scoring ever parses prose.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

Move = Literal["C", "D"]


class _ActionBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# --- Canonical micro-mechanism (N-IPD) ------------------------------------


class CooperateAction(_ActionBase):
    """Single collective vote to cooperate (neighbourhood mode)."""

    type: Literal["cooperate"] = "cooperate"


class DefectAction(_ActionBase):
    """Single collective vote to defect (neighbourhood mode)."""

    type: Literal["defect"] = "defect"


class PairwiseVoteAction(_ActionBase):
    """One move per opponent (pairwise mode).

    ``moves`` must contain exactly the other agents' ids — the validator in
    the mechanism enforces this, so an agent can neither skip nor invent
    opponents.
    """

    type: Literal["pairwise_vote"] = "pairwise_vote"
    moves: dict[str, Move]


# --- Evidence Commons -------------------------------------------------------


class InspectEvidenceAction(_ActionBase):
    """Spend inspection budget to read one evidence item's structured facts."""

    type: Literal["inspect_evidence"] = "inspect_evidence"
    evidence_id: str


class ShareEvidenceAction(_ActionBase):
    """Make an evidence item you hold visible to others (costly)."""

    type: Literal["share_evidence"] = "share_evidence"
    evidence_id: str


class ProposeClaimAction(_ActionBase):
    """Propose that ``proposition_id`` fills briefing slot ``slot_id``, citing evidence."""

    type: Literal["propose_claim"] = "propose_claim"
    slot_id: str
    proposition_id: str
    evidence_ids: tuple[str, ...] = ()


class ChallengeClaimAction(_ActionBase):
    """Contest an existing claim, optionally citing counter-evidence."""

    type: Literal["challenge_claim"] = "challenge_claim"
    claim_id: str
    evidence_ids: tuple[str, ...] = ()


class VerifyClaimAction(_ActionBase):
    """Spend verification budget to check a claim against its cited evidence."""

    type: Literal["verify_claim"] = "verify_claim"
    claim_id: str


class ApproveClaimAction(_ActionBase):
    """Endorse a claim for inclusion in the final briefing."""

    type: Literal["approve_claim"] = "approve_claim"
    claim_id: str


class WithholdAction(_ActionBase):
    """Explicit free-ride: do nothing this round, pay no effort cost."""

    type: Literal["withhold"] = "withhold"


class AbstainAction(_ActionBase):
    """Safe no-op. Also the configured fallback for invalid LLM output."""

    type: Literal["abstain"] = "abstain"
    reason: str = ""


Action = Annotated[
    Union[
        CooperateAction,
        DefectAction,
        PairwiseVoteAction,
        InspectEvidenceAction,
        ShareEvidenceAction,
        ProposeClaimAction,
        ChallengeClaimAction,
        VerifyClaimAction,
        ApproveClaimAction,
        WithholdAction,
        AbstainAction,
    ],
    Field(discriminator="type"),
]


class ActionProposal(BaseModel):
    """What a policy returns: a typed action plus observable public rationale.

    ``justification`` is a concise public statement (recorded in the ledger);
    it is never hidden chain-of-thought. ``message_to``/``message`` allow one
    optional agent-to-agent message where the interaction plane permits it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Action
    justification: str = ""
    message_to: str | None = None
    message: str = ""
