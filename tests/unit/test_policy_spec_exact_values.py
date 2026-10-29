"""Serialized policy values must not be silently normalized before hashing."""

import pytest
from pydantic import ValidationError

from collaborative_hill.experiments.scenario import PolicySpec


@pytest.mark.parametrize("name,params", [
    ("tft_threshold", {"threshold_num": 1.0, "threshold_den": 2}),
    ("ptft", {"epsilon": 0.0}),
    ("ec_conditional_contributor", {"warmup_rounds": 5.0}),
    ("extension-policy", {"value": 1.0}),
    ("extension-policy", {"value": b"1"}),
])
def test_float_and_bytes_are_not_normalized_to_valid_spec_primitives(name, params):
    with pytest.raises(ValidationError):
        PolicySpec.model_validate({"name": name, "params": params})


def test_valid_exact_values_keep_their_types_and_strings():
    params = {"integer": 1, "rational": "2/4", "decimal": "0.50", "boolean": True}
    spec = PolicySpec(name="extension-policy", params=params)
    assert spec.model_dump()["params"] == params
    assert type(spec.params["integer"]) is int
    assert type(spec.params["boolean"]) is bool
