"""Post hoc ideal-Bernoulli benchmark of the fixed Study 002 RESULTS.json readout.

No episodes or bootstrap draws are run. Input identities and summaries are
audited at report level; raw ledger chains are not reverified by this script.
"""

import argparse
import hashlib
import io
import json
import re
import tempfile
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Any
from urllib.parse import quote

import study002_markov
from study002_markov import benchmark, independent_probability_power, monte_carlo_standard_error
from study002_model import (
    BOOTSTRAP_SAMPLES,
    ROUNDS,
    SEED,
    STOCHASTIC_REPLICATES,
    STUDY_DIR,
    WINDOW,
    Condition,
    conditions,
    generated_files,
)
from study002_model import (
    generate as check_design,
)

from collaborative_hill.engine.hashing import canonical_json, frac_str
from collaborative_hill.experiments.study import load_study, study_hash

REPORT_VERSION = "study002_exact_benchmark@1"
FIXED_HASHES = {
    "deterministic": "175140649a108a4f5ea33a4c7a1decf74cdc777a9d47057839a54b7e24ed22eb",
    "stochastic": "728392210a4aa437ba2a1f6e4d8be73f99b96b896e596e81a8969c121623754f",
}
POPULATIONS = ((3, 2), (5, 4), (5, 3))
SUFFIXES = (".json", ".md", ".svg")


def _fraction(value: Any, label: str) -> Fraction:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an exact fraction string")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid exact fraction for {label}") from exc


def _average(values: list[Fraction]) -> Fraction:
    return sum(values, Fraction()) / len(values)


def _verify_metric(summary: dict[str, Any], rows: list[dict[str, Any]], metric: str) -> None:
    values = [_fraction(row[metric], metric) for row in rows]
    average = _average(values)
    variance = sum(((value - average) ** 2 for value in values), Fraction()) / (len(values) - 1)
    if (
        summary["episodes"] != len(rows)
        or _fraction(summary["mean"], metric) != average
        or _fraction(summary["sample_variance"], metric) != variance
    ):
        raise ValueError(f"inconsistent episode count, mean or sample variance for {metric}")


def _validate_episodes(
    data: dict[str, Any], catalog: dict[str, Condition]
) -> dict[
    str,
    list[dict[str, Any]],
]:
    rows = data["episodes"]
    if not isinstance(rows, list) or len(rows) != 221:
        raise ValueError("expected all 221 original episode records")
    by_condition: dict[str, list[dict[str, Any]]] = {cid: [] for cid in catalog}
    identities, seals = set(), set()
    for row in rows:
        cid, replicate = row["condition_id"], row["replicate"]
        if cid not in catalog:
            raise ValueError("unexpected episode condition")
        condition = catalog[cid]
        count = 1 if condition.deterministic else STOCHASTIC_REPLICATES
        if type(replicate) is not int or not 0 <= replicate < count:
            raise ValueError("invalid episode replicate")
        identity = (cid, replicate)
        if identity in identities:
            raise ValueError("duplicate episode identity")
        identities.add(identity)
        if row["run_id"] != f"{cid}-r{replicate:03d}" or row["seed_root"] != [SEED, cid, replicate]:
            raise ValueError("episode run or independent seed identity mismatch")
        seal = row["final_event_hash"]
        if (
            not isinstance(seal, str)
            or re.fullmatch(r"[0-9a-f]{64}", seal) is None
            or seal in seals
        ):
            raise ValueError("invalid or duplicate retained terminal event hash")
        seals.add(seal)
        first_zero = row["first_all_d_round"]
        if first_zero is not None and (type(first_zero) is not int or not 0 <= first_zero < ROUNDS):
            raise ValueError("invalid observed first all-D round")
        for metric in ("mean_cooperation", "final_window_cooperation"):
            if not 0 <= _fraction(row[metric], metric) <= 1:
                raise ValueError("observed cooperation must lie in [0, 1]")
        zero_window = _fraction(row["final_window_cooperation"], "final window") == 0
        if zero_window != (first_zero is not None and first_zero <= ROUNDS - WINDOW):
            raise ValueError("final window and absorption record disagree")
        by_condition[cid].append(row)
    for cid, condition in catalog.items():
        expected = 1 if condition.deterministic else STOCHASTIC_REPLICATES
        if len(by_condition[cid]) != expected:
            raise ValueError("condition episode roster is incomplete")
    return by_condition


def _validate_source(data: dict[str, Any], study_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Audit report identity and arithmetic; this is not a raw-ledger replay."""
    canonical_json(data)
    fixed = {
        "schema_version": 1,
        "analysis_version": "study002@1",
        "status": "unfrozen_exploratory_draft",
        "episode_count": 221,
        "seed": SEED,
        "seed_protocol": "legacy-independent-v1",
        "rounds": ROUNDS,
        "final_window": WINDOW,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "bootstrap_seed": SEED,
        "study_hashes": FIXED_HASHES,
    }
    if any(data.get(key) != expected for key, expected in fixed.items()):
        raise ValueError("RESULTS identity does not match the fixed Study 002 readout")
    check_design(study_dir, check=True)
    for component, source in (
        ("deterministic", study_dir),
        ("stochastic", study_dir / "stochastic"),
    ):
        spec, resolved = load_study(source)
        if study_hash(spec, resolved) != FIXED_HASHES[component]:
            raise ValueError("current study inputs do not match the fixed readout hashes")
    catalog = {condition.condition_id: condition for condition in conditions()}
    for component, deterministic in (("deterministic", True), ("stochastic", False)):
        if set(data[component]) != {
            cid for cid, c in catalog.items() if c.deterministic == deterministic
        }:
            raise ValueError("RESULTS condition roster does not match the fixed design")
    rows = _validate_episodes(data, catalog)
    for cid, condition in catalog.items():
        if condition.deterministic:
            cell = data["deterministic"][cid]
            if cell["episodes"] != 1 or any(
                cell["measured"][metric] != rows[cid][0][metric]
                for metric in ("mean_cooperation", "final_window_cooperation", "first_all_d_round")
            ):
                raise ValueError("inconsistent deterministic episode summary")
            continue
        measured = data["stochastic"][cid]["measured"]
        for metric in ("mean_cooperation", "final_window_cooperation"):
            _verify_metric(measured[metric], rows[cid], metric)
        curve = [
            _fraction(value, "measured trajectory")
            for value in measured["mean_cooperation_by_round"]
        ]
        if (
            len(curve) != ROUNDS
            or any(not 0 <= value <= 1 for value in curve)
            or curve[0] != Fraction(condition.reciprocators, condition.n_agents)
            or _average(curve) != _fraction(measured["mean_cooperation"]["mean"], "mean")
            or _average(curve[-WINDOW:])
            != _fraction(measured["final_window_cooperation"]["mean"], "final mean")
        ):
            raise ValueError("measured trajectory disagrees with the episode summaries")
        absorbed = sum(row["first_all_d_round"] is not None for row in rows[cid])
        if (
            measured["absorbed_by_round_49"] != absorbed
            or measured["censored_at_50"] != STOCHASTIC_REPLICATES - absorbed
        ):
            raise ValueError("inconsistent observed absorption count")
    return rows


def _metric_comparison(measured: dict[str, Any], expected: str, variance: str) -> dict[str, Any]:
    return {
        "observed_mean": measured["mean"],
        "observed_sample_variance": measured["sample_variance"],
        "expected_mean": expected,
        "model_episode_variance": variance,
        "observed_minus_expected": frac_str(Fraction(measured["mean"]) - Fraction(expected)),
        "model_monte_carlo": monte_carlo_standard_error(variance, replicates=STOCHASTIC_REPLICATES),
    }


def independent_difference(include: dict[str, Any], exclude: dict[str, Any]) -> dict[str, Any]:
    """Add the two mean variances; equal replicate labels do not create pairs."""
    observed = Fraction(include["observed_mean"]) - Fraction(exclude["observed_mean"])
    expected = Fraction(include["expected_mean"]) - Fraction(exclude["expected_mean"])
    variance = Fraction(include["model_monte_carlo"]["variance_of_mean"]) + Fraction(
        exclude["model_monte_carlo"]["variance_of_mean"]
    )
    # Already a variance of the difference of means: use only the helper's sqrt,
    # not its n=1 metadata, which would misdescribe the two 32-episode samples.
    display = monte_carlo_standard_error(frac_str(variance), replicates=1)
    return {
        "observed_difference": frac_str(observed),
        "expected_difference": frac_str(expected),
        "observed_minus_expected": frac_str(observed - expected),
        "model_monte_carlo_variance": frac_str(variance),
        "model_mcse_decimal_approximation": display["standard_error_decimal_approximation"],
        "mcse_approximation_significant_digits": display["approximation_significant_digits"],
        "variance_rule": "Var(mean_include) + Var(mean_exclude); independent conditions",
    }


def build_report(results: Path, *, study_dir: Path = STUDY_DIR) -> dict[str, Any]:
    source_bytes = results.read_bytes()
    try:
        data = json.loads(source_bytes)
        rows = _validate_source(data, study_dir)
    except (KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
        raise ValueError("malformed Study 002 RESULTS report") from exc
    cells = {}
    versions = set()
    for condition in conditions():
        if condition.deterministic:
            continue
        assert condition.denominator is not None
        cid = condition.condition_id
        analytical = benchmark(
            condition.n_agents,
            condition.reciprocators,
            condition.denominator,
            rounds=ROUNDS,
            window=WINDOW,
        )
        versions.add(analytical["analysis_version"])
        original = data["stochastic"][cid]
        expected = original["analytical_expectation"]
        if any(
            analytical[key] != expected[key]
            for key in (
                "mean_cooperation",
                "final_window_cooperation",
                "cooperation_by_round",
            )
        ):
            raise ValueError("Markov means disagree with the original closed-form expectations")
        measured = original["measured"]
        cells[cid] = {
            "n_agents": condition.n_agents,
            "reciprocators": condition.reciprocators,
            "fixed_defectors": condition.n_agents - condition.reciprocators,
            "denominator": condition.denominator,
            "episodes": len(rows[cid]),
            "episode_mean": _metric_comparison(
                measured["mean_cooperation"],
                analytical["mean_cooperation"],
                analytical["variance_mean_cooperation"],
            ),
            "final_window_mean": _metric_comparison(
                measured["final_window_cooperation"],
                analytical["final_window_cooperation"],
                analytical["variance_final_window_cooperation"],
            ),
            "absorption": {
                "F40": analytical["final_window_all_d_probability"],
                "F49": analytical["absorption_probability_by_last_round"],
                "observed_absorbed_by_round_40": sum(
                    row["first_all_d_round"] is not None and row["first_all_d_round"] <= 40
                    for row in rows[cid]
                ),
                "observed_absorbed_by_round_49": measured["absorbed_by_round_49"],
                "observed_zero_final_windows": sum(
                    Fraction(row["final_window_cooperation"]) == 0 for row in rows[cid]
                ),
                "all_final_windows_zero_probability": independent_probability_power(
                    analytical["final_window_all_d_probability"], power=len(rows[cid])
                ),
            },
            "observed_cooperation_by_round": measured["mean_cooperation_by_round"],
            "analytical_cooperation_by_round": analytical["cooperation_by_round"],
        }
    if len(versions) != 1:
        raise ValueError("mixed analytical benchmark versions")
    contrasts = {}
    for n, m in POPULATIONS:
        include, exclude = [
            cells[f"nb-n{n}-m{m}-ptft-{suffix}"] for suffix in ("include", "exclude")
        ]
        contrasts[f"n{n}-m{m}"] = {
            "direction": "include_self minus exclude_self",
            "episodes_include": include["episodes"],
            "episodes_exclude": exclude["episodes"],
            **{
                metric: independent_difference(include[metric], exclude[metric])
                for metric in ("episode_mean", "final_window_mean")
            },
        }
        original = data["denominator_contrasts"][f"n{n}-m{m}"]
        calculated = contrasts[f"n{n}-m{m}"]["episode_mean"]
        if (
            original["measured_difference"] != calculated["observed_difference"]
            or original["analytical_expected_difference"] != calculated["expected_difference"]
            or original["episodes_include"] != 32
            or original["episodes_exclude"] != 32
        ):
            raise ValueError("original denominator contrast is inconsistent")
    result = {
        "schema_version": 1,
        "report_version": REPORT_VERSION,
        "benchmark_version": next(iter(versions)),
        "status": "post_hoc_analytical_benchmark",
        "model": "ideal_rational_bernoulli",
        "source_results_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(
            Path(study002_markov.__file__).read_bytes()
        ).hexdigest(),
        "source_analysis_version": data["analysis_version"],
        "source_episode_count": len(data["episodes"]),
        "study_hashes": data["study_hashes"],
        "seed_protocol": data["seed_protocol"],
        "seed": data["seed"],
        "rounds": ROUNDS,
        "final_window_rounds": list(range(ROUNDS - WINDOW, ROUNDS)),
        "stochastic_episodes_per_condition": STOCHASTIC_REPLICATES,
        "source_bootstrap": {
            "samples": data["bootstrap_samples"],
            "seed": data["bootstrap_seed"],
            "status": "retained unchanged in RESULTS; not recomputed here",
        },
        "source_audit_scope": (
            "RESULTS identities and internal arithmetic; no fresh raw-ledger chain verification"
        ),
        "sampler_scope": (
            "Ideal rational Bernoulli model; existing PRNG and binary-float sampling unchanged"
        ),
        "cells": cells,
        "denominator_contrasts": contrasts,
    }
    canonical_json(result)
    return result


def _decimal(value: str) -> str:
    fraction = Fraction(value)
    with localcontext(Context(prec=24, rounding=ROUND_HALF_EVEN)):
        return format(Decimal(fraction.numerator) / Decimal(fraction.denominator), ".8g")


def _label(cell: dict[str, Any]) -> str:
    return f"N={cell['n_agents']}, m={cell['reciprocators']}"


def render_markdown(report: dict[str, Any], figure_name: str) -> str:
    lines = [
        "# Study 002 — post hoc exact pTFT benchmark",
        "",
        "**Post hoc analytical extension of the existing unfrozen exploratory readout.** "
        "The six pTFT cells retain their original 32 independently seeded episodes each. "
        "The source contains 221 episodes in total, including 29 deterministic controls. "
        "No new episodes, parameter fitting, exclusions or bootstrap draws are introduced.",
        "",
        "The ideal rational Bernoulli model has positive expected final-window cooperation "
        "in every mixed population, although all 32 observed final windows in each cell were zero. "
        "The exact absorption calculation below quantifies how probable that finite-sample event "
        "is under this ideal model. Zero observed variance is not zero model variance.",
        "",
        "## Observed and analytical trajectories",
        "",
        "![Observed mean cooperation and ideal analytical trajectories for three populations.]"
        f"({quote(figure_name)})",
        "",
        "Cooperation is cooperative votes divided by all eligible votes, including fixed AllD "
        "votes. Each observed line averages 32 episodes; the analytical line is an expectation, "
        "not a trajectory that each episode must follow. All panels cover t=0,…,49 on the same "
        "scale; the shaded region is t=40,…,49. Tiny positive analytical tails may be visually "
        "indistinguishable from zero on this scale.",
        "",
        "## Episode means and Monte Carlo variability",
        "",
        "Let A=(1/50)Σ(t=0…49) c_t. The model column Var(A) is the exact single-episode "
        "variance, including covariance across rounds. The empirical s² is the original "
        "between-episode sample variance. Model MCSE is sqrt(Var(A)/32). It describes the "
        "sampling variability of an average of 32 independent ideal-model episodes; it is "
        "neither an empirical variance estimate nor a normal confidence interval. "
        "All decimal entries below are approximations; the JSON retains exact fractions.",
        "",
        "| Population | Denominator | E[A] | Observed mean | Observed − E[A] | "
        "Model Var(A) | Empirical s² | Model MCSE |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in report["cells"].values():
        row = cell["episode_mean"]
        lines.append(
            f"| {_label(cell)} | {cell['denominator']} | {_decimal(row['expected_mean'])} | "
            f"{_decimal(row['observed_mean'])} | {_decimal(row['observed_minus_expected'])} | "
            f"{_decimal(row['model_episode_variance'])} | "
            f"{_decimal(row['observed_sample_variance'])} | "
            f"≈{row['model_monte_carlo']['standard_error_decimal_approximation']} |"
        )
    lines += [
        "",
        "## Final ten-round windows and absorption",
        "",
        "Let B=(1/10)Σ(t=40…49)c_t and T₀ be the first all-D round. Zero cooperation is "
        "absorbing, so F40=P(T₀≤40) is exactly the probability that an episode's entire final "
        "window is zero. F49=P(T₀≤49) instead describes absorption by the last observed round. "
        "For one cell's 32 independent ideal-model episodes, P(all 32 final windows zero)=F40^32. "
        "This is a model event probability, not a p-value. A displayed ≈1 can represent a "
        "strictly subunit probability; the exact base fraction and exponent remain authoritative.",
        "",
        "| Population | Denominator | E[B] | Observed mean | Model Var(B) | Model MCSE |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for cell in report["cells"].values():
        row = cell["final_window_mean"]
        lines.append(
            f"| {_label(cell)} | {cell['denominator']} | {_decimal(row['expected_mean'])} | "
            f"{row['observed_mean']} | {_decimal(row['model_episode_variance'])} | "
            f"≈{row['model_monte_carlo']['standard_error_decimal_approximation']} |"
        )
    lines += [
        "",
        "Every cell's empirical final-window sample variance is zero; the model variances "
        "above remain positive.",
        "",
        "| Population | Denominator | F40 | F49 | P(all 32 final windows zero) | "
        "Observed zero windows / n |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for cell in report["cells"].values():
        row = cell["absorption"]
        probability = row["all_final_windows_zero_probability"]
        lines.append(
            f"| {_label(cell)} | {cell['denominator']} | ≈{_decimal(row['F40'])} | "
            f"≈{_decimal(row['F49'])} | ≈{probability['decimal_approximation']} | "
            f"{row['observed_zero_final_windows']}/{cell['episodes']} |"
        )
    lines += [
        "",
        "## Independent denominator contrasts",
        "",
        "Each contrast is include-self minus exclude-self. Equal replicate numbers are labels, "
        "not matched pairs: the seed protocol allocates independent condition streams. "
        "The model variance of each difference is Var(mean_include)+Var(mean_exclude), "
        "with each cell mean variance equal to its single-episode variance divided by 32. "
        "The displayed MCSE is the square root of that sum; no covariance is subtracted.",
        "",
        "| Population | Outcome | Expected difference | Observed difference | "
        "Observed − expected | Model MC variance | Model MCSE |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for population, contrast in report["denominator_contrasts"].items():
        for metric, label in (
            ("episode_mean", "50-round mean"),
            ("final_window_mean", "Final-window mean"),
        ):
            row = contrast[metric]
            lines.append(
                f"| {population} | {label} | {_decimal(row['expected_difference'])} | "
                f"{_decimal(row['observed_difference'])} | "
                f"{_decimal(row['observed_minus_expected'])} | "
                f"{_decimal(row['model_monte_carlo_variance'])} | "
                f"≈{row['model_mcse_decimal_approximation']} |"
            )
    lines += [
        "",
        "## Derivation, provenance and limits",
        "",
        "X_t counts cooperating pTFT agents among m reciprocators and N−m fixed defectors, "
        "with X₀=m and c_t=X_t/N. Include-self gives X_(t+1)|X_t=x ~ Binomial(m,x/N). "
        "Exclude-self gives the sum of independent Binomial(x,(x−1)/(N−1)) and "
        "Binomial(m−x,x/(N−1)) variables. The finite transition matrix and moments are "
        "computed with rational arithmetic in [study002_markov.py](study002_markov.py).",
        "",
        "The conditional mean is λx, with λ=m/N or (m−1)/(N−1). For t≥s, "
        "Cov(X_s,X_t)=λ^(t−s)Var(X_s). Summing marginal variances and twice the "
        "cross-time covariances, then dividing by (N×window length)², gives each "
        "window-mean variance. This is an analytical extension developed after the observed "
        "readout, not an additional preregistered prediction.",
        "",
        f"- Report version: `{report['report_version']}`; "
        f"benchmark version: `{report['benchmark_version']}`.",
        f"- Source [RESULTS.json](RESULTS.json) SHA-256: `{report['source_results_sha256']}`.",
        f"- Benchmark source SHA-256: `{report['benchmark_source_sha256']}`.",
        *[
            f"- {component} study hash: `{digest}`"
            for component, digest in report["study_hashes"].items()
        ],
        "- The generator checks both current study hashes, the condition roster, all 221 "
        "episode identities and retained terminal hash formats, and reconciles reported "
        "means/variances with per-episode outcomes. It reads the sealed-derived report; "
        "it does not independently reverify or replay the original raw ledger chains. "
        "The original terminal hashes remain inspectable in RESULTS.json.",
        "- The original [RESULTS.md](RESULTS.md) and its 2,000-draw bootstrap readout remain "
        "unchanged, including the reported marginal interval discrepancy. This extension "
        "does not replace that readout with normal intervals or significance decisions.",
        "- The benchmark assumes ideal independent rational Bernoulli choices. The existing "
        "simulator uses finite-precision PRNG draws and binary-floating-point probabilities. "
        "Its sampling semantics, study inputs and source results are unchanged. Neither "
        "human nor LLM behavior is inferred.",
        "",
        "## Reproduce without new episodes",
        "",
        "From the repository root with the committed dependencies installed:",
        "",
        "```sh",
        "python studies/002-nipd-sensitivity/generate_exact_benchmark.py --check",
        "python studies/002-nipd-sensitivity/generate_exact_benchmark.py "
        "--output artifacts/exact-benchmark/EXACT_PTFT_BENCHMARK",
        "```",
        "",
        "`--check` regenerates the JSON, Markdown and SVG in temporary files and compares "
        "them byte-for-byte without rewriting existing evidence. Ordinary generation permits "
        "fresh outputs or byte-identical no-ops and refuses divergent existing files. "
        "SVG generation uses a fixed hash salt, fixed styling and no date metadata.",
        "",
    ]
    return "\n".join(lines)


def render_svg(report: dict[str, Any]) -> bytes:
    import matplotlib as mpl
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.ticker import PercentFormatter

    with mpl.rc_context():
        mpl.rcdefaults()
        mpl.rcParams.update(
            {
                "font.family": "DejaVu Sans",
                "font.size": 10,
                "svg.fonttype": "none",
                "svg.hashsalt": REPORT_VERSION,
                "axes.edgecolor": "#52606D",
                "text.color": "#1F2933",
                "axes.labelcolor": "#1F2933",
            }
        )
        figure = Figure(figsize=(12.6, 4.7), facecolor="white")
        FigureCanvasAgg(figure)
        axes = figure.subplots(1, 3, sharex=True, sharey=True)
        colors = {"include": "#1967A3", "exclude": "#B36A08"}
        markers = {"include": "o", "exclude": "s"}
        for axis, (n, m) in zip(axes, POPULATIONS, strict=True):
            axis.axvspan(40, 49, color="#EDF0F2", zorder=0)
            for suffix in ("include", "exclude"):
                cell = report["cells"][f"nb-n{n}-m{m}-ptft-{suffix}"]
                observed = [
                    float(Fraction(value)) for value in cell["observed_cooperation_by_round"]
                ]
                expected = [
                    float(Fraction(value)) for value in cell["analytical_cooperation_by_round"]
                ]
                axis.plot(
                    range(ROUNDS),
                    observed,
                    color=colors[suffix],
                    linewidth=1.6,
                    marker=markers[suffix],
                    markersize=3.1,
                    markevery=2,
                    label=f"Observed · {suffix}-self",
                    zorder=3,
                )
                axis.plot(
                    range(ROUNDS),
                    expected,
                    color=colors[suffix],
                    linewidth=1.7,
                    linestyle="--" if suffix == "include" else ":",
                    label=f"Ideal expectation · {suffix}-self",
                    zorder=2,
                )
            axis.set_title(f"N={n}, m={m}, fixed AllD={n - m}", fontsize=11, pad=12)
            axis.set_xlim(0, 49)
            axis.set_ylim(-0.025, 1.025)
            axis.set_xticks([0, 10, 20, 30, 40, 49])
            axis.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
            axis.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
            axis.set_xlabel("Round t")
            axis.grid(axis="y", color="#D9E0E5", linewidth=0.6)
            axis.spines[["top", "right"]].set_visible(False)
            axis.tick_params(axis="both", length=3, colors="#52606D")
        axes[0].set_ylabel("Cooperative votes / all eligible votes")
        handles, labels = axes[0].get_legend_handles_labels()
        figure.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.87),
            ncol=4,
            frameon=False,
            fontsize=9,
            handlelength=2.8,
            columnspacing=1.6,
        )
        figure.suptitle(
            "pTFT cooperation: observed means and ideal analytical expectations",
            fontsize=15,
            fontweight="bold",
            y=0.99,
        )
        figure.text(
            0.5,
            0.91,
            "32 independent observed episodes per denominator in every panel · t=0–49",
            ha="center",
            fontsize=10,
        )
        figure.text(
            0.06,
            0.035,
            "Post hoc ideal rational Bernoulli benchmark · Shading: final window t=40–49. "
            "Positive analytical tails remain exact in the accompanying JSON.",
            fontsize=9,
        )
        figure.subplots_adjust(left=0.075, right=0.985, bottom=0.18, top=0.71, wspace=0.14)
        stream = io.BytesIO()
        figure.savefig(stream, format="svg", metadata={"Date": None, "Creator": REPORT_VERSION})
        # Matplotlib emits trailing spaces in path attributes; normalize their
        # insignificant whitespace so the generated artifact is a clean Git diff.
        return b"\n".join(line.rstrip() for line in stream.getvalue().splitlines()) + b"\n"


def _validate_output(results: Path, output: Path, study_dir: Path) -> None:
    protected = {(study_dir / relative).resolve() for relative in generated_files()}
    protected.update(
        (study_dir / name).resolve()
        for name in (
            "RESULTS.json",
            "RESULTS.md",
            "README.md",
            "SOURCE_PROVENANCE.json",
            "study.lock.json",
            "stochastic/study.lock.json",
        )
    )
    protected.add(results.resolve())
    if any(output.with_suffix(suffix).resolve() in protected for suffix in SUFFIXES):
        raise ValueError("benchmark outputs must preserve source RESULTS and original study inputs")


def generate(
    results: Path, output: Path, *, study_dir: Path = STUDY_DIR, check: bool = False
) -> dict[str, Any]:
    _validate_output(results, output, study_dir)
    report = build_report(results, study_dir=study_dir)
    targets = {
        output.with_suffix(".json"): (json.dumps(report, sort_keys=True, indent=2) + "\n").encode(),
        output.with_suffix(".md"): render_markdown(
            report, output.with_suffix(".svg").name
        ).encode(),
        output.with_suffix(".svg"): render_svg(report),
    }
    if check:
        with tempfile.TemporaryDirectory(prefix="chl-study002-exact-check-") as temporary:
            for target, content in targets.items():
                fresh = Path(temporary) / target.name
                fresh.write_bytes(content)
                if not target.exists():
                    raise ValueError(f"missing exact benchmark output: {target.name}")
                if target.read_bytes() != fresh.read_bytes():
                    raise ValueError(f"exact benchmark output differs: {target.name}")
        return report
    for target, content in targets.items():
        if target.exists() and target.read_bytes() != content:
            raise ValueError(f"output differs from existing {target.name}; choose a fresh prefix")
    output.parent.mkdir(parents=True, exist_ok=True)
    for target, content in targets.items():
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(content)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=STUDY_DIR / "RESULTS.json")
    parser.add_argument("--study-dir", type=Path, default=STUDY_DIR)
    parser.add_argument(
        "--output",
        type=Path,
        default=STUDY_DIR / "EXACT_PTFT_BENCHMARK",
        help="output prefix for .json, .md and .svg",
    )
    parser.add_argument(
        "--check", action="store_true", help="read-only byte-for-byte regeneration check"
    )
    args = parser.parse_args()
    try:
        report = generate(args.results, args.output, study_dir=args.study_dir, check=args.check)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    action = "Verified" if args.check else "Generated"
    print(
        f"{action} post hoc exact benchmark for {len(report['cells'])} fixed 32-episode cells; "
        f"source RESULTS SHA-256={report['source_results_sha256']}"
    )


if __name__ == "__main__":
    main()
