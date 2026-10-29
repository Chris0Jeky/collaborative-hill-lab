"""Versioned, locally observed N-IPD on a fixed undirected graph (ADR-0011).

The legacy complete-population engine is unchanged. Graph worlds explicitly
choose summed or mean incident-edge rewards. Isolates receive zero, and their
unplayed proposals are excluded from eligible interaction votes.
"""

import random
from fractions import Fraction
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator

from collaborative_hill.domain.actions import (
    Action,
    CooperateAction,
    DefectAction,
    Move,
    PairwiseVoteAction,
)
from collaborative_hill.domain.world.nipd import NIPDParams, pairwise_game
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.hashing import frac_str

GRAPH_NIPD_ENGINE_VERSION = 1


class UndirectedGraph(BaseModel):
    """Canonical labelled simple graph; roster equality is checked by the world.

    Normalize ordering only. Invalid edges are rejected, never deduplicated,
    silently symmetrized or supplemented with invented vertices.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["undirected"] = "undirected"
    version: StrictInt = Field(default=1, ge=1, le=1)
    adjacency: dict[StrictStr, tuple[StrictStr, ...]]

    @model_validator(mode="after")
    def _canonical_adjacency(self) -> Self:
        vertices = set(self.adjacency)
        if any(not a.strip() for a in vertices):
            raise ValueError("graph vertex ids must be non-empty")
        for agent, neighbors in self.adjacency.items():
            if len(neighbors) != len(set(neighbors)):
                raise ValueError(f"duplicate neighbor for {agent}")
            if agent in neighbors:
                raise ValueError(f"self-loop at {agent}")
            unknown = set(neighbors) - vertices
            if unknown:
                raise ValueError(f"unknown graph vertices for {agent}: {sorted(unknown)}")
            for neighbor in neighbors:
                if agent not in self.adjacency[neighbor]:
                    raise ValueError(f"adjacency must be symmetric: {agent}, {neighbor}")
        if not any(self.adjacency.values()):
            raise ValueError("graph N-IPD requires at least one edge")
        ordered = {a: tuple(sorted(self.adjacency[a])) for a in sorted(vertices)}
        object.__setattr__(self, "adjacency", ordered)
        return self


class GraphNIPDMechanism:
    """A deterministic simultaneous edge game with local observations."""

    def __init__(self, *, agent_ids: list[str], mode: str, params: NIPDParams,
                 rounds: int, adjacency: dict[str, tuple[str, ...]],
                 payoff_aggregation: str) -> None:
        if mode not in ("pairwise", "neighbourhood"):
            raise ValueError(f"unknown graph N-IPD mode: {mode}")
        if payoff_aggregation not in ("sum", "mean"):
            raise ValueError(f"unknown graph payoff aggregation: {payoff_aggregation}")
        if type(rounds) is not int or rounds <= 0:
            raise ValueError("graph rounds must be a positive integer")
        if len(set(agent_ids)) != len(agent_ids):
            raise ValueError("duplicate agent ids")
        graph = UndirectedGraph(adjacency=adjacency)
        if set(agent_ids) != set(graph.adjacency):
            raise ValueError("graph adjacency must cover exactly the agent roster")
        self._agent_ids = sorted(agent_ids)
        self._adjacency = dict(graph.adjacency)
        self._edges = tuple((a, b) for a in self._agent_ids
                            for b in self._adjacency[a] if a < b)
        self._active = tuple(a for a in self._agent_ids if self._adjacency[a])
        self._isolated = tuple(a for a in self._agent_ids if not self._adjacency[a])
        self.mode = mode
        self.params = params
        self.rounds = rounds
        self.payoff_aggregation = payoff_aggregation

    def agent_ids(self) -> list[str]:
        return list(self._agent_ids)

    def initial_state(self) -> dict[str, Any]:
        return {"round": 0, "last_moves": None,
                "scores": dict.fromkeys(self._agent_ids, "0")}

    def is_terminal(self, state: dict[str, Any]) -> bool:
        return int(state["round"]) >= self.rounds

    def observe(self, state: dict[str, Any], agent_id: str) -> dict[str, Any]:
        if agent_id not in self._adjacency:
            raise ValueError(f"unknown agent: {agent_id}")
        neighbors = self._adjacency[agent_id]
        obs: dict[str, Any] = {
            "mechanism": "nipd_graph", "engine_version": GRAPH_NIPD_ENGINE_VERSION,
            "mode": self.mode, "round": state["round"],
            "n_agents": len(self._agent_ids), "self_id": agent_id,
            "neighbors": list(neighbors), "degree": len(neighbors),
            "payoff_aggregation": self.payoff_aggregation,
        }
        last = state["last_moves"]
        if self.mode == "pairwise":
            obs["opponents"] = list(neighbors)
            obs["moves_against_me"] = (None if last is None else
                                       {a: last[a][agent_id] for a in neighbors})
            obs["my_last_moves"] = (None if last is None else
                                    {a: last[agent_id][a] for a in neighbors})
        else:
            obs["others_cooperated_last_round"] = (None if last is None else
                                                   sum(last[a] == "C" for a in neighbors))
            obs["my_last_move"] = None if last is None else last[agent_id]
        return obs

    def validate_action(self, state: dict[str, Any], agent_id: str,
                        action: Action) -> str | None:
        del state
        if agent_id not in self._adjacency:
            return f"unknown agent: {agent_id}"
        if self.mode == "neighbourhood":
            if isinstance(action, CooperateAction | DefectAction):
                return None
            return f"graph neighbourhood accepts cooperate/defect, got {action.type}"
        if isinstance(action, PairwiseVoteAction):
            expected = set(self._adjacency[agent_id])
            got = set(action.moves)
            if got == expected:
                return None
            return ("graph pairwise vote must cover exactly neighbors; "
                    f"missing={sorted(expected - got)} extra={sorted(got - expected)}")
        return f"graph pairwise accepts pairwise_vote, got {action.type}"

    def resolve(self, state: dict[str, Any], actions: dict[str, Action],
                rng: random.Random) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        del rng  # randomness belongs to the policies, not edge resolution
        if set(actions) != set(self._agent_ids):
            raise ValueError("resolve requires exactly one action per agent")
        if self.is_terminal(state):
            raise ValueError("cannot resolve a terminal graph state")
        for agent in self._agent_ids:
            error = self.validate_action(state, agent, actions[agent])
            if error is not None:
                raise ValueError(f"illegal action by {agent}: {error}")

        rnd = int(state["round"])
        payoffs = dict.fromkeys(self._agent_ids, Fraction(0))
        payload: dict[str, Any] = {
            "round": rnd, "mode": self.mode, "mechanism": "nipd_graph",
            "engine_version": GRAPH_NIPD_ENGINE_VERSION,
            "payoff_aggregation": self.payoff_aggregation,
            "isolated_agents": list(self._isolated),
        }
        new_last: Any
        if self.mode == "pairwise":
            moves: dict[str, dict[str, Move]] = {}
            for agent in self._agent_ids:
                act = actions[agent]
                assert isinstance(act, PairwiseVoteAction)  # validated above
                moves[agent] = dict(sorted(act.moves.items()))
            pair_results = []
            for a, b in self._edges:
                pa, pb = pairwise_game(moves[a][b], moves[b][a], self.params)
                payoffs[a] += pa
                payoffs[b] += pb
                pair_results.append({"a": a, "b": b, "move_ab": moves[a][b],
                                     "move_ba": moves[b][a]})
            payload.update({
                "pair_results": pair_results,
                "cooperative_votes": sum(move == "C" for row in moves.values()
                                         for move in row.values()),
                "total_votes": 2 * len(self._edges),
            })
            new_last = moves
        else:
            flat: dict[str, Move] = {
                a: "C" if isinstance(actions[a], CooperateAction) else "D"
                for a in self._agent_ids
            }
            for a, b in self._edges:
                pa, pb = pairwise_game(flat[a], flat[b], self.params)
                payoffs[a] += pa
                payoffs[b] += pb
            payload.update({
                "moves": {a: flat[a] for a in self._active},
                "cooperative_votes": sum(flat[a] == "C" for a in self._active),
                "total_votes": len(self._active),
            })
            new_last = flat
        if self.payoff_aggregation == "mean":
            for agent in self._active:
                payoffs[agent] /= len(self._adjacency[agent])
        new_scores = {a: frac_str(Fraction(state["scores"][a]) + payoffs[a])
                      for a in self._agent_ids}
        new_state = {"round": rnd + 1, "last_moves": new_last, "scores": new_scores}
        events: list[dict[str, Any]] = [
            {"event_type": EventType.WORLD_TRANSITIONED.value,
             "actor": "engine", "payload": payload},
        ]
        events.extend(
            {"event_type": EventType.REWARD_ASSIGNED.value, "actor": "engine",
             "payload": {"agent_id": a, "round": rnd, "reward": frac_str(payoffs[a]),
                         "cumulative": new_scores[a]}}
            for a in self._agent_ids
        )
        return new_state, events
