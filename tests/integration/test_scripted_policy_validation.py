"""Bad scripted policy inputs fail before study or branch output is created."""

import json
import shutil

import pytest

from collaborative_hill.experiments.study import run_study

from ._helpers import STUDY_000, find_run_dirs, run_cli


@pytest.mark.parametrize("params,key", [
    ({"epslion": "1/10"}, "epslion"),
    ({"epsilon": "2"}, "epsilon"),
    ({"denominator": "included_self"}, "denominator"),
])
def test_invalid_later_condition_is_rejected_before_any_study_output(tmp_path, params, key):
    study = tmp_path / "study"
    shutil.copytree(STUDY_000, study)
    scenario_path = study / "scenarios/nb-2ptfte-allc-incself.json"
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    scenario["cognition"]["agents"][0]["policy"]["params"] = params
    scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    artifacts = tmp_path / "artifacts"

    result = run_cli("run", str(study), "--artifacts", str(artifacts), "--replicates", "1")

    assert result.returncode == 2, result.stdout + result.stderr
    assert key in result.stderr
    assert not artifacts.exists()


@pytest.fixture
def branch_parent(tmp_path):
    artifacts = tmp_path / "parent"
    run_study(STUDY_000, artifacts, only_condition="nb-2ptft-alld-incself",
              replicates_override=1)
    return find_run_dirs(artifacts)[0]


@pytest.mark.parametrize("override,key", [
    ("ptft:epsilon=2", "epsilon"),
    ("tft_threshold:threshold_num=3,threshold_den=2", "threshold"),
    ("ptft:denominator=included_self", "denominator"),
    ("allc:epsilon=1/10", "epsilon"),
])
def test_branch_uses_the_same_parameter_contract_without_creating_output(
    tmp_path, branch_parent, override, key,
):
    child = tmp_path / "child"
    result = run_cli("branch", str(branch_parent), "--at-event", "130",
                     "--override", f"a1={override}", "--out", str(child))

    assert result.returncode == 2, result.stdout + result.stderr
    assert key in result.stderr
    assert not child.exists()
