"""Structural interfaces for the kernel's lifecycle seams. Protocols, not inheritance.

An LLM is never authoritative for anything defined here: payoffs, world truth,
evidence validity, permissions, and metrics are all computed by deterministic
typed code (locked principle; ADR-0001). Metrics are deliberately NOT a
protocol — they are versioned pure functions over sealed events
(`metrics/__init__.py::METRIC_VERSIONS`), and the runner never imports them.
"""

import random
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from collaborative_hill.domain.actions import Action, ActionProposal
from collaborative_hill.engine.seeds import SeedPath


@runtime_checkable
class MechanismEngine(Protocol):
    """Deterministic world: state init, legality, observation, resolution.

    State is a canonical-JSON-safe dict (no floats; fractions as strings) so
    it can be checkpointed, hashed, and diffed. All randomness comes from rng
    streams handed in by the runner — a mechanism never creates its own.
    """

    def agent_ids(self) -> list[str]: ...

    def initial_state(self) -> dict[str, Any]: ...

    def is_terminal(self, state: dict[str, Any]) -> bool: ...

    def observe(self, state: dict[str, Any], agent_id: str) -> dict[str, Any]:
        """Agent-visible observation DTO. MUST NOT contain hidden truth fields."""
        ...

    def validate_action(self, state: dict[str, Any], agent_id: str, action: Action) -> str | None:
        """None if legal; otherwise a machine-readable rejection reason."""
        ...

    def resolve(
        self,
        state: dict[str, Any],
        actions: dict[str, Action],
        rng: random.Random,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Apply one simultaneous round. Returns (new_state, domain event payloads).

        Each returned payload dict carries an ``event_type`` key naming an
        :class:`~collaborative_hill.engine.events.EventType` value; the runner
        wraps them into hash-chained envelopes.
        """
        ...


class RoundOpeningMechanism(Protocol):
    """Optional mechanism seam for public information due before observations.

    The runner supplies independently keyed streams under its mechanism root.
    The key must identify the draw itself; the runner adds no implicit round.
    Return a detached state and domain events using the same envelope contract
    as ``resolve``. Existing mechanisms need not implement this seam.
    """

    def prepare_round(
        self,
        state: dict[str, Any],
        rng_for_key: Callable[[SeedPath], random.Random],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]: ...


@runtime_checkable
class AgentPolicy(Protocol):
    """Proposes typed actions from observations. Scripted, replayed, or LLM-backed."""

    policy_id: str

    def propose(
        self, observation: dict[str, Any], rng: random.Random
    ) -> ActionProposal: ...
