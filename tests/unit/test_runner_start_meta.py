"""Supplemental RunStarted metadata cannot change the engine's recorded facts."""

import pytest
from _fixtures import AGENTS, nipd

from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.seeds import LEGACY_SEED_PROTOCOL, PAIRED_SEED_PROTOCOL
from collaborative_hill.engine.store import FileEventStore, RunPaths


def _inputs(paired):
    mechanism = nipd("pairwise", rounds=1)
    policies = {agent: build_nipd_policy("allc", "pairwise", {}) for agent in AGENTS}
    config = RunConfig(
        study_id="metadata-study", run_id="metadata-run", seed_root=(7, "condition", 0),
        seed_protocol=PAIRED_SEED_PROTOCOL if paired else LEGACY_SEED_PROTOCOL,
        policy_seed_root=(7, "shared", 0) if paired else None,
        scenario_block="shared" if paired else None,
    )
    return {"mechanism": mechanism, "policies": policies, "config": config}


def _snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def _expected_start(paired):
    expected = {
        "agents": ["a1", "a2", "a3"],
        "policies": dict.fromkeys(AGENTS, "allc[pairwise]@1"),
        "seed_root": ["7", "condition", "0"],
        "invalid_action_policy": "fail",
    }
    if paired:
        expected.update({
            "seed_protocol": "paired-policy-v2",
            "policy_seed_root": ["7", "shared", "0"],
            "scenario_block": "shared",
        })
    return expected


@pytest.mark.parametrize("paired", [False, True], ids=["legacy", "paired"])
@pytest.mark.parametrize("existing", [False, True], ids=["fresh", "populated"])
@pytest.mark.parametrize("key", [
    "agents", "policies", "seed_root", "invalid_action_policy",
    "seed_protocol", "policy_seed_root", "scenario_block",
])
def test_reserved_start_metadata_fails_before_any_artifact_mutation(
    tmp_path, paired, existing, key,
):
    inputs = _inputs(paired)
    paths = RunPaths(tmp_path / "run").create()
    if existing:
        run_episode(**inputs, paths=paths)
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match=rf"start_meta.*reserved.*{key}"):
        run_episode(**inputs, paths=paths, start_meta={key: "caller-supplied"})
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("paired", [False, True], ids=["legacy", "paired"])
def test_reserved_start_metadata_rejected_for_continuation_on_absent_paths(tmp_path, paired):
    inputs = _inputs(paired)
    paths = RunPaths(tmp_path / "missing")
    start_state = inputs["mechanism"].initial_state()
    with pytest.raises(ValueError, match="start_meta.*reserved.*seed_root"):
        run_episode(**inputs, paths=paths, start_state=start_state,
                    start_meta={"seed_root": None})
    assert not paths.root.exists()


@pytest.mark.parametrize("paired", [False, True], ids=["legacy", "paired"])
def test_matching_reserved_value_still_rejected(tmp_path, paired):
    inputs = _inputs(paired)
    paths = RunPaths(tmp_path / "run").create()
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="start_meta.*reserved.*seed_protocol"):
        run_episode(**inputs, paths=paths,
                    start_meta={"seed_protocol": inputs["config"].seed_protocol})
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("paired", [False, True], ids=["legacy", "paired"])
def test_supplemental_start_metadata_preserved(tmp_path, paired):
    inputs = _inputs(paired)
    paths = RunPaths(tmp_path / "run").create()
    supplemental = {
        "scenario_hash": "scenario", "mechanism_hash": "mechanism", "narrative_hash": "narrative",
        "notes": {"seed_root": ["nested supplemental value"]},
    }
    result = run_episode(**inputs, paths=paths, start_meta=supplemental)
    assert result.status == "completed"
    started = FileEventStore(paths.events).load_all(verify=True)[0]
    assert started.payload == {**_expected_start(paired), **supplemental}
    assert set(supplemental) == {"scenario_hash", "mechanism_hash", "narrative_hash", "notes"}


@pytest.mark.parametrize("paired", [False, True], ids=["legacy", "paired"])
def test_start_metadata_is_snapshotted_before_mechanism_callbacks(tmp_path, monkeypatch, paired):
    inputs = _inputs(paired)
    paths = RunPaths(tmp_path / "run").create()
    supplemental = {"scenario_hash": "scenario"}
    mechanism = inputs["mechanism"]
    original_agent_ids = mechanism.agent_ids

    def mutate_caller_metadata():
        supplemental.update({
            "agents": "spoofed", "policies": "spoofed", "seed_root": "spoofed",
            "invalid_action_policy": "spoofed", "seed_protocol": "spoofed",
            "policy_seed_root": "spoofed", "scenario_block": "spoofed",
        })
        return original_agent_ids()

    monkeypatch.setattr(mechanism, "agent_ids", mutate_caller_metadata)
    result = run_episode(**inputs, paths=paths, start_meta=supplemental)
    assert result.status == "completed"
    assert supplemental["seed_protocol"] == "spoofed"  # the callback ran
    started = FileEventStore(paths.events).load_all(verify=True)[0]
    assert started.payload == {**_expected_start(paired), "scenario_hash": "scenario"}


@pytest.mark.parametrize("paired", [False, True], ids=["legacy", "paired"])
def test_none_and_empty_start_metadata_produce_identical_ledgers(tmp_path, paired):
    inputs = _inputs(paired)
    omitted = RunPaths(tmp_path / "omitted").create()
    empty = RunPaths(tmp_path / "empty").create()
    run_episode(**inputs, paths=omitted)
    run_episode(**inputs, paths=empty, start_meta={})
    assert omitted.events.read_bytes() == empty.events.read_bytes()
