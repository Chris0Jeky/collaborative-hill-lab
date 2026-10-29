"""Study/CLI/replay/branch paths over a mocked HTTP boundary; no live calls."""

import io
import json
import socket
import urllib.error
import urllib.request

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.llm import build_openai_compatible_policy
from collaborative_hill.agents.scripted.ec_policies import ECFreeriderPolicy
from collaborative_hill.cli import app
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.store import FileCheckpointStore
from collaborative_hill.experiments.scenario import NarrativeSkin
from collaborative_hill.experiments.study import run_study, validate_study

SECRET = "workflow-fixture-credential-never-persist"
PARAMS = {"endpoint": "https://provider.invalid/v1/chat/completions",
          "model_id": "requested-model", "max_completion_tokens": 64,
          "temperature": "0", "api_key_env": "CHL_WORKFLOW_TEST_TOKEN"}
GOOD = '{"action":{"type":"abstain"}}'


def response(text=GOOD, *, usage=True, refusal=None):
    return {"model": "reported-version", "choices": [{"finish_reason": "stop",
            "message": {"role": "assistant", "content": text, "refusal": refusal}}],
            "usage": {"prompt_tokens": 17, "completion_tokens": 3} if usage else None}


@pytest.fixture
def wire(monkeypatch):
    responses, requests = [], []

    class Response(io.BytesIO):
        status = 200

    def open_request(opener, request, *, timeout):
        del opener, timeout
        requests.append(request)
        assert responses, "unexpected extra HTTP request"
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return Response(json.dumps(item).encode())

    def no_network(*args, **kwargs):
        pytest.fail("workflow test attempted a real socket connection")

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", open_request)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setenv("CHL_WORKFLOW_TEST_TOKEN", SECRET)
    return responses, requests


def write_study(path, *, params=None, rounds=3):
    path.mkdir()
    scenario = {
        "scenario_id": "provider-workflow",
        "world": {"kind": "evidence_commons", "slots": {"s": ["true", "false"]},
                  "true_propositions": {"s": "true"}, "params": {"rounds": rounds}},
        "information": {"evidence": [{
            "evidence_id": "e", "source_id": "source", "slot_id": "s",
            "proposition_id": "true", "stance": "supports", "truth_aligned": True,
            "initial_holders": ["a1"],
        }]},
        "interaction": {"structure": "commons"},
        "cognition": {"agents": [
            {"agent_id": "a1", "policy": {"name": "llm_openai_compatible",
                                             "params": params or PARAMS}},
            {"agent_id": "a2", "policy": {"name": "ec_freerider"}},
        ]},
    }
    (path / "scenario.json").write_text(json.dumps(scenario), encoding="utf-8")
    (path / "skin.json").write_text('{"skin_id":"plain"}', encoding="utf-8")
    (path / "study.json").write_text(json.dumps({
        "study_id": "provider-workflow", "seed": 7, "checkpoint_every": 1,
        "conditions": [{"condition_id": "c", "scenario": "scenario.json", "skin": "skin.json"}],
    }), encoding="utf-8")


def run_fixture(tmp_path, wire, *, params=None, responses=None):
    study = tmp_path / "study"
    write_study(study, params=params)
    wire[0].extend(responses if responses is not None else [response()] * 3)
    results = run_study(study, tmp_path / "runs", allow_provider_requests=True)
    run_dir = next((tmp_path / "runs").glob("**/manifest.json")).parent
    return results[0], run_dir, json.loads((run_dir / "manifest.json").read_text())


def assert_no_secret(root):
    for path in root.rglob("*"):
        if path.is_file():
            assert SECRET.encode() not in path.read_bytes(), path


def test_validation_is_offline_and_execution_needs_explicit_opt_in(tmp_path, wire, monkeypatch):
    study = tmp_path / "study"
    write_study(study)
    monkeypatch.delenv("CHL_WORKFLOW_TEST_TOKEN")
    assert validate_study(study)["frozen"] is False
    with pytest.raises(ValueError, match="allow_provider_requests=True"):
        run_study(study, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()
    cli = CliRunner().invoke(app, ["run", str(study), "--artifacts", str(tmp_path / "cli")])
    assert cli.exit_code == 2
    assert "--allow-provider-requests" in cli.output
    assert not (tmp_path / "cli").exists()
    assert wire[1] == []


def test_missing_credentials_fail_before_output_or_requests(tmp_path, wire, monkeypatch):
    study = tmp_path / "study"
    write_study(study)
    monkeypatch.delenv("CHL_WORKFLOW_TEST_TOKEN")
    with pytest.raises(ValueError, match="credential environment variable is unavailable"):
        run_study(study, tmp_path / "runs", allow_provider_requests=True)
    assert wire[1] == []
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("invalid", [{"api_key": SECRET},
    {"endpoint": f"https://user:{SECRET}@provider.invalid/chat"},
])
def test_rejected_credentials_do_not_appear_in_cli_diagnostics(tmp_path, wire, invalid):
    study = tmp_path / "study"
    write_study(study, params={**PARAMS, **invalid})
    cli = CliRunner().invoke(app, ["run", str(study), "--allow-provider-requests"])
    assert cli.exit_code == 2
    assert SECRET not in cli.output
    assert wire[1] == []


def test_run_records_actual_usage_and_replay_needs_no_credentials(tmp_path, wire, monkeypatch):
    result, run_dir, manifest = run_fixture(tmp_path, wire)
    assert result.status == "completed"
    assert (manifest["input_tokens"], manifest["output_tokens"],
            manifest["cost_usd"]) == (51, 9, None)
    assert manifest["providers"] == {"a1": "requested-model"}
    assert manifest["reported_models"] == {"a1": ["reported-version"]}
    assert manifest["sampling"]["a1"] == {"max_completion_tokens": 64, "temperature": "0"}
    assert manifest["provider_usage"]["a1"]["request_attempts"] == 3
    assert manifest["provider_usage_scope"] == "episode"
    transcript = (run_dir / "llm_transcript.jsonl").read_text().splitlines()
    assert len(transcript) == 3
    assert all(json.loads(row)["input_tokens"] == 17 for row in transcript)
    monkeypatch.delenv("CHL_WORKFLOW_TEST_TOKEN")
    assert replay_run(run_dir).chains_match
    assert len(wire[1]) == 3
    assert_no_secret(tmp_path / "runs")


@pytest.mark.parametrize("replies,params,expected_status,attempts,tokens", [
    ([response(), response(usage=False), response()], None, "completed", 3, None),
    ([response("bad json"), response(), response(), response()],
     {**PARAMS, "max_retries": 1}, "completed", 4, 68),
    ([response(), response(refusal="fixture refusal")], None, "failed", 2, 34),
    ([response(), TimeoutError(SECRET)], None, "failed", 2, None),
])
def test_usage_covers_invalid_failed_and_unmeasured_calls(
        tmp_path, wire, replies, params, expected_status, attempts, tokens):
    result, run_dir, manifest = run_fixture(tmp_path, wire, params=params, responses=replies)
    assert result.status == expected_status
    assert manifest["provider_usage"]["a1"]["request_attempts"] == attempts
    assert manifest["input_tokens"] == tokens
    assert manifest["cost_usd"] is None
    assert replay_run(run_dir).chains_match
    assert len(wire[1]) == attempts
    assert_no_secret(tmp_path / "runs")


def test_rate_limit_retry_does_not_turn_partial_usage_into_a_total(tmp_path, wire):
    error = urllib.error.HTTPError(PARAMS["endpoint"], 429, SECRET, {}, io.BytesIO(b""))
    _, run_dir, manifest = run_fixture(
        tmp_path, wire, params={**PARAMS, "rate_limit_retries": 1, "retry_delay_seconds": 0},
        responses=[error, response(), response(), response()],
    )
    assert manifest["input_tokens"] is manifest["output_tokens"] is None
    assert manifest["provider_usage"]["a1"]["known_input_tokens"] == 51
    assert manifest["provider_usage"]["a1"]["request_attempts"] == 4
    assert manifest["provider_usage"]["a1"]["completion_calls"] == 3
    assert replay_run(run_dir).chains_match


def test_network_parent_can_branch_offline_with_scripted_replacement(tmp_path, wire, monkeypatch):
    _, parent, parent_manifest = run_fixture(tmp_path, wire)
    fork = FileCheckpointStore(parent / "checkpoints").list_seqs()[0]
    monkeypatch.delenv("CHL_WORKFLOW_TEST_TOKEN")
    with pytest.raises(ValueError, match="allow_provider_requests=True"):
        branch_run(parent_dir=parent, fork_seq=fork, child_dir=tmp_path / "denied",
                   child_run_id="denied", policy_overrides={})
    assert not (tmp_path / "denied").exists()
    child = tmp_path / "scripted-child"
    result, _ = branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
                          child_run_id="scripted-child",
                          policy_overrides={"a1": ECFreeriderPolicy()})
    assert result.status == "completed"
    manifest = json.loads((child / "manifest.json").read_text())
    assert manifest["providers"] == manifest["provider_metadata"] == manifest["sampling"] == {}
    assert manifest["reported_models"] == manifest["provider_usage"] == {}
    assert manifest["input_tokens"] is manifest["output_tokens"] is manifest["cost_usd"] is None
    assert manifest["provider_usage_scope"] is None
    assert parent_manifest["input_tokens"] == 51
    assert not (child / "llm_transcript.jsonl").exists()
    assert replay_run(child).chains_match
    assert len(wire[1]) == 3


def test_reused_override_usage_and_transcript_include_only_continuation(tmp_path, wire):
    _, parent, _ = run_fixture(tmp_path, wire)
    fork = FileCheckpointStore(parent / "checkpoints").list_seqs()[0]
    _, resolved, _ = load_run(parent)
    policy = build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), PARAMS)
    wire[0].extend([response()] * 3)
    # Earlier use of the same object is not usage of this future branch.
    mechanism = resolved.build_mechanism()
    policy.propose(mechanism.observe(mechanism.initial_state(), "a1"), None)
    with pytest.raises(ValueError, match="allow_provider_requests=True"):
        branch_run(parent_dir=parent, fork_seq=fork, child_dir=tmp_path / "denied-override",
                   child_run_id="denied-override", policy_overrides={"a1": policy})
    assert not (tmp_path / "denied-override").exists()
    child = tmp_path / "provider-child"
    result, _ = branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
                          child_run_id="provider-child", policy_overrides={"a1": policy},
                          allow_provider_requests=True)
    assert result.status == "completed"
    manifest = json.loads((child / "manifest.json").read_text())
    assert (manifest["input_tokens"], manifest["output_tokens"]) == (34, 6)
    assert manifest["provider_usage"]["a1"]["completion_calls"] == 2
    assert manifest["provider_usage_scope"] == "continuation"
    rows = [json.loads(row) for row in (child / "llm_transcript.jsonl").read_text().splitlines()]
    assert [row["round"] for row in rows] == [1, 2]
    assert replay_run(child).chains_match
    assert len(wire[1]) == 6
    assert_no_secret(child)


def test_branch_execution_provenance_describes_current_code_and_time(tmp_path, wire, monkeypatch):
    _, parent, _ = run_fixture(tmp_path, wire)
    fork = FileCheckpointStore(parent / "checkpoints").list_seqs()[0]
    manifest_path = parent / "manifest.json"
    old = json.loads(manifest_path.read_text())
    old.update(code_commit="historical-code", started_at="2000-01-01T00:00:00+00:00",
               ended_at="2000-01-01T00:01:00+00:00", pricing_table_version="old-price",
               pricing_table_date="2000-01-01")
    manifest_path.write_text(json.dumps(old))
    monkeypatch.setattr("collaborative_hill.experiments.manifests.git_provenance",
                        lambda root: ("current-code", False))
    child = tmp_path / "new-provenance"
    branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
               child_run_id="new-provenance", policy_overrides={"a1": ECFreeriderPolicy()})
    new = json.loads((child / "manifest.json").read_text())
    assert new["code_commit"] == "current-code"
    assert new["worktree_dirty"] is False
    assert new["started_at"] > old["ended_at"]
    assert new["ended_at"] >= new["started_at"]
    assert new["pricing_table_version"] is new["pricing_table_date"] is None


def test_cli_explicit_request_flag_executes_mocked_workflow(tmp_path, wire):
    study = tmp_path / "study"
    write_study(study, rounds=1)
    wire[0].append(response())
    result = CliRunner().invoke(app, ["run", str(study), "--artifacts", str(tmp_path / "runs"),
                                     "--allow-provider-requests"])
    assert result.exit_code == 0, result.output
    assert "completed" in result.output
    assert len(wire[1]) == 1
