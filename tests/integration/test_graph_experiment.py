"""Canonical deterministic fixture, hand predictions, and sealed exact readout."""

import importlib.util
import json
import shutil
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from collaborative_hill.engine.hashing import canonical_json, content_hash

pytestmark = pytest.mark.integration
SCRIPT = Path(__file__).resolve().parents[2] / "experiments/graph-topology/graph_experiment.py"


@pytest.fixture(scope="module")
def experiment():
    spec = importlib.util.spec_from_file_location("graph_topology_experiment", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_design_crosses_topology_role_and_policy_with_literal_expected_means(experiment):
    cells = experiment.cells()
    assert len(cells) == len({c.condition_id for c in cells}) == 18
    # Independent finite sums of the pre-execution eight-round curves.
    means = {
        ("complete", "a1", "targeted"): "5/8",
        ("complete", "a2", "linked"): "1/10",
        ("ring", "a1", "targeted"): "5/8",
        ("ring", "a2", "linked"): "3/20",
        ("star", "a1", "targeted"): "1/16",
        ("star", "a1", "linked"): "1/16",
        ("star", "a2", "targeted"): "49/64",
        ("star", "a2", "linked"): "5/32",
        ("star", "a1", "quorum"): "1/10",
        ("star", "a2", "quorum"): "4/5",
    }
    for cell in cells:
        curve = experiment.expected_curve(cell)
        assert len(curve) == 8
        key = (cell.topology, cell.defector, cell.policy)
        if key in means:
            assert sum(map(Fraction, curve), Fraction(0)) / 8 == Fraction(means[key])


def test_canonical_fixture_generation_is_byte_identical_and_read_only_check(experiment, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    experiment.generate(first)
    experiment.generate(second)
    expected = experiment.canonical_files()
    assert len(expected) == 20  # 18 scenarios, one skin, one study
    mtimes = {name: (first / name).stat().st_mtime_ns for name in expected}
    experiment.generate(first, check=True)
    experiment.generate(first)  # identical no-op
    assert {name: (first / name).stat().st_mtime_ns for name in expected} == mtimes
    for name, data in expected.items():
        assert (first / name).read_bytes() == (second / name).read_bytes() == data


def test_fixture_preflights_every_output_and_never_writes_into_frozen_study(experiment, tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "skin.json").write_text("different", encoding="utf-8")
    with pytest.raises(ValueError, match="different"):
        experiment.generate(fixture)
    assert sorted(p.name for p in fixture.iterdir()) == ["skin.json"]
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    (frozen / "study.lock.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen"):
        experiment.generate(frozen)
    assert sorted(p.name for p in frozen.iterdir()) == ["study.lock.json"]


@pytest.fixture(scope="module")
def measured(experiment, tmp_path_factory):
    root = tmp_path_factory.mktemp("graph-experiment")
    study, artifacts = root / "study", root / "artifacts"
    experiment.generate(study)
    experiment.execute(study, artifacts)
    return study, artifacts, experiment.collect_report(study, artifacts)


def test_all_cells_match_predeclared_curves_and_keep_exact_provenance(measured):
    _, _, report = measured
    assert report["episode_count"] == report["matching_analytical_curves"] == 18
    assert report["rounds"] == 8 and report["payoff_aggregation"] == "mean"
    assert len(report["cells"]) == 18
    for result in report["cells"].values():
        assert result["observed_curve"] == result["analytical_curve"]
        assert result["replicate"] == 0 and result["replay_verified"]
        assert len(result["terminal_event_hash"]) == 64
        assert set(result["scores"]) == {"a1", "a2", "a3", "a4", "a5"}
    assert report["cells"]["star-d-a2-targeted"]["mean_cooperation"] == "49/64"
    assert report["cells"]["star-d-a1-quorum"]["mean_cooperation"] == "1/10"
    assert report["execution_source"]["commit_kind"].startswith("local_source_checkout")
    canonical_json(report)  # floats in any nested report value are forbidden


def test_report_regeneration_is_byte_identical_and_preflights_both_files(
    experiment, measured, tmp_path,
):
    study, artifacts, report = measured
    assert experiment.collect_report(study, artifacts) == report
    prefix = tmp_path / "RESULTS"
    experiment.write_report(report, prefix)
    paths = [prefix.with_suffix(suffix) for suffix in (".json", ".md")]
    snapshot = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    experiment.write_report(report, prefix)
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths] == snapshot
    blocked = tmp_path / "blocked"
    blocked.with_suffix(".md").write_text("retain this", encoding="utf-8")
    with pytest.raises(ValueError, match="different"):
        experiment.write_report(report, blocked)
    assert not blocked.with_suffix(".json").exists()
    assert blocked.with_suffix(".md").read_text(encoding="utf-8") == "retain this"


@pytest.mark.parametrize("damage", ["missing", "extra", "source", "source-missing-dependency"])
def test_readout_rejects_incomplete_extra_or_corrupt_source_evidence(
    experiment, measured, tmp_path, damage,
):
    study, artifacts, _ = measured
    copied = tmp_path / "copied"
    shutil.copytree(artifacts, copied)
    ledger = next(copied.rglob("events.jsonl"))
    if damage == "missing":
        ledger.unlink()
    elif damage == "extra":
        shutil.copytree(ledger.parent, copied / "extra")
    else:
        source = copied / "EXECUTION_SOURCE.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        if damage == "source-missing-dependency":
            data["files"].pop("requirements-lock.txt")
            data["files_sha256"] = content_hash({"domain": data["domain"], "files": data["files"]})
        else:
            data["files_sha256"] = "0" * 64
        source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        experiment.collect_report(study, copied)


def test_execution_requires_a_fresh_root_before_creating_any_new_runs(experiment, measured):
    study, artifacts, _ = measured
    before = {p.relative_to(artifacts) for p in artifacts.rglob("*")}
    with pytest.raises(ValueError, match="fresh"):
        experiment.execute(study, artifacts)
    assert {p.relative_to(artifacts) for p in artifacts.rglob("*")} == before


def test_run_rejects_alternate_report_destinations_before_execution(
    experiment, tmp_path, monkeypatch,
):
    study, artifacts = tmp_path / "study", tmp_path / "artifacts"
    experiment.generate(study)
    # This destination would otherwise collide with a file created during the
    # future execution, although it is absent during a static preflight.
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--run", "--study-dir", str(study),
                                      "--artifacts", str(artifacts), "--output",
                                      str(artifacts / "EXECUTION_SOURCE")])
    with pytest.raises(SystemExit) as exc:
        experiment.main()
    assert exc.value.code == 2
    assert not artifacts.exists()

