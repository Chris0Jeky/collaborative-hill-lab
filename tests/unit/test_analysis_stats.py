"""Hand-computed factorial and multiplicity oracles; no simulation claims."""

from fractions import Fraction as F
from unittest.mock import Mock, call

import pytest

from collaborative_hill.reporting.analysis import _attrition, _blocks
from collaborative_hill.reporting.analysis_stats import (
    CELLS,
    _t_critical,
    bootstrap_means,
    contrasts,
    describe,
    holm,
    interval,
    paired_t_interval,
    percentile,
)


@pytest.mark.parametrize(("raw", "expected"), [
    ([".01", ".04", ".03"], [".03", ".06", ".06"]),
    ([".04", ".01", ".03"], [".06", ".03", ".06"]),
    ([".5", ".5", "1"], ["1", "1", "1"]),
    (["0", "0", "1"], ["0", "0", "1"]),
    ([], []),
])
def test_holm_oracles(raw, expected):
    assert holm(list(map(F, raw))) == list(map(F, expected))


def test_holm_rejects_invalid_probability():
    with pytest.raises(ValueError, match="p-values"):
        holm([F(-1)])


def test_percentile_interpolates_exactly():
    assert percentile([F(0), F(10)], F(1, 40)) == F(1, 4)
    assert percentile([F(0), F(10)], F(39, 40)) == F(39, 4)


def test_bootstrap_seed_and_intervals():
    values = list(map(F, [0, 1, 3, 8, 15]))
    first = bootstrap_means(values, seed=42, samples=79, scope="test")
    assert first == bootstrap_means(values, seed=42, samples=79, scope="test")
    other = bootstrap_means(values, seed=43, samples=79, scope="test")
    assert interval(first) != interval(other)
    assert first != bootstrap_means(values, seed=42, samples=79, scope="other")


def test_bootstrap_draws_exactly_n_indices_per_replicate(monkeypatch):
    # Independent index/mean oracle: three replicates of three episodes or blocks.
    # Drawing 2n, even from duplicated values, must fail rather than narrow the CI.
    rng = Mock()
    rng.randrange.side_effect = [0, 0, 2, 1, 2, 2, 0, 1, 1]
    factory = Mock(return_value=rng)
    monkeypatch.setattr("collaborative_hill.reporting.analysis_stats.rng_for", factory)
    draws = bootstrap_means(list(map(F, [0, 6, 12])), seed=42, samples=3, scope="oracle")
    factory.assert_called_once_with(42, "chl.analyze.v1", "oracle")
    assert rng.randrange.call_args_list == [call(3)] * 9
    assert draws == list(map(F, [4, 10, 4]))


def test_equal_cell_weighting_and_contrast_signs():
    cells = dict(zip(CELLS, [list(map(F, v)) for v in (
        [0, 2], [2, 4, 6], [4, 6, 8, 10], [10, 12],
    )], strict=True))
    # Cell means 1,4,7,11. E1=(7+11-1-4)/2; E2=(4+11-1-7)/2.
    results = contrasts(cells, seed=42, samples=79)
    assert [results[k]["estimate"] for k in ("E1", "E2", "E3")] == ["13/2", "7/2", "1"]
    p = [F(results[k]["p_unadjusted"]) for k in ("E1", "E2", "E3")]
    assert [F(results[k]["p_holm"]) for k in ("E1", "E2", "E3")] == holm(p)


def test_centered_bootstrap_tail_and_holm_have_independent_literal_oracles(monkeypatch):
    # Each cell has nonzero episode variance. Predetermined valid cell-mean
    # resamples give E1 draws [1,1,1,1], E2 [1,3,-1,1], E3 [2,2,2,2].
    # Their centered tail counts are 0,2,0, so the +1 correction gives
    # 1/5,3/5,1/5. Holm across all three gives 3/5 for every contrast.
    draws = dict(zip(CELLS, [list(map(F, values)) for values in (
        [0, 0, 2, 2], [0, 2, 0, 2], [0, 0, 2, 2], [2, 4, 2, 4],
    )], strict=True))
    monkeypatch.setattr("collaborative_hill.reporting.analysis_stats.bootstrap_means",
                        lambda values, **kwargs: draws[kwargs["scope"]])
    cells = {c: list(map(F, [2, 4] if c == "attr-ledger" else [0, 2])) for c in CELLS}
    result = contrasts(cells, seed=42, samples=4)
    assert [result[c]["estimate"] for c in ("E1", "E2", "E3")] == ["1", "1", "2"]
    assert [result[c]["p_unadjusted"] for c in ("E1", "E2", "E3")] == ["1/5", "3/5", "1/5"]
    assert [result[c]["p_holm"] for c in ("E1", "E2", "E3")] == ["3/5", "3/5", "3/5"]


def test_degenerate_cells_never_have_intervals_or_p_values():
    cells = {c: [F(i)] * 20 for i, c in enumerate(CELLS)}
    result = contrasts(cells, seed=42, samples=79)
    assert result["E1"]["estimate"] == "2"
    for effect in result.values():
        assert effect["ci95"] is None
        assert effect["p_unadjusted"] is None
        assert effect["p_holm"] is None
        assert effect["inference_unavailable"] == "zero_between_episode_variance"
    summary = describe([F(1)] * 20, seed=42, samples=79, scope="cell")
    assert summary["n"] == 20
    assert summary["n_effective"] == 1
    assert summary["ci95"] is None


def test_missing_cell_has_no_estimate():
    result = contrasts({c: [] for c in CELLS}, seed=42, samples=79)
    assert all(r["estimate"] is None and r["ci95"] is None for r in result.values())


def test_paired_bootstrap_uses_entire_blocks():
    blocks = [dict(zip(CELLS, map(F, values), strict=True)) for values in (
        [0, 2, 4, 8], [10, 14, 16, 22], [30, 32, 39, 45],
    )]
    cells = {c: [b[c] for b in blocks] for c in CELLS}
    results = contrasts(cells, blocks=blocks, seed=42, samples=79)
    # E1 block differences: 5,7,11, each carrying all four episodes.
    assert results["E1"]["paired_differences"] == ["5", "7", "11"]
    assert results["E1"]["estimate"] == "23/3"
    expected = bootstrap_means(list(map(F, [5, 7, 11])), seed=42, samples=79, scope="blocks")
    assert results["E1"]["ci95"] == interval(expected)
    assert results["E1"]["t_ci95_check"] is not None


def test_constant_block_contrasts_do_not_manufacture_precision():
    blocks = [dict(zip(CELLS, map(F, values), strict=True))
              for values in ([0, 2, 4, 8], [10, 12, 14, 18])]
    result = contrasts({c: [b[c] for b in blocks] for c in CELLS},
                       blocks=blocks, seed=42, samples=79)
    assert result["E1"]["estimate"] == "5"
    assert result["E1"]["ci95"] is None
    assert result["E1"]["t_ci95_check"] is None


@pytest.mark.parametrize(("df", "critical"), [(1, 12.7062047364), (2, 4.30265272975),
                                             (10, 2.22813885196), (100, 1.98397151845)])
def test_student_t_quantile_reference_values(df, critical):
    assert _t_critical(df) == pytest.approx(critical, rel=1e-9)


def test_paired_t_interval_oracle():
    # Mean 2, SE=1/sqrt(3), t(.975,2)=4.30265272975.
    lower, upper = paired_t_interval(list(map(F, [1, 2, 3])))
    assert float(lower) == pytest.approx(-.48413771172)
    assert float(upper) == pytest.approx(4.48413771172)


def test_attrition_counts_and_chi_square_oracle():
    # Each cell has 9 completed + 1 failed: no differential attrition, X^2=0, p=1.
    rows = [{"condition_id": c} for c in CELLS for _ in range(9)]
    exclusions = [{"condition_id": c, "reason": "run_failed"} for c in CELLS]
    result = _attrition(rows, exclusions)
    assert all(c["inclusion_rate"] == "9/10" for c in result["per_cell"].values())
    assert result["differential_attrition"]["statistic"] == "0"
    assert result["differential_attrition"]["p_value"] == "1"
    assert result["differential_attrition"]["small_expected_counts"] is True


@pytest.mark.parametrize(("providers", "policy", "reason"), [
    ({"a1": "fake/model"}, "ec_freerider@1", "provider_randomness_not_verified_for_pairing"),
    ({}, "unverified-random-policy", "policy_randomness_coupling_not_verified"),
])
def test_pairing_requires_verified_randomness(providers, policy, reason):
    blocks, unavailable = _blocks([{"seed_protocol": "paired-policy-v2", "providers": providers,
                                   "policies": {"a1": policy}}])
    assert blocks is None
    assert unavailable == reason
