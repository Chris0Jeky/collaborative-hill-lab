"""Recorded provider outcomes replay offline; impossible failure boundaries refuse."""

import json
import shutil

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.agents.llm.providers import ProviderError
from collaborative_hill.cli import app
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.hashing import GENESIS_HASH
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore, RunPaths
from collaborative_hill.experiments import study

from ._helpers import (
    default_ec_evidence,
    ec_item,
    ec_spec,
    find_run_dirs,
    plain_skin,
    write_study,
)

pytestmark = pytest.mark.metamorphic
GOOD = '{"action":{"type":"abstain"}}'
ILLEGAL = '{"action":{"type":"inspect_evidence","evidence_id":"NOPE"}}'


def _run(tmp_path, monkeypatch, *, agent="a2", fail_at=1, malformed=None,
         paired=False, good=GOOD, invalid_action_policy="fail"):
    directory = tmp_path / "study"
    write_study(directory, study_id="provider-replay", seed=17, checkpoint_every=1,
                conditions=[("cell", ec_spec(default_ec_evidence(), rounds=4), plain_skin())])
    path = directory / "study.json"
    data = json.loads(path.read_text())
    data["invalid_action_policy"] = invalid_action_policy
    if paired:
        data["seed_protocol"] = "paired-policy-v2"
        data["conditions"][0]["scenario_block"] = "shared"
    path.write_text(json.dumps(data))
    policies = {}

    def build(resolved):
        for a in resolved.spec.cognition.agents:
            policies[a.agent_id] = LLMPolicy(
                a.agent_id,
                FakeProvider(lambda p, i, a=a: malformed if a.agent_id == "a1"
                             and malformed is not None else good,
                             fail_at=fail_at if a.agent_id == agent else None),
                resolved.skin, max_retries=2,
            )
        return policies

    monkeypatch.setattr(study, "build_policies", build)
    result, = study.run_study(directory, tmp_path / "runs")
    run_dir, = find_run_dirs(tmp_path / "runs")
    return run_dir, result, policies


def _no_provider(*args, **kwargs):
    pytest.fail("replay must not call any provider or LLM policy")


def _assert_replay(run_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(FakeProvider, "complete", _no_provider)
    monkeypatch.setattr(LLMPolicy, "propose", _no_provider)
    # Replay must use only the ledger and frozen scenario/manifest.
    (run_dir / "llm_transcript.jsonl").unlink(missing_ok=True)
    shutil.rmtree(run_dir / "checkpoints")
    before = {p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
    saved = tmp_path / "saved"
    report = replay_run(run_dir, keep_dir=saved)
    assert report.chains_match, report.detail
    assert report.original_events == report.replayed_events
    original, _, manifest = load_run(run_dir)
    replayed = FileEventStore(saved / "replay" / "events.jsonl").load_all(verify=True)
    assert [e.hashed_view() for e in original] == [e.hashed_view() for e in replayed]
    assert replayed[-1] == original[-1]
    assert all(manifest[key] is None for key in ("input_tokens", "output_tokens", "cost_usd"))
    assert before == {p.relative_to(run_dir): p.read_bytes()
                      for p in run_dir.rglob("*") if p.is_file()}
    cli = CliRunner().invoke(app, ["replay", str(run_dir)])
    assert cli.exit_code == 0, cli.output
    assert json.loads(cli.stdout)["chains_match"] is True


@pytest.mark.parametrize("paired", [False, True])
@pytest.mark.parametrize("agent", ["a1", "a2", "a3"])
@pytest.mark.parametrize("fail_at", [0, 2])
def test_provider_failure_replays_exact_chain_and_seal(tmp_path, monkeypatch,
                                                      paired, agent, fail_at):
    run_dir, result, policies = _run(tmp_path, monkeypatch, agent=agent,
                                     fail_at=fail_at, paired=paired)
    assert result.status == "failed"
    assert result.rounds_played == fail_at
    assert result.failure_reason == (
        f"policy error for {agent}: ProviderError: simulated provider outage at call {fail_at}"
    )
    assert policies[agent].provider.calls == fail_at + 1
    _assert_replay(run_dir, tmp_path, monkeypatch)


@pytest.mark.parametrize("agent,message", [
    ("a", "alias: ProviderError: outage"),
    ("a: ProviderError: alias", "outage"),
])
@pytest.mark.parametrize("fail_at", [0, 2])
def test_provider_failure_uses_proposal_boundary_for_prefix_ids(
    tmp_path, monkeypatch, agent, message, fail_at,
):
    directory = tmp_path / "study"
    evidence = (ec_item("e1", "src", "s1", "p1a", "supports"),)
    spec = ec_spec(evidence, rounds=4, agents=(
        ("a: ProviderError: alias", "ec_contributor"), ("a", "ec_contributor"),
    ))
    write_study(directory, study_id="prefix-ids", seed=17, checkpoint_every=1,
                conditions=[("cell", spec, plain_skin())])

    def reply(prompt, index):
        if index >= fail_at:
            raise ProviderError(message)
        return GOOD

    def build(resolved):
        return {
            a.agent_id: LLMPolicy(
                a.agent_id,
                FakeProvider(reply if a.agent_id == agent else [GOOD] * 4), resolved.skin,
            )
            for a in resolved.spec.cognition.agents
        }

    monkeypatch.setattr(study, "build_policies", build)
    result, = study.run_study(directory, tmp_path / "runs")
    run_dir, = find_run_dirs(tmp_path / "runs")
    assert result.status == "failed" and result.rounds_played == fail_at
    # Both agents produce identical seal text; only the proposal boundary differs.
    assert result.failure_reason == (
        "policy error for a: ProviderError: alias: ProviderError: outage"
    )
    _assert_replay(run_dir, tmp_path, monkeypatch)


@pytest.mark.parametrize("malformed", ["garbage", '{"action":{"type":"teleport"}}'])
@pytest.mark.parametrize("fail_at", [None, 2])
def test_retry_exhaustion_replays_with_or_without_provider_failure(
    tmp_path, monkeypatch, malformed, fail_at,
):
    run_dir, result, policies = _run(tmp_path, monkeypatch, malformed=malformed, fail_at=fail_at)
    assert result.status == ("completed" if fail_at is None else "failed")
    events, _, _ = load_run(run_dir)
    abstentions = [e for e in events if e.event_type == EventType.ACTION_PROPOSED
                  and e.actor == "a1"]
    assert len(abstentions) == (4 if fail_at is None else 3)
    assert policies["a1"].provider.calls == len(abstentions) * 3
    assert all(e.payload["proposal"]["action"]["reason"] == "invalid_llm_output"
               for e in abstentions)
    _assert_replay(run_dir, tmp_path, monkeypatch)


def test_provider_failure_during_retry_replays(tmp_path, monkeypatch):
    run_dir, result, policies = _run(tmp_path, monkeypatch, agent="a1",
                                     fail_at=1, malformed="garbage")
    assert result.status == "failed" and result.rounds_played == 0
    assert policies["a1"].provider.calls == 2
    assert len(policies["a1"].transcript) == 1
    _assert_replay(run_dir, tmp_path, monkeypatch)


@pytest.mark.parametrize("invalid_action_policy", ["fail", "abstain"])
def test_illegal_action_path_stays_distinct(tmp_path, monkeypatch, invalid_action_policy):
    run_dir, result, _ = _run(tmp_path, monkeypatch, fail_at=None, good=ILLEGAL,
                              invalid_action_policy=invalid_action_policy)
    assert result.status == ("failed" if invalid_action_policy == "fail" else "completed")
    events, _, _ = load_run(run_dir)
    assert any(e.event_type == EventType.ACTION_REJECTED for e in events)
    _assert_replay(run_dir, tmp_path, monkeypatch)


def test_failed_branch_replays_without_parent(tmp_path, monkeypatch):
    parent, _, policies = _run(tmp_path, monkeypatch, fail_at=2)
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    child = tmp_path / "child"
    # Rebuild the provider policies at the branch boundary, with a later outage.
    overrides = {a: LLMPolicy(a, FakeProvider([GOOD] * 20, fail_at=1 if a == "a3" else None),
                             p.skin) for a, p in policies.items()}
    result, _ = branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
                          child_run_id="failed-child", policy_overrides=overrides)
    assert result.status == "failed" and "a3: ProviderError" in result.failure_reason
    shutil.rmtree(parent)
    _assert_replay(child, tmp_path, monkeypatch)


def _rewrite(run_dir, events):
    """Rehash and repin mutations, so hash-integrity checks alone cannot catch them."""
    parent_hash = GENESIS_HASH
    sealed = []
    for seq, event in enumerate(events):
        draft = event.model_copy(update={"seq": seq, "parent_hash": parent_hash})
        rehashed = draft.model_copy(update={"event_hash": draft.compute_hash()})
        sealed.append(rehashed)
        parent_hash = rehashed.event_hash
    RunPaths(run_dir).events.write_text(
        "".join(e.model_dump_json() + "\n" for e in sealed), encoding="utf-8"
    )
    path = RunPaths(run_dir).manifest
    manifest = json.loads(path.read_text())
    manifest.update(status="failed", event_count=len(sealed),
                    final_event_hash=sealed[-1].event_hash,
                    failure_reason=sealed[-1].payload["reason"])
    path.write_text(json.dumps(manifest))
    FileEventStore(RunPaths(run_dir).events).load_all(verify=True)


@pytest.mark.parametrize("mutation", ["earlier_agent", "later_agent", "unknown_agent",
                                     "round", "state", "type", "missing_observation",
                                     "missing_proposal", "illegal_proposal"])
def test_inconsistent_recorded_provider_failure_fails_closed(tmp_path, monkeypatch, mutation):
    run_dir, _, _ = _run(tmp_path, monkeypatch)
    events, _, _ = load_run(run_dir)
    seal = events[-1]
    payload = dict(seal.payload)
    if mutation.endswith("agent"):
        target = {"earlier_agent": "a1", "later_agent": "a3", "unknown_agent": "unknown"}
        payload["reason"] = payload["reason"].replace("for a2:", f"for {target[mutation]}:")
    elif mutation == "round":
        seal = seal.model_copy(update={"logical_time": seal.logical_time + 1})
    elif mutation == "state":
        payload["final_state_hash"] = "0" * 64
    elif mutation == "type":
        payload["reason"] = payload["reason"].replace("ProviderError:", "KeyError:")
    elif mutation in {"missing_observation", "missing_proposal"}:
        kind = (EventType.OBSERVATION_ISSUED if mutation == "missing_observation"
                else EventType.ACTION_PROPOSED)
        index = next(i for i, e in enumerate(events) if e.event_type == kind)
        del events[index]
    else:
        index = next(i for i, e in enumerate(events) if e.event_type == EventType.ACTION_PROPOSED)
        proposal = dict(events[index].payload)
        proposal["proposal"] = json.loads(ILLEGAL)
        events[index] = events[index].model_copy(update={"payload": proposal})
    events[-1] = seal.model_copy(update={"payload": payload})
    _rewrite(run_dir, events)
    monkeypatch.setattr(FakeProvider, "complete", _no_provider)
    cli = CliRunner().invoke(app, ["replay", str(run_dir)])
    assert cli.exit_code == 2, cli.output
    assert "recorded provider failure" in cli.output or "recorded failure" in cli.output
    assert "Traceback" not in cli.output


def test_provider_failure_cannot_replace_engine_completion(tmp_path, monkeypatch):
    run_dir, result, _ = _run(tmp_path, monkeypatch, fail_at=None)
    assert result.status == "completed"
    events, _, _ = load_run(run_dir)
    events[-1] = events[-1].model_copy(update={
        "event_type": EventType.RUN_FAILED,
        "payload": {"reason": "policy error for a2: ProviderError: forged terminal failure",
                    "final_state_hash": events[-1].payload["final_state_hash"]},
    })
    _rewrite(run_dir, events)
    monkeypatch.setattr(FakeProvider, "complete", _no_provider)
    report = replay_run(run_dir)
    assert not report.chains_match
    assert report.first_divergence_seq == len(events) - 1
    assert "recorded failure inconsistent" in report.detail
    assert "RunCompleted" in report.detail
