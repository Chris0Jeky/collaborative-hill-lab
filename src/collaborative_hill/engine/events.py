"""Append-only, hash-linked event ledger.

Every run is a totally ordered sequence of immutable events. Each event's
``event_hash`` is the SHA-256 of the canonical JSON of its *hashed view* —
all envelope fields except ``event_hash`` itself and ``meta``. ``parent_hash``
links each event to its predecessor (``GENESIS_HASH`` for seq 0), so a sealed
ledger is tamper-evident end to end: replaying the run must reproduce the
identical chain, byte for byte.

``meta`` is the only mutable-world escape hatch: wall-clock timestamps,
durations, token counts. It is recorded for provenance but NEVER hashed, so
identical replays on different days produce identical chains.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from collaborative_hill.engine.hashing import GENESIS_HASH, Json, content_hash


class EventType(StrEnum):
    RUN_STARTED = "RunStarted"
    OBSERVATION_ISSUED = "ObservationIssued"
    ACTION_PROPOSED = "ActionProposed"
    ACTION_REJECTED = "ActionRejected"
    ACTION_ACCEPTED = "ActionAccepted"
    TOOL_INVOKED = "ToolInvoked"
    MESSAGE_SENT = "MessageSent"
    EVIDENCE_INSPECTED = "EvidenceInspected"
    EVIDENCE_SHARED = "EvidenceShared"
    CLAIM_PROPOSED = "ClaimProposed"
    CLAIM_CHALLENGED = "ClaimChallenged"
    CLAIM_VERIFIED = "ClaimVerified"
    CLAIM_APPROVED = "ClaimApproved"
    INSTITUTION_APPLIED = "InstitutionApplied"
    REWARD_ASSIGNED = "RewardAssigned"
    WORLD_TRANSITIONED = "WorldTransitioned"
    CHECKPOINT_CREATED = "CheckpointCreated"
    RUN_COMPLETED = "RunCompleted"
    RUN_FAILED = "RunFailed"


ENGINE_ACTOR = "engine"


class Event(BaseModel):
    """Immutable event envelope. See module docstring for hashing rules."""

    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    study_id: str
    run_id: str
    seq: int
    logical_time: int
    actor: str
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    parent_hash: str
    event_hash: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)

    def hashed_view(self) -> dict[str, Json]:
        """The exact dict whose canonical JSON is hashed. Excludes event_hash and meta."""
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "run_id": self.run_id,
            "seq": self.seq,
            "logical_time": self.logical_time,
            "actor": self.actor,
            "event_type": self.event_type.value,
            "payload": self.payload,
            "parent_hash": self.parent_hash,
        }

    def compute_hash(self) -> str:
        return content_hash(self.hashed_view())


class ChainError(ValueError):
    """A ledger violated append-only hash-chain invariants."""


def make_event(
    *,
    study_id: str,
    run_id: str,
    seq: int,
    logical_time: int,
    actor: str,
    event_type: EventType,
    payload: dict[str, Any],
    parent_hash: str,
    meta: dict[str, Any] | None = None,
) -> Event:
    """Build an event with its hash sealed in. Payload must be canonical-JSON-safe."""
    draft = Event(
        study_id=study_id,
        run_id=run_id,
        seq=seq,
        logical_time=logical_time,
        actor=actor,
        event_type=event_type,
        payload=payload,
        parent_hash=parent_hash,
        meta=meta or {},
    )
    return draft.model_copy(update={"event_hash": draft.compute_hash()})


def verify_chain(events: list[Event]) -> None:
    """Verify seq continuity, parent linkage, and every event hash. Raises ChainError."""
    prev_hash = GENESIS_HASH
    for i, event in enumerate(events):
        if event.seq != i:
            raise ChainError(f"seq gap at index {i}: expected {i}, got {event.seq}")
        if event.parent_hash != prev_hash:
            raise ChainError(f"broken parent link at seq {i}")
        recomputed = event.compute_hash()
        if event.event_hash != recomputed:
            raise ChainError(f"hash mismatch at seq {i}: stored {event.event_hash[:12]}…")
        prev_hash = event.event_hash
