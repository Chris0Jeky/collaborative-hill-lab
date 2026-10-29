"""Canonical Study 002 generation, repeat-count design, and immutability guards."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from collaborative_hill.engine.hashing import canonical_json
from collaborative_hill.experiments.study import load_study, validate_study

STUDY = Path(__file__).resolve().parents[2] / "studies/002-nipd-sensitivity"
pytestmark = pytest.mark.integration


def generate(*args):
    script = STUDY / "generate_study.py"
    assert script.exists(), "Study 002 canonical generator is not implemented"
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          capture_output=True, text=True, check=False)


def json_snapshot(directory):
    return {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*.json")}


def test_generator_is_canonical_and_repeat_counts_are_in_separate_studies(tmp_path):
    output = tmp_path / "draft"
    result = generate("--output", output)
    assert result.returncode == 0, result.stderr
    assert json_snapshot(output) == {
        path: data for path, data in json_snapshot(STUDY).items()
        if path.parts[0] in {"scenarios", "skins", "stochastic", "study.json"}
    }
    specs = []
    for path, count, replicates in [(output, 29, 1), (output / "stochastic", 6, 32)]:
        spec, resolved = load_study(path)
        specs.append(spec)
        assert len(resolved) == count
        assert spec.replicates == replicates
        assert spec.seed_protocol == "legacy-independent-v1"
        assert not validate_study(path)["frozen"]
        canonical_json(spec.model_dump(mode="json"))  # Rejects any hashed float.
        for scenario in resolved.values():
            canonical_json(scenario.model_dump(mode="json"))
    assert specs[0].study_id != specs[1].study_id
    before = json_snapshot(output)
    assert generate("--output", output).returncode == 0
    assert generate("--check", "--output", output).returncode == 0
    assert json_snapshot(output) == before


@pytest.mark.parametrize("component", ["", "stochastic"])
def test_generator_refuses_frozen_component_before_any_write(tmp_path, component):
    directory = tmp_path / component
    directory.mkdir(exist_ok=True)
    lock = directory / "study.lock.json"
    lock.write_text("human-owned frozen fixture", encoding="utf-8")
    before = json_snapshot(tmp_path)
    result = generate("--output", tmp_path)
    assert result.returncode == 2
    assert "frozen" in result.stderr
    assert json_snapshot(tmp_path) == before


def test_generator_check_and_write_both_refuse_drift_without_overwrite(tmp_path):
    output = tmp_path / "draft"
    assert generate("--output", output).returncode == 0
    path = output / "scenarios/nb-n3-m2-q1-2.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["world"]["rounds"] = 51
    path.write_text(json.dumps(data), encoding="utf-8")
    before = json_snapshot(output)
    for mode in [(), ("--check",)]:
        result = generate(*mode, "--output", output)
        assert result.returncode == 2
        assert "differs" in result.stderr
        assert json_snapshot(output) == before


def test_generator_does_not_overwrite_another_study(tmp_path):
    study = tmp_path / "study.json"
    study.write_text('{"study_id":"a-different-human-owned-study"}', encoding="utf-8")
    before = json_snapshot(tmp_path)
    result = generate("--output", tmp_path)
    assert result.returncode == 2
    assert json_snapshot(tmp_path) == before
    assert not (tmp_path / "scenarios").exists()
