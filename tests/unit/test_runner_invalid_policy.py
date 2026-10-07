"""Fail-fast on unknown invalid_action_policy values (typo guard).

"Abstain", "abstain " (trailing space), and "" must raise ValidationError at
the spec/config boundary instead of silently behaving as "fail" at runtime.
"""

import pytest
from _fixtures import AGENTS, ec_hand_example, run_episode_tmp
from pydantic import ValidationError

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.runner import RunConfig
from collaborative_hill.experiments.manifests import RunManifest
from collaborative_hill.experiments.scenario import NarrativeSkin
from collaborative_hill.experiments.study import ConditionSpec, StudySpec

SKIN = NarrativeSkin(skin_id="plain")


def _study_kwargs(policy: str) -> dict:
    return {
        "study_id": "study-t",
        "seed": 0,
        "invalid_action_policy": policy,
        "conditions": (
            ConditionSpec(condition_id="c", scenario="scenarios/s.json", skin="skins/k.json"),
        ),
    }


def _manifest_kwargs(policy: str) -> dict:
    return {
        "study_id": "study-t",
        "condition_id": "c",
        "run_id": "run-t",
        "replicate": 0,
        "scenario_hash": "s",
        "mechanism_hash": "m",
        "narrative_hash": "n",
        "evidence_corpus_hash": "e",
        "institution": {},
        "invalid_action_policy": policy,
    }


@pytest.mark.parametrize("bad", ["Abstain", "abstain ", ""])
def test_run_config_rejects_unknown_policy(bad):
    with pytest.raises(ValidationError):
        RunConfig(study_id="s", run_id="r", seed_root=("seed",), invalid_action_policy=bad)


@pytest.mark.parametrize("bad", ["Abstain", "abstain ", ""])
def test_study_spec_rejects_unknown_policy(bad):
    with pytest.raises(ValidationError):
        StudySpec(**_study_kwargs(bad))


@pytest.mark.parametrize("bad", ["Abstain", "abstain ", ""])
def test_run_manifest_rejects_unknown_policy(bad):
    with pytest.raises(ValidationError):
        RunManifest(**_manifest_kwargs(bad))


@pytest.mark.parametrize("good", ["fail", "abstain"])
def test_run_config_accepts_known_policies(good):
    config = RunConfig(study_id="s", run_id="r", seed_root=("seed",), invalid_action_policy=good)
    assert config.invalid_action_policy == good


@pytest.mark.parametrize("good", ["fail", "abstain"])
def test_study_spec_accepts_known_policies(good):
    spec = StudySpec(**_study_kwargs(good))
    assert spec.invalid_action_policy == good


def test_invalid_action_still_falls_back_under_abstain(tmp_path):
    script = ['{"action":{"type":"inspect_evidence","evidence_id":"NOPE"}}'] * 40
    mech = ec_hand_example(InstitutionConfig(), rounds=2)
    policies = {a: LLMPolicy(a, FakeProvider(list(script)), SKIN) for a in AGENTS}
    result, events, _paths = run_episode_tmp(
        mech, policies, tmp_path, invalid_action_policy="abstain", run_id="ill_abstain")
    assert result.status == "completed"
    rejected = [e for e in events if e.event_type == EventType.ACTION_REJECTED]
    assert rejected
    fallbacks = [e for e in events if e.event_type == EventType.ACTION_ACCEPTED
                 and e.payload.get("fallback")]
    assert fallbacks
    assert fallbacks[0].payload["action"]["type"] == "abstain"
