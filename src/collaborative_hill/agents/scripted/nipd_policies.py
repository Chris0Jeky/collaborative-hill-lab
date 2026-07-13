"""Scripted N-IPD policies, including every TFT variant the legacy work conflated.

The legacy audit (docs/research/_discovery/legacy-code-audit.md) found that
"TFT" silently meant three different decision rules across the legacy engines.
Here each is a distinct, named, versioned policy so Study 000 can deconfound
interaction structure from strategy choice:

- ``tft_pairwise``   deterministic per-opponent reciprocity (paper's pairwise TFT)
- ``tft_linked``     one move copied to all opponents; defects if ANY opponent
                     defected against it (legacy npdl's "pairwise" TFT)
- ``ptft``           probabilistic group TFT: P(C) = cooperation ratio last round,
                     with an explicit denominator convention (the legacy code and
                     paper text disagree: include_self /N vs exclude_self /(N-1))
- ``tft_threshold``  quorum TFT: C iff last-round cooperation ratio >= threshold
                     (legacy npdl's "ecosystem-aware TFT", threshold 0.5)

All policies are stateless: everything they need is in the observation, and all
randomness comes from the per-decision rng stream handed in by the runner.
``epsilon`` adds TFT-E-style exploration (with prob epsilon, play a fair coin).
"""

import random
from typing import Any

from collaborative_hill.domain.actions import (
    ActionProposal,
    CooperateAction,
    DefectAction,
    Move,
    PairwiseVoteAction,
)


def _explore(move: Move, epsilon: float, rng: random.Random) -> Move:
    """With probability epsilon, replace the intended move with a fair coin flip."""
    if epsilon > 0 and rng.random() < epsilon:
        return "C" if rng.random() < 0.5 else "D"
    return move


def _neighbourhood_action(move: Move) -> ActionProposal:
    action = CooperateAction() if move == "C" else DefectAction()
    return ActionProposal(action=action)


class AllCPolicy:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.policy_id = f"allc[{mode}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        del rng
        if self.mode == "pairwise":
            return ActionProposal(
                action=PairwiseVoteAction(moves={o: "C" for o in observation["opponents"]})
            )
        return _neighbourhood_action("C")


class AllDPolicy:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.policy_id = f"alld[{mode}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        del rng
        if self.mode == "pairwise":
            return ActionProposal(
                action=PairwiseVoteAction(moves={o: "D" for o in observation["opponents"]})
            )
        return _neighbourhood_action("D")


class RandomPolicy:
    """Fair-coin move each decision (per opponent in pairwise mode)."""

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.policy_id = f"random[{mode}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        if self.mode == "pairwise":
            moves: dict[str, Move] = {
                o: ("C" if rng.random() < 0.5 else "D")
                for o in sorted(observation["opponents"])
            }
            return ActionProposal(action=PairwiseVoteAction(moves=moves))
        return _neighbourhood_action("C" if rng.random() < 0.5 else "D")


class PairwiseTFTPolicy:
    """Per-opponent Tit-for-Tat: start C, then mirror what each opponent played
    against me last round. The paper's pairwise reciprocator."""

    def __init__(self, epsilon: float = 0.0) -> None:
        self.epsilon = epsilon
        self.policy_id = f"tft_pairwise[eps={epsilon}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        against_me = observation["moves_against_me"]
        moves: dict[str, Move] = {}
        for o in sorted(observation["opponents"]):
            intended: Move = "C" if against_me is None else against_me[o]
            moves[o] = _explore(intended, self.epsilon, rng)
        return ActionProposal(action=PairwiseVoteAction(moves=moves))


class LinkedTFTPolicy:
    """Legacy npdl 'pairwise' TFT: ONE move for all opponents; defect if ANY
    opponent defected against me last round. Reintroduces diffuse punishment
    inside the pairwise structure — kept as a deconfounding condition."""

    def __init__(self, epsilon: float = 0.0) -> None:
        self.epsilon = epsilon
        self.policy_id = f"tft_linked[eps={epsilon}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        against_me = observation["moves_against_me"]
        if against_me is None:
            intended: Move = "C"
        else:
            intended = "D" if "D" in against_me.values() else "C"
        move = _explore(intended, self.epsilon, rng)
        return ActionProposal(
            action=PairwiseVoteAction(moves={o: move for o in observation["opponents"]})
        )


class ProbabilisticTFTPolicy:
    """Group TFT: cooperate with probability equal to last round's cooperation ratio.

    ``denominator`` pins the legacy ambiguity explicitly:
    - "exclude_self": ratio = others_cooperated / (N-1)   (paper text reading)
    - "include_self": ratio = (others_cooperated + [I cooperated]) / N
                      (legacy standalone figure-generating code)
    First round: cooperate.
    """

    def __init__(self, denominator: str = "exclude_self", epsilon: float = 0.0) -> None:
        if denominator not in ("exclude_self", "include_self"):
            raise ValueError(f"unknown denominator convention: {denominator}")
        self.denominator = denominator
        self.epsilon = epsilon
        self.policy_id = f"ptft[{denominator},eps={epsilon}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        others_c = observation["others_cooperated_last_round"]
        if others_c is None:
            intended: Move = "C"
        else:
            n = observation["n_agents"]
            if self.denominator == "exclude_self":
                ratio = others_c / (n - 1)
            else:
                mine = 1 if observation["my_last_move"] == "C" else 0
                ratio = (others_c + mine) / n
            intended = "C" if rng.random() < ratio else "D"
        return _neighbourhood_action(_explore(intended, self.epsilon, rng))


class ThresholdTFTPolicy:
    """Quorum TFT (legacy npdl 'ecosystem-aware TFT'): cooperate iff last round's
    other-cooperation ratio >= threshold. First round: cooperate."""

    def __init__(self, threshold_num: int = 1, threshold_den: int = 2,
                 epsilon: float = 0.0) -> None:
        self.threshold_num = threshold_num
        self.threshold_den = threshold_den
        self.epsilon = epsilon
        self.policy_id = f"tft_threshold[{threshold_num}/{threshold_den},eps={epsilon}]@1"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        others_c = observation["others_cooperated_last_round"]
        if others_c is None:
            intended: Move = "C"
        else:
            n_others = observation["n_agents"] - 1
            # exact comparison: others_c/n_others >= num/den  <=>  others_c*den >= num*n_others
            at_quorum = others_c * self.threshold_den >= self.threshold_num * n_others
            intended = "C" if at_quorum else "D"
        return _neighbourhood_action(_explore(intended, self.epsilon, rng))


def build_nipd_policy(name: str, mode: str, params: dict[str, Any]) -> Any:
    """Registry: construct a scripted N-IPD policy from a spec name + params."""
    if name == "allc":
        return AllCPolicy(mode)
    if name == "alld":
        return AllDPolicy(mode)
    if name == "random":
        return RandomPolicy(mode)
    if name == "tft_pairwise":
        if mode != "pairwise":
            raise ValueError("tft_pairwise requires pairwise mode")
        return PairwiseTFTPolicy(epsilon=params.get("epsilon", 0.0))
    if name == "tft_linked":
        if mode != "pairwise":
            raise ValueError("tft_linked requires pairwise mode")
        return LinkedTFTPolicy(epsilon=params.get("epsilon", 0.0))
    if name == "ptft":
        if mode != "neighbourhood":
            raise ValueError("ptft requires neighbourhood mode")
        return ProbabilisticTFTPolicy(
            denominator=params.get("denominator", "exclude_self"),
            epsilon=params.get("epsilon", 0.0),
        )
    if name == "tft_threshold":
        if mode != "neighbourhood":
            raise ValueError("tft_threshold requires neighbourhood mode")
        return ThresholdTFTPolicy(
            threshold_num=params.get("threshold_num", 1),
            threshold_den=params.get("threshold_den", 2),
            epsilon=params.get("epsilon", 0.0),
        )
    raise ValueError(f"unknown scripted NIPD policy: {name}")
