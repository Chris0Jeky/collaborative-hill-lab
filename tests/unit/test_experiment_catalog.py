"""Catalog coverage, read-only planning and safe delegation to existing entry points."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from collaborative_hill.cli import app
from collaborative_hill.experiments import catalog

REPO = Path(__file__).resolve().parents[2]


def test_all_shipped_studies_and_experiments_are_discoverable():
    catalog.validate_catalog(REPO)
    entries = catalog.catalog_data(REPO)["entries"]
    assert {entry["source"] for entry in entries if entry["kind"] != "archive"} == {
        path.relative_to(REPO).as_posix()
        for parent in ("studies", "experiments") for path in (REPO / parent).iterdir()
        if path.is_dir() and not path.name.startswith((".", "__"))
    }
    assert len({entry["experiment_id"] for entry in entries}) == len(entries)
    assert {path for entry in entries for path in entry["study_specs"]} == {
        path.relative_to(REPO).as_posix()
        for parent in ("studies", "experiments")
        for path in (REPO / parent).rglob("study.json")
    }
    for entry in entries:
        assert entry["question"] and entry["evidence"] and entry["readouts"]
        if entry["kind"] != "archive":
            assert entry["check_steps"] and entry["check_scope"]


def test_catalog_detects_omissions_and_stale_paths(monkeypatch):
    original = catalog.CATALOG
    monkeypatch.setattr(catalog, "CATALOG", original[1:])
    with pytest.raises(ValueError, match="uncataloged studies"):
        catalog.validate_catalog(REPO)
    broken = replace(original[0], readouts=("missing-catalog-reference.md",))
    monkeypatch.setattr(catalog, "CATALOG", (broken, *original[1:]))
    with pytest.raises(ValueError, match="missing or external"):
        catalog.validate_catalog(REPO)


def test_cli_catalog_json_and_text_have_matching_identifiers():
    cli = CliRunner()
    data = cli.invoke(app, ["catalog", "--json"])
    assert data.exit_code == 0, data.output
    document = json.loads(data.output)
    assert document["schema_version"] == 1
    text = cli.invoke(app, ["catalog"])
    assert text.exit_code == 0
    for entry in document["entries"]:
        assert entry["experiment_id"] in text.output


@pytest.mark.parametrize("entry", catalog.CATALOG, ids=lambda item: item.experiment_id)
def test_all_executable_plans_are_read_only_and_use_offline_argv(entry, tmp_path):
    if entry.kind == "archive":
        with pytest.raises(ValueError, match="archived reference"):
            catalog.experiment_plan(REPO, entry.experiment_id)
        return
    output = tmp_path / "fresh output; literally a name"
    plan = catalog.experiment_plan(
        REPO, entry.experiment_id, output=output if entry.run_steps else None)
    assert not output.exists()
    assert plan["cwd"] == str(REPO)
    assert plan["provider_requests"] is False
    assert plan["writes_source_artifacts"] is False
    assert plan["commands"] and plan["scope"]
    for command in plan["commands"]:
        assert command[0] == sys.executable
        assert "--allow-provider-requests" not in command
        assert "freeze" not in command
        assert not any("{out}" in argument for argument in command)
    check = catalog.experiment_plan(REPO, entry.experiment_id, check=True)
    assert check["operation"] == "check" and check["output"] is None
    assert not check["clean_source_required"]


def test_study002_recipe_runs_both_components_before_generating_its_readout(tmp_path):
    plan = catalog.experiment_plan(REPO, "study-002", output=tmp_path / "new")
    assert plan["commands"][0][1].endswith("/run_study.py")
    assert plan["commands"][1][1].endswith("/generate_report.py")
    assert "--output" in plan["commands"][1]
    # Its own read-only planning interface verifies the two independently declared components.
    result = subprocess.run([*plan["commands"][0], "--plan"], cwd=REPO,
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "deterministic +" in result.stdout and "stochastic episodes" in result.stdout
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("existing_kind", ["directory", "file"])
def test_existing_outputs_are_rejected_without_changes(tmp_path, existing_kind):
    output = tmp_path / "occupied"
    if existing_kind == "directory":
        output.mkdir()
    else:
        output.write_text("original", encoding="utf-8")
    result = CliRunner().invoke(app, ["experiment", "run", "graph-topology", "--out", str(output)])
    assert result.exit_code == 2
    assert "already exists" in result.output
    if output.is_file():
        assert output.read_text(encoding="utf-8") == "original"
    else:
        assert list(output.iterdir()) == []


def test_outputs_cannot_be_written_under_sources_or_inside_existing_runs(tmp_path):
    with pytest.raises(ValueError, match="under artifacts"):
        catalog.validate_output(REPO, REPO / "studies" / "accidental-output")
    run = tmp_path / "run"
    run.mkdir()
    (run / "events.jsonl").write_text("sealed evidence", encoding="utf-8")
    with pytest.raises(ValueError, match="inside an existing evidence run"):
        catalog.validate_output(REPO, run / "nested" / "out")


def test_output_symlinks_do_not_bypass_guards(tmp_path):
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(REPO / "studies", target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")
    with pytest.raises(ValueError, match="under artifacts"):
        catalog.validate_output(REPO, alias / "nested-output")
    dangling = tmp_path / "dangling"
    dangling.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="already exists"):
        catalog.validate_output(REPO, dangling)


def test_executor_does_not_precreate_output_uses_literal_argv_and_stops_on_failure(
    monkeypatch, tmp_path,
):
    output = tmp_path / "fresh output; $not_a_command"
    calls = []

    def fail(command, **kwargs):
        assert not output.exists()
        assert str(output) in command
        assert kwargs["cwd"] == REPO and kwargs["shell"] is False
        assert kwargs["env"]["PYTHONPATH"].startswith(str(REPO / "src"))
        calls.append(command)
        output.mkdir()
        (output / "failure.txt").write_text("retain this", encoding="utf-8")
        return subprocess.CompletedProcess(command, 7)

    monkeypatch.setattr(catalog.subprocess, "run", fail)
    assert catalog.execute_experiment(REPO, "study-002", output=output) == 7
    assert len(calls) == 1
    assert (output / "failure.txt").read_text(encoding="utf-8") == "retain this"


@pytest.mark.parametrize("arguments", [
    ["plan", "unknown"], ["run", "study-000"],
    ["run", "sparse-ptft", "--out", "unused"],
    ["check", "legacy-audit"], ["plan", "audit-feedback", "--check", "--out", "unused"],
])
def test_invalid_cli_requests_fail_before_any_execution(arguments, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("invalid request launched a process")
    monkeypatch.setattr(catalog.subprocess, "run", unexpected)
    result = CliRunner().invoke(app, ["experiment", *arguments])
    assert result.exit_code == 2, result.output


def test_cli_plan_resolves_relative_output_from_callers_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["experiment", "plan", "audit-feedback", "--out", "new",
                                     "--json"])
    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)
    assert plan["output"] == str(tmp_path / "new")
    assert plan["cwd"] == str(REPO)
    assert plan["clean_source_required"] is True
    assert list(tmp_path.iterdir()) == []
