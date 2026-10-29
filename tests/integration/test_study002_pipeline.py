"""Study 002 uses real sealed runs, with strict identity and whole-episode checks."""

import importlib.util
import json
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from collaborative_hill.engine.events import ChainError
from collaborative_hill.engine.hashing import canonical_json
from collaborative_hill.engine.replay import replay_run
from collaborative_hill.experiments.study import load_study, run_study

STUDY = Path(__file__).resolve().parents[2] / "studies/002-nipd-sensitivity"
pytestmark = pytest.mark.integration


def report_module():
    assert (STUDY / "generate_report.py").exists(), "Study 002 report is not implemented"
    sys.path.insert(0, str(STUDY))
    try:
        spec = importlib.util.spec_from_file_location(
            "study002_report", STUDY / "generate_report.py",
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(STUDY))


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    root = tmp_path_factory.mktemp("study002")
    for cid in ("nb-n3-m2-q1-2", "nb-n5-m4-q76-100", "pw-n5-m4-tft"):
        run_study(STUDY, root, only_condition=cid)
    run_study(STUDY / "stochastic", root,
              only_condition="nb-n5-m4-ptft-include", replicates_override=2)
    return {p.parent.parent.name + ":" + p.parent.name: p.parent
            for p in root.glob("*/*/*/manifest.json")}


def episode(directory):
    report = report_module()
    cid = directory.parent.name
    condition = next(c for c in report.conditions() if c.condition_id == cid)
    source = STUDY if condition.deterministic else STUDY / "stochastic"
    spec, resolved = load_study(source)
    return report.read_episode(directory, condition, spec, resolved)


@pytest.mark.parametrize("cid,mean,final,scores", [
    ("nb-n3-m2-q1-2", "2/3", "2/3", {"a1": "75", "a2": "75", "a3": "250"}),
    ("nb-n5-m4-q76-100", "2/125", "0",
     {"a1": "205/4", "a2": "205/4", "a3": "205/4", "a4": "205/4", "a5": "54"}),
    ("pw-n5-m4-tft", "151/250", "3/5",
     {"a1": "499", "a2": "499", "a3": "499", "a4": "499", "a5": "216"}),
])
def test_sealed_mechanism_matches_independent_oracles_and_replay(runs, cid, mean, final, scores):
    directory = runs[f"{cid}:{cid}-r000"]
    result = episode(directory)
    assert result["mean_cooperation"] == mean
    assert result["final_window_cooperation"] == final
    assert result["scores"] == scores
    assert replay_run(directory).chains_match
    canonical_json(result)


@pytest.mark.parametrize("damage", [
    "study_hash", "replicate", "condition_id", "truncated", "duplicate_seed", "policy",
])
def test_report_rejects_misattributed_or_unsealed_episode(tmp_path, runs, damage):
    original = runs["nb-n3-m2-q1-2:nb-n3-m2-q1-2-r000"]
    target = tmp_path / original.parent.name / original.name
    shutil.copytree(original, target)
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if damage == "truncated":
        path = target / "events.jsonl"
        path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n", encoding="utf-8")
    elif damage == "duplicate_seed":
        manifest["replicate"] = 1  # Leave seed unchanged: it is not a second independent run.
    elif damage == "policy":
        manifest["policies"]["a1"] = "alld[neighbourhood]@1"
    else:
        manifest[damage] = -1 if damage == "replicate" else "wrong"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises((ValueError, ChainError)):
        episode(target)


def test_stochastic_episodes_keep_distinct_roots_and_are_not_round_replicates(runs):
    cid = "nb-n5-m4-ptft-include"
    rows = [episode(runs[f"{cid}:{cid}-r{r:03d}"]) for r in range(2)]
    assert rows[0]["seed_root"] != rows[1]["seed_root"]
    report = report_module()
    summary = report.describe([Fraction(row["mean_cooperation"]) for row in rows],
                              scope="fixture", samples=100)
    assert summary["episodes"] == 2  # Not 100 rounds or 500 agent-rounds.


def test_descriptive_statistics_use_episode_variance_and_guard_degenerate_sample():
    report = report_module()
    summary = report.describe([Fraction(1, 3), Fraction(2, 3)], scope="fixture", samples=100)
    assert summary["mean"] == "1/2"
    assert summary["sample_variance"] == "1/18"
    repeated = report.describe([Fraction()] * 32, scope="fixture", samples=100)
    assert repeated["episodes"] == 32
    assert repeated["ci95"] is None
    assert repeated["uncertainty_note"] == "zero_observed_between_episode_variance"
    with pytest.raises(ValueError, match="samples"):
        report.describe([Fraction(0), Fraction(1)], scope="fixture", samples=1)


def test_report_refuses_incomplete_design_without_writing(runs):
    report = report_module()
    one = next(iter(runs.values()))
    root = one.parent.parent.parent
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="missing|incomplete"):
        report.analyze(root, study_dir=STUDY, samples=100)
    after = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert after == before


def test_episode_measurement_ignores_poisoned_metric_cache(tmp_path, runs):
    original = runs["nb-n3-m2-q1-2:nb-n3-m2-q1-2-r000"]
    target = tmp_path / original.parent.name / original.name
    shutil.copytree(original, target)
    metrics = target / "metrics"
    metrics.mkdir(exist_ok=True)
    cache = metrics / "metrics.json"
    cache.write_text('{"cooperation":{"mean_cooperation":999}}', encoding="utf-8")
    before = cache.read_bytes()
    assert episode(target)["mean_cooperation"] == "2/3"
    assert cache.read_bytes() == before


def test_independent_contrast_bootstrap_does_not_pair_equal_replicate_labels():
    report = report_module()
    # Independent resampling of {0,1} minus {0,1} has extremes -1,+1.
    # Reusing the same bootstrap stream would silently yield [0,0].
    rows = [{"mean_cooperation": "0"}, {"mean_cooperation": "1"}]
    result = report._denominator_contrast(rows, rows, 3, 2, 2000)
    assert result["measured_difference"] == "0"
    assert result["ci95"] == ["-1", "1"]
    assert result["episodes_include"] == result["episodes_exclude"] == 2


def test_report_flags_marginal_bootstrap_misses_without_calling_them_confirmation():
    report = report_module()
    cells = {cid: {"analytical_expectation": {"mean_cooperation": expected},
                   "measured": {"mean_cooperation": {"ci95": interval}}}
             for cid, expected, interval in [
                 ("above", "1/2", ["0", "1/4"]),
                 ("below", "0", ["1/4", "1/2"]),
                 ("boundary", "1/4", ["1/4", "1/2"]),
                 ("withheld", "1/2", None),
             ]}
    assert report.expectation_interval_misses(cells) == ["above", "below"]


@pytest.mark.parametrize("output_kind", ["prediction", "specification", "run_manifest"])
def test_report_output_cannot_overwrite_predictions_specification_or_sealed_run(
    tmp_path, runs, output_kind,
):
    report = report_module()
    root = next(iter(runs.values())).parent.parent.parent
    output = {"prediction": STUDY / "README",
              "specification": STUDY / "study",
              "run_manifest": next(iter(runs.values())) / "manifest"}[output_kind]
    with pytest.raises(ValueError, match="output"):
        report.validate_output(output, study_dir=STUDY, artifacts=root)


def test_report_preflights_both_outputs_and_preserves_divergent_existing_files(tmp_path):
    report = report_module()
    output = tmp_path / "human-owned"
    markdown = output.with_suffix(".md")
    markdown.write_text("preserve these existing notes", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        report.write_outputs(output, json_text='{"measured":1}\n', markdown="new report\n")
    assert markdown.read_text(encoding="utf-8") == "preserve these existing notes"
    assert not output.with_suffix(".json").exists()  # Preflight precedes either write.


def test_report_allows_byte_identical_regeneration_without_rewriting(tmp_path):
    report = report_module()
    output = tmp_path / "report"
    report.write_outputs(output, json_text='{"measured":1}\n', markdown="report\n")
    paths = [output.with_suffix(suffix) for suffix in (".json", ".md")]
    before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths]
    report.write_outputs(output, json_text='{"measured":1}\n', markdown="report\n")
    assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths] == before


def test_top_level_runner_preflights_both_components_and_has_no_plan_side_effects(tmp_path):
    script = STUDY / "run_study.py"
    assert script.exists(), "Study 002 top-level runner is not implemented"
    artifacts = tmp_path / "artifacts"
    command = [sys.executable, str(script), "--artifacts", str(artifacts)]
    plan = subprocess.run([*command, "--plan"], text=True, capture_output=True, check=False)
    assert plan.returncode == 0, plan.stderr
    assert "29 deterministic" in plan.stdout and "192 stochastic" in plan.stdout
    assert not artifacts.exists()
    artifacts.mkdir()
    marker = artifacts / "do-not-overwrite.txt"
    marker.write_text("preserved", encoding="utf-8")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    assert result.returncode == 2
    assert "fresh" in result.stderr
    assert list(artifacts.iterdir()) == [marker]
    assert marker.read_text(encoding="utf-8") == "preserved"
