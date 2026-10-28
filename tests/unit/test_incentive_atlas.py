"""Exact oracles for the unfrozen atlas; no production weights are selected."""

import importlib.util
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path

import pytest

ATLAS_PATH = Path(__file__).resolve().parents[2] / "experiments/incentive-atlas/atlas.py"
spec = importlib.util.spec_from_file_location("incentive_atlas", ATLAS_PATH)
assert spec is not None and spec.loader is not None
atlas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atlas)


def test_hand_derived_misinformation_coefficient():
    # Private FCC accepts two true slots and one false. False quality costs 12,
    # and a2 earns +3 for proposing, +2 for verifying truth, -2 for verifying false.
    summary = {
        "briefing": [{"correct": True}, {"correct": False}, {"correct": True}],
        "individual_credit": {"a2": "3"},
        "effort": {"a2": 14},
    }
    assert atlas.coefficients(summary)["a2"] == (F(2, 3), F(3), F(-18))


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    return atlas.collect(tmp_path_factory.mktemp("atlas-baseline"))


@pytest.fixture(scope="module")
def regions(baseline):
    return atlas.derive(baseline)


def test_hand_derived_payoffs_and_region_boundaries(baseline, regions):
    # CCC private: one true slot, proposer 3 and two verifier credits 2,
    # effort 13 each. Shared: two true slots, credits 6/4/4, effort 15 each.
    assert regions["cells"]["attributable/private"]["payoffs"]["CCC"] == {
        "a1": ["1/3", "3", "-13"], "a2": ["1/3", "2", "-13"],
        "a3": ["1/3", "2", "-13"],
    }
    assert regions["cells"]["attributable/shared_ledger"]["payoffs"]["CCC"] == {
        "a1": ["2/3", "6", "-15"], "a2": ["2/3", "4", "-15"],
        "a3": ["2/3", "4", "-15"],
    }
    # FCC private: two true and one false slot; the wrong slot is NOT b-scaled.
    assert regions["cells"]["attributable/private"]["payoffs"]["FCC"] == {
        "a1": ["2/3", "0", "-4"], "a2": ["2/3", "3", "-18"],
        "a3": ["2/3", "2", "-18"],
    }
    assert len(baseline) == 4
    for cell, data in regions["cells"].items():
        assert set(data["payoffs"]) == {"CCC", "CCF", "CFC", "CFF", "FCC", "FCF", "FFC", "FFF"}
        assert len(data["deviations"]) == 12
        private = cell.endswith("/private")
        assert data["c2_difference"] == (["1", "7", "-39"] if private else ["2", "14", "-45"])
        assert data["c1_uniform_witness"]["gain"] == (
            ["0", "0", "7"] if private else ["0", "0", "9"])


@pytest.mark.parametrize("b,r,private,shared", [
    (12, 1, False, False), (0, 0, False, False),
    ("31/2", 1, False, False), ("15501/1000", 1, False, True),
    (32, 1, False, True), ("32001/1000", 1, True, True),
    (0, "39/7", False, True), (0, "45/14", False, False),
    (40, 0, True, True), (12, 4, True, True), (0, 7, True, True),
])
def test_strict_half_planes_and_failure_witnesses(regions, b, r, private, shared):
    for cell, result in atlas.evaluate(regions, b, r)["cells"].items():
        expected = private if cell.endswith("/private") else shared
        assert result["c1"] is True
        assert result["c2"] is expected
        assert result["admissible"] is expected
        assert result["failed_conditions"] == ([] if expected else ["C2"])
        witness = result["failure_witnesses"]["C2"]
        if expected:
            assert witness is None
        else:
            assert sum(map(F, witness["CCC"].values())) <= sum(map(F, witness["FFF"].values()))


def test_weak_c1_is_not_ccc_temptation_or_pareto(regions):
    strong_credit = atlas.evaluate(regions, 0, 7)["cells"]
    for topology in ("private", "shared_ledger"):
        result = strong_credit[f"attributable/{topology}"]
        assert result["admissible"] is True
        assert all(F(d["value"]) < 0 for d in result["ccc_deviations"])
    result = atlas.evaluate(regions, 12, 4)["cells"]["attributable/private"]
    assert result["ccc_utilities"] == {"a1": "3", "a2": "-1", "a3": "-1"}
    boundary = atlas.evaluate(regions, 3, 4)["cells"]["attributable/shared_ledger"]
    assert [d["value"] for d in boundary["ccc_deviations"]] == ["-8", "0", "0"]


def test_c1_failure_requires_all_deviations_not_one_counterexample(regions):
    synthetic = deepcopy(regions)
    for data in synthetic["cells"].values():
        for deviation in data["deviations"]:
            deviation["gain"] = ["0", "0", "0"]
    for row in atlas.evaluate(synthetic, 40, 0)["cells"].values():
        assert row["c1"] is False
        assert row["c2"] is True
        assert row["admissible"] is False
        assert row["failed_conditions"] == ["C1"]
        assert len(row["failure_witnesses"]["C1"]) == 12


@pytest.mark.parametrize("b,r", atlas.PROBES)
def test_fresh_engine_matches_symbolic_payoffs_and_actions(tmp_path, baseline, regions, b, r):
    fresh = atlas.collect(tmp_path, b, r)
    atlas.verify_point(regions, baseline, fresh, b, r)
    run = tmp_path / "atlas-attr-priv-FCC"
    assert atlas.replay_run(run).chains_match


def test_rejects_payoff_or_behavior_drift(baseline, regions):
    changed = deepcopy(baseline)
    changed["attributable/private"]["FCC"]["summary"]["utility"]["a1"] = "999"
    with pytest.raises(ValueError, match="payoff mismatch"):
        atlas.verify_point(regions, baseline, changed, 12, 1)
    changed = deepcopy(baseline)
    changed["attributable/private"]["FCC"]["action_hash"] = "changed"
    with pytest.raises(ValueError, match="behavior changed"):
        atlas.verify_point(regions, baseline, changed, 12, 1)
    with pytest.raises(ValueError, match="C3 invariance"):
        atlas.derive(changed)


@pytest.mark.parametrize("b,r", [(-1, 1), (1, -1), (0.1, 1), (1, True)])
def test_rejects_out_of_domain_and_inexact_input(tmp_path, b, r):
    with pytest.raises(ValueError):
        atlas.collect(tmp_path, b, r)
    assert not list(tmp_path.iterdir())


def test_original_input_and_lock_bytes_unchanged_and_outputs_refuse_overwrite(tmp_path, baseline):
    before = atlas.study_snapshot()
    assert all(v["validation"]["frozen"] is False for v in before.values())
    assert before["000-legacy-reproduction"]["validation"]["study_hash"] == (
        "5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f")
    assert before["001-evidence-commons"]["validation"]["study_hash"] == (
        "a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe")
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("keep")
    with pytest.raises(FileExistsError):
        atlas.build(tmp_path)
    with pytest.raises(ValueError, match="outside the original studies"):
        atlas.build(atlas.REPO / "studies/001-evidence-commons/atlas-output")
    assert sentinel.read_text() == "keep"
    assert before == atlas.study_snapshot()
