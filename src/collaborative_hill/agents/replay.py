"""Replay policy: re-issues the proposals recorded in a sealed ledger.

Carries the ORIGINAL policy_id: the RunStarted payload (which is hashed)
records policy ids, so a replay must present itself exactly as the recorded
policy did or the chain would diverge at seq 0 by construction.
"""

from typing import Any

from collaborative_hill.domain.actions import ActionProposal
from collaborative_hill.engine.events import Event, EventType


class ReplayPolicy:
    def __init__(self, agent_id: str, original_policy_id: str,
                 proposals_by_round: dict[int, ActionProposal]) -> None:
        self.agent_id = agent_id
        self.policy_id = original_policy_id
        self._proposals = proposals_by_round

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        del rng
        t = int(observation["round"])
        if t not in self._proposals:
            raise KeyError(f"no recorded proposal for agent {self.agent_id} round {t}")
        return self._proposals[t]


def proposals_from_events(events: list[Event]) -> dict[str, dict[int, ActionProposal]]:
    """Extract per-agent, per-round recorded proposals from a ledger."""
    out: dict[str, dict[int, ActionProposal]] = {}
    for ev in events:
        if ev.event_type == EventType.ACTION_PROPOSED:
            agent = ev.payload["agent_id"]
            proposal = ActionProposal.model_validate(ev.payload["proposal"])
            out.setdefault(agent, {})[ev.logical_time] = proposal
    return out


def policy_ids_from_events(events: list[Event]) -> dict[str, str]:
    for ev in events:
        if ev.event_type == EventType.RUN_STARTED:
            return dict(ev.payload["policies"])
    raise ValueError("ledger has no RunStarted event")
