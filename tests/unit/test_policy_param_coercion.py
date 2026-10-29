"""Coercion of scripted policy params from stringly sources (CLI, study JSON)."""

import random

import pytest
from pydantic import ValidationError

from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import DefectAction
from collaborative_hill.experiments.scenario import PolicySpec


def test_epsilon_fraction_string():
    assert coerce_policy_params("tft_pairwise", {"epsilon": "1/10"}) == {"epsilon": 0.1}


def test_threshold_strings_become_ints():
    coerced = coerce_policy_params(
        "tft_threshold", {"threshold_num": "3", "threshold_den": "4"}
    )
    assert coerced == {"threshold_num": 3, "threshold_den": 4}
    assert type(coerced["threshold_num"]) is int
    assert type(coerced["threshold_den"]) is int


def test_share_evidence_false_string():
    assert coerce_policy_params("ec_contributor", {"share_evidence": "False"}) == {
        "share_evidence": False
    }


def test_share_evidence_true_string_case_insensitive():
    assert coerce_policy_params("ec_contributor", {"share_evidence": "true"}) == {
        "share_evidence": True
    }


def test_share_evidence_real_bool_passes_through():
    assert coerce_policy_params("ec_contributor", {"share_evidence": True}) == {
        "share_evidence": True
    }


@pytest.mark.parametrize("bad", ["maybe", "yes", "0", "", 1])
def test_share_evidence_bad_value_raises(bad):
    with pytest.raises(ValueError):
        coerce_policy_params("ec_contributor", {"share_evidence": bad})


def test_threshold_den_zero_raises():
    with pytest.raises(ValueError):
        coerce_policy_params("tft_threshold", {"threshold_den": "0"})


def test_threshold_num_non_integer_raises():
    with pytest.raises(ValueError):
        coerce_policy_params("tft_threshold", {"threshold_num": "x"})


def test_supported_denominator_passes_through():
    assert coerce_policy_params("ptft", {"denominator": "include_self"}) == {
        "denominator": "include_self"
    }


def test_ec_contributor_coerced_share_false():
    policy = build_ec_policy(
        "ec_contributor",
        coerce_policy_params("ec_contributor", {"share_evidence": "False"}),
    )
    assert policy.share_evidence is False


def test_threshold_policy_coerced_ints_and_defects_below_quorum():
    coerced = coerce_policy_params(
        "tft_threshold", {"threshold_num": "3", "threshold_den": "4"}
    )
    policy = build_nipd_policy("tft_threshold", "neighbourhood", coerced)
    assert type(policy.threshold_num) is int
    assert type(policy.threshold_den) is int
    observation = {
        "others_cooperated_last_round": 1,
        "n_agents": 4,
        "my_last_move": "C",
    }
    proposal = policy.propose(observation, random.Random(0))
    # 1*4 >= 3*3 is False -> below quorum -> Defect
    assert isinstance(proposal.action, DefectAction)


@pytest.mark.parametrize("name,params", [
    ("allc", {"epsilon": "1/10"}),
    ("alld", {"epsilon": "1/10"}),
    ("random", {"epsilon": "1/10"}),
    ("tft_pairwise", {"epslion": "1/10"}),
    ("tft_linked", {"threshold_num": 1}),
    ("ptft", {"share_evidence": True}),
    ("tft_threshold", {"denominator": "exclude_self"}),
    ("ec_contributor", {"share_evidnce": False}),
    ("ec_freerider", {"share_evidence": False}),
    ("ec_verifier", {"epsilon": 0}),
    ("ec_misinformer", {"share_evidence": True}),
])
def test_builtin_policies_reject_unsupported_keys(name, params):
    key = next(iter(params))
    with pytest.raises(ValueError, match=key):
        coerce_policy_params(name, params)
    with pytest.raises(ValidationError, match=key):
        PolicySpec(name=name, params=params)


@pytest.mark.parametrize("bad", [
    -1, "-1/10", 2, "11/10", "100000000000000000001/100000000000000000000",
])
def test_epsilon_must_be_an_exact_probability(bad):
    with pytest.raises(ValueError, match="epsilon"):
        coerce_policy_params("tft_pairwise", {"epsilon": bad})
    with pytest.raises(ValidationError, match="epsilon"):
        PolicySpec(name="tft_pairwise", params={"epsilon": bad})


@pytest.mark.parametrize("value,expected", [(0, 0.0), (1, 1.0), ("0/3", 0.0),
                                           ("1/1", 1.0), ("1/10", 0.1)])
def test_epsilon_boundaries_and_rationals_keep_exact_spec_values(value, expected):
    params = {"epsilon": value}
    assert coerce_policy_params("tft_pairwise", params) == {"epsilon": expected}
    assert PolicySpec(name="tft_pairwise", params=params).model_dump(mode="json") == {
        "name": "tft_pairwise", "params": params,
    }


@pytest.mark.parametrize("params", [
    {"threshold_num": -1}, {"threshold_num": "3"},
    {"threshold_num": 3, "threshold_den": "2"},
    {"threshold_num": "-1", "threshold_den": "-2"},
    {"threshold_den": 0}, {"threshold_num": True}, {"threshold_den": False},
    {"threshold_num": "1.5"},
])
def test_threshold_requires_integer_ratio_between_zero_and_one(params):
    with pytest.raises(ValueError, match="threshold"):
        coerce_policy_params("tft_threshold", params)
    with pytest.raises(ValidationError, match="threshold"):
        PolicySpec(name="tft_threshold", params=params)


@pytest.mark.parametrize("params,expected", [
    ({}, {}),
    ({"threshold_num": "0"}, {"threshold_num": 0}),
    ({"threshold_num": "2"}, {"threshold_num": 2}),
    ({"threshold_den": "1"}, {"threshold_den": 1}),
    ({"threshold_num": "3", "threshold_den": "3"},
     {"threshold_num": 3, "threshold_den": 3}),
])
def test_threshold_boundaries_use_builder_defaults_without_rewriting_specs(params, expected):
    assert coerce_policy_params("tft_threshold", params) == expected
    assert PolicySpec(name="tft_threshold", params=params).params == params


@pytest.mark.parametrize("bad", ["included_self", "", 1, True])
def test_ptft_rejects_unsupported_denominator(bad):
    with pytest.raises(ValueError, match="denominator"):
        coerce_policy_params("ptft", {"denominator": bad})
    with pytest.raises(ValidationError, match="denominator"):
        PolicySpec(name="ptft", params={"denominator": bad})


def test_non_scripted_policy_params_remain_extension_points():
    params = {"epsilon": "provider-defined", "custom": 7}
    assert coerce_policy_params("external-policy", params) == params
    assert PolicySpec(name="external-policy", params=params).params == params
    fake = {"script": "[]", "max_retries": 0}
    assert PolicySpec(name="llm_fake", params=fake).params == fake
