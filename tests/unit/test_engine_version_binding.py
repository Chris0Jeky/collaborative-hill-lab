"""Engine-version binding: mechanism_hash must change with NIPD_ENGINE_VERSION.

Calls mechanism_view and compile_scenario on the same ScenarioSpec with
NIPD_ENGINE_VERSION monkeypatched to 1 vs 2 and confirms the hashes differ,
so a behaviour-changing engine fix can never silently keep old hashes.
"""

from collaborative_hill.domain.world import nipd
from collaborative_hill.engine.hashing import content_hash
from collaborative_hill.experiments.scenario import (
    NarrativeSkin,
    ScenarioSpec,
    compile_scenario,
    mechanism_view,
)

SCENARIO = {
    "scenario_id": "nipd-version-binding",
    "world": {"kind": "nipd", "mode": "pairwise", "rounds": 5},
    "interaction": {"structure": "pairwise"},
    "cognition": {"agents": [
        {"agent_id": "a1", "policy": {"name": "allc"}},
        {"agent_id": "a2", "policy": {"name": "alld"}},
    ]},
}
SKIN = {"skin_id": "plain"}


def test_mechanism_hash_changes_with_engine_version(monkeypatch):
    spec = ScenarioSpec.model_validate(SCENARIO)
    skin = NarrativeSkin.model_validate(SKIN)

    monkeypatch.setattr(nipd, "NIPD_ENGINE_VERSION", 1)
    view1 = mechanism_view(spec)
    hash1 = content_hash(view1)
    resolved1 = compile_scenario(spec, skin)

    monkeypatch.setattr(nipd, "NIPD_ENGINE_VERSION", 2)
    view2 = mechanism_view(spec)
    hash2 = content_hash(view2)
    resolved2 = compile_scenario(spec, skin)

    assert view1["engine_version"] == 1
    assert view2["engine_version"] == 2
    assert hash1 != hash2
    assert resolved1.mechanism_hash == hash1
    assert resolved2.mechanism_hash == hash2
    assert resolved1.mechanism_hash != resolved2.mechanism_hash
