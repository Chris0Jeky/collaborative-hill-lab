"""Offline scripted fixture golden: twelve episodes, never agent-round rows."""

import json
import shutil
from pathlib import Path

import pytest

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.domain.actions import ActionProposal, InspectEvidenceAction
from collaborative_hill.engine.hashing import canonical_json
from collaborative_hill.experiments import study
from collaborative_hill.reporting.analysis import analyze_study

from ._helpers import STUDY_001, find_run_dirs, run_cli

pytestmark = pytest.mark.integration
GOLDEN = Path(__file__).parent / "golden" / "analysis_001.json"


def make_fixture(directory, *, paired=False, fail=False, invalid=False, monkeypatch=None,
                 change=None):
    source = directory / "study"
    shutil.copytree(STUDY_001, source)
    path = source / "study.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec["conditions"] = spec["conditions"][:4]
    spec["replicates"] = 3
    spec["checkpoint_every"] = 0
    if paired:
        spec["seed_protocol"] = "paired-policy-v2"
        for condition in spec["conditions"]:
            condition["scenario_block"] = "fixture"
    path.write_text(json.dumps(spec), encoding="utf-8")
    if change is not None:
        change(source)
    if fail or invalid:
        build = study.build_policies

        def failing_policies(resolved):
            policies = build(resolved)
            original = policies["a1"].propose
            calls = 0

            def fail_proposal(*args):
                nonlocal calls
                calls += 1
                if fail:
                    raise RuntimeError("synthetic failure")
                if calls == 1:
                    return ActionProposal(action=InspectEvidenceAction(evidence_id="missing"))
                return original(*args)

            policies["a1"].propose = fail_proposal
            return policies

        monkeypatch.setattr(study, "build_policies", failing_policies)
    study.run_study(source, directory / "artifacts")
    return find_run_dirs(directory / "artifacts")[0].parent.parent


@pytest.fixture(scope="module")
def scripted_artifacts(tmp_path_factory):
    return make_fixture(tmp_path_factory.mktemp("analysis"))


def snapshot(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_scripted_analysis_golden_and_no_writes(scripted_artifacts, monkeypatch):
    before = snapshot(scripted_artifacts)

    def forbidden(*args, **kwargs):
        pytest.fail("analysis must never rerun an episode")

    monkeypatch.setattr("collaborative_hill.engine.runner.run_episode", forbidden)
    result = analyze_study(scripted_artifacts)
    assert canonical_json(result) + "\n" == GOLDEN.read_text(encoding="utf-8")
    assert snapshot(scripted_artifacts) == before
    assert result["sap_status"] == "draft"
    assert result["exclusions"] == []
    assert len(result["episodes"]) == 12  # 4 cells * 3 episodes, not rounds * agents.
    assert {r["n_agents"] for r in result["episodes"]} == {3}
    assert all(c["n"] == 3 and c["n_effective"] == 1
               for c in result["primary"]["per_cell"].values())
    assert all(e["ci95"] is None for e in result["primary"]["family"].values())
    # This is mechanism geometry, not a statistical result. Accountability
    # redistributes credit; these observation-driven policies do not react to it.
    assert [result["primary"]["family"][e]["estimate"] for e in ("E1", "E2", "E3")] == [
        "0", "-1", "0",
    ]
    assert all(r["cost_usd"] is None and r["input_tokens"] is None
               and r["output_tokens"] is None for r in result["episodes"])


def test_analysis_cli_canonical_stdout_and_output(scripted_artifacts, tmp_path):
    expected = GOLDEN.read_text(encoding="utf-8")
    result = run_cli("analyze", str(scripted_artifacts))
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected
    output = tmp_path / "analysis.json"
    result = run_cli("analyze", str(scripted_artifacts), "--out", str(output))
    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8") == expected
    assert run_cli("analyze", str(scripted_artifacts), "--out", str(output)).returncode == 2
    assert output.read_text(encoding="utf-8") == expected
    run = next(scripted_artifacts.glob("*/*/manifest.json")).parent
    assert run_cli("analyze", str(scripted_artifacts), "--out",
                   str(run / "new.json")).returncode == 2
    assert not (run / "new.json").exists()


@pytest.mark.parametrize("damage", ["manifest_missing", "ledger_missing", "truncated", "hash",
                                    "scenario", "status", "replicate", "axes"])
def test_exclude_invalid_or_unsealed_runs(scripted_artifacts, tmp_path, damage):
    root = tmp_path / "artifacts"
    shutil.copytree(scripted_artifacts, root)
    run = root / "agg-priv" / "agg-priv-r000"
    manifest = run / "manifest.json"
    ledger = run / "events.jsonl"
    if damage == "manifest_missing":
        manifest.unlink()
    elif damage == "ledger_missing":
        ledger.unlink()
    elif damage == "truncated":
        ledger.write_text("\n".join(ledger.read_text(encoding="utf-8").splitlines()[:-1]) + "\n",
                          encoding="utf-8")
    elif damage == "hash":
        ledger.write_text(ledger.read_text(encoding="utf-8").replace('"seq":0', '"seq":1', 1),
                          encoding="utf-8")
    elif damage == "scenario":
        (run / "scenario.resolved.json").write_text("{}", encoding="utf-8")
    else:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data[{"status": "status", "replicate": "replicate", "axes": "condition_id"}[damage]] = {
            "status": "running", "replicate": 10, "axes": "attr-priv",
        }[damage]
        manifest.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_study(root)
    assert len(result["episodes"]) == 11
    assert len(result["exclusions"]) == 1
    assert result["attrition"]["per_cell"]["agg-priv"]["inclusion_rate"] == "2/3"


def test_copied_runs_are_not_extra_episodes(scripted_artifacts, tmp_path):
    root = tmp_path / "artifacts"
    shutil.copytree(scripted_artifacts, root)
    shutil.copytree(root / "agg-priv" / "agg-priv-r000", root / "agg-priv" / "zz-copy")
    result = analyze_study(root)
    assert len(result["episodes"]) == 12
    assert result["exclusions"][0]["reason"] == "duplicate_episode"
    assert result["attrition"]["per_cell"]["agg-priv"]["inclusion_rate"] == "1"


def test_exploratory_condition_never_enters_factorial(scripted_artifacts, tmp_path):
    root = tmp_path / "artifacts"
    shutil.copytree(scripted_artifacts, root)
    extra = root / "attr-priv-misinfo" / "extra"
    shutil.copytree(root / "attr-priv" / "attr-priv-r000", extra)
    path = extra / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["condition_id"] = "attr-priv-misinfo"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_study(root)
    assert len(result["episodes"]) == 12
    assert result["exclusions"][0]["reason"] == "outside_primary_2x2"


def test_mixed_study_hashes_are_refused(scripted_artifacts, tmp_path):
    root = tmp_path / "artifacts"
    shutil.copytree(scripted_artifacts, root)
    path = root / "agg-priv" / "agg-priv-r000" / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["study_hash"] = "other-study"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="one study identity"):
        analyze_study(root)


@pytest.mark.parametrize("paired", [False, True])
@pytest.mark.parametrize("nuisance", ["population", "task", "skin"])
def test_factorial_analysis_refuses_confounding_between_cells(tmp_path, paired, nuisance):
    def change(source):
        path = source / ("study.json" if nuisance == "skin" else "scenarios/attr-ledger.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        if nuisance == "population":
            data["cognition"]["agents"][2]["policy"]["name"] = "ec_verifier"
        elif nuisance == "task":
            data["world"]["params"]["rounds"] = 11
        else:
            data["conditions"][3]["skin"] = "skins/newsroom-desk.json"
        path.write_text(json.dumps(data), encoding="utf-8")

    root = make_fixture(tmp_path, paired=paired, change=change)
    with pytest.raises(ValueError, match="differ outside the two factorial axes"):
        analyze_study(root)


def test_failed_episodes_cannot_hide_a_confounding_population(tmp_path, monkeypatch):
    def change(source):
        path = source / "scenarios/attr-ledger.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["cognition"]["agents"][2]["policy"]["name"] = "ec_verifier"
        path.write_text(json.dumps(data), encoding="utf-8")

    root = make_fixture(tmp_path, fail=True, monkeypatch=monkeypatch, change=change)
    with pytest.raises(ValueError, match="differ outside the two factorial axes"):
        analyze_study(root)


@pytest.mark.parametrize("field", ["providers", "prompt_template_hashes", "sampling"])
def test_runtime_configuration_drift_is_not_pooled(scripted_artifacts, tmp_path, field):
    root = tmp_path / "artifacts"
    shutil.copytree(scripted_artifacts, root)
    path = root / "agg-priv" / "agg-priv-r000" / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data[field] = {"a1": {"temperature": "1/2"} if field == "sampling" else "changed"}
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="differ outside the two factorial axes"):
        analyze_study(root)


@pytest.mark.parametrize("failed_first", [False, True])
def test_conflicting_repeated_attempts_are_not_selected_by_directory_order(
    scripted_artifacts, tmp_path, monkeypatch, failed_first,
):
    root = tmp_path / "artifacts"
    shutil.copytree(scripted_artifacts, root)
    failed_root = make_fixture(tmp_path / "failed", fail=True, monkeypatch=monkeypatch)
    target = "00-retry" if failed_first else "zz-retry"
    shutil.copytree(failed_root / "agg-priv" / "agg-priv-r000", root / "agg-priv" / target)
    with pytest.raises(ValueError, match="conflicting artifacts for one episode"):
        analyze_study(root)


def test_misplaced_artifact_does_not_contaminate_the_selected_study(
    scripted_artifacts, tmp_path,
):
    root = tmp_path / "artifacts"
    shutil.copytree(scripted_artifacts, root)
    extra = root / "attr-ledger" / "zz-misplaced"
    shutil.copytree(root / "agg-priv" / "agg-priv-r000", extra)
    path = extra / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["study_hash"] = "outside-study"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_study(root)
    assert len(result["episodes"]) == 12
    assert [e["reason"] for e in result["exclusions"]] == ["condition_directory_mismatch"]


@pytest.mark.parametrize("paired", [False, True])
def test_failed_runs_are_exclusions_with_cell_counts(tmp_path, monkeypatch, paired):
    root = make_fixture(tmp_path, fail=True, monkeypatch=monkeypatch, paired=paired)
    result = analyze_study(root)
    assert result["episodes"] == []
    assert len(result["exclusions"]) == 12
    assert {e["reason"] for e in result["exclusions"]} == {"run_failed"}
    assert all(c["failed"] == 3 and c["inclusion_rate"] == "0"
               for c in result["attrition"]["per_cell"].values())
    assert all(e["estimate"] is None for e in result["primary"]["family"].values())
    assert result["seed_protocol"] == ("paired-policy-v2" if paired else "legacy-independent-v1")
    assert result["bootstrap"]["resampling_unit"] == (
        "scenario_block,replicate" if paired else "episode_within_cell"
    )


def test_separate_paired_blocks_may_declare_different_baseline_populations(tmp_path):
    def change(source):
        path = source / "study.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        # Each block is incomplete, so all inference must be unavailable. The
        # different baseline is allowed in an explicitly different block.
        data["conditions"][3]["scenario_block"] = "other-population"
        path.write_text(json.dumps(data), encoding="utf-8")
        path = source / "scenarios/attr-ledger.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["cognition"]["agents"][2]["policy"]["name"] = "ec_verifier"
        path.write_text(json.dumps(data), encoding="utf-8")

    result = analyze_study(make_fixture(tmp_path, paired=True, change=change))
    assert len(result["episodes"]) == 12
    assert all(effect["inference_unavailable"] == "incomplete_paired_blocks"
               and effect["ci95"] is None and effect["p_holm"] is None
               for effect in result["primary"]["family"].values())


def test_completed_invalid_action_episodes_are_included_as_run(tmp_path, monkeypatch):
    root = make_fixture(tmp_path, invalid=True, monkeypatch=monkeypatch)
    result = analyze_study(root)
    assert result["exclusions"] == []
    assert len(result["episodes"]) == 12
    assert all(r["invalid_action_count"] == 1 and r["fallback_abstentions"] == 1
               and r["invalid_action_rate"] == "1/36" for r in result["episodes"])
    assert all(c["invalid_action_count"] == 3 and c["mean_invalid_action_rate"] == "1/36"
               for c in result["attrition"]["per_cell"].values())
    assert result["sensitivity"]["excluding_high_invalid_rate"] == {
        "status": "not_run", "reason": "threshold_not_declared",
    }


@pytest.mark.parametrize(("script", "parser_failures", "rejections", "rate"), [
    (["garbage", "still not JSON"] * 12, 36, 0, "1"),
    (["garbage", "still not JSON", '{"action":{"type":"abstain","reason":"voluntary"}}',
      '{"action":{"type":"inspect_evidence","evidence_id":"missing"}}'] * 4,
     12, 12, "2/3"),
])
def test_parser_failure_abstentions_are_reported_separately(
    tmp_path, monkeypatch, script, parser_failures, rejections, rate,
):
    def malformed_policies(resolved):
        return {a.agent_id: LLMPolicy(a.agent_id, FakeProvider(list(script)), resolved.skin,
                                      max_retries=1) for a in resolved.spec.cognition.agents}

    monkeypatch.setattr(study, "build_policies", malformed_policies)
    result = analyze_study(make_fixture(tmp_path))
    assert result["exclusions"] == []
    assert len(result["episodes"]) == 12
    for row in result["episodes"]:
        assert row["invalid_llm_output_abstentions"] == parser_failures
        assert row["invalid_action_count"] == rejections
        assert row["fallback_abstentions"] == rejections
        assert row["invalid_action_rate"] == rate
    for cell in result["attrition"]["per_cell"].values():
        assert cell["invalid_llm_output_abstentions"] == 3 * parser_failures
        assert cell["invalid_action_count"] == 3 * rejections
        assert cell["fallback_abstentions"] == 3 * rejections
        assert cell["mean_invalid_action_rate"] == rate
    assert result["sensitivity"]["excluding_high_invalid_rate"] == {
        "status": "not_run", "reason": "threshold_not_declared",
    }


def test_paired_design_is_explicit_and_incomplete_blocks_are_flagged(tmp_path):
    root = make_fixture(tmp_path, paired=True)
    result = analyze_study(root)
    assert result["bootstrap"]["resampling_unit"] == "scenario_block,replicate"
    assert result["primary"]["family"]["E1"]["paired_differences"] == ["0", "0", "0"]
    # Losing one episode must not silently turn remaining cells into an unpaired design.
    (root / "agg-priv" / "agg-priv-r000" / "manifest.json").unlink()
    result = analyze_study(root)
    assert result["primary"]["family"]["E1"]["inference_unavailable"] == "incomplete_paired_blocks"


def test_empty_directory_is_an_error(tmp_path):
    result = run_cli("analyze", str(tmp_path))
    assert result.returncode == 2
    assert "no run artifacts" in result.stderr
