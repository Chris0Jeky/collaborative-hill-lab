"""Stateless local-degree reciprocity for graph N-IPD (ADR-0011).

The existing targeted policies already consume an explicit opponent list.
Neighbourhood policies need a distinct identity: population size is not the
denominator of a sparse local signal. No count-state lumpability is assumed.
"""

import random
from typing import Any, cast

from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import (
    ActionProposal,
    CooperateAction,
    DefectAction,
    Move,
)
from collaborative_hill.engine.interfaces import AgentPolicy


def _proposal(move: Move, epsilon: float, rng: random.Random) -> ActionProposal:
    if epsilon > 0 and rng.random() < epsilon:
        move = "C" if rng.random() < 0.5 else "D"
    return ActionProposal(action=CooperateAction() if move == "C" else DefectAction())


class GraphProbabilisticTFTPolicy:
    """Start C, then use cooperating-neighbor ratio, optionally including self.

    At degree zero persist the own previous move. This avoids inventing a
    denominator or interpreting absence of interaction as observed defection.
    Existing finite-precision Bernoulli and epsilon sampling are retained.
    """

    def __init__(self, denominator: str = "exclude_self", epsilon: float = 0.0) -> None:
        parsed = coerce_policy_params("ptft", {"denominator": denominator, "epsilon": epsilon})
        self.denominator = cast(str, parsed["denominator"])
        self.epsilon = cast(float, parsed["epsilon"])
        self.policy_id = f"graph_ptft[{self.denominator},eps={self.epsilon}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        others = observation["others_cooperated_last_round"]
        degree = observation["degree"]
        if others is None:
            intended: Move = "C"
        elif degree == 0:
            intended = cast(Move, observation["my_last_move"])
        else:
            if self.denominator == "exclude_self":
                ratio = others / degree
            else:
                mine = 1 if observation["my_last_move"] == "C" else 0
                ratio = (others + mine) / (degree + 1)
            intended = "C" if rng.random() < ratio else "D"
        return _proposal(intended, self.epsilon, rng)


class GraphThresholdTFTPolicy:
    """Inclusive quorum among neighbors; own last move persists at degree zero."""

    def __init__(self, threshold_num: int = 1, threshold_den: int = 2,
                 epsilon: float = 0.0) -> None:
        parsed = coerce_policy_params("tft_threshold", {
            "threshold_num": threshold_num, "threshold_den": threshold_den, "epsilon": epsilon,
        })
        self.threshold_num = cast(int, parsed["threshold_num"])
        self.threshold_den = cast(int, parsed["threshold_den"])
        self.epsilon = cast(float, parsed["epsilon"])
        self.policy_id = (f"graph_tft_threshold[{self.threshold_num}/{self.threshold_den},"
                          f"eps={self.epsilon}]@1")

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        others = observation["others_cooperated_last_round"]
        degree = observation["degree"]
        if others is None:
            intended: Move = "C"
        elif degree == 0:
            intended = cast(Move, observation["my_last_move"])
        else:
            at_quorum = others * self.threshold_den >= self.threshold_num * degree
            intended = "C" if at_quorum else "D"
        return _proposal(intended, self.epsilon, rng)


def build_graph_nipd_policy(name: str, mode: str, params: dict[str, Any]) -> AgentPolicy:
    """Use existing policy names/contracts with explicit graph-local behavior."""
    if mode not in ("pairwise", "neighbourhood"):
        raise ValueError(f"unknown graph N-IPD mode: {mode}")
    parsed = coerce_policy_params(name, params)
    if name in ("ptft", "tft_threshold") and mode != "neighbourhood":
        raise ValueError(f"{name} requires neighbourhood mode")
    if name == "ptft":
        return GraphProbabilisticTFTPolicy(
            denominator=cast(str, parsed.get("denominator", "exclude_self")),
            epsilon=cast(float, parsed.get("epsilon", 0.0)),
        )
    if name == "tft_threshold":
        return GraphThresholdTFTPolicy(
            threshold_num=cast(int, parsed.get("threshold_num", 1)),
            threshold_den=cast(int, parsed.get("threshold_den", 2)),
            epsilon=cast(float, parsed.get("epsilon", 0.0)),
        )
    return cast(AgentPolicy, build_nipd_policy(name, mode, parsed))
