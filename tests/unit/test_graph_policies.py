"""Local signals and matched decision streams pin graph policy behavior."""

from fractions import Fraction
from itertools import product
from math import prod

import pytest

from collaborative_hill.agents.scripted.graph_nipd_policies import (
    GraphProbabilisticTFTPolicy,
    GraphThresholdTFTPolicy,
    build_graph_nipd_policy,
)
from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import CooperateAction, DefectAction
from collaborative_hill.domain.world.graph_nipd import GraphNIPDMechanism
from collaborative_hill.domain.world.nipd import NIPDMechanism, NIPDParams
from collaborative_hill.engine.seeds import rng_for


class FixedDraws:
    def __init__(self, *draws):
        self.draws = iter(draws)

    def random(self):
        return next(self.draws)


def observation(*, degree=2, others=1, mine="C"):
    return {"mechanism": "nipd_graph", "n_agents": 100, "degree": degree,
            "others_cooperated_last_round": others, "my_last_move": mine}


@pytest.mark.parametrize("denominator,draw,expected", [
    ("exclude_self", 0.49, "cooperate"),
    ("exclude_self", 0.50, "defect"),
    ("include_self", 0.60, "cooperate"),
    ("include_self", 0.70, "defect"),
])
def test_ptft_uses_local_degree_and_own_move_not_global_population(denominator, draw, expected):
    policy = GraphProbabilisticTFTPolicy(denominator=denominator)
    assert policy.propose(observation(), FixedDraws(draw)).action.type == expected
    assert policy.policy_id.startswith("graph_ptft[")


@pytest.mark.parametrize("degree,others,num,den,expected", [
    (2, 1, 1, 2, "cooperate"),
    (2, 1, 51, 100, "defect"),
    (4, 3, 3, 4, "cooperate"),
    (4, 3, 76, 100, "defect"),
    (3, 0, 0, 1, "cooperate"),
    (3, 3, 1, 1, "cooperate"),
])
def test_local_quorum_is_exact_and_inclusive(degree, others, num, den, expected):
    policy = GraphThresholdTFTPolicy(threshold_num=num, threshold_den=den)
    obs = observation(degree=degree, others=others)
    assert policy.propose(obs, FixedDraws()).action.type == expected
    assert policy.policy_id.startswith("graph_tft_threshold[")


@pytest.mark.parametrize("policy", [
    GraphProbabilisticTFTPolicy("exclude_self"),
    GraphProbabilisticTFTPolicy("include_self"),
    GraphThresholdTFTPolicy(),
])
def test_isolated_policy_starts_c_then_persists_own_move_without_random_draws(policy):
    for others, mine, expected in ((None, None, "cooperate"),
                                  (0, "C", "cooperate"), (0, "D", "defect")):
        assert policy.propose(observation(degree=0, others=others, mine=mine),
                              FixedDraws()).action.type == expected


@pytest.mark.parametrize("name", ["ptft", "tft_threshold"])
def test_isolate_exploration_remains_explicit(name):
    policy = build_graph_nipd_policy(name, "neighbourhood", {"epsilon": "1"})
    action = policy.propose(observation(degree=0, others=0), FixedDraws(0.1, 0.9)).action
    assert isinstance(action, DefectAction)


@pytest.mark.parametrize("name,params", [
    ("ptft", {"denominator": "typo"}), ("ptft", {"epsilon": "-1/10"}),
    ("tft_threshold", {"threshold_num": 3, "threshold_den": 2}),
    ("tft_threshold", {"threshold_den": 0}), ("allc", {"epsilon": 0}),
    ("ptft", {"epislon": 0}),
])
def test_graph_builder_retains_builtin_parameter_contract(name, params):
    with pytest.raises(ValueError):
        build_graph_nipd_policy(name, "neighbourhood", params)


@pytest.mark.parametrize("name,mode", [("ptft", "pairwise"), ("tft_threshold", "pairwise"),
                                        ("tft_pairwise", "neighbourhood"),
                                        ("tft_linked", "neighbourhood")])
def test_graph_policy_mode_mismatch_is_rejected(name, mode):
    with pytest.raises(ValueError, match="requires"):
        build_graph_nipd_policy(name, mode, {})


@pytest.mark.parametrize("name,mode,params", [
    ("allc", "pairwise", {}), ("alld", "pairwise", {}),
    ("random", "pairwise", {}),
    ("tft_pairwise", "pairwise", {"epsilon": "1/5"}),
    ("tft_linked", "pairwise", {"epsilon": "1/5"}),
    ("allc", "neighbourhood", {}), ("alld", "neighbourhood", {}),
    ("random", "neighbourhood", {}),
    ("ptft", "neighbourhood", {"denominator": "include_self", "epsilon": "1/5"}),
    ("ptft", "neighbourhood", {"denominator": "exclude_self", "epsilon": "1/5"}),
    ("tft_threshold", "neighbourhood", {"threshold_num": 1, "threshold_den": 2,
                                        "epsilon": "1/5"}),
])
def test_complete_graph_matches_every_legacy_policy_with_matched_streams(name, mode, params):
    ids = ["a", "b", "c", "d", "e"]
    adjacency = {a: tuple(b for b in ids if b != a) for a in ids}
    graph = GraphNIPDMechanism(agent_ids=ids, adjacency=adjacency, mode=mode,
                               payoff_aggregation="sum" if mode == "pairwise" else "mean",
                               params=NIPDParams(), rounds=12)
    legacy = NIPDMechanism(agent_ids=ids, mode=mode, params=NIPDParams(), rounds=12)
    graph_policies = {a: build_graph_nipd_policy(name if a != "e" else "alld", mode,
                                                params if a != "e" else {}) for a in ids}
    old_policies = {a: build_nipd_policy(name if a != "e" else "alld", mode,
                                        coerce_policy_params(name, params) if a != "e" else {})
                    for a in ids}
    graph_state, old_state = graph.initial_state(), legacy.initial_state()
    for rnd in range(12):
        ga, oa = {}, {}
        for a in ids:
            ga[a] = graph_policies[a].propose(graph.observe(graph_state, a),
                                              rng_for("control", name, rnd, a)).action
            oa[a] = old_policies[a].propose(legacy.observe(old_state, a),
                                            rng_for("control", name, rnd, a)).action
        assert ga == oa
        graph_state, ge = graph.resolve(graph_state, ga, rng_for("world", rnd))
        old_state, oe = legacy.resolve(old_state, oa, rng_for("world", rnd))
        assert graph_state == old_state
        assert ge[1:] == oe[1:]
        assert ge[0]["payload"]["cooperative_votes"] == oe[0]["payload"]["cooperative_votes"]


def test_equal_global_cooperator_counts_need_not_give_equal_sparse_signals():
    # Ring a-b-c-d-a; both profiles have two C, with a itself C.
    # At a, {a,b} yields one C neighbor, while {a,c} yields none.
    graph = GraphNIPDMechanism(
        agent_ids=["a", "b", "c", "d"], mode="neighbourhood", params=NIPDParams(),
        rounds=2, payoff_aggregation="mean",
        adjacency={"a": ("b", "d"), "b": ("a", "c"),
                   "c": ("b", "d"), "d": ("a", "c")},
    )
    policy = GraphProbabilisticTFTPolicy("exclude_self")
    actions = []
    for cooperators in ({"a", "b"}, {"a", "c"}):
        state = graph.initial_state()
        state.update(round=1, last_moves={a: "C" if a in cooperators else "D"
                                          for a in graph.agent_ids()})
        actions.append(policy.propose(graph.observe(state, "a"), FixedDraws(0.4)).action)
    assert isinstance(actions[0], CooperateAction)
    assert isinstance(actions[1], DefectAction)


def test_sparse_fixed_defector_count_is_not_lumpable_exact_oracle():
    # Four-cycle, node 4 fixed D; only nodes 1,2,3 use exclude-self pTFT.
    # Adjacent C pair: p=(1/2,1/2,1/2). Opposite C pair: p=(0,1,0).
    graph = GraphNIPDMechanism(
        agent_ids=["1", "2", "3", "4"], mode="neighbourhood", params=NIPDParams(),
        rounds=4, payoff_aggregation="mean",
        adjacency={"1": ("2", "4"), "2": ("1", "3"),
                   "3": ("2", "4"), "4": ("1", "3")},
    )
    probabilities = []
    distributions = []
    for cooperators in ({"1", "2"}, {"1", "3"}):
        state = graph.initial_state()
        state.update(round=1, last_moves={a: "C" if a in cooperators else "D"
                                          for a in graph.agent_ids()})
        observations = [graph.observe(state, a) for a in ("1", "2", "3")]
        p = tuple(Fraction(obs["others_cooperated_last_round"], obs["degree"])
                  for obs in observations)
        probabilities.append(p)
        # Enumerate labelled independent Bernoulli outcomes, not a count-state
        # transition helper. This is an ideal rational-model proof, not a draw.
        mass = [Fraction(0) for _ in range(4)]
        for bits in product((0, 1), repeat=3):
            mass[sum(bits)] += prod((q if bit else 1 - q for q, bit in zip(p, bits, strict=True)),
                                    start=Fraction(1))
        distributions.append(mass)
    assert probabilities == [(Fraction(1, 2),) * 3, (Fraction(0), Fraction(1), Fraction(0))]
    assert distributions == [[Fraction(1, 8), Fraction(3, 8), Fraction(3, 8), Fraction(1, 8)],
                             [Fraction(0), Fraction(1), Fraction(0), Fraction(0)]]
    assert [sum(i * q for i, q in enumerate(mass)) for mass in distributions] == [Fraction(3, 2), 1]
    adjacent = probabilities[0]
    assert adjacent[0] * (1 - adjacent[1]) * adjacent[2] == Fraction(1, 8)

    def local_probabilities(bits):
        state = graph.initial_state()
        state.update(round=1, last_moves={"1": "C" if bits[0] else "D",
                                          "2": "C" if bits[1] else "D",
                                          "3": "C" if bits[2] else "D", "4": "D"})
        obs = [graph.observe(state, a) for a in ("1", "2", "3")]
        return tuple(Fraction(o["others_cooperated_last_round"], o["degree"]) for o in obs)

    def probability(p, bits):
        return prod((q if bit else 1 - q for q, bit in zip(p, bits, strict=True)),
                    start=Fraction(1))

    # Also rule out weak lumpability from the actual all-reciprocator-C start.
    # Both histories end at X2=2 but retain different X3 conditional means.
    history_mass = dict.fromkeys(((3, 3, 2), (3, 2, 2)), Fraction(0))
    weighted_next_mean = dict(history_mass)
    initial_p = local_probabilities((1, 1, 1))
    for first in product((0, 1), repeat=3):
        p_first = probability(initial_p, first)
        for second in product((0, 1), repeat=3):
            history = (3, sum(first), sum(second))
            if history in history_mass:
                mass = p_first * probability(local_probabilities(first), second)
                history_mass[history] += mass
                weighted_next_mean[history] += mass * sum(local_probabilities(second))
    assert history_mass == {(3, 3, 2): Fraction(1, 8), (3, 2, 2): Fraction(3, 16)}
    assert {h: weighted_next_mean[h] / p for h, p in history_mass.items()} == {
        (3, 3, 2): Fraction(3, 2), (3, 2, 2): Fraction(4, 3),
    }

