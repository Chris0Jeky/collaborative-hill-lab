"""Graph relabelling and skin relations use deterministic observation-driven agents."""

import pytest

from collaborative_hill.domain.world.graph_nipd import UndirectedGraph
from collaborative_hill.experiments.scenario import (
    AgentSpec,
    CognitionPlane,
    GraphNIPDWorld,
    InteractionPlane,
    NarrativeSkin,
    PolicySpec,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.metrics.cooperation import cooperation_metrics

from ._helpers import execute

pytestmark = pytest.mark.metamorphic

STAR = {"a": ("b", "c", "d"), "b": ("a",), "c": ("a",), "d": ("a",)}
BIJECTION = {"a": "z9", "b": "z1", "c": "z5", "d": "z2"}


def spec(mode, *, renamed=False):
    rename = BIJECTION if renamed else {a: a for a in STAR}
    adjacency = {rename[a]: tuple(rename[b] for b in neighbors) for a, neighbors in STAR.items()}
    order = ("d", "b", "a", "c") if renamed else tuple(STAR)
    policy = "tft_pairwise" if mode == "pairwise" else "tft_threshold"
    return ScenarioSpec(
        scenario_id="graph", world=GraphNIPDWorld(mode=mode, rounds=6, payoff_aggregation="mean"),
        interaction=InteractionPlane(structure=mode, graph=UndirectedGraph(adjacency=adjacency)),
        cognition=CognitionPlane(agents=tuple(
            AgentSpec(agent_id=rename[a], policy=PolicySpec(name="alld" if a == "b" else policy))
            for a in order
        )),
    )


@pytest.mark.parametrize("mode", ["pairwise", "neighbourhood"])
def test_graph_bijection_and_cognition_reordering_relabel_exact_outcomes(tmp_path, mode):
    base = compile_scenario(spec(mode), NarrativeSkin(skin_id="plain"))
    renamed = compile_scenario(spec(mode, renamed=True), NarrativeSkin(skin_id="plain"))
    first, events, _ = execute(base, tmp_path / "base")
    second, renamed_events, _ = execute(renamed, tmp_path / "renamed")
    assert first.status == second.status == "completed"
    assert {BIJECTION[a]: score for a, score in first.summary["scores"].items()} == (
        second.summary["scores"])
    first_metrics, second_metrics = cooperation_metrics(events), cooperation_metrics(renamed_events)
    assert first_metrics["cooperation_rate_by_round"] == second_metrics["cooperation_rate_by_round"]
    assert {BIJECTION[a]: v for a, v in first_metrics["per_agent_cooperation"].items()} == (
        second_metrics["per_agent_cooperation"])
    assert len(set(first.summary["scores"].values())) > 1


@pytest.mark.parametrize("mode", ["pairwise", "neighbourhood"])
def test_graph_skin_is_inert_with_narrative_metadata_excluded_from_start(tmp_path, mode):
    scenario = spec(mode)
    plain = compile_scenario(scenario, NarrativeSkin(skin_id="plain"))
    story = compile_scenario(scenario, NarrativeSkin(
        skin_id="islands", title="The Island Council", preamble="Trade with your neighbors.",
        agent_names={"a": "Aster", "b": "Bram", "c": "Cove", "d": "Dune"},
    ))
    assert plain.mechanism_hash == story.mechanism_hash
    assert plain.narrative_hash != story.narrative_hash
    assert plain.scenario_hash != story.scenario_hash
    # Identical RunConfig and no narrative-bearing start_meta: the full scripted
    # event chain is invariant. Standard study runs separately record skin identity.
    first, events, _ = execute(plain, tmp_path / "plain")
    second, story_events, _ = execute(story, tmp_path / "story")
    assert first.summary == second.summary
    assert [e.event_hash for e in events] == [e.event_hash for e in story_events]

