"""The lab console shows sealed behaviour faithfully and never hides a broken ledger."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.scripted.nipd_policies import AllCPolicy, AllDPolicy
from collaborative_hill.cli import app
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import Event, EventType
from collaborative_hill.engine.replay import load_run
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths
from collaborative_hill.experiments.study import run_study
from collaborative_hill.reporting import lab
from collaborative_hill.reporting.inspector import round_frames
from collaborative_hill.reporting.lab import (
    render_html,
    render_text,
    run_trace,
    trace_runs,
    write_console,
)

REPO = Path(__file__).resolve().parents[2]
STUDY_000 = REPO / "studies/000-legacy-reproduction"
STUDY_001 = REPO / "studies/001-evidence-commons"


@pytest.mark.parametrize("fork", [10, "ten"])
def test_root_fork_metadata_cannot_invent_inherited_history(nipd_root, tmp_path, fork):
    source = next(nipd_root.rglob("events.jsonl")).parent
    run = tmp_path / "root-with-stray-fork"
    shutil.copytree(source, run)
    path = run / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert not manifest.get("parent_run")
    manifest["fork_seq"] = fork
    path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    # The existing loader intentionally ignores unused root-manifest extras.
    # A new display must not turn that unbound field into verified ancestry.
    load_run(run)
    before = {str(p.relative_to(run)): p.read_bytes() for p in run.rglob("*") if p.is_file()}
    trace = run_trace(run)
    assert "broken" in trace and "fork_seq" in trace["broken"]
    assert "frames" not in trace
    assert {str(p.relative_to(run)): p.read_bytes()
            for p in run.rglob("*") if p.is_file()} == before


@pytest.fixture(scope="module")
def nipd_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("lab")
    run_study(STUDY_000, root, only_condition="pw-2tft-alld", replicates_override=2)
    run_study(STUDY_000, root, only_condition="nb-2tftthresh-alld", replicates_override=1)
    return root


@pytest.fixture(scope="module")
def ec_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("lab-ec")
    run_study(STUDY_001, root, replicates_override=1)
    return root


def _trace(root: Path, condition: str) -> dict:
    return next(t for t in trace_runs(root) if t["condition_id"] == condition)


def test_hand_checked_strips_for_scripted_populations(nipd_root):
    # Two targeted TFTs cooperate with each other and answer AllD with D after round one,
    # so each is mixed from round two. AllD never cooperates with anyone.
    pairwise = _trace(nipd_root, "pw-2tft-alld")
    a1, a2, defector = pairwise["strips"].values()
    assert defector == "D" * len(defector)
    assert a1 == a2 == "C" + "+" * (len(a1) - 1)
    assert pairwise["cooperation"][0] == 4 / 6
    assert pairwise["cooperation"][1] == 2 / 6

    # A 2/3 quorum tolerates the single defector indefinitely.
    threshold = _trace(nipd_root, "nb-2tftthresh-alld")
    assert list(threshold["strips"].values())[:2] == ["C" * 50, "C" * 50]


def test_ec_strip_comes_from_accepted_actions_and_terminal_seal(ec_root):
    trace = _trace(ec_root, "attr-priv-misinfo")
    assert trace["kind"] == "ec"
    assert set(trace["strips"]) == {"a1", "a2", "a3"}
    assert all(len(strip) == 12 for strip in trace["strips"].values())
    assert "".join(trace["strips"].values()).count("i") > 0
    assert trace["slots"] == 4
    assert 0 <= trace["slots_correct"] <= trace["slots_filled"] <= trace["slots"]


def test_rendering_is_a_pure_function_of_the_ledgers(nipd_root, tmp_path):
    first = tmp_path / "one.html"
    second = tmp_path / "two.html"
    write_console(nipd_root, first)
    write_console(nipd_root, second)
    assert first.read_bytes() == second.read_bytes()
    assert b"pw-2tft-alld" in first.read_bytes()


def test_tampered_and_truncated_ledgers_are_shown_as_broken(nipd_root, tmp_path):
    root = tmp_path / "copy"
    shutil.copytree(nipd_root, root)
    runs = sorted(path.parent for path in root.rglob("events.jsonl"))

    ledger = runs[0] / "events.jsonl"
    ledger.write_text(ledger.read_text(encoding="utf-8").replace('"C"', '"D"', 1),
                      encoding="utf-8")
    assert "broken" in run_trace(runs[0])

    lines = (runs[1] / "events.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    (runs[1] / "events.jsonl").write_text("".join(lines[:-1]), encoding="utf-8")
    assert "broken" in run_trace(runs[1])

    traces = trace_runs(root)
    assert sum("broken" in trace for trace in traces) == 2
    assert render_text(traces).count("BROKEN") == 2
    assert 'class="tile bad"' in render_html(traces)
    result = CliRunner().invoke(app, ["lab", str(root)])
    assert result.exit_code == 1
    assert "BROKEN" in result.output


def test_cli_reports_replay_and_refuses_an_empty_root(nipd_root, tmp_path):
    run = next(nipd_root.rglob("events.jsonl")).parent
    out = tmp_path / "console.html"
    result = CliRunner().invoke(app, ["lab", str(run), "--out", str(out), "--verify-replay"])
    assert result.exit_code == 0, result.output
    assert "replay 1/1 identical" in result.output
    assert "replay identical" in out.read_text(encoding="utf-8")
    assert CliRunner().invoke(app, ["lab", str(tmp_path / "nothing")]).exit_code == 2


def test_html_escapes_ledger_text():
    trace = {"run_id": "<r>", "condition_id": "<c>", "study_id": "<s>", "broken": "<b>"}
    page = render_html([trace])
    assert "<r>" not in page
    assert "<b>" not in page.replace("<b>0</b>", "").replace("<b>1</b>", "").replace("<b></b>", "")
    assert "&lt;r&gt;" in page


def _quick():
    spec = importlib.util.spec_from_file_location("quick", REPO / "scripts/quick.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["quick"] = module
    spec.loader.exec_module(module)
    return module


def test_quick_selects_by_import_closure_and_fails_towards_everything():
    quick = _quick()

    # A reporting leaf reaches its own tests and the CLI, not the kernel suites.
    tests, _, reasons = quick.plan(["src/collaborative_hill/reporting/lab.py"])
    assert not reasons
    assert "tests/integration/test_lab_console.py" in tests
    assert "tests/property/test_event_chain.py" not in tests

    # Kernel change: the hashing module reaches the graph gate through its imports.
    tests, gates, _ = quick.plan(["src/collaborative_hill/engine/hashing.py"])
    assert "check-graph" in gates
    assert len(tests) > 20

    # Data-only change selects its gate and the tests that mention it.
    tests, gates, _ = quick.plan(["experiments/responsive-commons/RESULTS.md"])
    assert gates == ["check-responsive"]
    assert any("responsive" in test for test in tests)

    assert quick.plan(["HANDOFF.md", "docs/adr/0001.md"]) == ([], [], [])
    assert quick.plan(["pyproject.toml"])[0] == ["tests/"]
    assert quick.plan(["some/new/thing.txt"])[0] == ["tests/"]
    assert quick.plan([".github/workflows/ci.yml"])[0] == ["tests/"]

    # Paths nothing can trace select everything rather than printing an empty green.
    assert quick.plan(["src/collaborative_hill/metrics/gone.py"])[0] == ["tests/"]
    assert quick.plan(["tests/integration/golden/analysis_001.json"])[0] == ["tests/"]

    # Relative test helpers reach their importers.
    tests, _, _ = quick.plan(["tests/metamorphic/_helpers.py"])
    assert "tests/metamorphic/test_replay_determinism.py" in tests

    # A study named only through a helper still selects the tests using that helper.
    tests, gates, _ = quick.plan(["studies/000-legacy-reproduction/study.json"])
    assert "validate" in gates
    assert "tests/integration/test_cli_end_to_end.py" in tests


def _event(event_type: EventType, logical_time: int, **payload) -> Event:
    return Event(study_id="s", run_id="r", seq=0, logical_time=logical_time, actor="a1",
                 event_type=event_type, payload=payload, parent_hash="0" * 64, event_hash="0" * 64)


def test_rejection_survives_its_fallback_and_an_unresolved_round():
    events = [_event(EventType.ACTION_ACCEPTED, 0, agent_id="a1",
                     action={"type": "inspect_evidence"}),
              _event(EventType.ACTION_ACCEPTED, 0, agent_id="a2",
                     action={"type": "withhold"}),
              _event(EventType.ACTION_REJECTED, 1, agent_id="a1"),
              _event(EventType.ACTION_ACCEPTED, 1, agent_id="a1", action={"type": "abstain"}),
              _event(EventType.ACTION_REJECTED, 3, agent_id="a2")]
    strips = lab._mark_rejections(lab._ec_strips(events, ["a1", "a2"]), events)
    assert strips == {"a1": "i!··", "a2": "w··!"}
    # A NIPD round rejected before resolution also lengthens the strip.
    assert lab._mark_rejections({"a1": "CC", "a2": "DD"}, events[2:3]) == {"a1": "C!", "a2": "DD"}


def test_unequal_replicates_keep_rounds_aligned():
    rows = [{"cooperation": [1.0, 1.0, 0.0, 0.0]}, {"cooperation": [0.0, 1.0]}]
    assert lab._mean_series(rows) == [0.5, 1.0, 0.0, 0.0]
    assert lab._heat_html(rows).count('class="gap"') == 2


def test_console_rejects_a_relabelled_manifest_and_separates_branches(nipd_root, tmp_path):
    source = next(nipd_root.rglob("events.jsonl")).parent
    run = tmp_path / "copy"
    shutil.copytree(source, run)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    original = dict(manifest["policies"])
    manifest["policies"]["a1"] = "allc@1"
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    assert "policies" in run_trace(run)["broken"]

    manifest["policies"] = original
    manifest.pop("replicate")
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    assert "broken" in run_trace(run)

    manifest["replicate"] = 0
    manifest["parent_run"] = "parent-r000"
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    assert "broken" in run_trace(run)


@pytest.mark.parametrize("shared_default_id", [False, True])
def test_real_branches_show_continuation_policies_without_pooling(
        nipd_root, tmp_path, shared_default_id):
    parent = next(path.parent for path in nipd_root.rglob("events.jsonl")
                  if path.parent.parent.name == "pw-2tft-alld")
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    parent_id = json.loads((parent / "manifest.json").read_text(encoding="utf-8"))["run_id"]
    traces = []
    for name, policy in (("cooperative-child", AllCPolicy("pairwise")),
                         ("defecting-child", AllDPolicy("pairwise"))):
        child = tmp_path / name
        # The CLI's default ID is identical for every branch at this checkpoint;
        # output directories and continuation policies can nevertheless differ.
        child_id = f"{parent_id}-branch{fork}" if shared_default_id else name
        _, branch = branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
                               child_run_id=child_id, policy_overrides={"a1": policy})
        trace = run_trace(child, verify_replay=True)
        assert "broken" not in trace, trace
        assert trace["policies"]["a1"] == policy.policy_id
        assert trace["fork_round"] == branch.fork_round
        assert trace["replay_identical"] is True
        for frame in trace["frames"]:
            records = [event for value in frame.values() if isinstance(value, list)
                       for event in value]
            assert all(event["inherited"] == (event["seq"] <= fork) for event in records)
        if name == "cooperative-child":
            assert trace["strips"]["a1"][branch.fork_round:] == "C" * (50 - branch.fork_round)
        else:
            assert trace["strips"]["a1"][branch.fork_round:] == "D" * (50 - branch.fork_round)
        traces.append(trace)

    assert len(lab._group(traces)) == 2  # Shared histories are not independent replicates.
    assert all(len(rows) == 1 for _, _, rows in lab._group(traces))
    assert all(len(rows) == 1 for _, _, rows in lab._group([traces[0], traces[0]]))
    assert "2/2 sealed" not in render_text(traces)
    assert "continuation" in render_text(traces)
    assert "continuation" in render_html(traces).lower()


def test_branch_display_uses_local_provenance_and_rejects_forged_fork(nipd_root, tmp_path):
    parent = next(path.parent for path in nipd_root.rglob("events.jsonl")
                  if path.parent.parent.name == "pw-2tft-alld")
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    child = tmp_path / "child"
    branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
               child_run_id="child", policy_overrides={"a1": AllCPolicy("pairwise")})
    record_path = child / "branch.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["parent_run_dir"] = str(tmp_path / "unavailable-parent")
    record_path.write_text(json.dumps(record), encoding="utf-8", newline="\n")
    assert "broken" not in run_trace(child)

    record["parent_event_hash_at_fork"] = "0" * 64
    record_path.write_text(json.dumps(record), encoding="utf-8", newline="\n")
    assert "broken" in run_trace(child)


def test_console_rejects_changed_resolved_scenario(nipd_root, tmp_path):
    parent = next(nipd_root.rglob("events.jsonl")).parent
    run = tmp_path / "altered-scenario"
    shutil.copytree(parent, run)
    path = run / "scenario.resolved.json"
    scenario = json.loads(path.read_text(encoding="utf-8"))
    scenario["scenario_hash"] = "0" * 64
    path.write_text(json.dumps(scenario), encoding="utf-8", newline="\n")
    assert "broken" in run_trace(run)


@pytest.mark.parametrize("manifest", [None, [], "not an object", True])
def test_malformed_manifest_is_shown_as_broken_without_crashing(nipd_root, tmp_path, manifest):
    parent = next(nipd_root.rglob("events.jsonl")).parent
    run = tmp_path / "malformed-manifest"
    shutil.copytree(parent, run)
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    assert "broken" in run_trace(run)
    result = CliRunner().invoke(app, ["lab", str(run)])
    assert result.exit_code == 1, result.output
    assert "BROKEN" in result.output


@pytest.mark.parametrize("seed_root", [None, 0, True])
def test_malformed_manifest_field_is_shown_as_broken(nipd_root, tmp_path, seed_root):
    parent = next(nipd_root.rglob("events.jsonl")).parent
    run = tmp_path / "malformed-field"
    shutil.copytree(parent, run)
    path = run / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["seed_root"] = seed_root
    path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    assert "broken" in run_trace(run)
    result = CliRunner().invoke(app, ["lab", str(run)])
    assert result.exit_code == 1, result.output
    assert "BROKEN" in result.output


def test_nested_and_legacy_branches_display_effective_policy_labels(nipd_root, tmp_path):
    parent = next(path.parent for path in nipd_root.rglob("events.jsonl")
                  if path.parent.parent.name == "pw-2tft-alld")
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    child = tmp_path / "first-child"
    branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
               child_run_id="first-child", policy_overrides={"a1": AllCPolicy("pairwise")})
    child_fork = FileCheckpointStore(RunPaths(child).checkpoints).list_seqs()[1]
    nested = tmp_path / "nested-child"
    _, branch = branch_run(parent_dir=child, fork_seq=child_fork, child_dir=nested,
                           child_run_id="nested-child", policy_overrides={
                               "a1": AllCPolicy("pairwise"), "a2": AllDPolicy("pairwise")})
    trace = run_trace(nested, verify_replay=True)
    assert "broken" not in trace, trace
    assert trace["policies"] == {"a1": "allc[pairwise]@1", "a2": "alld[pairwise]@1",
                                 "a3": "alld[pairwise]@1"}
    assert trace["fork_round"] == branch.fork_round
    assert trace["replay_identical"] is True

    # Legacy v1 branches stored root labels in manifest.json; branch.json carries
    # the effective labels. Compatibility must be read-only.
    manifest_path = nested / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["policies"] = json.loads((parent / "manifest.json").read_text())["policies"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    branch_path = nested / "branch.json"
    record = json.loads(branch_path.read_text(encoding="utf-8"))
    record["schema_version"] = 1
    branch_path.write_text(json.dumps(record), encoding="utf-8", newline="\n")
    before = {path.name: path.read_bytes() for path in (manifest_path, branch_path)}
    legacy = run_trace(nested, verify_replay=True)
    assert "broken" not in legacy, legacy
    assert legacy["policies"] == trace["policies"]
    assert legacy["replay_identical"] is True
    assert {path.name: path.read_bytes() for path in (manifest_path, branch_path)} == before


def test_empty_root_writes_no_page(tmp_path):
    out = tmp_path / "console.html"
    assert CliRunner().invoke(app, ["lab", str(tmp_path), "--out", str(out)]).exit_code == 2
    assert not out.exists()


def test_mutants_refuse_a_target_outside_the_overlay():
    target = str(REPO / "src/collaborative_hill/metrics/cooperation.py")
    done = subprocess.run([sys.executable, "scripts/mutants.py", target], cwd=REPO,
                          capture_output=True, text=True, check=False)
    assert done.returncode == 2
    assert "relative src/ path" in done.stderr


def test_quick_plan_runs_against_the_repository():
    done = subprocess.run([sys.executable, "scripts/quick.py", "HEAD", "--plan"], cwd=REPO,
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr
    assert "against HEAD" in done.stdout


def _inspection_data(page):
    marker = '<script type="application/json" id="inspection-data">'
    return json.loads(page.split(marker, 1)[1].split("</script>", 1)[0])


def test_round_inspector_preserves_exact_observations_actions_and_seal(nipd_root):
    run = next(path.parent for path in nipd_root.rglob("events.jsonl")
               if path.parent.parent.name == "pw-2tft-alld")
    events, _, _ = load_run(run)
    trace = run_trace(run)
    frames = trace["frames"]
    for event in events:
        if event.event_type == EventType.RUN_STARTED:
            continue
        frame = next(row for row in frames if row["round"] == event.logical_time)
        records = [item for value in frame.values() if isinstance(value, list) for item in value]
        record, = [item for item in records if item["seq"] == event.seq]
        assert record["payload"] == event.payload
        assert record["event_hash"] == event.event_hash
        assert record["inherited"] is False
    first = frames[0]
    assert first["round"] == 0
    assert len(first["observations"]) == 3
    # Outcomes are not merged into any earlier observation.
    assert all(item["payload"]["observation"]["moves_against_me"] is None
               for item in first["observations"])
    assert any(item["event_type"] == "WorldTransitioned" for item in first["outcomes"])
    assert frames[-1]["round"] == 50
    assert frames[-1]["observations"] == frames[-1]["actions"] == []
    assert frames[-1]["terminal"][0]["event_type"] == "RunCompleted"
    assert _inspection_data(render_html([trace]))[0]["frames"] == frames


def test_inspector_does_not_read_checkpoint_state_or_unhashed_metadata(ec_root, tmp_path):
    source = next(ec_root.rglob("events.jsonl")).parent
    run = tmp_path / "copy"
    shutil.copytree(source, run)
    ledger = run / "events.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        row["meta"] = {"untrusted_note": "DO-NOT-PROJECT-UNHASHED-METADATA"}
    ledger.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    for path in (run / "checkpoints").glob("*.json"):
        path.write_text('{"private": "DO-NOT-PROJECT-CHECKPOINT-STATE"}', encoding="utf-8")
    before = {path.relative_to(run): path.read_bytes() for path in run.rglob("*") if path.is_file()}
    trace = run_trace(run)
    assert "broken" not in trace
    page = render_html([trace])
    for forbidden in ("DO-NOT-PROJECT", "true_propositions", "truth_aligned"):
        assert forbidden not in page
    assert {path.relative_to(run): path.read_bytes()
            for path in run.rglob("*") if path.is_file()} == before


def test_round_inspector_keeps_released_audits_rejections_and_inherited_prefix_separate():
    report = {"slot_id": "s1", "proposition_id": "p1", "publish_round": 2,
              "verdict": "unavailable"}
    events = [
        _event(EventType.OBSERVATION_ISSUED, 0, agent_id="a1", observation={"round": 0}),
        _event(EventType.AUDIT_PUBLISHED, 2, report=report),
        _event(EventType.OBSERVATION_ISSUED, 2, agent_id="a1",
               observation={"round": 2, "audit": {"reports": [report]}}),
        _event(EventType.ACTION_REJECTED, 2, agent_id="a1", reason="budget exhausted"),
        _event(EventType.ACTION_ACCEPTED, 2, agent_id="a1",
               action={"type": "abstain"}, fallback=True),
        _event(EventType.RUN_FAILED, 3, reason="provider unavailable"),
    ]
    events = [event.model_copy(update={"seq": seq, "meta": {"ignored": "mutable"}})
              for seq, event in enumerate(events)]
    frames = round_frames(events, fork_seq=0)
    assert [frame["round"] for frame in frames] == [0, 2, 3]
    assert frames[0]["audits"] == []
    assert frames[0]["observations"][0]["inherited"] is True
    assert "audit" not in frames[0]["observations"][0]["payload"]["observation"]
    assert frames[1]["audits"][0]["payload"]["report"] == report
    assert frames[1]["audits"][0]["inherited"] is False
    assert [item["event_type"] for item in frames[1]["actions"]] == [
        "ActionRejected", "ActionAccepted"]
    assert frames[2]["observations"] == []
    assert frames[2]["terminal"][0]["payload"]["reason"] == "provider unavailable"
    assert "mutable" not in json.dumps(frames)


def test_inspector_projects_a_real_audited_run_without_future_findings(tmp_path):
    path = REPO / "experiments/audit-feedback/audit_feedback.py"
    spec = importlib.util.spec_from_file_location("lab_audit_fixture", path)
    assert spec is not None and spec.loader is not None
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)
    declaration, resolved = experiment.design()
    cell = {"kind": "audited_behavior", "truth": "q", "report": "p", "verdict": "negative",
            "publish_round": 4, "trace": None}
    cid = experiment.cell_id(cell)
    run = tmp_path / "audited"
    experiment.run_cell(cell, resolved[cid], run, declaration["design_hash"])
    trace = run_trace(run, verify_replay=True)
    assert "broken" not in trace
    assert trace["replay_identical"] is True
    report = {"slot_id": "s1", "proposition_id": "p", "publish_round": 4,
              "verdict": "negative"}
    for frame in trace["frames"]:
        assert len(frame["audits"]) == (1 if frame["round"] == 4 else 0)
        for event in frame["observations"]:
            reports = event["payload"]["observation"]["audit"]["reports"]
            assert reports == ([] if frame["round"] < 4 else [report])
    data, = _inspection_data(render_html([trace]))
    serialized = json.dumps(data)
    for key in experiment.HIDDEN_KEYS:
        assert f'"{key}":' not in serialized


def test_failed_run_inspector_keeps_partial_round_and_diagnostic(tmp_path, monkeypatch):
    from collaborative_hill.experiments import study

    original = study.build_policies

    def failing_policies(resolved, *, allow_provider_requests=False, overrides=None):
        policies = original(resolved, allow_provider_requests=allow_provider_requests,
                            overrides=overrides)

        def fail(*args):
            raise RuntimeError("synthetic provider outage")

        policies["a1"].propose = fail
        return policies

    monkeypatch.setattr(study, "build_policies", failing_policies)
    run_study(STUDY_001, tmp_path, only_condition="attr-priv-misinfo", replicates_override=1)
    run = next(tmp_path.rglob("events.jsonl")).parent
    trace = run_trace(run)
    assert trace["status"] == "failed"
    assert trace["kind"] == "ec"
    assert "quality" not in trace
    frame, = trace["frames"]
    assert len(frame["observations"]) == 3
    assert frame["actions"] == frame["outcomes"] == []
    assert frame["terminal"][0]["event_type"] == "RunFailed"
    assert "synthetic provider outage" in render_html([trace])
    assert "FAILED" in render_text([trace])


def test_inspector_has_every_verified_run_even_when_static_details_are_capped(nipd_root):
    traces = trace_runs(nipd_root)
    broken = {"run_id": "broken", "condition_id": "c", "study_id": "s", "broken": "invalid"}
    runs = _inspection_data(render_html([*traces, broken], max_detail=1))
    assert len(runs) == len(traces)
    assert [run["run_id"] for run in runs] == [trace["run_id"] for trace in traces]


def test_inspector_embedded_data_is_inert_and_round_trips(nipd_root):
    trace = deepcopy(trace_runs(nipd_root)[0])
    hostile = '</script><script>window.injected=true</script><img src=x onerror="boom">&\u2028'
    trace["run_id"] = hostile
    trace["frames"][0]["observations"][0]["payload"]["observation"]["label"] = hostile
    page = render_html([trace])
    assert hostile not in page
    assert "\\u003c/script\\u003e" in page
    decoded, = _inspection_data(page)
    assert decoded["run_id"] == hostile
    assert decoded["frames"][0]["observations"][0]["payload"]["observation"]["label"] == hostile
    assert ".innerHTML" not in page
    assert "fetch(" not in page


@pytest.mark.parametrize("relative", ["events.jsonl", "manifest.json", "scenario.resolved.json",
                                      "new.html", "checkpoints/new.html"])
def test_console_refuses_outputs_inside_evidence_runs(nipd_root, relative):
    run = next(nipd_root.rglob("events.jsonl")).parent
    before = {path.relative_to(run): path.read_bytes() for path in run.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="outside every run"):
        write_console(nipd_root, run / relative)
    assert {path.relative_to(run): path.read_bytes()
            for path in run.rglob("*") if path.is_file()} == before


def test_console_refuses_overwrite_and_symlink_aliases(nipd_root, tmp_path):
    out = tmp_path / "existing.html"
    out.write_text("preserve existing output", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        write_console(nipd_root, out)
    assert out.read_text(encoding="utf-8") == "preserve existing output"
    run = next(nipd_root.rglob("events.jsonl")).parent
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(run, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this platform")
    with pytest.raises(ValueError, match="outside every run"):
        write_console(nipd_root, alias / "new.html")
    assert not (run / "new.html").exists()


def test_console_exclusive_create_catches_output_appearing_during_render(
        nipd_root, tmp_path, monkeypatch):
    out = tmp_path / "racing.html"
    original = lab.render_html

    def render_and_create(*args, **kwargs):
        page = original(*args, **kwargs)
        out.write_text("another writer", encoding="utf-8")
        return page

    monkeypatch.setattr(lab, "render_html", render_and_create)
    with pytest.raises(FileExistsError):
        write_console(nipd_root, out)
    assert out.read_text(encoding="utf-8") == "another writer"


@pytest.mark.parametrize("ancestor", [False, True])
def test_console_parent_swap_during_render_cannot_redirect_into_evidence(
        nipd_root, tmp_path, monkeypatch, ancestor):
    source = next(nipd_root.rglob("events.jsonl")).parent
    run = tmp_path / "evidence"
    shutil.copytree(source, run)
    before = {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()}
    parent = tmp_path / "reports"
    (parent / "nested").mkdir(parents=True)
    out = parent / "nested" / "new.html"
    swapping = parent if ancestor else out.parent
    displaced = tmp_path / "displaced"
    original = lab.render_html
    attempted = []

    def render_and_swap(*args, **kwargs):
        page = original(*args, **kwargs)
        attempted.append(True)
        if os.name == "nt":
            # This assertion runs on Windows without requiring symlink privileges:
            # every ancestor must remain locked against rename during the callback.
            with pytest.raises(PermissionError):
                swapping.rename(displaced)
        else:
            swapping.rename(displaced)
            swapping.symlink_to(run, target_is_directory=True)
        return page

    monkeypatch.setattr(lab, "render_html", render_and_swap)
    write_console(run, out)
    assert attempted == [True]
    assert {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()} == before
    actual = out if os.name == "nt" else displaced / ("nested/new.html" if ancestor else "new.html")
    assert "<!doctype html>" in actual.read_text(encoding="utf-8")
