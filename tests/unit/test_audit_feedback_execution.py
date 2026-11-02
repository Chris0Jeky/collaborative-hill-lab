"""Actual-artifact audit-feedback checks; not additional research samples."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2] / "experiments/audit-feedback/audit_feedback.py"
SPEC = importlib.util.spec_from_file_location("audit_feedback", PATH)
assert SPEC and SPEC.loader
experiment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(experiment)


def choose(
    kind="audited_behavior", truth="q", report="p", verdict="negative", timing=4, trace=None
):
    return {
        "kind": kind,
        "truth": truth,
        "report": report,
        "verdict": verdict,
        "publish_round": timing,
        "trace": trace,
    }


def test_grid_and_endpoints_retain_every_declared_case_without_duplicate_runs():
    cells = experiment.cells()
    assert len(cells) == 76
    assert len({experiment.cell_id(cell) for cell in cells}) == 76
    assert {
        kind: sum(c["kind"] == kind for c in cells)
        for kind in ("audited_behavior", "unaudited_behavior", "unaudited_fixed", "audited_fixed")
    } == {
        "audited_behavior": 48,
        "unaudited_behavior": 4,
        "unaudited_fixed": 12,
        "audited_fixed": 12,
    }
    for cell in cells:
        resolved = experiment.compile_scenario(experiment.scenario(cell), experiment.SKIN)
        raw = resolved.spec.model_dump(mode="json")
        assert len(raw["information"]["evidence"]) == 3
        assert {e["proposition_id"] for e in raw["information"]["evidence"]} == {cell["report"]}
        assert raw["world"]["params"]["rounds"] == 8
        if cell["verdict"] is not None:
            config = raw["institution"]["audit"]
            correct = cell["truth"] == cell["report"]
            assert config["contract"]["accuracy"] == (
                "1"
                if cell["verdict"] == "unavailable" or (cell["verdict"] == "positive") == correct
                else "0"
            )
            assert config["generation"]["unavailable_probability"] == (
                "1" if cell["verdict"] == "unavailable" else "0"
            )
            assert config["contract"]["schedule"] == [
                {
                    "slot_id": "s1",
                    "proposition_id": cell["report"],
                    "publish_round": cell["publish_round"],
                }
            ]
        else:
            assert "audit" not in raw["institution"]


@pytest.mark.parametrize(
    "patch",
    [
        {"truth": "x"},
        {"report": "x"},
        {"publish_round": 4.0},
        {"publish_round": True},
        {"publish_round": 7},
        {"verdict": "bad"},
        {"trace": "A"},
        {"kind": "bad"},
        {"extra": "field"},
    ],
)
def test_out_of_design_cells_fail_before_execution(patch):
    with pytest.raises(ValueError, match="declared"):
        experiment.scenario({**choose(), **patch})


def test_source_guard_rejects_dirty_or_unidentified_code_before_output(monkeypatch, tmp_path):
    for provenance in (("a" * 40, True), (None, None), ("a" * 40, None)):
        monkeypatch.setattr(experiment, "git_provenance", lambda _, value=provenance: value)
        with pytest.raises(ValueError, match="clean committed"):
            experiment.source_provenance()
    assert list(tmp_path.iterdir()) == []


def test_existing_output_is_never_reused(tmp_path):
    destination = tmp_path / "occupied"
    destination.mkdir()
    sentinel = destination / "original.txt"
    sentinel.write_bytes(b"do not replace")
    with pytest.raises(FileExistsError):
        experiment.execute(destination)
    assert sentinel.read_bytes() == b"do not replace"
    assert list(destination.iterdir()) == [sentinel]


def test_execution_failure_retains_every_declared_cell_without_claiming_unrun_predictions(
    monkeypatch, tmp_path
):
    def fail_before_episode(*args):
        raise ValueError("deliberate fixture failure before any episode")

    monkeypatch.setattr(experiment, "run_cell", fail_before_episode)
    root = tmp_path / "failed-execution"
    with pytest.raises(ValueError, match="deliberate fixture"):
        experiment.execute(root)
    retained = json.loads((root / "FAILED_EXECUTION.json").read_text(encoding="utf-8"))
    assert retained["phase"] == "episodes"
    assert retained["prediction_readout_complete"] is False
    assert len(retained["cells"]) == 76
    assert set(retained["cells"]) == {experiment.cell_id(c) for c in experiment.cells()}
    assert all(row["artifact_status"] == "not-written" for row in retained["cells"].values())
    assert all(row["held"] is None for row in retained["predictions"].values())


def test_saved_input_tampering_fails_before_reading_runs(tmp_path):
    experiment.write_inputs(tmp_path / "inputs")
    target = tmp_path / "inputs/scenarios" / (experiment.cell_id(choose()) + ".json")
    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["world"]["params"]["cost_inspect"] = 99
    target.write_text(json.dumps(raw), encoding="utf-8", newline="\n")
    with pytest.raises(ValueError, match="saved inputs"):
        experiment.collect(tmp_path)


def test_predictions_retain_misses_with_unchanged_literal_expectations():
    cell = choose()
    schedule = experiment.oracle.literal_schedule("C", "p")
    outcomes = experiment.oracle.literal_outcome("C", "q", "p")
    record = {"cell": cell, "actions": schedule, **outcomes}
    assert experiment.readout.action_prediction(record)["held"] is True
    assert experiment.readout.task_prediction(record)["held"] is True
    changed = copy.deepcopy(record)
    changed["total_effort"] = 13
    changed["actions"][12]["action"] = {"type": "verify_claim", "claim_id": "c2"}
    action = experiment.readout.action_prediction(changed)
    task = experiment.readout.task_prediction(changed)
    assert action["held"] is False
    assert action["expected"][12]["action"] == {"type": "withhold"}
    assert action["actual"][12]["action"]["type"] == "verify_claim"
    assert task["held"] is False
    assert task["expected"]["total_effort"] == 12
    assert task["actual"]["total_effort"] == 13
    assert experiment.oracle.literal_outcome("C", "q", "p")["total_effort"] == 12


def literal_records():
    """Hand-oracle fixtures only; these are never retained as episode evidence."""
    records = {}
    for cell in experiment.cells():
        trace = experiment.readout.expected_trace(cell)
        records[experiment.cell_id(cell)] = {
            "cell": cell,
            "actions": experiment.oracle.literal_schedule(trace, cell["report"]),
            **experiment.oracle.literal_outcome(trace, cell["truth"], cell["report"]),
            "publication": {"report": {"verdict": cell["verdict"]}},
        }
    return records


def test_sixty_c3_bindings_reuse_controls_and_include_forced_false_acceptance():
    records = literal_records()
    checks = experiment.same_action_checks(records)
    assert len(checks) == 60
    assert all(row["held"] for row in checks)
    assert len({row["unaudited_shared_control"] for row in checks}) == 16
    forced_id = experiment.cell_id(choose(kind="audited_fixed", trace="A"))
    forced = next(row for row in checks if row["audited_cell"] == forced_id)
    assert forced["unaudited_shared_control"] == "base-tq-rp"
    records[forced_id]["collective_quality"] = 0
    failed = next(
        row for row in experiment.same_action_checks(records) if row["audited_cell"] == forced_id
    )
    assert failed["held"] is False
    assert failed["checks"]["collective_quality"] is False


def test_reweighting_uses_observed_task_and_finding_fields_and_retains_zero_mass_terms():
    records = literal_records()
    rows = experiment.readout.mixtures(records)
    assert len(rows) == 720
    assert all(row["held"] and row["quality_contrast_held"] for row in rows)
    assert all(len(row["endpoint_weights"]) == 12 for row in rows)
    assert any(term["mass"] == "0" for row in rows for term in row["endpoint_weights"])
    cid = experiment.cell_id(choose(truth="p", report="p", verdict="positive", timing=3))
    records[cid]["collective_quality"] = 11
    records[cid]["publication"]["report"]["verdict"] = "negative"
    changed = experiment.readout.mixtures(records)
    row = next(
        r
        for r in changed
        if r["source_error"] == "0"
        and r["audit_accuracy"] == "1"
        and r["unavailable"] == "0"
        and r["publish_round"] == 3
        and r["truth_view"] == "p"
    )
    assert row["held"] is False
    assert row["actual"]["signed_quality"] == "11"
    assert row["expected"]["signed_quality"] == "12"
    assert row["marginal_checks"]["available_correct"] is False


def test_failed_render_uses_measured_trace_and_does_not_print_success_claims():
    records = literal_records()
    failed_id = experiment.cell_id(choose(truth="p", report="p", verdict="positive", timing=3))
    records[failed_id]["actions"][9]["action"] = {"type": "withhold"}
    records[failed_id]["total_effort"] = 99
    result = {
        "episodes": records,
        "behavioral_episodes": 52,
        "fixed_action_episodes": 24,
        "verified_replays": 76,
        "branch_checks": dict.fromkeys(range(4), {}),
        "exact_mixtures": experiment.readout.mixtures(records),
        "design_hash": "test-fixture",
        "predictions": {f"P{i}": {"held": False} for i in range(1, 9)},
    }
    report = experiment.readout.render_report(result)
    assert "Measured traces" in report
    assert "unmatched / A | A" in report
    assert (
        "Positive and unavailable findings at every declared time follow the full A" not in report
    )
    assert "At a=3/4, accuracy among accepted claims rises" not in report
    assert "At least one timing/action/task/publication prediction failed" in report
    assert "The measured mixture rows fail" in report
    assert "| P1 | False |" in report


def original_source_fixture(tmp_path):
    source = {
        "schema": "audit-feedback-source-v1",
        "local_commit": "a" * 40,
        "worktree_dirty": False,
        "python_version": "3.12.14",
        "platform": "test-only",
        "dependency_lock_sha256": "b" * 64,
        "files_sha256": {"requirements-lock.txt": "b" * 64},
    }
    manifest = {
        "code_commit": "a" * 40,
        "worktree_dirty": False,
        "dependency_lock_sha256": "b" * 64,
    }
    (tmp_path / "runs/example").mkdir(parents=True)
    return source, manifest


@pytest.mark.parametrize(
    "damage",
    [
        "source-dirty",
        "source-zero",
        "manifest-zero",
        "unknown-schema",
        "missing-dirty",
        "non-object",
        "bad-commit",
        "bad-lock",
        "bad-files",
        "bad-file-path",
        "bad-file-hash",
        "missing-lock-binding",
        "extra-field",
    ],
)
def test_original_source_binding_rejects_malformed_or_dirty_claims(tmp_path, damage):
    source, manifest = original_source_fixture(tmp_path)
    if damage == "source-dirty":
        source["worktree_dirty"] = True
    elif damage in ("source-zero", "manifest-zero"):
        target = source if damage == "source-zero" else manifest
        target["worktree_dirty"] = 0
    elif damage == "unknown-schema":
        source["schema"] = "future"
    elif damage == "missing-dirty":
        source.pop("worktree_dirty")
    elif damage == "non-object":
        source = []
    elif damage == "bad-commit":
        source["local_commit"] = "not-a-commit"
    elif damage == "bad-lock":
        source["dependency_lock_sha256"] = None
    elif damage == "bad-files":
        source["files_sha256"] = []
    elif damage == "bad-file-path":
        source["files_sha256"]["../escape.py"] = "c" * 64
    elif damage == "bad-file-hash":
        source["files_sha256"]["source.py"] = 1
    elif damage == "missing-lock-binding":
        source["files_sha256"]["requirements-lock.txt"] = "c" * 64
    else:
        source["extra"] = "unexpected"
    experiment.write_json(tmp_path / "SOURCE_PROVENANCE.json", source)
    experiment.write_json(tmp_path / "runs/example/manifest.json", manifest)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.json")}
    with pytest.raises(ValueError, match="source provenance"):
        experiment._source_bindings(tmp_path, {"example"})
    assert all(path.read_bytes() == original for path, original in before.items())


def test_valid_original_source_binding_and_absent_reproduction_source_are_distinct(tmp_path):
    experiment._source_bindings(tmp_path, {"example"})
    source, manifest = original_source_fixture(tmp_path)
    experiment.write_json(tmp_path / "SOURCE_PROVENANCE.json", source)
    experiment.write_json(tmp_path / "runs/example/manifest.json", manifest)
    experiment._source_bindings(tmp_path, {"example"})


@pytest.fixture(scope="module")
def actual_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("audit-feedback-fixture")
    cell = choose()
    target = experiment.compile_scenario(experiment.scenario(cell), experiment.SKIN)
    digest = experiment.design()[0]["design_hash"]
    path = root / "parent"
    experiment.run_cell(cell, target, path, digest)
    return root, cell, target, path, digest


def test_actual_negative_report_precedes_round_four_observations_and_retains_trace_c(actual_run):
    _, cell, target, path, digest = actual_run
    record = experiment.episode_record(path, target, cell, digest)
    assert record["replay_verified"] is True
    assert record["collective_quality"] == 0
    assert record["total_effort"] == 12
    assert record["publication"]["held"] is True
    assert record["publication"]["published_count"] == 1
    assert record["publication"]["first_report_round"] == 4
    assert record["publication"]["checkpoints_checked"] == 8
    assert record["actions"] == experiment.oracle.literal_schedule("C", "p")
    assert record["budgets"] == {a: {"inspect": 0, "verify": 2} for a in ("a1", "a2", "a3")}


def test_actual_forced_verification_after_negative_report_still_accepts_wrong_claim(actual_run):
    root, _, _, _, digest = actual_run
    cell = choose(kind="audited_fixed", trace="A")
    target = experiment.compile_scenario(experiment.scenario(cell), experiment.SKIN)
    path = root / "forced"
    experiment.run_cell(cell, target, path, digest)
    record = experiment.episode_record(path, target, cell, digest)
    assert record["actions"] == experiment.oracle.literal_schedule("A", "p")
    assert record["collective_quality"] == -12
    assert record["total_effort"] == 24
    assert record["total_credit"] == "-7"
    assert record["total_utility"] == "-43"
    assert record["publication"]["held"] is True
    baseline_cell = choose(kind="unaudited_behavior", verdict=None, timing=None)
    baseline_target = experiment.compile_scenario(
        experiment.scenario(baseline_cell), experiment.SKIN
    )
    baseline_path = root / "unaudited-baseline"
    experiment.run_cell(baseline_cell, baseline_target, baseline_path, digest)
    baseline = experiment.episode_record(baseline_path, baseline_target, baseline_cell, digest)
    assert baseline["publication"]["published_count"] == 0
    assert baseline["publication"]["held"] is True
    assert all(record[field] == baseline[field] for field in experiment.readout.TASK_FIELDS)


def test_manifest_swap_and_altered_saved_schedule_are_not_repaired(actual_run):
    _, cell, target, path, digest = actual_run
    manifest_path = path / "manifest.json"
    original = manifest_path.read_bytes()
    altered = json.loads(original)
    altered["condition_id"] = "different-cell"
    manifest_path.write_text(json.dumps(altered), encoding="utf-8", newline="\n")
    try:
        with pytest.raises(ValueError, match="manifest"):
            experiment.episode_record(path, target, cell, digest)
        assert manifest_path.read_text(encoding="utf-8") == json.dumps(altered)
    finally:
        manifest_path.write_bytes(original)


def test_branch_fixtures_preserve_prefixes_publication_and_old_policy_override(actual_run):
    root, cell, target, path, _ = actual_run
    checks = experiment.branch_checks(root / "branches", path, target, cell)
    assert set(checks) == {
        "before_publication",
        "after_publication",
        "nested",
        "old_policy_override",
    }
    assert all(row["held"] and row["replay_verified"] for row in checks.values())
    assert checks["before_publication"]["new_publications"] == 1
    assert checks["after_publication"]["new_publications"] == 0
    assert checks["nested"]["new_publications"] == 0
    assert checks["old_policy_override"]["collective_quality"] == -12
    assert checks["old_policy_override"]["total_effort"] == 24
    child = root / "branches/old_policy_override"
    paths = (child / "manifest.json", child / "branch.json")
    originals = {path: path.read_bytes() for path in paths}
    changed = {path: json.loads(raw) for path, raw in originals.items()}
    fake_ids = dict.fromkeys(("a1", "a2", "a3"), "a-different-policy@99")
    changed[paths[0]]["policies"] = fake_ids
    changed[paths[1]]["changed_policies"] = fake_ids
    for file_path, raw in changed.items():
        experiment.write_json(file_path, raw)
    try:
        with pytest.raises(ValueError, match="policy"):
            experiment.audit_branches(root / "branches", path, target, cell)
    finally:
        for file_path, raw in originals.items():
            file_path.write_bytes(raw)
    for label in ("before_publication", "after_publication", "nested"):
        branch_path = root / "branches" / label / "branch.json"
        original = branch_path.read_bytes()
        raw = json.loads(original)
        raw["changed_policies"] = raw["unchanged_policies"]
        raw["unchanged_policies"] = {}
        experiment.write_json(branch_path, raw)
        try:
            with pytest.raises(ValueError, match="partition"):
                experiment.audit_branches(root / "branches", path, target, cell)
        finally:
            branch_path.write_bytes(original)
