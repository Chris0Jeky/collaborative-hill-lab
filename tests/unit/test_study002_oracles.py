"""Study 002 predictions are independent arithmetic, never simulated expectations."""

import importlib.util
from fractions import Fraction
from pathlib import Path

import pytest

MODEL_PATH = (Path(__file__).resolve().parents[2]
              / "studies/002-nipd-sensitivity/study002_model.py")


def model():
    assert MODEL_PATH.exists(), "Study 002 analytical model is not implemented"
    spec = importlib.util.spec_from_file_location("study002_model", MODEL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("cid,first,later,scores", [
    ("nb-n3-m2-q1-2", "2/3", "2/3", {"a1": "75", "a2": "75", "a3": "250"}),
    ("nb-n3-m2-q51-100", "2/3", "0", {"a1": "101/2", "a2": "101/2", "a3": "54"}),
    ("nb-n5-m4-q3-4", "4/5", "4/5",
     {"a1": "225/2", "a2": "225/2", "a3": "225/2", "a4": "225/2", "a5": "250"}),
    ("nb-n5-m4-q76-100", "4/5", "0",
     {"a1": "205/4", "a2": "205/4", "a3": "205/4", "a4": "205/4", "a5": "54"}),
    ("nb-n5-m3-q1-2", "3/5", "3/5",
     {"a1": "75", "a2": "75", "a3": "75", "a4": "200", "a5": "200"}),
    ("nb-n5-m3-q51-100", "3/5", "0",
     {"a1": "101/2", "a2": "101/2", "a3": "101/2", "a4": "53", "a5": "53"}),
    ("pw-n5-m4-tft", "4/5", "3/5",
     {"a1": "499", "a2": "499", "a3": "499", "a4": "499", "a5": "216"}),
    ("pw-n5-m4-linked", "4/5", "0",
     {"a1": "205", "a2": "205", "a3": "205", "a4": "205", "a5": "216"}),
])
def test_hand_derived_threshold_and_pairwise_paths(cid, first, later, scores):
    module = model()
    condition = next(c for c in module.conditions() if c.condition_id == cid)
    prediction = module.predict(condition)
    # Inclusive quorum mistakes, first-round omissions, and summed/averaged
    # payoff confusion all change these hand-derived literals.
    assert prediction["cooperation_by_round"] == [first] + [later] * 49
    assert prediction["scores"] == scores


@pytest.mark.parametrize("cid,decay,curve,average,final", [
    ("nb-n3-m2-ptft-include", "2/3", ["2/3", "4/9", "8/27"], "38/81", "10/27"),
    ("nb-n3-m2-ptft-exclude", "1/2", ["2/3", "1/3", "1/6"], "7/18", "1/4"),
    ("nb-n5-m4-ptft-include", "4/5", ["4/5", "16/25", "64/125"], "244/375", "72/125"),
    ("nb-n5-m4-ptft-exclude", "3/4", ["4/5", "3/5", "9/20"], "37/60", "21/40"),
    ("nb-n5-m3-ptft-include", "3/5", ["3/5", "9/25", "27/125"], "49/125", "36/125"),
    ("nb-n5-m3-ptft-exclude", "1/2", ["3/5", "3/10", "3/20"], "7/20", "9/40"),
])
def test_hand_derived_ptft_expectation_includes_initial_round(cid, decay, curve, average, final):
    module = model()
    condition = next(c for c in module.conditions() if c.condition_id == cid)
    prediction = module.predict(condition, rounds=3, window=2)
    assert prediction["decay_factor"] == decay
    assert prediction["cooperation_by_round"] == curve
    assert prediction["mean_cooperation"] == average
    assert prediction["final_window_cooperation"] == final
    assert prediction["scores"] is None  # Never pretend an expectation is a realized payoff.


def test_absorbing_controls_and_declared_repeat_counts():
    module = model()
    deterministic = [c for c in module.conditions() if c.deterministic]
    stochastic = [c for c in module.conditions() if not c.deterministic]
    assert len(deterministic) == 29
    assert len(stochastic) == 6
    for c in deterministic:
        if c.reciprocators == c.n_agents:
            prediction = module.predict(c)
            assert prediction["cooperation_by_round"] == ["1"] * 50
            assert set(prediction["scores"].values()) == {"150"}
        elif c.reciprocators == 0:
            prediction = module.predict(c)
            assert prediction["cooperation_by_round"] == ["0"] * 50
            assert set(prediction["scores"].values()) == {"50"}
    specs = module.study_specs()
    assert specs["deterministic"].replicates == 1
    assert specs["stochastic"].replicates == 32


def test_expected_decay_is_strictly_ordered_but_positive_at_finite_horizon():
    module = model()
    predictions = {c.condition_id: module.predict(c)
                   for c in module.conditions() if not c.deterministic}
    for n, m in [(3, 2), (5, 4), (5, 3)]:
        include = predictions[f"nb-n{n}-m{m}-ptft-include"]
        exclude = predictions[f"nb-n{n}-m{m}-ptft-exclude"]
        assert (Fraction(include["final_window_cooperation"])
                > Fraction(exclude["final_window_cooperation"]) > 0)


@pytest.mark.parametrize("rounds,window", [(0, 1), (3, 0), (3, 4)])
def test_prediction_refuses_invalid_observation_window(rounds, window):
    module = model()
    with pytest.raises(ValueError, match="window"):
        module.predict(module.conditions()[0], rounds=rounds, window=window)
