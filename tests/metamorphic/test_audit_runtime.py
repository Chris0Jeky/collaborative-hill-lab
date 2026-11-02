"""Opt-in audit runs retain their lifecycle, replay and artifact guarantees."""

import json
import shutil

import pytest

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.agents.scripted.ec_policies import ECFreeriderPolicy
from collaborative_hill.domain.institutions import AuditInstitutionConfig, InstitutionConfig
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import ChainError, EventType
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore
from collaborative_hill.experiments import study

from ._helpers import default_ec_evidence, ec_spec, find_run_dirs, plain_skin, write_study

pytestmark = pytest.mark.metamorphic
DEFAULT_SCHEDULE = (("s1", "p1a", 0), ("s1", "p1b", 0), ("s2", "p2a", 3))


def institution(schedule=DEFAULT_SCHEDULE):
    return AuditInstitutionConfig.model_validate_json(json.dumps({
        "accountability": "attributable", "evidence_topology": "shared_ledger",
        "audit": {
            "contract": {
                "contract_version": "ec-audit-observation@1", "audit_id": "runtime-fixture",
                "accuracy": "3/4", "accuracy_semantics": "symmetric-conditional-on-availability",
                "oracle_kind": "synthetic-trusted-oracle",
                "dependence": "independent-of-source-errors",
                "visibility": "public", "selection": "fixed-ex-ante-targets",
                "unavailable_semantics": "explicit-no-verdict",
                "schedule": [{"slot_id": slot, "proposition_id": prop, "publish_round": rnd}
                             for slot, prop, rnd in schedule],
            },
            "generation": {
                "generator_version": "ec-audit-generator@1", "unavailable_probability": "1/3",
                "draw_dependence": "independent-per-target",
                "unavailable_dependence": "independent-of-truth-source-errors-and-correctness",
            },
        },
    }))


def run_fixture(root, *, audit=True, schedule=DEFAULT_SCHEDULE, block="shared", agents=None):
    config = institution(schedule) if audit else InstitutionConfig(
        accountability="attributable", evidence_topology="shared_ledger")
    kwargs = {"agents": agents} if agents is not None else {}
    spec = ec_spec(default_ec_evidence(), rounds=6, institution=config, **kwargs)
    directory = write_study(root / "study", study_id="audit-runtime", seed=103,
                            checkpoint_every=1, conditions=[("cell", spec, plain_skin())])
    path = directory / "study.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["seed_protocol"] = "paired-policy-v2"
    data["conditions"][0]["scenario_block"] = block
    path.write_text(json.dumps(data), encoding="utf-8")
    result, = study.run_study(directory, root / "runs")
    run, = find_run_dirs(root / "runs")
    return run, result


@pytest.fixture(scope="module")
def valid_runs(tmp_path_factory):
    root = tmp_path_factory.mktemp("audit-runtime")
    runs = {}
    for audit in (False, True):
        run, result = run_fixture(root / str(audit), audit=audit)
        assert result.status == "completed"
        assert replay_run(run).chains_match
        runs[audit] = run
    return runs


def copied_run(tmp_path, valid_runs, *, audit=True):
    target = tmp_path / "run"
    shutil.copytree(valid_runs[audit], target)
    return target


def all_bytes(path):
    return {p.relative_to(path): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def reports(events):
    return [event.payload["report"] for event in events
            if event.event_type == EventType.AUDIT_PUBLISHED]


def fork_at(run, rnd):
    store = FileCheckpointStore(run / "checkpoints")
    return next(seq for seq in store.list_seqs() if store.load(seq)["logical_time"] == rnd)


def test_publication_precedes_observations_and_checkpoints_keep_only_released_reports(valid_runs):
    run = valid_runs[True]
    events, _, _ = load_run(run)
    findings = reports(events)
    assert [(r["slot_id"], r["proposition_id"], r["publish_round"]) for r in findings] == (
        list(DEFAULT_SCHEDULE)
    )
    for rnd in range(6):
        publications = [e for e in events if e.logical_time == rnd
                        and e.event_type == EventType.AUDIT_PUBLISHED]
        observations = [e for e in events if e.logical_time == rnd
                        and e.event_type == EventType.OBSERVATION_ISSUED]
        assert len(observations) == 3
        if publications:
            assert max(e.seq for e in publications) < min(e.seq for e in observations)
        for event in observations:
            observation = event.payload["observation"]
            assert observation["mechanism"] == "evidence_commons"
            assert observation["observation_schema_version"] == 3
            assert observation["audit"]["reports"] == [
                finding for finding in findings if finding["publish_round"] <= rnd
            ]
        assert all(set(e.payload) == {"contract_version", "audit_id", "contract_hash", "report"}
                   for e in publications)
    store = FileCheckpointStore(run / "checkpoints")
    for seq in store.list_seqs():
        record = store.load(seq)
        assert record["state"]["audit_reports"] == [
            finding for finding in findings if finding["publish_round"] < record["logical_time"]
        ]
    ledger = (run / "events.jsonl").read_text(encoding="utf-8")
    assert '"true_propositions"' not in ledger
    assert '"truth_aligned"' not in ledger
    assert '"accuracy"' not in ledger
    assert '"unavailable_probability"' not in ledger


@pytest.mark.parametrize("change", ["reorder", "add-target", "timing", "policy-root", "policy"])
def test_target_draws_survive_unrelated_schedule_and_policy_changes(tmp_path, valid_runs, change):
    schedule = list(DEFAULT_SCHEDULE)
    kwargs = {}
    if change == "reorder":
        schedule.reverse()
    elif change == "add-target":
        schedule.append(("s2", "p2b", 1))
    elif change == "timing":
        schedule[0] = ("s1", "p1a", 4)
    elif change == "policy-root":
        kwargs["block"] = "different-policy-stream"
    else:
        kwargs["agents"] = tuple((a, "ec_freerider") for a in ("a1", "a2", "a3"))
    changed, result = run_fixture(tmp_path, schedule=tuple(schedule), **kwargs)
    assert result.status == "completed"
    before, _, original_manifest = load_run(valid_runs[True])
    after, _, changed_manifest = load_run(changed)
    assert original_manifest["seed_root"] == changed_manifest["seed_root"]
    observed = {(r["slot_id"], r["proposition_id"]): r["verdict"] for r in reports(after)}
    assert {(r["slot_id"], r["proposition_id"]): r["verdict"] for r in reports(before)} == {
        target: observed[target] for target in {(s, p) for s, p, _ in DEFAULT_SCHEDULE}
    }
    if change == "policy-root":
        assert original_manifest["policy_seed_root"] != changed_manifest["policy_seed_root"]
    if change == "policy":
        assert original_manifest["policies"] != changed_manifest["policies"]


def test_branches_before_after_and_nested_replay_without_ancestors(tmp_path, valid_runs):
    parent = copied_run(tmp_path, valid_runs)
    parent_events, _, _ = load_run(parent)
    parent_bytes = (parent / "events.jsonl").read_bytes().splitlines(keepends=True)
    branches = []
    for name, rnd in (("before", 2), ("after", 4)):
        child = tmp_path / name
        seq = fork_at(parent, rnd)
        result, _ = branch_run(parent_dir=parent, fork_seq=seq, child_dir=child,
                               child_run_id=name, policy_overrides={})
        assert result.status == "completed"
        assert (child / "events.jsonl").read_bytes().splitlines(keepends=True)[:seq + 1] == (
            parent_bytes[:seq + 1]
        )
        assert reports(load_run(child)[0]) == reports(parent_events)
        branches.append(child)
    nested = tmp_path / "nested"
    before = branches[0]
    result, _ = branch_run(parent_dir=before, fork_seq=fork_at(before, 4), child_dir=nested,
                           child_run_id="nested", policy_overrides={
                               a: ECFreeriderPolicy() for a in ("a1", "a2", "a3")})
    assert result.status == "completed"
    assert reports(load_run(nested)[0]) == reports(parent_events)
    shutil.rmtree(parent)
    assert replay_run(before).chains_match
    assert replay_run(branches[1]).chains_match
    shutil.rmtree(before)
    shutil.rmtree(nested / "checkpoints")
    original = all_bytes(nested)
    assert replay_run(nested).chains_match
    assert all_bytes(nested) == original


@pytest.mark.parametrize("failing_agent", ["a1", "a3"])
def test_failure_at_publication_round_replays_offline(tmp_path, monkeypatch, failing_agent):
    def build(resolved, **kwargs):
        return {a.agent_id: LLMPolicy(
            a.agent_id, FakeProvider(['{"action":{"type":"abstain"}}'] * 6,
                                     fail_at=3 if a.agent_id == failing_agent else None),
            resolved.skin,
        ) for a in resolved.spec.cognition.agents}

    monkeypatch.setattr(study, "build_policies", build)
    run, result = run_fixture(tmp_path)
    assert result.status == "failed" and result.rounds_played == 3
    events, _, _ = load_run(run)
    assert len(reports(events)) == 3
    assert events[-1].event_type == EventType.RUN_FAILED
    publications = [e for e in events if e.event_type == EventType.AUDIT_PUBLISHED
                    and e.logical_time == 3]
    observations = [e for e in events if e.event_type == EventType.OBSERVATION_ISSUED
                    and e.logical_time == 3]
    assert publications[0].seq < min(e.seq for e in observations)
    assert len(observations) == 3

    def no_provider(*args, **kwargs):
        pytest.fail("audit replay must not call a provider or configured policy")

    monkeypatch.setattr(LLMPolicy, "propose", no_provider)
    monkeypatch.setattr(FakeProvider, "complete", no_provider)
    shutil.rmtree(run / "checkpoints")
    (run / "llm_transcript.jsonl").unlink()
    original = all_bytes(run)
    saved = tmp_path / "saved-replay"
    assert replay_run(run, keep_dir=saved).chains_match
    replayed = FileEventStore(saved / "replay/events.jsonl").load_all(verify=True)
    assert [e.hashed_view() for e in replayed] == [e.hashed_view() for e in events]
    assert all_bytes(run) == original


@pytest.mark.parametrize("damage", [
    "missing", "null", "empty", "legacy-only", "accuracy", "unavailability", "audit-id",
    "timing", "bool-round", "extra", "legacy-injected-audit", "legacy-accountability",
])
def test_manifest_institution_is_strictly_bound_before_replay_or_branch(
    tmp_path, valid_runs, damage,
):
    run = copied_run(tmp_path, valid_runs,
                     audit=damage not in {"legacy-injected-audit", "legacy-accountability"})
    path = run / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if damage == "missing":
        del manifest["institution"]
    elif damage == "null":
        manifest["institution"] = None
    elif damage == "empty":
        manifest["institution"] = {}
    elif damage == "legacy-only":
        del manifest["institution"]["audit"]
    elif damage == "legacy-injected-audit":
        manifest["institution"]["audit"] = institution().model_dump(mode="json")["audit"]
    elif damage == "legacy-accountability":
        manifest["institution"]["accountability"] = "aggregate"
    elif damage == "extra":
        manifest["institution"]["extra"] = "not-bound"
    else:
        audit = manifest["institution"]["audit"]
        if damage == "accuracy":
            audit["contract"]["accuracy"] = "1/2"
        elif damage == "unavailability":
            audit["generation"]["unavailable_probability"] = "1/2"
        elif damage == "audit-id":
            audit["contract"]["audit_id"] = "forged"
        else:
            audit["contract"]["schedule"][0]["publish_round"] = (
                False if damage == "bool-round" else 1
            )
    path.write_text(json.dumps(manifest), encoding="utf-8")
    original = all_bytes(run)
    FileEventStore(run / "events.jsonl").load_all(verify=True)
    with pytest.raises(ChainError, match="institution"):
        load_run(run)
    output, child = tmp_path / "replay-output", tmp_path / "child"
    with pytest.raises(ChainError, match="institution"):
        replay_run(run, keep_dir=output)
    with pytest.raises(ChainError, match="institution"):
        branch_run(parent_dir=run, fork_seq=fork_at(run, 2), child_dir=child,
                   child_run_id="invalid", policy_overrides={})
    assert not output.exists() and not child.exists()
    assert all_bytes(run) == original


def test_legacy_manifest_can_omit_institution_without_rewriting_original(tmp_path, valid_runs):
    run = copied_run(tmp_path, valid_runs, audit=False)
    path = run / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    del manifest["institution"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    original = all_bytes(run)
    assert load_run(run)[2].get("institution") is None
    assert replay_run(run).chains_match
    assert all_bytes(run) == original
