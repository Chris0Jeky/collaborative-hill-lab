"""Negative max_retries is rejected at build time; zero retries = one attempt."""

import json
import random

import pytest

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.domain.actions import AbstainAction
from collaborative_hill.experiments.scenario import (
    AgentSpec,
    CognitionPlane,
    ECWorld,
    InformationPlane,
    InteractionPlane,
    NarrativeSkin,
    PolicySpec,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import build_policies

SKIN = NarrativeSkin(skin_id="plain")
OBSERVATION = {
    "round": 0,
    "mechanism": "evidence_commons",
    "self_id": "a1",
    "slots": {},
    "evidence": [],
    "claims": [],
    "my_budgets": {"inspect": 6, "verify": 3},
    "my_effort_spent": 0,
}


def _ec_scenario_with_retries(max_retries: int) -> ScenarioSpec:
    return ScenarioSpec(
        scenario_id="ec-retries",
        world=ECWorld(
            slots={"s1": ("p1a", "p1b")},
            true_propositions={"s1": "p1a"},
        ),
        information=InformationPlane(
            evidence=(
                {
                    "evidence_id": "e1",
                    "source_id": "src1",
                    "slot_id": "s1",
                    "proposition_id": "p1a",
                    "stance": "supports",
                    "truth_aligned": True,
                    "initial_holders": ("a1",),
                },
            ),
        ),
        interaction=InteractionPlane(structure="commons"),
        cognition=CognitionPlane(
            agents=(
                AgentSpec(
                    agent_id="a1",
                    policy=PolicySpec(
                        name="llm_fake",
                        params={
                            "script": json.dumps(["garbage"]),
                            "max_retries": max_retries,
                        },
                    ),
                ),
            )
        ),
    )


def test_negative_max_retries_rejected():
    provider = FakeProvider(["garbage"])
    with pytest.raises(ValueError):
        LLMPolicy("a1", provider, SKIN, max_retries=-1)
    assert provider.calls == 0

    resolved = compile_scenario(_ec_scenario_with_retries(-1), SKIN)
    with pytest.raises(ValueError):
        build_policies(resolved)


def test_zero_retries_makes_one_attempt():
    provider = FakeProvider(["garbage"])
    policy = LLMPolicy("a1", provider, SKIN, max_retries=0)
    proposal = policy.propose(dict(OBSERVATION), random.Random(0))
    assert provider.calls == 1
    assert isinstance(proposal.action, AbstainAction)
    assert proposal.action.reason == "invalid_llm_output"
