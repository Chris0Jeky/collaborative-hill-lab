"""Coercion of scripted policy params from stringly sources (CLI, study JSON)."""

import random

import pytest

from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.domain.actions import DefectAction


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


def test_unknown_keys_pass_through():
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
