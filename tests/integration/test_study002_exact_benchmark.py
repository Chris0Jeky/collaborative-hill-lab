"""The post hoc benchmark preserves the fixed readout and its output evidence."""

import hashlib
import importlib.util
import json
import sys
from decimal import ROUND_DOWN, ROUND_UP, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree

import pytest

from collaborative_hill.engine.hashing import canonical_json

STUDY = Path(__file__).resolve().parents[2] / "studies/002-nipd-sensitivity"
RESULTS = STUDY / "RESULTS.json"
INCLUDE = "nb-n3-m2-ptft-include"
EXCLUDE = "nb-n3-m2-ptft-exclude"
pytestmark = pytest.mark.integration


def report_module():
    path = STUDY / "generate_exact_benchmark.py"
    assert path.exists(), "exact benchmark report is not implemented"
    sys.path.insert(0, str(STUDY))
    try:
        spec = importlib.util.spec_from_file_location("study002_exact_report", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(STUDY))


def snapshot(paths):
    return {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}


def test_fixed_results_identity_exact_comparisons_and_positive_unseen_tail():
    module = report_module()
    before = snapshot([RESULTS])
    result = module.build_report(RESULTS, study_dir=STUDY)
    assert snapshot([RESULTS]) == before
    assert result["source_results_sha256"] == hashlib.sha256(before[RESULTS][0]).hexdigest()
    assert result["source_episode_count"] == 221
    assert result["benchmark_version"] == "study002_markov@1"
    assert result["status"] == "post_hoc_analytical_benchmark"
    assert result["cells"][INCLUDE]["episode_mean"]["observed_mean"] == "19/600"
    assert result["cells"][EXCLUDE]["episode_mean"]["observed_mean"] == "121/4800"
    contrast = result["denominator_contrasts"]["n3-m2"]["episode_mean"]
    assert contrast["observed_difference"] == "31/4800"
    assert contrast["expected_difference"] == (
        "134713545610302282625737796611934036291/10103515968309550758039245005706703667200"
    )
    for cell in result["cells"].values():
        assert cell["episodes"] == 32
        final = cell["final_window_mean"]
        assert final["observed_mean"] == final["observed_sample_variance"] == "0"
        assert Fraction(final["expected_mean"]) > 0
        assert Fraction(final["model_episode_variance"]) > 0
        absorption = cell["absorption"]
        assert 0 < Fraction(absorption["F40"]) < Fraction(absorption["F49"]) < 1
        probability = absorption["all_final_windows_zero_probability"]
        assert probability["base_fraction"] == absorption["F40"]
        assert probability["power"] == 32
        assert 0 <= Decimal(probability["decimal_approximation"]) <= 1
        assert absorption["observed_zero_final_windows"] == 32
    canonical_json(result)


def test_independent_difference_adds_mean_variances_without_pairing():
    module = report_module()
    include = {
        "observed_mean": "1/2",
        "expected_mean": "1/3",
        "model_monte_carlo": {"variance_of_mean": "1/36"},
    }
    exclude = {
        "observed_mean": "1/4",
        "expected_mean": "1/6",
        "model_monte_carlo": {"variance_of_mean": "1/100"},
    }
    result = module.independent_difference(include, exclude)
    assert result["observed_difference"] == "1/4"
    assert result["expected_difference"] == "1/6"
    assert result["observed_minus_expected"] == "1/12"
    assert result["model_monte_carlo_variance"] == "17/450"
    assert Decimal("0.19") < Decimal(result["model_mcse_decimal_approximation"]) < Decimal("0.20")


def test_markdown_regeneration_ignores_ambient_decimal_rounding():
    module = report_module()
    report = module.build_report(RESULTS, study_dir=STUDY)
    with localcontext() as context:
        context.rounding = ROUND_DOWN
        down = module.render_markdown(report, "benchmark.svg")
        context.rounding = ROUND_UP
        up = module.render_markdown(report, "benchmark.svg")
    assert down == up


def test_svg_regeneration_ignores_and_preserves_ambient_plot_style():
    import matplotlib as mpl

    module = report_module()
    report = module.build_report(RESULTS, study_dir=STUDY)
    plain = module.render_svg(report)
    with mpl.rc_context({"axes.facecolor": "#000000", "lines.dashed_pattern": [8, 8]}):
        styled = module.render_svg(report)
        assert mpl.rcParams["axes.facecolor"] == "#000000"
    assert plain == styled


@pytest.mark.parametrize(
    "damage",
    [
        "study_hash",
        "roster",
        "sample_count",
        "duplicate_episode",
        "seed",
        "seal",
        "mean",
        "variance",
        "curve",
        "bootstrap",
    ],
)
def test_bad_source_identity_or_inconsistent_summary_fails_before_output(tmp_path, damage):
    module = report_module()
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    measured = data["stochastic"][INCLUDE]["measured"]
    if damage == "study_hash":
        data["study_hashes"]["stochastic"] = "0" * 64
    elif damage == "roster":
        del data["stochastic"][EXCLUDE]
    elif damage == "sample_count":
        measured["mean_cooperation"]["episodes"] = 31
    elif damage == "duplicate_episode":
        data["episodes"][-1] = data["episodes"][-2]
    elif damage == "seed":
        data["episodes"][-1]["seed_root"][0] = 0
    elif damage == "seal":
        data["episodes"][-1]["final_event_hash"] = "unverified"
    elif damage == "mean":
        measured["mean_cooperation"]["mean"] = "1/2"
    elif damage == "variance":
        measured["mean_cooperation"]["sample_variance"] = "0"
    elif damage == "curve":
        measured["mean_cooperation_by_round"][0] = "0"
    else:
        data["bootstrap_samples"] = 4000
    source = tmp_path / "RESULTS.json"
    source.write_text(json.dumps(data), encoding="utf-8")
    before = snapshot([source])
    output = tmp_path / "new" / "benchmark"
    with pytest.raises(ValueError):
        module.generate(source, output, study_dir=STUDY)
    assert snapshot([source]) == before
    assert not output.parent.exists()


def test_regeneration_and_check_preserve_all_three_files_and_source(tmp_path):
    module = report_module()
    output = tmp_path / "first" / "EXACT_PTFT_BENCHMARK"
    module.generate(RESULTS, output, study_dir=STUDY)
    paths = [output.with_suffix(suffix) for suffix in (".json", ".md", ".svg")]
    before = snapshot([RESULTS, *paths])
    module.generate(RESULTS, output, study_dir=STUDY)
    module.generate(RESULTS, output, study_dir=STUDY, check=True)
    assert snapshot([RESULTS, *paths]) == before
    other = tmp_path / "second" / output.name
    module.generate(RESULTS, other, study_dir=STUDY)
    assert [path.read_bytes() for path in paths] == [
        other.with_suffix(path.suffix).read_bytes() for path in paths
    ]
    assert ElementTree.fromstring(paths[-1].read_bytes()).tag == "{http://www.w3.org/2000/svg}svg"


@pytest.mark.parametrize("suffix", [".json", ".md", ".svg"])
def test_divergent_output_is_preserved_and_preflight_prevents_partial_writes(tmp_path, suffix):
    module = report_module()
    output = tmp_path / "benchmark"
    existing = output.with_suffix(suffix)
    existing.write_bytes(b"existing reviewed evidence\n")
    before = snapshot([existing])
    with pytest.raises(ValueError, match="differs"):
        module.generate(RESULTS, output, study_dir=STUDY)
    assert snapshot([existing]) == before
    assert set(tmp_path.iterdir()) == {existing}


def test_check_refuses_missing_or_changed_outputs_without_modifying_them(tmp_path):
    module = report_module()
    output = tmp_path / "missing" / "benchmark"
    with pytest.raises(ValueError, match="missing"):
        module.generate(RESULTS, output, study_dir=STUDY, check=True)
    assert not output.parent.exists()
    module.generate(RESULTS, output, study_dir=STUDY)
    svg = output.with_suffix(".svg")
    svg.write_bytes(svg.read_bytes() + b"\n<!-- reviewed annotation -->\n")
    paths = [output.with_suffix(suffix) for suffix in (".json", ".md", ".svg")]
    before = snapshot(paths)
    with pytest.raises(ValueError, match="differs"):
        module.generate(RESULTS, output, study_dir=STUDY, check=True)
    assert snapshot(paths) == before


def test_output_cannot_replace_the_source_results_or_original_study_inputs(tmp_path):
    module = report_module()
    source = tmp_path / "RESULTS.json"
    source.write_bytes(RESULTS.read_bytes())
    before = snapshot([source, STUDY / "study.json", STUDY / "README.md"])
    for output in (source.with_suffix(""), STUDY / "study", STUDY / "README"):
        with pytest.raises(ValueError, match="preserve"):
            module.generate(source, output, study_dir=STUDY)
    assert snapshot([source, STUDY / "study.json", STUDY / "README.md"]) == before
