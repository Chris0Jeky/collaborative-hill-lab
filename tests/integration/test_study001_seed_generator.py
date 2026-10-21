"""The paired draft is explicit and cannot overwrite the original or a frozen study."""

import json
import subprocess
import sys

import pytest

from collaborative_hill.engine.replay import replay_run
from collaborative_hill.experiments.study import run_study, validate_study

from ._helpers import STUDY_001, find_run_dirs

pytestmark = pytest.mark.integration
GENERATOR = STUDY_001 / "generate_study.py"
PAIRED = "paired-policy-v2"


def _generate(*args):
    return subprocess.run([sys.executable, str(GENERATOR), *map(str, args)],
                          capture_output=True, text=True, check=False)


def test_default_generator_reproduces_original_json_exactly(tmp_path):
    output = tmp_path / "legacy"
    result = _generate("--output", output)
    assert result.returncode == 0, result.stderr
    assert "legacy-independent-v1" in result.stdout
    for original in [STUDY_001 / "study.json", *STUDY_001.glob("scenarios/*.json"),
                     *STUDY_001.glob("skins/*.json")]:
        generated = output / original.relative_to(STUDY_001)
        assert generated.read_bytes() == original.read_bytes()


def test_opt_in_generator_runs_replays_and_stays_unfrozen(tmp_path):
    output = tmp_path / "paired"
    result = _generate("--seed-protocol", PAIRED, "--output", output)
    assert result.returncode == 0, result.stderr
    data = json.loads(output.joinpath("study.json").read_text())
    assert data["study_id"] == "001-evidence-commons-paired-v2"
    assert data["seed_protocol"] == PAIRED
    assert {c["scenario_block"] for c in data["conditions"]} == {"factorial", "misinformation"}
    assert validate_study(output)["study_hash"] != validate_study(STUDY_001)["study_hash"]
    assert not output.joinpath("study.lock.json").exists()
    results = run_study(output, tmp_path / "artifacts", replicates_override=1)
    assert len(results) == 5 and all(result.status == "completed" for result in results)
    for run_dir in find_run_dirs(tmp_path / "artifacts"):
        assert replay_run(run_dir).chains_match
        manifest = json.loads(run_dir.joinpath("manifest.json").read_text())
        assert manifest["study_frozen"] is False


def test_paired_generator_cannot_replace_checked_in_study():
    before = STUDY_001.joinpath("study.json").read_bytes()
    for args in [(), ("--output", STUDY_001)]:
        result = _generate("--seed-protocol", PAIRED, *args)
        assert result.returncode == 2
        assert "new draft directory" in result.stderr
    assert STUDY_001.joinpath("study.json").read_bytes() == before


def test_paired_generator_refuses_occupied_output(tmp_path):
    marker = tmp_path / "existing.txt"
    marker.write_text("preserved")
    result = _generate("--seed-protocol", PAIRED, "--output", tmp_path)
    assert result.returncode == 2
    assert "empty or new output" in result.stderr
    assert list(tmp_path.iterdir()) == [marker]
    assert marker.read_text() == "preserved"


def test_default_generator_cannot_downgrade_an_existing_paired_draft(tmp_path):
    output = tmp_path / "paired"
    assert _generate("--seed-protocol", PAIRED, "--output", output).returncode == 0
    before = {path: path.read_bytes() for path in output.rglob("*.json")}
    result = _generate("--output", output)
    assert result.returncode == 2
    assert "change seed protocol" in result.stderr
    assert {path: path.read_bytes() for path in output.rglob("*.json")} == before


@pytest.mark.parametrize("protocol", ["legacy-independent-v1", PAIRED])
def test_generator_refuses_frozen_output_before_writing(tmp_path, protocol):
    lock = tmp_path / "study.lock.json"
    lock.write_text("preserved frozen fixture")
    result = _generate("--seed-protocol", protocol, "--output", tmp_path)
    assert result.returncode == 2
    assert "frozen study" in result.stderr
    assert list(tmp_path.iterdir()) == [lock]
    assert lock.read_text() == "preserved frozen fixture"


def test_pairing_cannot_be_retrofitted_to_frozen_legacy_hash(tmp_path):
    output = tmp_path / "study"
    assert _generate("--output", output).returncode == 0
    old_hash = validate_study(output)["study_hash"]
    output.joinpath("study.lock.json").write_text(json.dumps({"study_hash": old_hash}))
    path = output / "study.json"
    data = json.loads(path.read_text())
    data["seed_protocol"] = PAIRED
    for condition in data["conditions"]:
        condition["scenario_block"] = "new-draft-block"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="changed after freeze"):
        run_study(output, tmp_path / "artifacts")
    assert not (tmp_path / "artifacts").exists()
