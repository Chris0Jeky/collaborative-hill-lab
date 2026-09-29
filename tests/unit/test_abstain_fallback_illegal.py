"""Reproduce: abstain fallback that is itself illegal fails the run.

A stub mechanism rejects every action, including the AbstainAction
fallback. With ``invalid_action_policy="abstain"`` the runner must seal
the RunResult as failed with an illegal-fallback reason (runner.py
fallback validate_action check), not silently accept the fallback.
"""

import random
from typing import Any

from _fixtures import run_episode_tmp

from collaborative_hill.domain.actions import ActionProposal, WithholdAction


class RejectAllMechanism:
    """Stub mechanism whose legality check rejects every action."""

    def agent_ids(self) -> list[str]:
        return ["a1"]

    def initial_state(self) -> dict[str, Any]:
        return {"round": 0}

    def is_terminal(self, state: dict[str, Any]) -> bool:
        return int(state["round"]) >= 1

    def observe(self, state: dict[str, Any], agent_id: str) -> dict[str, Any]:
        return {"round": int(state["round"])}

    def validate_action(self, state: dict[str, Any], agent_id: str, action: Any) -> str | None:
        return "reject-all"

    def resolve(
        self,
        state: dict[str, Any],
        actions: dict[str, Any],
        rng: random.Random,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        return ({"round": int(state["round"]) + 1}, [])


class IllegalPolicy:
    policy_id = "illegal-proposer"

    def propose(self, observation: dict[str, Any], rng: random.Random) -> ActionProposal:
        return ActionProposal(action=WithholdAction(), justification="")


def test_abstain_fallback_illegal_fails_run(tmp_path):
    result, _events, _paths = run_episode_tmp(
        RejectAllMechanism(),
        {"a1": IllegalPolicy()},
        tmp_path,
        invalid_action_policy="abstain",
        run_id="abstain_fallback_illegal",
    )
    assert result.status == "failed"
    assert result.failure_reason is not None
    assert "abstain fallback illegal" in result.failure_reason
