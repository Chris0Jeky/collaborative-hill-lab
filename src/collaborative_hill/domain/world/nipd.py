"""N-person Iterated Prisoner's Dilemma — the canonical micro-mechanism.

Two interaction structures, exactly as in Tcaci & Huyck (prisoners.tex, legacy
repo) and the legacy standalone experiment code:

- ``pairwise``: each round every agent plays an independent 2-player PD against
  each other agent (one move *per opponent*). Score = sum over the N-1 games.
  Direct, targetable reciprocity.
- ``neighbourhood``: each agent casts one collective vote. A cooperator earns
  S + (R-S) * k/(N-1) and a defector P + (T-P) * k/(N-1), where k is the number
  of *other* cooperators. Diffuse, untargetable reciprocity.

All payoff arithmetic is exact (``fractions.Fraction``); state stores payoffs
as canonical fraction strings so hashing and replay are byte-stable.

Payoff parameters default to the legacy canon T=5, R=3, P=1, S=0 (which
satisfies T > R > P > S and 2R > T + S — verified by the payoff oracle tests
against hand-derived tables, not against this code).
"""

import random
from fractions import Fraction
from itertools import combinations
from typing import Any

from pydantic import BaseModel, ConfigDict

from collaborative_hill.domain.actions import (
    Action,
    CooperateAction,
    DefectAction,
    Move,
    PairwiseVoteAction,
)
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.hashing import frac_str


class NIPDParams(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    T: int = 5
    R: int = 3
    P: int = 1
    S: int = 0

    def is_dilemma(self, n_agents: int) -> bool:
        """T>R>P>S and 2R>T+S — the Axelrod restrictions; holds for any N>=2."""
        del n_agents
        return self.T > self.R > self.P > self.S and 2 * self.R > self.T + self.S


def pairwise_game(move_a: Move, move_b: Move, params: NIPDParams) -> tuple[int, int]:
    """One 2-player PD. Returns (payoff_a, payoff_b) as exact ints."""
    table = {
        ("C", "C"): (params.R, params.R),
        ("C", "D"): (params.S, params.T),
        ("D", "C"): (params.T, params.S),
        ("D", "D"): (params.P, params.P),
    }
    return table[(move_a, move_b)]


def neighbourhood_payoff(move: Move, k_other_cooperators: int, n_agents: int,
                         params: NIPDParams) -> Fraction:
    """Linear public-goods payoff. ``k`` counts OTHER cooperators (self-excluded)."""
    k = Fraction(k_other_cooperators, n_agents - 1)
    if move == "C":
        return params.S + (params.R - params.S) * k
    return params.P + (params.T - params.P) * k


class NIPDMechanism:
    """Deterministic N-IPD engine for both interaction modes.

    State is minimal (event-sourced history lives in the ledger):
      round        - next round index (0-based)
      last_moves   - previous round's realized moves, shaped per mode; None at start
      scores       - cumulative payoff per agent, fraction strings
    """

    def __init__(self, *, agent_ids: list[str], mode: str, params: NIPDParams,
                 rounds: int) -> None:
        if mode not in ("pairwise", "neighbourhood"):
            raise ValueError(f"unknown NIPD mode: {mode}")
        if len(agent_ids) < 2:
            raise ValueError("NIPD needs at least 2 agents")
        if len(set(agent_ids)) != len(agent_ids):
            raise ValueError("duplicate agent ids")
        self._agent_ids = list(agent_ids)
        self.mode = mode
        self.params = params
        self.rounds = rounds

    def agent_ids(self) -> list[str]:
        return list(self._agent_ids)

    def initial_state(self) -> dict[str, Any]:
        return {
            "round": 0,
            "last_moves": None,
            "scores": {a: "0" for a in self._agent_ids},
        }

    def is_terminal(self, state: dict[str, Any]) -> bool:
        return int(state["round"]) >= self.rounds

    # -- observation ---------------------------------------------------------

    def observe(self, state: dict[str, Any], agent_id: str) -> dict[str, Any]:
        """Agent-visible view. Contains no other agent's full strategy or score.

        pairwise: what each opponent played *against me* last round (targeted
        information — the structural basis of the Collaborative Hill).
        neighbourhood: only the COUNT of other cooperators last round (diffuse
        information — the structural basis of the Tragic Valley).
        """
        obs: dict[str, Any] = {
            "mechanism": "nipd",
            "mode": self.mode,
            "round": state["round"],
            "n_agents": len(self._agent_ids),
            "self_id": agent_id,
        }
        last = state["last_moves"]
        if self.mode == "pairwise":
            others = [a for a in self._agent_ids if a != agent_id]
            obs["opponents"] = others
            if last is None:
                obs["moves_against_me"] = None
                obs["my_last_moves"] = None
            else:
                obs["moves_against_me"] = {o: last[o][agent_id] for o in others}
                obs["my_last_moves"] = {o: last[agent_id][o] for o in others}
        else:
            if last is None:
                obs["others_cooperated_last_round"] = None
                obs["my_last_move"] = None
            else:
                obs["others_cooperated_last_round"] = sum(
                    1 for a in self._agent_ids if a != agent_id and last[a] == "C"
                )
                obs["my_last_move"] = last[agent_id]
        return obs

    # -- legality -------------------------------------------------------------

    def validate_action(self, state: dict[str, Any], agent_id: str,
                        action: Action) -> str | None:
        del state
        if self.mode == "neighbourhood":
            if isinstance(action, CooperateAction | DefectAction):
                return None
            return f"neighbourhood mode accepts cooperate/defect, got {action.type}"
        if isinstance(action, PairwiseVoteAction):
            expected = {a for a in self._agent_ids if a != agent_id}
            got = set(action.moves)
            if got != expected:
                missing = sorted(expected - got)
                extra = sorted(got - expected)
                return f"pairwise vote must cover exactly opponents; missing={missing} extra={extra}"
            return None
        return f"pairwise mode accepts pairwise_vote, got {action.type}"

    # -- resolution -----------------------------------------------------------

    def resolve(
        self,
        state: dict[str, Any],
        actions: dict[str, Action],
        rng: random.Random,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        del rng  # the NIPD world itself is deterministic; randomness lives in policies
        if set(actions) != set(self._agent_ids):
            raise ValueError("resolve requires exactly one action per agent")
        rnd = int(state["round"])
        payoffs: dict[str, Fraction]
        if self.mode == "pairwise":
            moves: dict[str, dict[str, Move]] = {}
            for a, act in actions.items():
                assert isinstance(act, PairwiseVoteAction)
                moves[a] = dict(act.moves)
            payoffs = {a: Fraction(0) for a in self._agent_ids}
            pair_results = []
            for a, b in combinations(self._agent_ids, 2):
                pa, pb = pairwise_game(moves[a][b], moves[b][a], self.params)
                payoffs[a] += pa
                payoffs[b] += pb
                pair_results.append(
                    {"a": a, "b": b, "move_ab": moves[a][b], "move_ba": moves[b][a]}
                )
            transition_payload: dict[str, Any] = {
                "round": rnd,
                "mode": "pairwise",
                "pair_results": pair_results,
            }
            new_last: Any = moves
            coop_votes = sum(
                1 for a in self._agent_ids for b in self._agent_ids
                if a != b and moves[a][b] == "C"
            )
            transition_payload["cooperative_votes"] = coop_votes
            transition_payload["total_votes"] = len(self._agent_ids) * (len(self._agent_ids) - 1)
        else:
            flat: dict[str, Move] = {}
            for a, act in actions.items():
                flat[a] = "C" if isinstance(act, CooperateAction) else "D"
            payoffs = {}
            for a in self._agent_ids:
                k = sum(1 for o in self._agent_ids if o != a and flat[o] == "C")
                payoffs[a] = neighbourhood_payoff(flat[a], k, len(self._agent_ids), self.params)
            transition_payload = {
                "round": rnd,
                "mode": "neighbourhood",
                "moves": dict(sorted(flat.items())),
                "cooperative_votes": sum(1 for m in flat.values() if m == "C"),
                "total_votes": len(self._agent_ids),
            }
            new_last = flat

        new_scores = {
            a: frac_str(Fraction(state["scores"][a]) + payoffs[a]) for a in self._agent_ids
        }
        new_state = {"round": rnd + 1, "last_moves": new_last, "scores": new_scores}

        events: list[dict[str, Any]] = [
            {"event_type": EventType.WORLD_TRANSITIONED.value, "actor": "engine",
             "payload": transition_payload}
        ]
        for a in sorted(self._agent_ids):
            events.append(
                {"event_type": EventType.REWARD_ASSIGNED.value, "actor": "engine",
                 "payload": {"agent_id": a, "round": rnd, "reward": frac_str(payoffs[a]),
                             "cumulative": new_scores[a]}}
            )
        return new_state, events
