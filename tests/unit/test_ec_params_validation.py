"""ECParams non-negative validation: costs/budgets/benefits/penalties reject
negatives at construction, while credit_* fields still allow negatives."""

import pytest
from pydantic import ValidationError

from collaborative_hill.domain.world.evidence_commons import ECParams


def test_defaults_construct():
    params = ECParams()
    assert params.cost_propose == 1
    assert params.benefit_correct_slot == 12
    assert params.penalty_wrong_slot == 12


@pytest.mark.parametrize(
    "field,value",
    [
        ("rounds", -1),
        ("inspect_budget", -1),
        ("verify_budget", -5),
        ("cost_inspect", -1),
        ("cost_share", -1),
        ("cost_propose", -5),
        ("cost_verify", -1),
        ("cost_challenge", -5),
    ],
)
def test_negative_cost_rejected(field, value):
    with pytest.raises(ValidationError):
        ECParams(**{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("benefit_correct_slot", -1),
        ("penalty_wrong_slot", -5),
    ],
)
def test_negative_benefit_penalty_rejected(field, value):
    with pytest.raises(ValidationError):
        ECParams(**{field: value})


def test_negative_credits_still_allowed():
    params = ECParams(credit_propose_accepted_wrong=-3)
    assert params.credit_propose_accepted_wrong == -3
