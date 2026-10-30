"""Exact sparse pTFT: independent histories, policy boundary and regeneration."""

import importlib.util
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest
from _sparse_ptft_oracle import histories

from collaborative_hill.agents.scripted.graph_nipd_policies import GraphProbabilisticTFTPolicy
from collaborative_hill.domain.world.graph_nipd import GraphNIPDMechanism
from collaborative_hill.domain.world.nipd import NIPDParams
from collaborative_hill.engine.hashing import canonical_json

REPO = Path(__file__).resolve().parents[2]
HERE = REPO / "experiments/sparse-ptft"
RING = {"a": ("b", "d"), "b": ("a", "c"), "c": ("b", "d"), "d": ("a", "c")}
STAR = {"a": ("b", "c", "d"), "b": ("a",), "c": ("a",), "d": ("a",)}
RULES = ("include_self", "exclude_self")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def exact():
    return load("sparse_ptft_exact", HERE / "sparse_ptft_exact.py")


@pytest.fixture(scope="module")
def generator(exact):
    return load("sparse_ptft_generate", HERE / "generate.py")


@pytest.mark.parametrize("rule", RULES)
@pytest.mark.parametrize("graph", [RING, STAR])
@pytest.mark.parametrize("fixed", [(), ("a",), ("d",), ("a", "b", "c", "d")])
def test_independent_copying_histories_match_all_moments(exact, graph, fixed, rule):
    rounds = 4
    paths = histories(graph, fixed, rule, rounds)
    model = exact.GraphPTFT(graph, fixed, rule)
    matrix = model.transition_matrix()
    assert len(matrix) == 2 ** (len(graph) - len(fixed))
    assert all(sum(row) == 1 and all(p >= 0 for p in row) for row in matrix)
    record = model.benchmark(rounds)
    counts = {h: tuple(map(sum, h)) for h in paths}
    means = [sum(p * counts[h][t] for h, p in paths.items()) for t in range(rounds)]
    seconds = [sum(p * counts[h][t] ** 2 for h, p in paths.items()) for t in range(rounds)]
    average = sum(p * F(sum(counts[h]), len(graph) * rounds) for h, p in paths.items())
    variance = sum(p * (F(sum(counts[h]), len(graph) * rounds) - average) ** 2
                   for h, p in paths.items())
    cross = sum(sum(p * counts[h][s] * counts[h][t] for h, p in paths.items())
                - means[s] * means[t] for s in range(rounds) for t in range(s + 1, rounds))
    absorption = [sum(p for h, p in paths.items() if counts[h][t] == 0) for t in range(rounds)]
    assert list(map(F, record["expected_cooperators_by_round"])) == means
    assert list(map(F, record["expected_squared_cooperators_by_round"])) == seconds
    assert F(record["mean_cooperation"]) == average
    assert F(record["variance_mean_cooperation"]) == variance
    assert F(record["variance_cumulative_cooperators"]) == variance * (len(graph) * rounds) ** 2
    assert F(record["variance_terms"]["sum_cross_time_count_covariances"]) == cross
    assert list(map(F, record["absorption_by_round"])) == absorption
    assert list(map(F, record["first_all_d_by_round"])) == [
        absorption[0], *(absorption[t] - absorption[t - 1] for t in range(1, rounds))]
    assert F(record["restricted_mean_first_all_d_round"]) == sum(1 - p for p in absorption[:-1])
    assert list(map(F, record["last_round_state_probabilities"])) == [
        sum(p for h, p in paths.items() if h[-1] == state) for state in model.states]
    canonical_json(record)


@pytest.mark.parametrize("rule", RULES)
def test_complete_graph_projection_matches_existing_benchmark(exact, rule):
    old = load("sparse_complete_control", REPO / "studies/002-nipd-sensitivity/study002_markov.py")
    for n in range(2, 6):
        agents = tuple(map(str, range(n)))
        graph = {a: tuple(b for b in agents if b != a) for a in agents}
        for m in range(n + 1):
            model = exact.GraphPTFT(graph, agents[m:], rule)
            assert model.count_projection() == old.transition_matrix(n, m, rule)
            for rounds in (1, 4, 8):
                record, control = model.benchmark(rounds), old.benchmark(n, m, rule, rounds=rounds)
                for key in ("expected_cooperators_by_round",
                            "expected_squared_cooperators_by_round",
                            "cooperation_by_round", "absorption_by_round", "mean_cooperation",
                            "variance_mean_cooperation", "variance_terms"):
                    assert record[key] == control[key]


def test_four_cycle_and_initialized_count_history_witness(exact):
    model = exact.GraphPTFT(RING, ("d",), "exclude_self")
    matrix = model.transition_matrix()
    adjacent, opposite = (1, 1, 0, 0), (1, 0, 1, 0)
    pmfs = []
    for state in (adjacent, opposite):
        row = matrix[model.states.index(state)]
        pmfs.append(tuple(sum(p for s, p in zip(model.states, row, strict=True) if sum(s) == k)
                          for k in range(4)))
    assert pmfs == [(F(1, 8), F(3, 8), F(3, 8), F(1, 8)), (F(0), F(1), F(0), F(0))]
    assert matrix[model.states.index(adjacent)][model.states.index(opposite)] == F(1, 8)
    for rule in RULES:
        with pytest.raises(ValueError, match="not lumpable"):
            exact.GraphPTFT(RING, ("d",), rule).count_projection()
    paths = histories(RING, ("d",), "exclude_self", 4)
    for prefix, probability, next_mean in (((3, 3, 2), F(1, 8), F(3, 2)),
                                            ((3, 2, 2), F(3, 16), F(4, 3))):
        selected = {h: p for h, p in paths.items() if tuple(map(sum, h[:3])) == prefix}
        assert sum(selected.values()) == probability
        assert sum(p * sum(h[-1]) for h, p in selected.items()) / probability == next_mean


@pytest.mark.parametrize("graph", [RING, STAR])
@pytest.mark.parametrize("rule", RULES)
def test_vertex_relabeling_preserves_labeled_laws_and_oracle(exact, graph, rule):
    rename = {"a": "z", "b": "j", "c": "x", "d": "b"}
    relabeled = {rename[a]: tuple(rename[b] for b in neighbors) for a, neighbors in graph.items()}
    first = exact.GraphPTFT(graph, ("d",), rule)
    second = exact.GraphPTFT(relabeled, (rename["d"],), rule)

    def permute(state):
        votes = {rename[a]: vote for a, vote in zip(first.agents, state, strict=True)}
        return tuple(votes[a] for a in second.agents)

    indices = [second.states.index(permute(state)) for state in first.states]
    p, q = first.transition_matrix(), second.transition_matrix()
    assert p == tuple(tuple(q[i][j] for j in indices) for i in indices)
    original = histories(graph, ("d",), rule, 3)
    assert {tuple(permute(s) for s in h): p for h, p in original.items()} == histories(
        relabeled, (rename["d"],), rule, 3)
    for key in ("cooperation_by_round", "variance_mean_cooperation", "absorption_by_round"):
        assert first.benchmark(4)[key] == second.benchmark(4)[key]


class ProbabilityProbe:
    def __init__(self):
        self.thresholds = []

    def random(self):
        return self

    def __lt__(self, threshold):
        self.thresholds.append(threshold)
        return False


@pytest.mark.parametrize("graph", [RING, STAR])
@pytest.mark.parametrize("rule", RULES)
@pytest.mark.parametrize("aggregation", ["sum", "mean"])
def test_probabilities_match_real_policy_on_real_observations(exact, graph, rule, aggregation):
    model = exact.GraphPTFT(graph, ("d",), rule)
    world = GraphNIPDMechanism(agent_ids=list(graph), adjacency=graph, mode="neighbourhood",
                               params=NIPDParams(), rounds=8, payoff_aggregation=aggregation)
    policy = GraphProbabilisticTFTPolicy(rule)
    for actor in model.dynamic_agents:
        assert policy.propose(world.observe(world.initial_state(), actor), ProbabilityProbe()
                              ).action.type == "cooperate"
    for state in model.states:
        probabilities = model.probabilities(state)
        for i, actor in enumerate(model.agents):
            if actor == "d":
                assert probabilities[i] == 0
                continue
            observation = world.observe({"round": 1, "last_moves": {
                a: "C" if v else "D" for a, v in zip(model.agents, state, strict=True)}}, actor)
            probe = ProbabilityProbe()
            policy.propose(observation, probe)
            assert probe.thresholds == [float(probabilities[i])]
    assert F(float(F(1, 3))) != F(1, 3)  # Rounded thresholds are not ideal rational draws.


@pytest.mark.parametrize("graph,fixed,rule,match", [
    (RING, ("missing",), "exclude_self", "fixed_defectors"),
    (RING, ("d", "d"), "exclude_self", "fixed_defectors"),
    (RING, "d", "exclude_self", "fixed_defectors"),
    (RING, (), "typo", "denominator"),
    ({"a": ("b",), "b": ("a",), "c": ("d",), "d": ("c",)}, (), "include_self", "connected"),
    ({"a": ("b",), "b": ("a",), "c": ()}, (), "include_self", "connected"),
    ({str(i): tuple(str(j) for j in range(7) if j != i) for i in range(7)},
     (), "exclude_self", "at most 6"),
    ({"a": ("b",), "b": ()}, (), "exclude_self", "symmetric"),
    ({"a": ("a", "b"), "b": ("a",)}, (), "exclude_self", "self-loop"),
])
def test_unsupported_inputs_fail_clearly(exact, graph, fixed, rule, match):
    with pytest.raises(ValueError, match=match):
        exact.GraphPTFT(graph, fixed, rule)


@pytest.mark.parametrize("state", [(1, 0), (1, 1, 1, 1), (True, 0, 0, 0), (2, 0, 0, 0)])
def test_invalid_action_vectors_fail(exact, state):
    with pytest.raises(ValueError, match="state"):
        exact.GraphPTFT(RING, ("d",), "exclude_self").probabilities(state)


@pytest.mark.parametrize("rounds", [0, -1, True, 1.5, 51])
def test_unsupported_horizons_fail(exact, rounds):
    with pytest.raises(ValueError, match="rounds"):
        exact.GraphPTFT(RING, ("d",), "exclude_self").benchmark(rounds)


def test_maximum_supported_state_space_is_exact(exact):
    agents = tuple(map(str, range(6)))
    graph = {a: tuple(b for b in agents if b != a) for a in agents}
    model = exact.GraphPTFT(graph, (), "include_self")
    assert len(model.states) == 64
    assert all(sum(row) == 1 and all(p >= 0 for p in row) for row in model.transition_matrix())


def test_byte_regeneration_is_read_only_and_rejects_drift(generator, tmp_path):
    generator.generate(tmp_path)
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    generator.generate(tmp_path, check=True)
    generator.generate(tmp_path)
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    canonical_json(json.loads((tmp_path / "EXACT.json").read_text(encoding="utf-8")))
    for path in tmp_path.iterdir():
        path.write_bytes(b"drift\n")
        with pytest.raises(ValueError, match="differs"):
            generator.generate(tmp_path, check=True)
        with pytest.raises(ValueError, match="refusing"):
            generator.generate(tmp_path)
        assert path.read_bytes() == b"drift\n"
        path.write_bytes(before[path.name][0])
    with pytest.raises(ValueError, match="missing"):
        generator.generate(tmp_path / "absent", check=True)


def test_star_hub_and_leaf_have_different_exact_results(exact):
    hub = exact.GraphPTFT(STAR, ("a",), "exclude_self").benchmark(4)
    leaf = exact.GraphPTFT(STAR, ("d",), "exclude_self").benchmark(4)
    assert hub["cooperation_by_round"] == ["3/4", "0", "0", "0"]
    assert hub["mean_cooperation"] == "3/16"
    assert hub["variance_mean_cooperation"] == "0"
    assert leaf["cooperation_by_round"] == ["3/4", "2/3", "1/2", "4/9"]
    assert F(leaf["variance_mean_cooperation"]) > 0
