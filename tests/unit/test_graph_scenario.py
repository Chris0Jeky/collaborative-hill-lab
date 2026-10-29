"""New graph identities are canonical; historical complete identities stay fixed."""

from pathlib import Path

import pytest

from collaborative_hill.domain.world.graph_nipd import UndirectedGraph
from collaborative_hill.experiments.scenario import (
    AgentSpec,
    CognitionPlane,
    GraphNIPDWorld,
    InteractionPlane,
    NarrativeSkin,
    NIPDWorld,
    PolicySpec,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import load_study, study_hash

ROOT = Path(__file__).resolve().parents[2]
PATH = {"a": ("b",), "b": ("a", "c"), "c": ("b",)}


def scenario(adjacency=PATH, *, aggregation="mean", order=("a", "b", "c")):
    return ScenarioSpec(
        scenario_id="graph", world=GraphNIPDWorld(
            mode="neighbourhood", rounds=3, payoff_aggregation=aggregation,
        ),
        interaction=InteractionPlane(structure="neighbourhood",
                                     graph=UndirectedGraph(adjacency=adjacency)),
        cognition=CognitionPlane(agents=tuple(
            AgentSpec(agent_id=a, policy=PolicySpec(name="allc")) for a in order
        )),
    )


def compiled(spec):
    return compile_scenario(spec, NarrativeSkin(skin_id="plain"))


def test_canonical_adjacency_order_has_same_resolved_hashes_and_serialization():
    first = scenario()
    second = scenario({"c": ("b",), "b": ("c", "a"), "a": ("b",)})
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert compiled(first) == compiled(second)


def test_graph_roster_order_is_game_invariant_but_cognition_identity_is_retained():
    first = compiled(scenario())
    second = compiled(scenario(order=("c", "a", "b")))
    assert first.mechanism_hash == second.mechanism_hash
    assert first.scenario_hash != second.scenario_hash
    assert second.build_mechanism().agent_ids() == ["a", "b", "c"]


def test_topology_aggregation_and_engine_version_change_graph_identity(monkeypatch):
    import collaborative_hill.domain.world.graph_nipd as module

    baseline = compiled(scenario()).mechanism_hash
    triangle = {"a": ("b", "c"), "b": ("a", "c"), "c": ("a", "b")}
    assert compiled(scenario(triangle)).mechanism_hash != baseline
    assert compiled(scenario(aggregation="sum")).mechanism_hash != baseline
    monkeypatch.setattr(module, "GRAPH_NIPD_ENGINE_VERSION", 2)
    assert compiled(scenario()).mechanism_hash != baseline


def test_graph_requires_explicit_aggregation_and_strict_positive_rounds():
    with pytest.raises(ValueError, match="payoff_aggregation"):
        GraphNIPDWorld(mode="pairwise")
    for rounds in (0, -1, True, 1.5, "2"):
        with pytest.raises(ValueError, match="rounds"):
            GraphNIPDWorld(mode="pairwise", rounds=rounds, payoff_aggregation="sum")


@pytest.mark.parametrize("kind", ["graph-with-literal", "legacy-with-graph", "wrong-mode"])
def test_incompatible_world_interaction_is_rejected(kind):
    data = scenario().model_dump(mode="json")
    if kind == "graph-with-literal":
        data["interaction"]["graph"] = "complete"
    elif kind == "legacy-with-graph":
        data["world"] = NIPDWorld(mode="neighbourhood", rounds=3).model_dump(mode="json")
    else:
        data["interaction"]["structure"] = "pairwise"
    with pytest.raises(ValueError):
        ScenarioSpec.model_validate(data)


def test_graph_vertices_must_equal_full_cognition_roster():
    with pytest.raises(ValueError, match="roster"):
        scenario({**PATH, "isolate": ()})
    with pytest.raises(ValueError, match="roster"):
        scenario(order=("a", "b", "c", "isolate"))


def test_complete_graph_new_world_is_distinct_from_legacy_identity():
    data = scenario({"a": ("b", "c"), "b": ("a", "c"), "c": ("a", "b")})
    old = data.model_dump(mode="json")
    old["world"] = NIPDWorld(mode="neighbourhood", rounds=3).model_dump(mode="json")
    old["interaction"]["graph"] = "complete"
    assert (compiled(data).mechanism_hash
            != compiled(ScenarioSpec.model_validate(old)).mechanism_hash)


@pytest.mark.parametrize("directory,expected", [
    ("000-legacy-reproduction",
     "5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f"),
    ("001-evidence-commons", "a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe"),
    ("002-nipd-sensitivity", "175140649a108a4f5ea33a4c7a1decf74cdc777a9d47057839a54b7e24ed22eb"),
    ("002-nipd-sensitivity/stochastic",
     "728392210a4aa437ba2a1f6e4d8be73f99b96b896e596e81a8969c121623754f"),
])
def test_all_existing_study_content_hashes_are_unchanged(directory, expected):
    spec, resolved = load_study(ROOT / "studies" / directory)
    assert study_hash(spec, resolved) == expected

