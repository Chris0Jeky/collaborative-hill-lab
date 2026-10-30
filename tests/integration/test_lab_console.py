"""The lab console shows sealed behaviour faithfully and never hides a broken ledger."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from collaborative_hill.cli import app
from collaborative_hill.engine.events import Event, EventType
from collaborative_hill.experiments.study import run_study
from collaborative_hill.reporting import lab
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
    assert run_trace(run)["condition_id"].endswith("(branch of parent-r000)")


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
