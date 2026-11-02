"""Exact readout and retained prediction comparisons for audit feedback."""

from fractions import Fraction
from typing import Any

import audit_closed_form as oracle

TASK_FIELDS = (
    "actions",
    "briefing",
    "budgets",
    "effort",
    "collective_quality",
    "individual_credit",
    "utility",
    "total_effort",
    "total_credit",
    "total_utility",
    "contribution_fraction",
    "correct_slots",
    "wrong_slots",
)
WEIGHTED_FIELDS = {
    "correct_accepted": "correct_slots",
    "wrong_accepted": "wrong_slots",
    "signed_quality": "collective_quality",
    "total_credit": "total_credit",
    "total_effort": "total_effort",
    "contribution_fraction": "contribution_fraction",
    "total_utility": "total_utility",
}


def expected_trace(cell: dict[str, Any]) -> str:
    if cell["trace"] is not None:
        return str(cell["trace"])
    return oracle.trace_for(cell["verdict"], cell["publish_round"])


def action_prediction(record: dict[str, Any]) -> dict[str, Any]:
    cell = record["cell"]
    expected = oracle.literal_schedule(expected_trace(cell), cell["report"])
    return {
        "held": record["actions"] == expected,
        "expected": expected,
        "actual": record["actions"],
    }


def task_prediction(record: dict[str, Any]) -> dict[str, Any]:
    cell = record["cell"]
    expected = oracle.literal_outcome(expected_trace(cell), cell["truth"], cell["report"])
    actual = {key: record[key] for key in expected}
    return {"held": actual == expected, "expected": expected, "actual": actual}


def _compact_prediction(record: dict[str, Any], *, actions: bool) -> dict[str, Any]:
    comparison = action_prediction(record) if actions else task_prediction(record)
    row = {"held": comparison["held"], "expected_trace": expected_trace(record["cell"])}
    if not comparison["held"]:
        row.update(expected=comparison["expected"], actual=comparison["actual"])
    return row


def _weighted_task(terms: list[tuple[Fraction, dict[str, Any]]]) -> dict[str, str | None]:
    values = {
        target: sum((mass * Fraction(record[source]) for mass, record in terms), Fraction())
        for target, source in WEIGHTED_FIELDS.items()
    }
    accepted = values["correct_accepted"] + values["wrong_accepted"]
    return {
        **{key: str(value) for key, value in values.items()},
        "acceptance": str(accepted),
        "selective_accuracy": str(values["correct_accepted"] / accepted) if accepted else None,
    }


def _baseline(records: dict[str, dict[str, Any]], error: str, view: str) -> dict[str, str | None]:
    terms = []
    for record in records.values():
        cell = record["cell"]
        if cell["kind"] != "unaudited_behavior":
            continue
        truth_mass = Fraction(1, 2) if view == "mixed" else Fraction(cell["truth"] == view)
        source_mass = 1 - Fraction(error) if cell["truth"] == cell["report"] else Fraction(error)
        terms.append((truth_mass * source_mass, record))
    return _weighted_task(terms)


def mixtures(records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    index = {
        (
            r["cell"]["truth"],
            r["cell"]["report"],
            r["cell"]["verdict"],
            r["cell"]["publish_round"],
        ): (cid, r)
        for cid, r in records.items()
        if r["cell"]["kind"] == "audited_behavior"
    }
    rows = []
    for law in oracle.law_grid():
        e, a, u = law["source_error"], law["audit_accuracy"], law["unavailable"]
        weights = oracle.cell_weights(e, a, u, law["truth_view"])
        terms, bindings = [], []
        negative = unavailable = available_correct = source_error = Fraction()
        for weight in weights:
            cid, record = index[
                (weight["truth"], weight["report"], weight["verdict"], law["publish_round"])
            ]
            mass = Fraction(weight["weight"])
            terms.append((mass, record))
            bindings.append({"cell_id": cid, "mass": str(mass)})
            actual_verdict = record["publication"]["report"]["verdict"]
            correct_source = weight["truth"] == weight["report"]
            negative += mass * (actual_verdict == "negative")
            unavailable += mass * (actual_verdict == "unavailable")
            source_error += mass * (not correct_source)
            available_correct += mass * (
                actual_verdict != "unavailable" and (actual_verdict == "positive") == correct_source
            )
        actual = {
            **_weighted_task(terms),
            "negative_mass": str(negative),
            "available_correct_mass": str(available_correct),
            "conditional_audit_accuracy": str(available_correct / (1 - unavailable))
            if unavailable < 1
            else None,
        }
        baseline = _baseline(records, e, law["truth_view"])
        checks = {
            "mass_one": sum(mass for mass, _ in terms) == 1,
            "source_error": source_error == Fraction(e),
            "unavailable": unavailable == Fraction(u),
            "available_correct": available_correct == (1 - Fraction(u)) * Fraction(a),
            "closed_form": actual == law["expected"],
            "baseline": baseline == oracle.baseline(e),
        }
        quality_delta = Fraction(str(actual["signed_quality"])) - Fraction(
            str(baseline["signed_quality"])
        )
        expected_delta = (
            12 * (1 - Fraction(u)) * (Fraction(a) + Fraction(e) - 1)
            if law["publish_round"] in (3, 4)
            else Fraction()
        )
        rows.append(
            {
                **law,
                "actual": actual,
                "baseline": baseline,
                "endpoint_weights": bindings,
                "marginal_checks": checks,
                "held": all(checks.values()),
                "quality_contrast": str(quality_delta),
                "quality_contrast_expected": str(expected_delta),
                "quality_contrast_held": quality_delta == expected_delta,
            }
        )
    return rows


def predictions(result: dict[str, Any]) -> dict[str, Any]:
    records = result["episodes"]
    actions = {
        cid: _compact_prediction(record, actions=True)
        for cid, record in records.items()
        if record["cell"]["kind"].endswith("behavior")
    }
    tasks = {cid: _compact_prediction(record, actions=False) for cid, record in records.items()}
    replay = {cid: record["replay_verified"] for cid, record in records.items()}
    return {
        "P1": {"held": all(row["held"] for row in actions.values()), "cells": actions},
        "P2": {"held": all(row["held"] for row in tasks.values()), "cells": tasks},
        "P3": {
            "held": len(result["same_action_integrity"]) == 60
            and all(row["held"] for row in result["same_action_integrity"]),
            "comparisons": len(result["same_action_integrity"]),
        },
        "P4": {
            "held": all(r["publication"]["held"] for r in records.values()),
            "audited_runs": sum(r["cell"]["verdict"] is not None for r in records.values()),
        },
        "P5": {
            "held": all(row["held"] for row in result["truth_controls"]),
            "comparisons": len(result["truth_controls"]),
        },
        "P6": {
            "held": len(result["exact_mixtures"]) == 720
            and all(row["held"] for row in result["exact_mixtures"]),
            "rows": len(result["exact_mixtures"]),
        },
        "P7": {
            "held": all(row["quality_contrast_held"] for row in result["exact_mixtures"])
            and all(row["held"] for row in result["exact_mixtures"]),
            "checks": "full grid includes hand checkpoints, unavailable, zero and late nulls",
        },
        "P8": {
            "held": len(records) == 76
            and all(replay.values())
            and all(row["held"] for row in result["branch_checks"].values()),
            "original_run_replays": replay,
            "separate_branch_fixture_replays": len(result["branch_checks"]),
        },
    }


def measured_trace(record: dict[str, Any]) -> str:
    for trace in oracle.TRACES:
        if record["actions"] == oracle.literal_schedule(trace, record["cell"]["report"]):
            return trace
    return "unmatched"


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Audit feedback: exact synthetic readout",
        "",
        "Exploratory and unfrozen. The [pre-execution design](DESIGN.md) fixes the policy,",
        "all conditional cells and the exact mixture laws. This is a synthetic scripted",
        "response experiment; audit accuracy and independence are assumed, not measured.",
        "",
        f"Retained runs: **{result['behavioral_episodes']} behavioral + "
        f"{result['fixed_action_episodes']} fixed-action controls = {len(result['episodes'])}**.",
        f"All {result['verified_replays']} original chains were replayed. "
        f"The {len(result['branch_checks'])} branch fixtures are separate software checks.",
        f"The {len(result['exact_mixtures'])} exact-law rows are reweightings, not extra runs.",
        "",
        "## Predeclared predictions",
        "",
        "| Prediction | Held | Scope |",
        "|---|---|---|",
    ]
    descriptions = {
        "P1": "52 literal behavioral schedules",
        "P2": "76 literal task outcomes",
        "P3": "60 same-action audit-on/off comparisons",
        "P4": "publication before observation, persistence and hidden-field boundaries",
        "P5": "paired truth controls and first permitted divergence",
        "P6": "720 exact laws, marginals and conditional denominators",
        "P7": "quality threshold, selective accuracy, coverage, zero and late controls",
        "P8": "76 original replays and four separate branch fixtures",
    }
    for name, row in result["predictions"].items():
        lines.append(f"| {name} | {row['held']} | {descriptions[name]} |")
    lines += [
        "",
        "All cells, exact weights, retained failures and complete typed actions appear in",
        "[RESULTS.json](RESULTS.json). A failed prediction remains visible; this report",
        "does not revise its expected value.",
        "",
        "## Publication timing",
        "",
        "Paired columns show R=T first and R!=T second.",
        "",
        "| Finding / round | Measured traces (correct / wrong) | Expected trace | "
        "Accepted slots (correct / wrong) | Effort (correct / wrong) | "
        "Contribution (correct / wrong) | "
        "Quality correct / wrong | Total utility correct / wrong |",
        "|---|---|---|---|---|---|---|---|",
    ]
    records = list(result["episodes"].values())
    for verdict, timing in (
        ("positive", 3),
        ("unavailable", 3),
        ("negative", 3),
        ("negative", 4),
        ("negative", 5),
        ("negative", 6),
    ):
        pair = [
            next(
                r
                for r in records
                if r["cell"]
                == {
                    "kind": "audited_behavior",
                    "truth": truth,
                    "report": "p",
                    "verdict": verdict,
                    "publish_round": timing,
                    "trace": None,
                }
            )
            for truth in ("p", "q")
        ]
        good, bad = pair
        lines.append(
            f"| {verdict} / {timing} | {measured_trace(good)} / {measured_trace(bad)} | "
            f"{expected_trace(good['cell'])} | "
            f"{good['accepted_slots']} / {bad['accepted_slots']} | "
            f"{good['total_effort']} / {bad['total_effort']} | "
            f"{good['contribution_fraction']} / {bad['contribution_fraction']} | "
            f"{good['collective_quality']} / "
            f"{bad['collective_quality']} | {good['total_utility']} / {bad['total_utility']} |"
        )
    if all(result["predictions"][name]["held"] is True for name in ("P1", "P2", "P4")):
        lines += [
            "",
            "Positive and unavailable findings at every declared time follow the full A",
            "schedule. A negative finding at round 5 arrives after c1 already has two",
            "supports: suppressing the redundant second verification round saves effort",
            "without changing its acceptance or signed quality. Round 6 is a task null.",
        ]
    else:
        lines += [
            "",
            "At least one timing/action/task/publication prediction failed. The table",
            "shows measured outcomes and expected traces separately. Consult the retained",
            "cell comparisons before drawing the predeclared timing conclusions.",
        ]
    if all(result["predictions"][name]["held"] is True for name in ("P2", "P3")):
        lines += [
            "",
            "The forced-A controls include wrong accepted claims after early negative",
            "findings. Every same-action task comparison passes, including these controls.",
        ]
    else:
        lines += [
            "",
            "At least one task or same-action comparison failed. The task-invariance",
            "prediction is not established by this response table.",
        ]
    lines += [
        "",
        "## Exact accuracy/coverage tradeoff",
        "",
        "These rows use source-error e=1/10, unavailable probability u=0, round 3",
        "publication and the equal truth mixture. The three source reports are perfectly",
        "correlated despite distinct labels. The released audit error is independent of",
        "that common error by the declared synthetic law.",
        "",
        "| Assumed audit accuracy | Acceptance | Selective accuracy | Signed quality | "
        "Total utility | Quality contrast |",
        "|---|---|---|---|---|---|",
    ]
    selected = [
        row
        for row in result["exact_mixtures"]
        if row["source_error"] == "1/10"
        and row["unavailable"] == "0"
        and row["publish_round"] == 3
        and row["truth_view"] == "mixed"
    ]
    for row in selected:
        actual = row["actual"]
        lines.append(
            f"| {row['audit_accuracy']} | {actual['acceptance']} | "
            f"{actual['selective_accuracy']} | {actual['signed_quality']} | "
            f"{actual['total_utility']} | {row['quality_contrast']} |"
        )
    baseline = selected[0]["baseline"]
    lines.append(
        f"| Unaudited baseline | {baseline['acceptance']} | {baseline['selective_accuracy']}"
        f" | {baseline['signed_quality']} | {baseline['total_utility']} | 0 |"
    )
    if all(result["predictions"][name]["held"] is True for name in ("P6", "P7")):
        lines += [
            "",
            "Under the declared law, early publication changes signed quality by",
            "`12(1-u)(a+e-1)`. At a=3/4, accuracy among accepted claims rises while",
            "acceptance and signed quality fall. At a=9/10 the quality contrast is zero.",
            "At complete unavailability, measured task outcomes equal baseline.",
        ]
    else:
        lines += [
            "",
            "The measured mixture rows fail at least one predeclared formula or marginal",
            "check. The quality threshold and tradeoff are not established by this run;",
            "the exact expected and actual values remain separate in RESULTS.json.",
        ]
    lines += [
        "",
        "Selective accuracy is undefined at zero acceptance. Conditional audit accuracy",
        "is undefined at complete unavailability. Both denominators use JSON null.",
        "",
        "## Execution and interpretation",
        "",
        "Each released verdict was generated by the production endpoint configuration",
        "recorded in its own manifest. Intermediate accuracy/unavailability rows are",
        "explicit exact mixtures of those conditional responses; no manifest was",
        "rewritten to impersonate a nondegenerate execution. The policy ignores opaque",
        "contract hashes and probability settings, using only released public findings.",
        "",
        "No audit effort price, optimized policy, endogenous audit selection, learned",
        "reliability, calibrated deployment accuracy, live provider or human outcome is",
        "estimated. The fixture has one slot and an eight-round horizon. Audit accuracy,",
        "missingness, independence and free cost remain explicit assumptions.",
        "The current LLM EC prompt renderer does not include the audit envelope.",
        "This experiment uses the separately registered scripted veto policy; an",
        "audit-aware LLM prompt would need a separately versioned renderer and design.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python experiments/audit-feedback/audit_feedback.py --out artifacts/audit-feedback-new",
        "python experiments/audit-feedback/audit_feedback.py --check",
        "```",
        "",
        "Original `--out` execution requires clean committed source and a fresh directory.",
        "[SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json) binds its actual execution",
        "commit, dependency lock and source digests. `--check` regenerates sealed runs",
        "and branch fixtures in a temporary directory, replays them and byte-compares",
        "the retained JSON/Markdown readouts. Original raw evidence is audited separately.",
        f"Design hash: `{result['design_hash']}`.",
        "",
    ]
    return "\n".join(lines)
