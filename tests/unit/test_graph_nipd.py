"""Graph mechanism oracles are literal edge-game arithmetic, not helper output."""

from copy import deepcopy
from itertools import product

import pytest

from collaborative_hill.domain.actions import (
    AbstainAction,
    CooperateAction,
    DefectAction,
    PairwiseVoteAction,
)
from collaborative_hill.domain.world.graph_nipd import GraphNIPDMechanism, UndirectedGraph
from collaborative_hill.domain.world.nipd import NIPDMechanism, NIPDParams
from collaborative_hill.engine.hashing import canonical_json
from collaborative_hill.engine.seeds import rng_for

RING = {"a": ("b", "d"), "b": ("a", "c"), "c": ("b", "d"), "d": ("a", "c")}
STAR = {"a": ("b", "c", "d"), "b": ("a",), "c": ("a",), "d": ("a",)}
ISOLATE = {"a": ("b",), "b": ("a",), "c": ()}


def mechanism(adjacency=RING, mode="neighbourhood", aggregation="mean", **kwargs):
    return GraphNIPDMechanism(
        agent_ids=list(adjacency), adjacency=adjacency, mode=mode,
        payoff_aggregation=aggregation, params=NIPDParams(), rounds=kwargs.pop("rounds", 3),
        **kwargs,
    )


def broadcast(letters):
    return {a: CooperateAction() if move == "C" else DefectAction()
            for a, move in letters.items()}


def resolve(mech, actions, state=None):
    return mech.resolve(state or mech.initial_state(), actions, rng_for("graph-oracle"))


@pytest.mark.parametrize("adjacency,aggregation,expected", [
    (RING, "sum", {"a": "3", "b": "3", "c": "6", "d": "6"}),
    (RING, "mean", {"a": "3/2", "b": "3/2", "c": "3", "d": "3"}),
    (STAR, "sum", {"a": "3", "b": "3", "c": "5", "d": "5"}),
    (STAR, "mean", {"a": "1", "b": "3", "c": "5", "d": "5"}),
])
def test_ring_and_star_broadcast_hand_rewards(adjacency, aggregation, expected):
    # C,C,D,D. Ring: each C has one C neighbor, each D one C neighbor.
    # Star: center C meets C,D,D; each leaf has exactly one opponent.
    mech = mechanism(adjacency, aggregation=aggregation)
    state, events = resolve(mech, broadcast({"a": "C", "b": "C", "c": "D", "d": "D"}))
    assert state["scores"] == expected
    assert events[0]["payload"]["cooperative_votes"] == 2
    assert events[0]["payload"]["total_votes"] == 4
    canonical_json(state)
    canonical_json(events)


@pytest.mark.parametrize("aggregation,expected", [
    ("sum", {"a": "8", "b": "8", "c": "1", "d": "1"}),
    ("mean", {"a": "4", "b": "4", "c": "1/2", "d": "1/2"}),
])
def test_targeted_ring_actions_hand_rewards(aggregation, expected):
    # ab: CC=(3,3); ad: DC=(5,0); bc: DC=(5,0); cd: DD=(1,1).
    mech = mechanism(mode="pairwise", aggregation=aggregation)
    actions = {
        "a": PairwiseVoteAction(moves={"b": "C", "d": "D"}),
        "b": PairwiseVoteAction(moves={"a": "C", "c": "D"}),
        "c": PairwiseVoteAction(moves={"b": "C", "d": "D"}),
        "d": PairwiseVoteAction(moves={"a": "C", "c": "D"}),
    }
    state, events = resolve(mech, actions)
    assert state["scores"] == expected
    assert events[0]["payload"]["cooperative_votes"] == 4
    assert events[0]["payload"]["total_votes"] == 8


@pytest.mark.parametrize("mode", ["pairwise", "neighbourhood"])
@pytest.mark.parametrize("aggregation", ["sum", "mean"])
def test_isolate_zero_reward_and_excluded_interaction_votes(mode, aggregation):
    mech = mechanism(ISOLATE, mode, aggregation)
    actions = (broadcast({"a": "C", "b": "D", "c": "C"}) if mode == "neighbourhood"
               else {"a": PairwiseVoteAction(moves={"b": "C"}),
                     "b": PairwiseVoteAction(moves={"a": "D"}),
                     "c": PairwiseVoteAction(moves={})})
    state, events = resolve(mech, actions)
    assert state["scores"] == {"a": "0", "b": "5", "c": "0"}
    payload = events[0]["payload"]
    assert payload["isolated_agents"] == ["c"]
    assert payload["cooperative_votes"] == 1
    assert payload["total_votes"] == 2
    if mode == "neighbourhood":
        assert payload["moves"] == {"a": "C", "b": "D"}
        assert state["last_moves"]["c"] == "C"
    assert mech.observe(state, "c")["degree"] == 0
    assert mech.observe(state, "c")["neighbors"] == []


def test_scores_accumulate_and_terminal_round_is_exact():
    mech = mechanism(STAR, rounds=2)
    actions = broadcast({"a": "C", "b": "C", "c": "D", "d": "D"})
    state, _ = resolve(mech, actions)
    assert state["round"] == 1 and not mech.is_terminal(state)
    state, _ = resolve(mech, actions, state)
    assert state["scores"] == {"a": "2", "b": "6", "c": "10", "d": "10"}
    assert state["round"] == 2 and mech.is_terminal(state)


def test_adjacency_order_is_canonical_and_input_is_not_mutated():
    submitted = {"c": ["b"], "b": ["c", "a"], "a": ["b"]}
    snapshot = deepcopy(submitted)
    graph = UndirectedGraph(adjacency=submitted)
    assert list(graph.adjacency) == ["a", "b", "c"]
    assert graph.adjacency == {"a": ("b",), "b": ("a", "c"), "c": ("b",)}
    assert submitted == snapshot
    assert UndirectedGraph.model_validate_json(graph.model_dump_json()) == graph


@pytest.mark.parametrize("adjacency,match", [
    ({"a": ("a",)}, "self"),
    ({"a": ("b", "b"), "b": ("a",)}, "duplicate"),
    ({"a": ("b",), "b": ()}, "symmetric"),
    ({"a": ("ghost",), "b": ()}, "unknown"),
    ({"a": (), "b": ()}, "at least one edge"),
    ({}, "at least one edge"),
    ({"": ("b",), "b": ("",)}, "non-empty"),
    ({" ": ("b",), "b": (" ",)}, "non-empty"),
])
def test_invalid_graph_is_rejected(adjacency, match):
    with pytest.raises(ValueError, match=match):
        UndirectedGraph(adjacency=adjacency)


@pytest.mark.parametrize("bad", [0, 2, True, "1", 1.0])
def test_graph_version_is_strict_and_supported(bad):
    with pytest.raises(ValueError):
        UndirectedGraph(adjacency=ISOLATE, version=bad)


@pytest.mark.parametrize("rounds", [0, -1, True, 1.5, "2"])
def test_direct_constructor_rejects_invalid_round_count(rounds):
    with pytest.raises(ValueError, match="rounds"):
        mechanism(rounds=rounds)


@pytest.mark.parametrize("ids", [["a", "b"], ["a", "b", "c", "ghost"], ["a", "b", "b"]])
def test_roster_must_match_adjacency_exactly(ids):
    with pytest.raises(ValueError):
        GraphNIPDMechanism(agent_ids=ids, adjacency=ISOLATE, mode="pairwise",
                           params=NIPDParams(), rounds=2, payoff_aggregation="sum")


@pytest.mark.parametrize("action", [
    PairwiseVoteAction(moves={"b": "C"}),
    PairwiseVoteAction(moves={"b": "C", "c": "C", "d": "D"}),
    PairwiseVoteAction(moves={"a": "C", "b": "C", "d": "D"}),
    CooperateAction(), AbstainAction(),
])
def test_illegal_pairwise_actions_rejected_by_gate_and_direct_resolve(action):
    mech = mechanism(mode="pairwise")
    state = mech.initial_state()
    actions = {a: PairwiseVoteAction(moves=dict.fromkeys(neighbors, "C"))
               for a, neighbors in RING.items()}
    actions["a"] = action
    assert mech.validate_action(state, "a", action) is not None
    with pytest.raises(ValueError, match="a"):
        mech.resolve(state, actions, rng_for("invalid"))
    assert state == mech.initial_state()


def test_unknown_observer_actor_and_incomplete_joint_action_rejected():
    mech = mechanism()
    state = mech.initial_state()
    with pytest.raises(ValueError, match="unknown agent"):
        mech.observe(state, "ghost")
    assert mech.validate_action(state, "ghost", CooperateAction()) is not None
    assert mech.validate_action(state, "a", PairwiseVoteAction(moves={})) is not None
    with pytest.raises(ValueError, match="exactly"):
        resolve(mech, {"a": CooperateAction()})


@pytest.mark.parametrize("mode", ["pairwise", "neighbourhood"])
def test_nonincident_actions_and_all_scores_are_observation_invisible(mode):
    mech = mechanism(mode=mode)
    actions = (broadcast(dict.fromkeys(RING, "C")) if mode == "neighbourhood"
               else {a: PairwiseVoteAction(moves=dict.fromkeys(neighbors, "C"))
                     for a, neighbors in RING.items()})
    state, _ = resolve(mech, actions)
    changed = deepcopy(state)
    changed["scores"] = dict.fromkeys(RING, "999999")
    if mode == "neighbourhood":
        changed["last_moves"]["c"] = "D"  # the only nonneighbor of a
    else:
        changed["last_moves"]["c"] = {"b": "D", "d": "D"}
        changed["last_moves"]["b"]["c"] = "D"  # b's move toward somebody else
    before = mech.observe(state, "a")
    assert before == mech.observe(changed, "a")
    assert before["neighbors"] == ["b", "d"]
    assert before["degree"] == 2 and before["n_agents"] == 4
    assert '"c"' not in canonical_json(before)
    if mode == "neighbourhood":
        assert before["others_cooperated_last_round"] == 2
        assert "moves_against_me" not in before


def test_complete_neighbourhood_matches_all_eight_legacy_profiles():
    ids = ["a", "b", "c"]
    adjacency = {a: tuple(b for b in ids if b != a) for a in ids}
    graph = mechanism(adjacency)
    legacy = NIPDMechanism(agent_ids=ids, mode="neighbourhood", params=NIPDParams(), rounds=3)
    for letters in product("CD", repeat=3):
        actions = broadcast(dict(zip(ids, letters, strict=True)))
        new, graph_events = resolve(graph, actions)
        old, legacy_events = resolve(legacy, actions)
        assert new == old
        assert graph_events[1:] == legacy_events[1:]
        for key, value in legacy_events[0]["payload"].items():
            assert graph_events[0]["payload"][key] == value


def test_complete_pairwise_matches_all_64_legacy_directed_profiles():
    ids = ["a", "b", "c"]
    adjacency = {a: tuple(b for b in ids if b != a) for a in ids}
    graph = mechanism(adjacency, mode="pairwise", aggregation="sum")
    legacy = NIPDMechanism(agent_ids=ids, mode="pairwise", params=NIPDParams(), rounds=3)
    directed = [(a, b) for a in ids for b in ids if a != b]
    for letters in product("CD", repeat=6):
        maps = {a: {} for a in ids}
        for (a, b), move in zip(directed, letters, strict=True):
            maps[a][b] = move
        actions = {a: PairwiseVoteAction(moves=moves) for a, moves in maps.items()}
        new, graph_events = resolve(graph, actions)
        old, legacy_events = resolve(legacy, actions)
        assert new == old
        assert graph_events[1:] == legacy_events[1:]
        for key, value in legacy_events[0]["payload"].items():
            assert graph_events[0]["payload"][key] == value

