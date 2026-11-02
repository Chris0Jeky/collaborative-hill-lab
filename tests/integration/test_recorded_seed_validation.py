"""Malformed recorded roots fail before replay or branch can create output."""

import json
import shutil

import pytest

from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.hashing import GENESIS_HASH
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.seeds import LEGACY_SEED_PROTOCOL, PAIRED_SEED_PROTOCOL
from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore
from collaborative_hill.experiments.study import run_study

from ._helpers import STUDY_000, find_run_dirs, run_cli

pytestmark = pytest.mark.integration

PROTOCOLS = (LEGACY_SEED_PROTOCOL, PAIRED_SEED_PROTOCOL)
MALFORMED_ROOTS = [
    None, 7, True, "seed", {"seed": 7}, [None], [True], [1.5], [[]], [{}], ["a\x1fb"],
]


def _write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8", newline="\n")


@pytest.fixture(scope="module")
def valid_runs(tmp_path_factory):
    """Real, replayable stochastic runs with the two supported seed protocols."""
    root = tmp_path_factory.mktemp("recorded-seeds")
    runs = {}
    for protocol in PROTOCOLS:
        directory = root / protocol / "study"
        directory.mkdir(parents=True)
        scenario = json.loads((STUDY_000 / "scenarios/pw-3tft.json").read_text())
        scenario["world"]["rounds"] = 3
        for agent in scenario["cognition"]["agents"]:
            agent["policy"] = {"name": "random"}
        _write_json(directory / "scenario.json", scenario)
        _write_json(directory / "skin.json", {"skin_id": "plain"})
        condition = {"condition_id": "c", "scenario": "scenario.json", "skin": "skin.json"}
        if protocol == PAIRED_SEED_PROTOCOL:
            condition["scenario_block"] = "shared"
        _write_json(directory / "study.json", {
            "study_id": "recorded-seeds", "seed": 7, "replicates": 1,
            "checkpoint_every": 1, "seed_protocol": protocol, "conditions": [condition],
        })
        artifacts = root / protocol / "artifacts"
        result, = run_study(directory, artifacts)
        assert result.status == "completed"
        run_dir, = find_run_dirs(artifacts)
        assert load_run(run_dir)[2]["seed_protocol"] == protocol
        assert replay_run(run_dir).chains_match
        runs[protocol] = run_dir
    return runs


def _changed_run(tmp_path, valid_runs, protocol, **changes):
    run_dir = tmp_path / "run"
    shutil.copytree(valid_runs[protocol], run_dir)
    path = run_dir / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest.update(changes)
    _write_json(path, manifest)
    return run_dir


def _replace_start_fields(run_dir, **changes):
    """Keep the test chain hash-valid so malformed metadata reaches validation."""
    path = run_dir / "events.jsonl"
    events = FileEventStore(path).load_all(verify=True)
    previous = GENESIS_HASH
    lines = []
    for event in events:
        payload = {**event.payload, **changes} if event.seq == 0 else event.payload
        draft = event.model_copy(update={"payload": payload, "parent_hash": previous})
        sealed = draft.model_copy(update={"event_hash": draft.compute_hash()})
        previous = sealed.event_hash
        lines.append(sealed.model_dump_json() + "\n")
    path.write_text("".join(lines), encoding="utf-8", newline="\n")
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["final_event_hash"] = previous
    _write_json(manifest_path, manifest)
    FileEventStore(path).load_all(verify=True)


@pytest.mark.parametrize("protocol", PROTOCOLS)
@pytest.mark.parametrize("value", MALFORMED_ROOTS)
def test_load_rejects_malformed_mechanism_root(tmp_path, valid_runs, protocol, value):
    run_dir = _changed_run(tmp_path, valid_runs, protocol, seed_root=value)
    with pytest.raises(ValueError, match="seed_root"):
        load_run(run_dir)


@pytest.mark.parametrize("value", [*MALFORMED_ROOTS, []])
def test_load_rejects_malformed_paired_policy_root(tmp_path, valid_runs, value):
    run_dir = _changed_run(tmp_path, valid_runs, PAIRED_SEED_PROTOCOL, policy_seed_root=value)
    with pytest.raises(ValueError, match="policy_seed_root"):
        load_run(run_dir)


@pytest.mark.parametrize("protocol", PROTOCOLS)
@pytest.mark.parametrize("value", [None, 7, True, [], {}, "future-protocol"])
def test_load_rejects_malformed_protocol(tmp_path, valid_runs, protocol, value):
    run_dir = _changed_run(tmp_path, valid_runs, protocol, seed_protocol=value)
    with pytest.raises(ValueError, match="seed_protocol"):
        load_run(run_dir)


@pytest.mark.parametrize("protocol", PROTOCOLS)
@pytest.mark.parametrize("value", [7, True, [], {}, "", "  ", "a\x1fb"])
def test_load_rejects_malformed_block(tmp_path, valid_runs, protocol, value):
    run_dir = _changed_run(tmp_path, valid_runs, protocol, scenario_block=value)
    with pytest.raises(ValueError, match="scenario_block|reserved separator"):
        load_run(run_dir)


@pytest.mark.parametrize("protocol", PROTOCOLS)
@pytest.mark.parametrize("command", ["replay", "branch"])
@pytest.mark.parametrize(("field", "value"), [
    ("seed_root", None), ("seed_root", 7), ("scenario_block", 7),
])
def test_cli_rejects_bad_metadata_without_traceback_or_output(
    tmp_path, valid_runs, protocol, command, field, value,
):
    run_dir = _changed_run(tmp_path, valid_runs, protocol, **{field: value})
    original = {p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
    fork = FileCheckpointStore(run_dir / "checkpoints").list_seqs()[0]
    replay_output, child = tmp_path / "replay-output", tmp_path / "child"
    args = [command, str(run_dir)]
    if command == "branch":
        args.extend(["--at-event", str(fork), "--override", "a1=allc", "--out", str(child)])
    result = run_cli(*args)
    assert result.returncode == 2, result.stderr
    assert result.stdout == ""
    assert result.stderr.startswith("error: ")
    assert field in result.stderr
    assert "Traceback" not in result.stderr
    with pytest.raises(ValueError, match=field):
        replay_run(run_dir, keep_dir=replay_output)
    with pytest.raises(ValueError, match=field):
        branch_run(parent_dir=run_dir, fork_seq=fork, child_dir=child,
                   child_run_id="child", policy_overrides={})
    assert not replay_output.exists()
    assert not child.exists()
    assert {p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()} == (
        original
    )


@pytest.mark.parametrize("protocol", PROTOCOLS)
@pytest.mark.parametrize(("field", "value"), [
    ("seed_root", ["a\x1fb"]), ("scenario_block", 7), ("seed_protocol", []),
])
def test_hash_valid_start_does_not_make_matching_malformed_metadata_valid(
    tmp_path, valid_runs, protocol, field, value,
):
    run_dir = _changed_run(tmp_path, valid_runs, protocol, **{field: value})
    _replace_start_fields(run_dir, **{field: value})
    with pytest.raises(ValueError, match="seed|scenario_block|reserved separator"):
        load_run(run_dir)


@pytest.mark.parametrize(("field", "value"), [
    ("policy_seed_root", ["7"]), ("scenario_block", "undeclared-block"),
])
def test_legacy_start_cannot_declare_ignored_pairing_fields(tmp_path, valid_runs, field, value):
    run_dir = _changed_run(tmp_path, valid_runs, LEGACY_SEED_PROTOCOL)
    _replace_start_fields(run_dir, **{field: value})
    with pytest.raises(ValueError, match=field):
        load_run(run_dir)


@pytest.mark.parametrize("protocol", PROTOCOLS)
def test_valid_integer_and_string_roots_replay_and_branch_without_rewriting(
    tmp_path, valid_runs, protocol,
):
    run_dir = _changed_run(tmp_path, valid_runs, protocol)
    path = run_dir / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["seed_root"] = [str(c) for c in manifest["seed_root"]]
    if protocol == PAIRED_SEED_PROTOCOL:
        manifest["policy_seed_root"] = [str(c) for c in manifest["policy_seed_root"]]
    else:
        # The original format omitted all three protocol fields.
        for field in ("seed_protocol", "policy_seed_root", "scenario_block"):
            del manifest[field]
        manifest["schema_version"] = 1
    _write_json(path, manifest)
    original = {p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
    events, _, loaded = load_run(run_dir)
    assert loaded["seed_protocol"] == protocol
    assert replay_run(run_dir).chains_match
    child = tmp_path / "child"
    fork = FileCheckpointStore(run_dir / "checkpoints").list_seqs()[0]
    branch_run(parent_dir=run_dir, fork_seq=fork, child_dir=child,
               child_run_id="child", policy_overrides={})
    child_events, _, child_manifest = load_run(child)
    assert child_manifest["seed_root"] == manifest["seed_root"]
    assert child_events[:fork + 1] == events[:fork + 1]
    assert replay_run(child).chains_match
    assert {p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()} == (
        original
    )


@pytest.mark.parametrize("protocol", PROTOCOLS)
def test_well_typed_root_must_still_agree_with_run_started(tmp_path, valid_runs, protocol):
    run_dir = _changed_run(tmp_path, valid_runs, protocol, seed_root=["different"])
    with pytest.raises(ValueError, match="seed_root.*disagrees"):
        load_run(run_dir)
