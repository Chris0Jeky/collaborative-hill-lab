"""A user can discover, run and inspect one real experiment through the public CLI."""

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from collaborative_hill.cli import app

REPO = Path(__file__).resolve().parents[2]


def _digests(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


def test_catalog_plan_run_monitor_and_replay_console_share_a_real_artifact_root(tmp_path):
    cli = CliRunner()
    destination = tmp_path / "graph-runs"
    source = REPO / "experiments/graph-topology"
    source_before = _digests(source)

    catalog = cli.invoke(app, ["catalog", "--json"])
    assert catalog.exit_code == 0, catalog.output
    assert "graph-topology" in json.dumps(json.loads(catalog.stdout))
    plan = cli.invoke(app, ["experiment", "plan", "graph-topology",
                            "--out", str(destination), "--json"])
    assert plan.exit_code == 0, plan.output
    assert json.loads(plan.stdout)
    assert not destination.exists()

    executed = cli.invoke(app, ["experiment", "run", "graph-topology",
                                "--out", str(destination)])
    assert executed.exit_code == 0, executed.output
    assert len(list(destination.rglob("events.jsonl"))) == 18
    original_runs = _digests(destination)

    health = cli.invoke(app, ["monitor", str(destination), "--json"])
    assert health.exit_code == 0, health.output
    assert json.loads(health.stdout)["counts"] == {
        "completed": 18, "failed": 0, "unsealed": 0, "broken": 0,
    }

    console = tmp_path / "graph-console.html"
    inspected = cli.invoke(app, ["lab", str(destination), "--out", str(console),
                                 "--verify-replay"])
    assert inspected.exit_code == 0, inspected.output
    assert "replay 1/1 identical" in inspected.output
    assert "<!doctype html>" in console.read_text(encoding="utf-8").lower()
    assert _digests(destination) == original_runs
    assert _digests(source) == source_before

    repeated = cli.invoke(app, ["experiment", "run", "graph-topology",
                                "--out", str(destination)])
    assert repeated.exit_code != 0
    assert _digests(destination) == original_runs
