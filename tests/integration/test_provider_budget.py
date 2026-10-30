"""Request-attempt admission, planning and continuation scope over a mocked HTTP boundary.

No test here opens a socket: ``wire`` replaces the opener and fails on a real connection.
"""

# ruff: noqa: F811  (the imported ``wire`` fixture is re-requested as a test argument)
import io
import itertools
import json
import urllib.error

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.llm import RequestBudget, build_openai_compatible_policy
from collaborative_hill.cli import app
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.replay import replay_run
from collaborative_hill.engine.store import FileCheckpointStore
from collaborative_hill.experiments.manifests import RunManifest
from collaborative_hill.experiments.scenario import NarrativeSkin
from collaborative_hill.experiments.study import run_study, validate_study

from .test_provider_workflow import (  # noqa: F401 (wire is a pytest fixture)
    PARAMS,
    SECRET,
    response,
    wire,
    write_study,
)

EPISODE, RUN = "request_attempt_limit_episode", "request_attempt_limit_run"


def execute(tmp_path, wire, budget, *, params=None, replies=(), replicates=None):
    study = tmp_path / "study"
    if not study.exists():
        write_study(study, params=params)
    wire[0].extend(replies)
    results = run_study(study, tmp_path / "runs", allow_provider_requests=True,
                        replicates_override=replicates, request_budget=budget)
    runs = sorted((tmp_path / "runs").glob("**/manifest.json"))
    return results, [json.loads(path.read_text()) for path in runs], [p.parent for p in runs]


def too_many(code):
    return urllib.error.HTTPError(PARAMS["endpoint"], code, SECRET, {}, io.BytesIO(b""))


def test_exhaustion_before_the_first_request_sends_nothing_and_seals_run_failed(tmp_path, wire):
    results, (manifest,), (run_dir,) = execute(
        tmp_path, wire, RequestBudget(max_episode_attempts=0))
    assert results[0].status == "failed"
    assert EPISODE in results[0].failure_reason
    assert wire[1] == []
    budget = manifest["request_budget"]
    assert budget["stop_reason"] == EPISODE
    assert budget["admitted"] == {"episode": 0, "run": 0}
    assert budget["limits"] == {"episode": 0, "run": None, "deadline_seconds": None}
    assert manifest["provider_usage"]["a1"]["request_attempts"] == 0
    assert manifest["input_tokens"] is manifest["output_tokens"] is manifest["cost_usd"] is None
    assert replay_run(run_dir).chains_match


def test_repair_and_429_retries_all_draw_on_one_episode_budget(tmp_path, wire, monkeypatch):
    sleeps = []
    monkeypatch.setattr("time.sleep", sleeps.append)
    params = {**PARAMS, "max_retries": 1, "rate_limit_retries": 1, "retry_delay_seconds": 2}
    # round 0: 429, invalid JSON (attempt 2), repair (attempt 3); round 1 is refused.
    results, (manifest,), _ = execute(
        tmp_path, wire, RequestBudget(max_episode_attempts=3), params=params,
        replies=[too_many(429), response("not json"), response()])
    assert results[0].status == "failed"
    assert len(wire[1]) == 3
    assert sleeps == [2]
    assert manifest["request_budget"]["admitted"]["episode"] == 3
    assert manifest["request_budget"]["stop_reason"] == EPISODE
    assert manifest["provider_usage"]["a1"]["request_attempts"] == 3
    assert manifest["provider_usage"]["a1"]["completion_calls"] == 3


def test_429_with_unknown_usage_stops_before_the_retry_and_its_sleep(tmp_path, wire, monkeypatch):
    sleeps = []
    monkeypatch.setattr("time.sleep", sleeps.append)
    params = {**PARAMS, "rate_limit_retries": 1, "retry_delay_seconds": 1}
    results, (manifest,), _ = execute(
        tmp_path, wire, RequestBudget(max_episode_attempts=1), params=params,
        replies=[too_many(429)])
    assert results[0].status == "failed"
    assert len(wire[1]) == 1 and sleeps == []
    usage = manifest["provider_usage"]["a1"]
    assert (usage["request_attempts"], usage["input_measured_attempts"]) == (1, 0)
    assert manifest["input_tokens"] is manifest["output_tokens"] is None
    assert manifest["request_budget"]["admitted"]["episode"] == 1


def test_partial_measurements_stay_partial_when_the_budget_stops_the_episode(tmp_path, wire):
    _, (manifest,), _ = execute(
        tmp_path, wire, RequestBudget(max_episode_attempts=2),
        replies=[response(), response(usage=False)])
    usage = manifest["provider_usage"]["a1"]
    assert (usage["request_attempts"], usage["known_input_tokens"],
            usage["input_measured_attempts"]) == (2, 17, 1)
    assert manifest["input_tokens"] is manifest["output_tokens"] is None
    assert manifest["cost_usd"] is None
    assert manifest["status"] == "failed"


def test_late_response_is_kept_and_only_the_next_request_is_refused(tmp_path, wire):
    ticks = itertools.count(0, 6)  # construction=0 (deadline 10), admissions at 6, 12, ...
    budget = RequestBudget(deadline_seconds=10, clock=lambda: float(next(ticks)))
    results, (manifest,), _ = execute(tmp_path, wire, budget, replies=[response()])
    assert results[0].status == "failed"
    assert len(wire[1]) == 1
    assert manifest["request_budget"]["stop_reason"] == "deadline_exceeded"
    assert manifest["request_budget"]["deadline_check"] == "between_requests_monotonic"
    assert manifest["input_tokens"] == 17  # the admitted request's measured usage survives


def test_timeout_counts_as_spent_and_a_later_episode_is_refused_not_started(tmp_path, wire):
    ticks = itertools.count(0, 6)
    budget = RequestBudget(deadline_seconds=10, clock=lambda: float(next(ticks)))
    results, manifests, _ = execute(tmp_path, wire, budget, replicates=2,
                                    replies=[TimeoutError(SECRET)])
    first, second = manifests
    assert [r.status for r in results] == ["failed", "failed"]
    assert first["request_budget"]["admitted"] == {"episode": 1, "run": 1}
    assert first["request_budget"]["stop_reason"] is None  # the transport failed, not the budget
    assert first["provider_usage"]["a1"]["request_attempts"] == 1
    assert second["request_budget"]["stop_reason"] == "deadline_exceeded"
    assert second["request_budget"]["admitted_before"] == {"episode": 0, "run": 1}
    assert len(wire[1]) == 1


def test_run_limit_propagates_to_later_episodes_without_resetting(tmp_path, wire):
    results, (first, second), _ = execute(
        tmp_path, wire, RequestBudget(max_run_attempts=3), replicates=2,
        replies=[response()] * 3)
    assert [r.status for r in results] == ["completed", "failed"]
    assert len(wire[1]) == 3
    assert first["request_budget"]["admitted"] == {"episode": 3, "run": 3}
    assert first["request_budget"]["stop_reason"] is None
    assert second["request_budget"]["stop_reason"] == RUN
    assert second["request_budget"]["admitted_before"] == {"episode": 0, "run": 3}
    assert RUN in results[1].failure_reason


def test_cancellation_is_checked_between_requests(tmp_path, wire):
    cancelled = []
    budget = RequestBudget(cancelled=lambda: bool(cancelled))
    # Cancel as soon as the first request is admitted.
    original = budget.admit

    def admit_then_cancel(**kwargs):
        original(**kwargs)
        cancelled.append(True)

    budget.admit = admit_then_cancel
    results, (manifest,), _ = execute(tmp_path, wire, budget, replies=[response()] * 2)
    assert results[0].status == "failed"
    assert manifest["request_budget"]["stop_reason"] == "cancelled"
    assert len(wire[1]) == 1


def test_deadline_that_the_retry_delay_would_pass_refuses_the_retry_before_sleeping(
        tmp_path, wire, monkeypatch):
    sleeps = []
    monkeypatch.setattr("time.sleep", sleeps.append)
    params = {**PARAMS, "rate_limit_retries": 1, "retry_delay_seconds": 10}
    budget = RequestBudget(deadline_seconds=5, clock=lambda: 0.0)
    # deadline 5 > now 0, so the first POST is admitted; a 10 s delay would pass it.
    results, (manifest,), _ = execute(tmp_path, wire, budget, params=params,
                                      replies=[too_many(429)])
    assert results[0].status == "failed" and sleeps == [] and len(wire[1]) == 1
    assert manifest["request_budget"]["stop_reason"] == "deadline_exceeded"


def test_budget_never_enters_hashes_ledgers_or_policy_identity(tmp_path, wire):
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
    big = RequestBudget(max_run_attempts=99, max_episode_attempts=99, deadline_seconds=3600)
    plain = execute(tmp_path / "a", wire, None, replies=[response()] * 3)
    limited = execute(tmp_path / "b", wire, big, replies=[response()] * 3)
    (left,), (right,) = plain[1], limited[1]
    assert left["request_budget"] is None
    assert right["request_budget"]["admitted"] == {"episode": 3, "run": 3}
    for key in ("scenario_hash", "mechanism_hash", "narrative_hash", "study_hash", "policies",
                "final_event_hash", "event_count", "provider_usage", "input_tokens"):
        assert left[key] == right[key], key


def test_budget_does_not_waive_the_explicit_request_opt_in(tmp_path, wire):
    study = tmp_path / "study"
    write_study(study)
    with pytest.raises(ValueError, match="allow_provider_requests=True"):
        run_study(study, tmp_path / "runs", request_budget=RequestBudget(max_run_attempts=9))
    assert not (tmp_path / "runs").exists() and wire[1] == []


def test_continuation_keeps_charging_the_same_budget(tmp_path, wire):
    budget = RequestBudget(max_run_attempts=4)
    _, (parent_manifest,), (parent,) = execute(
        tmp_path, wire, budget, replies=[response()] * 3)
    assert parent_manifest["request_budget"]["admitted"] == {"episode": 3, "run": 3}
    fork = FileCheckpointStore(parent / "checkpoints").list_seqs()[0]
    policy = build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), PARAMS,
                                            budget=budget)
    wire[0].extend([response()] * 2)
    result, _ = branch_run(parent_dir=parent, fork_seq=fork, child_dir=tmp_path / "child",
                           child_run_id="child", policy_overrides={"a1": policy},
                           allow_provider_requests=True, request_budget=budget)
    child = json.loads((tmp_path / "child" / "manifest.json").read_text())
    assert result.status == "failed" and RUN in result.failure_reason
    record = child["request_budget"]
    assert (record["scope"], record["stop_reason"]) == ("continuation", RUN)
    assert record["admitted_before"] == {"episode": 3, "run": 3}
    assert record["admitted"] == {"episode": 4, "run": 4}
    assert child["provider_usage_scope"] == "continuation"
    assert child["provider_usage"]["a1"]["request_attempts"] == 1
    assert len(wire[1]) == 4
    assert replay_run(tmp_path / "child").chains_match


def test_branch_refuses_a_network_policy_that_does_not_share_the_budget(tmp_path, wire):
    _, _, (parent,) = execute(tmp_path, wire, None, replies=[response()] * 3)
    fork = FileCheckpointStore(parent / "checkpoints").list_seqs()[0]
    stray = build_openai_compatible_policy("a1", NarrativeSkin(skin_id="plain"), PARAMS)
    with pytest.raises(ValueError, match="share the continuation's request_budget"):
        branch_run(parent_dir=parent, fork_seq=fork, child_dir=tmp_path / "child",
                   child_run_id="child", policy_overrides={"a1": stray},
                   allow_provider_requests=True, request_budget=RequestBudget(max_run_attempts=9))
    assert not (tmp_path / "child").exists()


def test_scripted_child_of_a_budgeted_parent_does_not_inherit_its_budget(tmp_path, wire):
    from collaborative_hill.agents.scripted.ec_policies import ECFreeriderPolicy

    _, _, (parent,) = execute(tmp_path, wire, RequestBudget(max_run_attempts=9),
                              replies=[response()] * 3)
    fork = FileCheckpointStore(parent / "checkpoints").list_seqs()[0]
    branch_run(parent_dir=parent, fork_seq=fork, child_dir=tmp_path / "child",
               child_run_id="child", policy_overrides={"a1": ECFreeriderPolicy()})
    assert "request_budget" not in json.loads((tmp_path / "child" / "manifest.json").read_text())


@pytest.mark.parametrize("bad", [-1, True, 1.5, "3"])
def test_budget_settings_are_nonnegative_integers(bad):
    for name in ("max_episode_attempts", "max_run_attempts", "deadline_seconds"):
        with pytest.raises(ValueError, match="nonnegative integer"):
            RequestBudget(**{name: bad})


def test_unconfigured_budget_is_unlimited_and_manifest_field_is_optional():
    budget = RequestBudget()
    for _ in range(1000):
        budget.admit()
    assert budget.snapshot()["limits"] == {"episode": None, "run": None,
                                           "deadline_seconds": None}
    assert RunManifest.model_fields["request_budget"].default is None


def test_plan_is_offline_separates_repairs_from_429_retries_and_never_reads_credentials(
        tmp_path, wire, monkeypatch):
    study = tmp_path / "study"
    write_study(study, params={**PARAMS, "max_retries": 2, "rate_limit_retries": 1})
    monkeypatch.delenv("CHL_WORKFLOW_TEST_TOKEN")
    cli = CliRunner().invoke(app, ["study", "plan", str(study), "--replicates", "2",
                                   "--max-episode-request-attempts", "17",
                                   "--max-run-request-attempts", "36"])
    assert cli.exit_code == 0, cli.output
    plan = json.loads(cli.output)
    episode = plan["conditions"]["c"]
    assert episode["rounds"] == 3
    assert episode["max_logical_completions"] == 9  # 3 rounds x (1 + 2 repairs)
    assert episode["max_action_repair_completions"] == 6
    assert episode["max_rate_limit_retry_attempts"] == 9
    assert episode["max_http_request_attempts"] == 18
    assert episode["requested_output_token_ceiling"] == 18 * 64
    assert plan["selection"]["max_http_request_attempts"] == 36
    assert plan["limits"]["worst_case_exceeds_episode_limit"] is True
    assert plan["limits"]["worst_case_exceeds_run_limit"] is False
    assert plan["offline"] is True
    assert wire[1] == [] and not (tmp_path / "runs").exists()
    assert validate_study(study)["frozen"] is False  # planning wrote nothing to the study


def test_plan_without_limits_reports_no_comparison_and_rejects_bad_selection(tmp_path, wire):
    study = tmp_path / "study"
    write_study(study)
    plan = json.loads(CliRunner().invoke(app, ["study", "plan", str(study)]).output)
    assert plan["limits"] == {"episode": None, "run": None,
                              "worst_case_exceeds_episode_limit": None,
                              "worst_case_exceeds_run_limit": None}
    assert plan["conditions"]["c"]["llm_agents"]["a1"]["network"] is True
    bad = CliRunner().invoke(app, ["study", "plan", str(study), "--condition", "nope"])
    assert bad.exit_code == 2


def test_cli_budget_flags_stop_the_run_with_a_stable_reason(tmp_path, wire):
    study = tmp_path / "study"
    write_study(study)
    result = CliRunner().invoke(app, [
        "run", str(study), "--artifacts", str(tmp_path / "runs"), "--allow-provider-requests",
        "--max-run-request-attempts", "0"])
    assert result.exit_code == 2
    assert RUN in result.output
    assert wire[1] == []
    manifest = json.loads(next((tmp_path / "runs").glob("**/manifest.json")).read_text())
    assert manifest["request_budget"]["limits"]["run"] == 0
