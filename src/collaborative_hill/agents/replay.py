"""Replay policy: re-issues the proposals recorded in a sealed ledger.

Carries the ORIGINAL policy_id: the RunStarted payload (which is hashed)
records policy ids, so a replay must present itself exactly as the recorded
policy did or the chain would diverge at seq 0 by construction.
"""

from typing import Any

from collaborative_hill.agents.llm.providers import ProviderError
from collaborative_hill.domain.actions import ActionProposal
from collaborative_hill.engine.events import Event, EventType


class ReplayPolicy:
    def __init__(self, agent_id: str, original_policy_id: str,
                 proposals_by_round: dict[int, ActionProposal],
                 provider_errors_by_round: dict[int, str] | None = None) -> None:
        self.agent_id = agent_id
        self.policy_id = original_policy_id
        self._proposals = proposals_by_round
        self._provider_errors = provider_errors_by_round or {}
        if self._proposals.keys() & self._provider_errors.keys():
            raise ValueError(
                f"recorded provider failure for {agent_id} conflicts with a recorded proposal"
            )

    def propose(self, observation: dict[str, Any], rng: Any) -> ActionProposal:
        del rng
        t = int(observation["round"])
        if t in self._provider_errors:
            raise ProviderError(self._provider_errors[t])
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


def provider_errors_from_events(events: list[Event]) -> dict[str, dict[int, str]]:
    """Decode the existing typed provider-error seal, never arbitrary exceptions.

    This is a recorded policy input, not authority over engine state or timing:
    the runner must reach this agent's proposal call and regenerate the entire
    prefix and terminal state hash. Chain comparison rejects any inconsistency.
    No new hashed fields are needed, so historical seals remain unchanged.
    """
    terminal = events[-1]
    if terminal.event_type != EventType.RUN_FAILED:
        return {}
    reason = terminal.payload.get("reason")
    if isinstance(reason, str):
        # The runner calls policies in sorted order; IDs/messages can share prefixes.
        proposed = {ev.payload["agent_id"] for ev in events
                    if ev.event_type == EventType.ACTION_PROPOSED
                    and ev.logical_time == terminal.logical_time}
        agent = next((a for a in sorted(policy_ids_from_events(events)) if a not in proposed), None)
        if agent is not None:
            prefix = f"policy error for {agent}: ProviderError: "
            if reason.startswith(prefix):
                return {agent: {terminal.logical_time: reason[len(prefix):]}}
    return {}


def policy_ids_from_events(events: list[Event]) -> dict[str, str]:
    for ev in events:
        if ev.event_type == EventType.RUN_STARTED:
            return dict(ev.payload["policies"])
    raise ValueError("ledger has no RunStarted event")
