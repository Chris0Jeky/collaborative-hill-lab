"""Exact pTFT benchmarks checked against labelled choices, not binomial formulas."""

import importlib.util
import itertools
import sys
from decimal import ROUND_DOWN, ROUND_UP, Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path

import pytest

from collaborative_hill.engine.hashing import canonical_json

MODULE_PATH = (Path(__file__).resolve().parents[2]
               / "studies/002-nipd-sensitivity/study002_markov.py")


@pytest.fixture(scope="module")
def markov():
    assert MODULE_PATH.exists(), "Study 002 exact Markov benchmark is not implemented"
    spec = importlib.util.spec_from_file_location("study002_markov", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def labelled_choices(previous, n, denominator):
    """Enumerate each agent's next vote from its own labelled neighborhood."""
    population = previous + (0,) * (n - len(previous))
    for following in itertools.product((0, 1), repeat=len(previous)):
        probability = F(1)
        for agent, vote in enumerate(following):
            observed = [move for seat, move in enumerate(population)
                        if denominator == "include_self" or seat != agent]
            chance = F(sum(observed), len(observed))
            probability *= chance if vote else 1 - chance
        if probability:
            yield following, probability


def labelled_paths(n, m, denominator, rounds):
    paths = {((1,) * m, (m,)): F(1)}
    for _ in range(rounds - 1):
        following_paths = {}
        for (previous, counts), probability in paths.items():
            for following, chance in labelled_choices(previous, n, denominator):
                key = (following, (*counts, sum(following)))
                following_paths[key] = following_paths.get(key, F()) + probability * chance
        paths = following_paths
    assert sum(paths.values()) == 1
    return paths


@pytest.mark.parametrize("denominator,rows", [
    ("include_self", [["1", "0", "0"], ["4/9", "4/9", "1/9"], ["1/9", "4/9", "4/9"]]),
    ("exclude_self", [["1", "0", "0"], ["1/2", "1/2", "0"], ["1/4", "1/2", "1/4"]]),
])
def test_n3_m2_transition_rows_have_literal_oracles(markov, denominator, rows):
    assert markov.transition_matrix(3, 2, denominator) == tuple(
        tuple(map(F, row)) for row in rows
    )


@pytest.mark.parametrize("denominator", ["include_self", "exclude_self"])
def test_count_chain_matches_every_small_labelled_transition(markov, denominator):
    for n in range(2, 6):
        for m in range(n + 1):
            matrix = markov.transition_matrix(n, m, denominator)
            assert len(matrix) == m + 1
            for previous in itertools.product((0, 1), repeat=m):
                expected = [F()] * (m + 1)
                for following, probability in labelled_choices(previous, n, denominator):
                    expected[sum(following)] += probability
                assert matrix[sum(previous)] == tuple(expected)
                assert sum(matrix[sum(previous)]) == 1


@pytest.mark.parametrize("denominator", ["include_self", "exclude_self"])
def test_moments_absorption_and_episode_variance_match_labelled_histories(markov, denominator):
    rounds = 3
    for n in range(2, 5):
        for m in range(n + 1):
            paths = labelled_paths(n, m, denominator, rounds)
            means = [sum(probability * counts[t] for (_, counts), probability in paths.items())
                     for t in range(rounds)]
            seconds = [sum(probability * counts[t] ** 2
                           for (_, counts), probability in paths.items()) for t in range(rounds)]
            average = sum(probability * F(sum(counts), n * rounds)
                          for (_, counts), probability in paths.items())
            variance = sum(probability * (F(sum(counts), n * rounds) - average) ** 2
                           for (_, counts), probability in paths.items())
            cross_covariances = sum(
                sum(probability * counts[s] * counts[t]
                    for (_, counts), probability in paths.items()) - means[s] * means[t]
                for s in range(rounds) for t in range(s + 1, rounds)
            )
            result = markov.benchmark(n, m, denominator, rounds=rounds)
            assert list(map(F, result["expected_cooperators_by_round"])) == means
            assert list(map(F, result["expected_squared_cooperators_by_round"])) == seconds
            assert list(map(F, result["cooperation_by_round"])) == [mean / n for mean in means]
            assert F(result["mean_cooperation"]) == average
            assert F(result["variance_mean_cooperation"]) == variance
            assert F(result["variance_terms"]["sum_cross_time_count_covariances"]) == (
                cross_covariances
            )
            assert list(map(F, result["absorption_by_round"])) == [
                sum(probability for (_, counts), probability in paths.items() if counts[t] == 0)
                for t in range(rounds)
            ]
            canonical_json(result)


@pytest.mark.parametrize("denominator,first,second,absorption,average,variance,marginal,cross", [
    ("include_self", ["2", "4/3", "8/9"], ["4", "20/9", "112/81"],
     ["0", "1/9", "29/81"], "38/81", "44/2187", "28/27", "8/27"),
    ("exclude_self", ["2", "1", "1/2"], ["4", "3/2", "5/8"],
     ["0", "1/4", "9/16"], "7/18", "11/648", "7/8", "1/4"),
])
def test_three_round_hand_oracle_includes_cross_time_covariance(
    markov, denominator, first, second, absorption, average, variance, marginal, cross,
):
    result = markov.benchmark(3, 2, denominator, rounds=3)
    assert result["expected_cooperators_by_round"] == first
    assert result["expected_squared_cooperators_by_round"] == second
    assert result["absorption_by_round"] == absorption
    assert result["absorption_probability_by_last_round"] == absorption[-1]
    assert result["mean_cooperation"] == average
    assert result["variance_mean_cooperation"] == variance
    assert result["variance_terms"] == {
        "sum_count_variances": marginal,
        "sum_cross_time_count_covariances": cross,
        "normalizer": "81",
    }


@pytest.mark.parametrize("denominator,average,variance", [
    ("include_self", "5/9", "1/81"), ("exclude_self", "1/2", "1/72"),
])
def test_two_round_hand_oracle(markov, denominator, average, variance):
    result = markov.benchmark(3, 2, denominator, rounds=2)
    assert result["mean_cooperation"] == average
    assert result["variance_mean_cooperation"] == variance


@pytest.mark.parametrize("denominator,average,variance,zero_probability", [
    ("include_self", "10/27", "11/243", "1/9"),
    ("exclude_self", "1/4", "11/288", "1/4"),
])
def test_final_window_hand_oracle_preserves_time_covariance_and_zero_event(
    markov, denominator, average, variance, zero_probability,
):
    result = markov.benchmark(3, 2, denominator, rounds=3, window=2)
    assert result["final_window"] == 2
    assert result["final_window_cooperation"] == average
    assert result["variance_final_window_cooperation"] == variance
    assert result["final_window_all_d_probability"] == zero_probability
    assert F(zero_probability) < F(result["absorption_probability_by_last_round"])


@pytest.mark.parametrize("window", [0, -1, 4, True, 2.0, "2"])
def test_invalid_final_window_is_rejected(markov, window):
    with pytest.raises(ValueError, match="window"):
        markov.benchmark(3, 2, "include_self", rounds=3, window=window)


@pytest.mark.parametrize("denominator", ["include_self", "exclude_self"])
@pytest.mark.parametrize("n", [2, 3, 5])
def test_absorbing_boundaries_and_initial_round(markov, denominator, n):
    for m, cooperation, absorption in ((0, "0", "1"), (n, "1", "0")):
        result = markov.benchmark(n, m, denominator, rounds=4)
        assert result["cooperation_by_round"] == [cooperation] * 4
        assert result["mean_cooperation"] == cooperation
        assert result["variance_mean_cooperation"] == "0"
        assert result["absorption_by_round"] == [absorption] * 4
    first_only = markov.benchmark(n, n - 1, denominator, rounds=1)
    assert F(first_only["mean_cooperation"]) == F(n - 1, n)
    assert first_only["variance_mean_cooperation"] == "0"
    assert first_only["absorption_probability_by_last_round"] == "0"


def test_single_exclude_self_reciprocator_collapses_after_initial_round(markov):
    result = markov.benchmark(3, 1, "exclude_self", rounds=4)
    assert result["cooperation_by_round"] == ["1/3", "0", "0", "0"]
    assert result["mean_cooperation"] == "1/12"
    assert result["variance_mean_cooperation"] == "0"
    assert result["absorption_by_round"] == ["0", "1", "1", "1"]


@pytest.mark.parametrize("field,value", [
    ("n_agents", 1), ("n_agents", True), ("n_agents", 3.0), ("n_agents", "3"),
    ("reciprocators", -1), ("reciprocators", 4), ("reciprocators", True),
    ("reciprocators", 2.0), ("reciprocators", "2"),
    ("rounds", 0), ("rounds", -1), ("rounds", True), ("rounds", 3.0), ("rounds", "3"),
    ("denominator", "other"), ("denominator", None),
])
def test_invalid_model_parameters_are_rejected(markov, field, value):
    parameters = {"n_agents": 3, "reciprocators": 2, "denominator": "include_self", "rounds": 3}
    parameters[field] = value
    with pytest.raises(ValueError, match=field):
        markov.benchmark(**parameters)
    if field != "rounds":
        parameters.pop("rounds")
        with pytest.raises(ValueError, match=field):
            markov.transition_matrix(**parameters)


def test_f40_and_f49_remain_distinct_exact_probabilities(markov):
    result = markov.benchmark(5, 4, "include_self", rounds=50)
    absorption = list(map(F, result["absorption_by_round"]))
    assert len(absorption) == 50
    assert 0 < absorption[40] < absorption[49] < 1
    assert result["absorption_probability_by_last_round"] == result["absorption_by_round"][49]
    assert result["status"] == "post_hoc_analytical_benchmark"
    assert result["model"] == "ideal_rational_bernoulli"
    assert result["absorption_state"] == 0
    assert F(result["variance_mean_cooperation"]) > 0
    canonical_json(result)


def test_model_mc_error_retains_exact_variance_and_labels_decimal_approximation(markov):
    result = markov.monte_carlo_standard_error("1/81", replicates=4)
    assert result["variance_of_mean"] == "1/324"
    assert Decimal(result["standard_error_decimal_approximation"]) == pytest.approx(
        Decimal(1) / Decimal(18), rel=Decimal("1e-11"),
    )
    assert result["replicates"] == 4
    assert result["basis"] == "independent ideal-model episodes"
    canonical_json(result)


def test_probability_power_retains_symbolic_exactness_without_relaxing_digit_limit(markov):
    # The expanded exact power would need over 5,700 decimal digits. The
    # expression is exact; its bounded decimal display may round up to one.
    denominator = 10 ** 180
    base = f"{denominator - 1}/{denominator}"
    limit = sys.get_int_max_str_digits()
    result = markov.independent_probability_power(base, power=32)
    assert result["base_fraction"] == base
    assert result["power"] == 32
    assert Decimal(result["decimal_approximation"]) == 1
    assert "expanded_fraction" not in result
    assert sys.get_int_max_str_digits() == limit
    assert Decimal(markov.independent_probability_power("3/4", power=2)[
        "decimal_approximation"
    ]) == Decimal("0.5625")
    canonical_json(result)


@pytest.mark.parametrize("rounding", [ROUND_DOWN, ROUND_UP])
def test_decimal_displays_do_not_depend_on_ambient_decimal_context(markov, rounding):
    expected_se = markov.monte_carlo_standard_error("1/81", replicates=4)
    expected_power = markov.independent_probability_power("1/3", power=3)
    with localcontext() as context:
        context.prec = 3
        context.rounding = rounding
        assert markov.monte_carlo_standard_error("1/81", replicates=4) == expected_se
        assert markov.independent_probability_power("1/3", power=3) == expected_power


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "2"])
def test_display_helpers_require_positive_integer_episode_counts(markov, value):
    with pytest.raises(ValueError, match="replicates"):
        markov.monte_carlo_standard_error("1/81", replicates=value)
    with pytest.raises(ValueError, match="power"):
        markov.independent_probability_power("1/2", power=value)


@pytest.mark.parametrize("base", ["-1/2", "3/2", "not-a-fraction"])
def test_probability_power_rejects_invalid_probability(markov, base):
    with pytest.raises(ValueError):
        markov.independent_probability_power(base, power=2)


def test_mc_error_rejects_negative_variance(markov):
    with pytest.raises(ValueError, match="variance"):
        markov.monte_carlo_standard_error("-1/81", replicates=4)
