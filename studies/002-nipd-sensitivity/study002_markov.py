"""Post-hoc exact finite-population pTFT benchmark for the ideal Bernoulli model.

There are N agents: m pTFT agents and N-m fixed AllD agents, complete
neighborhood observation, and zero exploration. X_t counts cooperating pTFT
agents; X_0=m and the requested rounds include this initial round.

With self included, X_(t+1) | X_t=x is Binomial(m, x/N). With self excluded,
the x previous cooperators and m-x previous defectors use probabilities
(x-1)/(N-1) and x/(N-1), respectively. Their independent binomials convolve.

The conditional count mean is lambda*x, where lambda=m/N or (m-1)/(N-1).
For t>=s, E[X_t X_s]=lambda**(t-s) E[X_s**2], hence the count covariance is
lambda**(t-s) Var(X_s). Summing these covariances, including both off-diagonal
halves, and dividing by (N*rounds)**2 gives the episode-mean variance.

Absorption here means reaching X=0, not reaching any absorbing state. All-C
controls remain all-C. This module reads no run artifacts, invokes no simulator,
and changes neither its finite-precision Bernoulli sampling nor its hashes.
Benchmark records contain exact fraction strings. Separate Decimal helpers
provide labeled display approximations, never normal intervals or empirical
certainty claims. This extension is post hoc, not a preregistered prediction.
"""

from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction
from math import comb
from typing import Any, Literal

from collaborative_hill.engine.hashing import frac_str

Denominator = Literal["include_self", "exclude_self"]
Matrix = tuple[tuple[Fraction, ...], ...]
DISPLAY_DIGITS = 12


def _integer_at_least(value: int, minimum: int, name: str) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _binomial(trials: int, probability: Fraction) -> tuple[Fraction, ...]:
    # An absent group has no probability parameter: at x=0 the unused
    # exclude-self cooperator probability is negative; at x=m=N the unused
    # defector probability exceeds one. Neither enters an actual draw.
    if trials == 0:
        return (Fraction(1),)
    return tuple(Fraction(comb(trials, successes)) * probability ** successes
                 * (1 - probability) ** (trials - successes)
                 for successes in range(trials + 1))


def transition_matrix(n_agents: int, reciprocators: int, denominator: Denominator) -> Matrix:
    """Exact count transitions, with rows and columns ordered 0,...,m."""
    _integer_at_least(n_agents, 2, "n_agents")
    _integer_at_least(reciprocators, 0, "reciprocators")
    if reciprocators > n_agents:
        raise ValueError("reciprocators must be <= n_agents")
    if denominator not in ("include_self", "exclude_self"):
        raise ValueError("denominator must be include_self or exclude_self")
    rows = []
    for count in range(reciprocators + 1):
        if denominator == "include_self":
            rows.append(_binomial(reciprocators, Fraction(count, n_agents)))
            continue
        cooperators = _binomial(count, Fraction(count - 1, n_agents - 1))
        defectors = _binomial(reciprocators - count, Fraction(count, n_agents - 1))
        row = [Fraction()] * (reciprocators + 1)
        for a, probability_a in enumerate(cooperators):
            for b, probability_b in enumerate(defectors):
                row[a + b] += probability_a * probability_b
        rows.append(tuple(row))
    return tuple(rows)


def _moments(matrix: Matrix, rounds: int) -> tuple[
    list[Fraction], list[Fraction], list[Fraction], tuple[Fraction, ...],
]:
    distribution = (Fraction(),) * (len(matrix) - 1) + (Fraction(1),)
    first, second, absorption = [], [], []
    for t in range(rounds):
        first.append(sum((count * p for count, p in enumerate(distribution)), Fraction()))
        second.append(sum((count * count * p for count, p in enumerate(distribution)), Fraction()))
        absorption.append(distribution[0])
        if t + 1 < rounds:
            distribution = tuple(
                sum((p * matrix[count][following] for count, p in enumerate(distribution)),
                    Fraction())
                for following in range(len(matrix))
            )
    return first, second, absorption, distribution


def _mean_variance(first: list[Fraction], second: list[Fraction], decay: Fraction,
                   n_agents: int) -> tuple[Fraction, dict[str, str]]:
    count_variances = [square - average * average
                       for average, square in zip(first, second, strict=True)]
    marginal_sum = sum(count_variances, Fraction())
    cross_sum, future_decay_sum = Fraction(), Fraction()
    # At round s, future_decay_sum = lambda + ... + lambda**(rounds-1-s).
    # This reverse recurrence sums all distinct cross-time covariances in O(R).
    for variance in reversed(count_variances):
        cross_sum += variance * future_decay_sum
        future_decay_sum = decay * (1 + future_decay_sum)
    normalizer = (n_agents * len(first)) ** 2
    return (marginal_sum + 2 * cross_sum) / normalizer, {
        "sum_count_variances": frac_str(marginal_sum),
        "sum_cross_time_count_covariances": frac_str(cross_sum),
        "normalizer": frac_str(normalizer),
    }


def benchmark(n_agents: int, reciprocators: int, denominator: Denominator, *,
              rounds: int = 50, window: int | None = None) -> dict[str, Any]:
    """Exact finite-horizon record; no simulation, sampled data, or fitted terms.

    ``absorption_by_round[t]`` is P(X_t=0)=P(first all-D round<=t), since
    zero is absorbing. Thus for Study 002, index 40 describes a zero final-ten
    window and index 49 describes absorption by the last observed round.
    When requested, the final-window mean and variance include its full
    cross-time covariance, and its all-zero probability is F_(rounds-window).
    """
    _integer_at_least(rounds, 1, "rounds")
    if window is not None:
        _integer_at_least(window, 1, "window")
        if window > rounds:
            raise ValueError("window must be <= rounds")
    matrix = transition_matrix(n_agents, reciprocators, denominator)
    decay = (Fraction(reciprocators, n_agents) if denominator == "include_self"
             else Fraction(reciprocators - 1, n_agents - 1))
    first, second, absorption, distribution = _moments(matrix, rounds)
    variance, variance_terms = _mean_variance(first, second, decay, n_agents)
    result = {
        "schema_version": 1, "analysis_version": "study002_markov@1",
        "status": "post_hoc_analytical_benchmark", "model": "ideal_rational_bernoulli",
        "n_agents": n_agents, "reciprocators": reciprocators,
        "fixed_defectors": n_agents - reciprocators, "epsilon": "0",
        "denominator": denominator, "rounds": rounds,
        "initial_cooperators": reciprocators, "first_round_index": 0,
        "absorption_state": 0,
        # With no reciprocators the formal exclude-self coefficient is negative
        # but multiplies only zeros; there is no population decay to describe.
        "decay_factor": frac_str(decay) if reciprocators else None,
        "transition_probabilities": [[frac_str(p) for p in row] for row in matrix],
        "last_round_state_probabilities": [frac_str(p) for p in distribution],
        "expected_cooperators_by_round": [frac_str(value) for value in first],
        "expected_squared_cooperators_by_round": [frac_str(value) for value in second],
        "cooperation_by_round": [frac_str(value / n_agents) for value in first],
        "absorption_by_round": [frac_str(p) for p in absorption],
        "absorption_probability_by_last_round": frac_str(absorption[-1]),
        "mean_cooperation": frac_str(sum(first, Fraction()) / (n_agents * rounds)),
        "variance_mean_cooperation": frac_str(variance), "variance_terms": variance_terms,
        "sampler_scope": "Ideal rational Bernoulli benchmark; the existing finite-precision "
                         "PRNG and binary-float policy sampling are unchanged.",
    }
    if window is not None:
        window_variance, window_terms = _mean_variance(first[-window:], second[-window:],
                                                      decay, n_agents)
        result.update({
            "final_window": window,
            "final_window_cooperation": frac_str(sum(first[-window:], Fraction())
                                                 / (n_agents * window)),
            "variance_final_window_cooperation": frac_str(window_variance),
            "final_window_variance_terms": window_terms,
            "final_window_all_d_probability": frac_str(absorption[rounds - window]),
        })
    return result


def _exact_fraction(value: str, name: str) -> Fraction:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an exact fraction string")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{name} must be an exact fraction string") from exc


def monte_carlo_standard_error(episode_variance_fraction: str, *,
                               replicates: int) -> dict[str, Any]:
    """Display-only SE from exact model episode variance / independent replicates.

    This is a model calculation, not an empirical variance estimate or a normal
    confidence interval. Zero variance in a sampled dataset is not an input to
    this benchmark and must not be interpreted as population certainty.
    """
    _integer_at_least(replicates, 1, "replicates")
    variance = _exact_fraction(episode_variance_fraction, "episode variance")
    if variance < 0:
        raise ValueError("episode variance must be nonnegative")
    variance_of_mean = variance / replicates
    with localcontext(Context(prec=DISPLAY_DIGITS + 12, rounding=ROUND_HALF_EVEN)):
        approximate = (Decimal(variance_of_mean.numerator)
                       / Decimal(variance_of_mean.denominator)).sqrt()
        display = format(approximate, f".{DISPLAY_DIGITS}g")
    return {
        "basis": "independent ideal-model episodes", "replicates": replicates,
        "variance_of_mean": frac_str(variance_of_mean),
        "standard_error_decimal_approximation": display,
        "approximation_significant_digits": DISPLAY_DIGITS,
    }


def independent_probability_power(base_fraction: str, *, power: int) -> dict[str, Any]:
    """Exact independent-event product as a compact expression plus decimal display.

    Do not expand the rational power: realistic 50-round probabilities raised
    to 32 episodes can exceed Python's integer-to-string digit limit. Keeping
    the base and exponent is exact and does not relax that process-wide limit.
    """
    _integer_at_least(power, 1, "power")
    probability = _exact_fraction(base_fraction, "base probability")
    if not 0 <= probability <= 1:
        raise ValueError("base probability must be in [0, 1]")
    with localcontext(Context(prec=DISPLAY_DIGITS + 12, rounding=ROUND_HALF_EVEN)):
        approximate = (Decimal(probability.numerator) / Decimal(probability.denominator)) ** power
        display = format(approximate, f".{DISPLAY_DIGITS}g")
    return {
        "base_fraction": frac_str(probability), "power": power,
        "decimal_approximation": display, "approximation_significant_digits": DISPLAY_DIGITS,
    }
