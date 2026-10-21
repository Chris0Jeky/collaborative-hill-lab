"""The seed audit exposes scheduled kernel streams without running a study."""

import json
import random
import shutil

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.cli import app
from collaborative_hill.experiments import study

from ._helpers import STUDY_000, STUDY_001

pytestmark = pytest.mark.integration
RUNNER = CliRunner()
CELLS = {"agg-priv", "agg-ledger", "attr-priv", "attr-ledger"}


def _copy_study(tmp_path, *, paired=False, source=STUDY_001):
    directory = tmp_path / "study"
    shutil.copytree(source, directory, ignore=shutil.ignore_patterns("__pycache__"))
    if paired:
        path = directory / "study.json"
        data = json.loads(path.read_text())
        data["seed_protocol"] = "paired-policy-v2"
        for condition in data["conditions"]:
            condition["scenario_block"] = (
                "factorial" if condition["condition_id"] in CELLS else "misinformation"
            )
        path.write_text(json.dumps(data))
    return directory


def _snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def _invoke(directory, *options):
    return RUNNER.invoke(app, ["study", "audit-seeds", str(directory), *options])


def _audit(directory, *options):
    result = _invoke(directory, *options)
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)


def test_paired_audit_shares_only_declared_policy_streams_and_is_read_only(tmp_path, monkeypatch):
    directory = _copy_study(tmp_path, paired=True)
    monkeypatch.chdir(tmp_path)
    before = _snapshot(tmp_path)
    result = _invoke(directory, "--replicate", "1", "--round", "2")
    assert result.exit_code == 0, result.output
    assert _invoke(directory, "--replicate", "1", "--round", "2").stdout == result.stdout
    assert _snapshot(tmp_path) == before
    audit = json.loads(result.stdout)
    assert audit["schema_version"] == 1
    assert audit["study_hash"] == study.validate_study(directory)["study_hash"]
    assert audit["seed_protocol"] == "paired-policy-v2"
    assert audit["replicate"] == 1
    assert audit["round"] == 2
    assert audit["frozen"] is False
    conditions = audit["conditions"]
    assert set(conditions) == CELLS | {"attr-priv-misinfo"}
    shared = conditions["agg-priv"]["agents"]
    for condition in CELLS:
        entry = conditions[condition]
        assert entry["scenario_block"] == "factorial"
        assert entry["round_count"] == 12
        assert entry["agents"] == shared
    assert shared["a1"]["policy_id"] == "ec_contributor[share=True]@1"
    assert len({agent["kernel_stream"]["derived_seed"] for agent in shared.values()}) == 3
    assert conditions["attr-priv-misinfo"]["scenario_block"] == "misinformation"
    assert (conditions["attr-priv-misinfo"]["agents"]["a1"]["kernel_stream"]
            != shared["a1"]["kernel_stream"])
    mechanism_seeds = {entry["mechanism_stream"]["derived_seed"]
                       for entry in conditions.values()}
    assert len(mechanism_seeds) == 5
    assert mechanism_seeds.isdisjoint(
        agent["kernel_stream"]["derived_seed"] for agent in shared.values()
    )
    for options in [("--replicate", "0", "--round", "2"),
                    ("--replicate", "1", "--round", "3")]:
        changed = _audit(directory, *options)
        assert changed["conditions"]["agg-priv"]["agents"] != shared


def test_legacy_audit_matches_independently_recorded_runner_draws(tmp_path):
    directory = _copy_study(tmp_path)
    audit = _audit(directory)
    assert audit["seed_protocol"] == "legacy-independent-v1"
    # Observed from the actual legacy run_study pipeline before the CRN fix.
    expected = {
        "agg-priv": 14442509083846134711,
        "agg-ledger": 15968561580677346032,
        "attr-priv": 17485811729684596417,
        "attr-ledger": 2761447364641609127,
        "attr-priv-misinfo": 6346500906894703209,
    }
    for condition, entry in audit["conditions"].items():
        assert entry["scenario_block"] is None
        stream = entry["agents"]["a1"]["kernel_stream"]
        assert stream["seed_path"] == [20260713, condition, 0, "agent", "a1", "round", 0]
        assert random.Random(int(stream["derived_seed"])).getrandbits(64) == expected[condition]


def test_llm_audit_identifies_unused_kernel_stream_without_calling_provider(tmp_path, monkeypatch):
    directory = _copy_study(tmp_path)
    scenario_path = directory / "scenarios/agg-priv.json"
    scenario = json.loads(scenario_path.read_text())
    scenario["cognition"]["agents"][0]["policy"] = {"name": "llm_fake", "params": {}}
    scenario_path.write_text(json.dumps(scenario))
    before = _snapshot(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("a seed audit must not run, freeze, propose, or call a provider")

    for name in ("run_study", "run_episode", "freeze_study"):
        monkeypatch.setattr(study, name, forbidden)
    monkeypatch.setattr(LLMPolicy, "propose", forbidden)
    monkeypatch.setattr(FakeProvider, "complete", forbidden)
    audit = _audit(directory)
    agent = audit["conditions"]["agg-priv"]["agents"]["a1"]
    assert agent["policy_id"].startswith("llm[fake-provider/fake-model-1,")
    assert agent["kernel_rng_usage"] == "unused_by_current_llm_adapter"
    assert audit["scope"] == "kernel_seed_allocation"
    assert "provider randomness is not paired" in " ".join(audit["notes"])
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(("option", "value", "message"), [
    ("--replicate", "-1", "replicate"),
    ("--replicate", "3", "replicate"),
    ("--round", "-1", "round"),
    ("--round", "12", "round"),
])
def test_invalid_requests_exit_two_without_output_or_mutation(tmp_path, option, value, message):
    directory = _copy_study(tmp_path)
    before = _snapshot(tmp_path)
    result = _invoke(directory, option, value)
    assert result.exit_code == 2
    assert message in result.stderr
    assert not result.stdout
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(("source", "rounds"), [(STUDY_000, 3), (STUDY_001, 3)])
def test_round_limit_uses_each_conditions_actual_mechanism_schedule(tmp_path, source, rounds):
    directory = _copy_study(tmp_path, source=source)
    data = json.loads((directory / "study.json").read_text())
    condition = data["conditions"][0]
    path = directory / condition["scenario"]
    scenario = json.loads(path.read_text())
    world = scenario["world"]
    schedule = world if world["kind"] == "nipd" else world["params"]
    schedule["rounds"] = rounds
    path.write_text(json.dumps(scenario))
    before = _snapshot(tmp_path)
    assert _audit(directory, "--round", str(rounds - 1))["round"] == rounds - 1
    result = _invoke(directory, "--round", str(rounds))
    assert result.exit_code == 2
    assert condition["condition_id"] in result.stderr
    assert "0..2" in result.stderr
    assert not result.stdout
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(("source", "rounds"), [
    (STUDY_000, 0), (STUDY_000, -1), (STUDY_001, 0),
])
def test_initially_terminal_conditions_have_no_streams_to_audit(tmp_path, source, rounds):
    directory = _copy_study(tmp_path, source=source)
    data = json.loads((directory / "study.json").read_text())
    path = directory / data["conditions"][0]["scenario"]
    scenario = json.loads(path.read_text())
    world = scenario["world"]
    schedule = world if world["kind"] == "nipd" else world["params"]
    schedule["rounds"] = rounds
    path.write_text(json.dumps(scenario))
    before = _snapshot(tmp_path)
    result = _invoke(directory)
    assert result.exit_code == 2
    assert "no scheduled rounds" in result.stderr
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("drift", [False, True])
def test_frozen_audit_checks_current_hash_without_changing_lock(tmp_path, drift):
    directory = _copy_study(tmp_path)
    locked_hash = study.validate_study(directory)["study_hash"]
    (directory / "study.lock.json").write_text(json.dumps({"study_hash": locked_hash}))
    if drift:
        path = directory / "study.json"
        data = json.loads(path.read_text())
        data["seed"] += 1
        path.write_text(json.dumps(data))
    before = _snapshot(tmp_path)
    result = _invoke(directory)
    if drift:
        assert result.exit_code == 2
        assert "changed after freeze" in result.stderr
        assert not result.stdout
    else:
        assert result.exit_code == 0, result.output
        audit = json.loads(result.stdout)
        assert audit["frozen"] is True
        assert audit["study_hash"] == locked_hash
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("lock", [
    pytest.param({"study_hash": 123}, id="integer-hash"),
    pytest.param({"study_hash": 1.5}, id="float-hash"),
    pytest.param({"study_hash": []}, id="array-hash"),
    pytest.param({"study_hash": {}}, id="object-hash"),
    pytest.param({"study_hash": None}, id="null-hash"),
    pytest.param({"study_hash": True}, id="true-hash"),
    pytest.param({"study_hash": False}, id="false-hash"),
    pytest.param({"study_hash": ""}, id="empty-hash"),
    pytest.param({"study_hash": "0" * 63}, id="short-hash"),
    pytest.param({"study_hash": "0" * 65}, id="long-hash"),
    pytest.param({"study_hash": "g" * 64}, id="nonhex-hash"),
    pytest.param({"study_hash": "A" * 64}, id="uppercase-hash"),
    pytest.param({"study_hash": "0" * 64 + "\n"}, id="trailing-newline-hash"),
    pytest.param({}, id="missing-hash"),
    pytest.param([], id="array-lock"),
    pytest.param(None, id="null-lock"),
    pytest.param(123, id="integer-lock"),
    pytest.param(True, id="boolean-lock"),
    pytest.param("0" * 64, id="string-lock"),
])
def test_invalid_lock_schema_exits_two_without_json_or_mutation(tmp_path, lock):
    directory = _copy_study(tmp_path)
    (directory / "study.lock.json").write_text(json.dumps(lock))
    before = _snapshot(tmp_path)
    result = _invoke(directory)
    assert result.exit_code == 2, result.exception
    assert "invalid study.lock.json" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout
    assert _snapshot(tmp_path) == before


def test_missing_study_is_a_usage_error_without_creating_directory(tmp_path):
    missing = tmp_path / "missing"
    result = _invoke(missing)
    assert result.exit_code == 2
    assert "study.json" in result.stderr
    assert not missing.exists()


@pytest.mark.parametrize("invalid", ["empty-study", "missing-block", "bad-lock", "unknown-policy"])
def test_invalid_configuration_fails_before_output_or_mutation(tmp_path, invalid):
    directory = _copy_study(tmp_path)
    if invalid == "bad-lock":
        (directory / "study.lock.json").write_text("{}")
    elif invalid == "unknown-policy":
        path = directory / "scenarios/agg-priv.json"
        data = json.loads(path.read_text())
        data["cognition"]["agents"][0]["policy"] = {"name": "unknown-policy"}
        path.write_text(json.dumps(data))
    else:
        path = directory / "study.json"
        data = json.loads(path.read_text())
        if invalid == "empty-study":
            data["conditions"] = []
        else:
            data["seed_protocol"] = "paired-policy-v2"
        path.write_text(json.dumps(data))
    before = _snapshot(tmp_path)
    result = _invoke(directory)
    assert result.exit_code == 2, result.exception
    assert "error:" in result.stderr
    assert not result.stdout
    assert _snapshot(tmp_path) == before
