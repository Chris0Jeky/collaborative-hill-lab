"""CRN must hold through run_study, not just when callers hand-pick equal roots."""

import json
import shutil

import pytest

from collaborative_hill.domain.actions import AbstainAction, ActionProposal, WithholdAction
from collaborative_hill.domain.world.evidence_commons import EvidenceCommonsMechanism
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths
from collaborative_hill.experiments import study
from collaborative_hill.experiments.manifests import RunManifest
from collaborative_hill.reporting.report import run_report, study_report, write_run_metrics

from ._helpers import STUDY_000, STUDY_001, find_run_dirs

pytestmark = pytest.mark.integration

LEGACY = "legacy-independent-v1"
PAIRED = "paired-policy-v2"
CELLS = {"agg-priv", "agg-ledger", "attr-priv", "attr-ledger"}


class DrawAuditPolicy:
    """One unchanged policy; expose raw draws without assuming observations match."""

    policy_id = "seed-audit@1"

    def propose(self, observation, rng):
        action = (WithholdAction() if observation["accountability"] == "aggregate"
                  else AbstainAction(reason="attributable-observation"))
        return ActionProposal(action=action, justification=str(rng.getrandbits(64)))


def _audit_policies(resolved):
    return {agent.agent_id: DrawAuditPolicy() for agent in resolved.spec.cognition.agents}


def _copy_paired_study(tmp_path):
    directory = tmp_path / "paired-study"
    shutil.copytree(STUDY_001, directory)
    path = directory / "study.json"
    data = json.loads(path.read_text())
    data["seed_protocol"] = PAIRED
    data["replicates"] = 2
    for condition in data["conditions"]:
        condition["scenario_block"] = (
            "factorial" if condition["condition_id"] in CELLS else "misinformation"
        )
    path.write_text(json.dumps(data))
    return directory


def _draws(events, min_round=0):
    return {
        (event.payload["agent_id"], event.logical_time):
            event.payload["proposal"]["justification"]
        for event in events
        if event.event_type == EventType.ACTION_PROPOSED and event.logical_time >= min_round
    }


def test_current_study001_has_independent_streams_and_is_labeled_honestly(tmp_path, monkeypatch):
    monkeypatch.setattr(study, "build_policies", _audit_policies)
    study.run_study(STUDY_001, tmp_path, replicates_override=1)
    first_draws = {}
    for directory in find_run_dirs(tmp_path):
        events, _, manifest = load_run(directory)
        first_draws[manifest["condition_id"]] = _draws(events)[("a1", 0)]
        assert manifest["seed_protocol"] == LEGACY
        assert manifest["policy_seed_root"] is None
        assert manifest["scenario_block"] is None
        assert "seed_protocol" not in events[0].payload  # old ledger format is preserved
    # Measured on the unmodified authoritative-main code before this fix.
    assert first_draws == {
        "agg-priv": "14442509083846134711",
        "agg-ledger": "15968561580677346032",
        "attr-priv": "17485811729684596417",
        "attr-ledger": "2761447364641609127",
        "attr-priv-misinfo": "6346500906894703209",
    }


def test_paired_study001_draws_match_across_cells_and_separate_other_scopes(tmp_path, monkeypatch):
    directory = _copy_paired_study(tmp_path)
    monkeypatch.setattr(study, "build_policies", _audit_policies)
    # Existing world dynamics are deterministic. Make a test-only stochastic world
    # consumer observable so this also exercises the actual mechanism stream.
    original_resolve = EvidenceCommonsMechanism.resolve

    def resolve(self, state, actions, rng):
        draw = str(rng.getrandbits(64))
        new_state, events = original_resolve(self, state, actions, rng)
        return new_state, [*events, {
            "event_type": EventType.WORLD_TRANSITIONED.value,
            "payload": {"mechanism_draw": draw},
        }]

    monkeypatch.setattr(EvidenceCommonsMechanism, "resolve", resolve)
    results = study.run_study(directory, tmp_path / "artifacts")
    assert len(results) == 10 and all(result.status == "completed" for result in results)
    repeated = study.run_study(directory, tmp_path / "repeat")
    assert [r.final_event_hash for r in results] == [r.final_event_hash for r in repeated]
    runs = {}
    for run_dir in find_run_dirs(tmp_path / "artifacts"):
        events, _, manifest = load_run(run_dir)
        runs[(manifest["condition_id"], manifest["replicate"])] = (events, manifest, run_dir)
        assert manifest["seed_protocol"] == PAIRED
        assert events[0].payload["seed_protocol"] == PAIRED
        assert events[0].payload["scenario_block"] == manifest["scenario_block"]
        assert events[0].payload["policy_seed_root"] == list(map(str, manifest["policy_seed_root"]))
        assert replay_run(run_dir).chains_match

    for replicate in range(2):
        expected = _draws(runs[("agg-priv", replicate)][0])
        assert len(expected) == 36  # 3 agents x 12 rounds, all non-vacuous
        assert len(set(expected.values())) == 36  # agents and rounds stay distinct
        mechanism_draws = []
        for cell in CELLS:
            events, _, _ = runs[(cell, replicate)]
            assert _draws(events) == expected
            mechanism_draws.append(next(e.payload["mechanism_draw"] for e in events
                                        if "mechanism_draw" in e.payload))
        assert len(set(mechanism_draws)) == 4  # mechanism draws stay condition-specific
        assert set(mechanism_draws).isdisjoint(expected.values())
        assert _draws(runs[("attr-priv-misinfo", replicate)][0]) != expected
    assert _draws(runs[("agg-priv", 0)][0]) != _draws(runs[("agg-priv", 1)][0])

    aggregate = runs[("agg-priv", 0)][0]
    attributable = runs[("attr-priv", 0)][0]
    def proposals(events):
        return [e.payload["proposal"]["action"] for e in events
                if e.event_type == EventType.ACTION_PROPOSED]

    assert proposals(aggregate) != proposals(attributable)  # equal draws != equal actions

    parent_events, parent_manifest, parent_dir = runs[("agg-priv", 0)]
    fork_seq = FileCheckpointStore(RunPaths(parent_dir).checkpoints).list_seqs()[0]
    child_dir = tmp_path / "child"
    _, branch = branch_run(parent_dir=parent_dir, fork_seq=fork_seq, child_dir=child_dir,
                           child_run_id="paired-child", policy_overrides={})
    child_events, _, child_manifest = load_run(child_dir)
    assert _draws(child_events, branch.fork_round) == _draws(parent_events, branch.fork_round)
    assert child_manifest["policy_seed_root"] == parent_manifest["policy_seed_root"]
    assert child_manifest["scenario_block"] == "factorial"
    assert child_manifest["seed_protocol"] == PAIRED
    assert child_dir.joinpath("events.jsonl").read_bytes().splitlines()[:fork_seq + 1] == (
        parent_dir.joinpath("events.jsonl").read_bytes().splitlines()[:fork_seq + 1]
    )


@pytest.mark.parametrize(("directory", "condition", "expected_hash", "events", "chain"), [
    (STUDY_000, "pw-3tft",
     "5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f", 656,
     "93993cc6f74f7aa2d936f94859193490a2ebaca009646e15c5a5526ca2914ec6"),
    (STUDY_001, "attr-ledger",
     "a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe", 148,
     "eea9a355b8562246e4e439f7f04f0a59c580a27d373c9508844c215744b31c48"),
])
def test_legacy_hashes_ledgers_and_old_manifest_replay_stay_exact(
    tmp_path, directory, condition, expected_hash, events, chain,
):
    assert study.validate_study(directory)["study_hash"] == expected_hash
    result, = study.run_study(directory, tmp_path / "artifacts", only_condition=condition,
                             replicates_override=1)
    assert result.event_count == events
    assert result.final_event_hash == chain
    run_dir, = find_run_dirs(tmp_path / "artifacts")
    manifest_path = run_dir / "manifest.json"
    data = json.loads(manifest_path.read_text())
    for field in ("seed_protocol", "policy_seed_root", "scenario_block"):
        data.pop(field)
    data["schema_version"] = 1
    manifest_path.write_text(json.dumps(data))
    old_bytes = manifest_path.read_bytes()
    assert RunManifest.model_validate(data).seed_protocol == LEGACY
    assert load_run(run_dir)[2]["seed_protocol"] == LEGACY
    assert replay_run(run_dir).chains_match
    assert LEGACY in run_report(run_dir).read_text()
    assert LEGACY in study_report(run_dir.parent.parent).read_text()
    fork_seq = FileCheckpointStore(RunPaths(run_dir).checkpoints).list_seqs()[0]
    child_dir = tmp_path / "legacy-child"
    branch_run(parent_dir=run_dir, fork_seq=fork_seq, child_dir=child_dir,
               child_run_id="legacy-child", policy_overrides={})
    assert load_run(child_dir)[2]["seed_protocol"] == LEGACY
    assert manifest_path.read_bytes() == old_bytes


@pytest.mark.parametrize("field", [
    "seed_protocol", "policy_seed_root", "scenario_block", "seed_root", "remove-v2-fields",
])
def test_replay_and_branch_reject_changed_paired_seed_metadata(tmp_path, field):
    directory = _copy_paired_study(tmp_path)
    study.run_study(directory, tmp_path / "artifacts", only_condition="agg-priv",
                    replicates_override=1)
    parent_dir, = find_run_dirs(tmp_path / "artifacts")
    manifest_path = parent_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if field == "remove-v2-fields":
        for key in ("seed_protocol", "policy_seed_root", "scenario_block"):
            del manifest[key]
    elif field.endswith("_root"):
        manifest[field][0] += 1
    else:
        manifest[field] = "changed"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="seed|scenario_block"):
        replay_run(parent_dir)
    for reporter in (write_run_metrics, run_report, study_report):
        with pytest.raises(ValueError, match="seed|scenario_block"):
            reporter(parent_dir.parent.parent if reporter is study_report else parent_dir)
    assert not parent_dir.joinpath("metrics/metrics.json").exists()
    assert not parent_dir.joinpath("report.md").exists()
    assert not parent_dir.parent.parent.joinpath("report.md").exists()
    fork_seq = FileCheckpointStore(RunPaths(parent_dir).checkpoints).list_seqs()[0]
    child_dir = tmp_path / "child"
    with pytest.raises(ValueError, match="seed|scenario_block"):
        branch_run(parent_dir=parent_dir, fork_seq=fork_seq, child_dir=child_dir,
                   child_run_id="child", policy_overrides={})
    assert not child_dir.exists()
