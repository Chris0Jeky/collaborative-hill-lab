"""Exact factorial contrasts and precommitted literal prediction evaluation."""

import itertools
from fractions import Fraction
from typing import Any

from collaborative_hill.engine.hashing import frac_str

CONTEXTS = ("corroborated-private", "conflicted-private", "echo-private",
            "conflicted-ledger", "defender-private", "unread-private")
TRUTHS = ("accurate", "misleading")
FACTORS = "SHCR"
FACTOR_KEYS = ("evidence_screen", "share_contradictions", "challenge_claims",
               "require_read_citation")
VARIANTS = tuple("".join(bits) for bits in itertools.product("01", repeat=4))
SHORT = dict(zip(CONTEXTS, ("cp", "xp", "ep", "xl", "dp", "up"), strict=True))
METRICS = {"quality": "collective_quality", "contribution": "contribution_fraction",
           "effort": "total_effort", "credit": "total_credit", "utility": "total_utility",
           "accepted_slots": "accepted_slots"}


def cells() -> list[dict[str, str]]:
    return [{"context": context, "truth": truth, "variant": variant}
            for context, truth, variant in itertools.product(CONTEXTS, TRUTHS, VARIANTS)]


def cell_id(item: dict[str, str]) -> str:
    return f"{SHORT[item['context']]}-{item['truth'][0]}-{item['variant']}"


def expected_outcome(context: str, variant: str) -> tuple[int, int, int, str]:
    """Literal K,E,G,A table from DESIGN.md, never derived from policy execution."""
    screen, share, challenge, read = variant
    if context == "corroborated-private":
        return 2, 48, 14, "13/14"
    if context == "echo-private":
        return (2, 48, 14, "13/14") if screen == "0" else (0, 24, 0, "4/7")
    if context == "unread-private":
        return (1, 10, 5, "3/14") if read == "0" else (0, 8, 0, "4/21")
    if context == "conflicted-ledger":
        if screen == "1":
            return 0, 18, 0, "3/7"
        return (2, 42, 14, "11/14") if challenge == "0" else (0, 48, 0, "1")
    private = {
        "000": (2, 41, 14, "16/21"), "001": (2, 40, 14, "11/14"),
        "010": (2, 48, 14, "13/14"), "011": (0, 42, 0, "1"),
        "100": (1, 26, 5, "4/7"), "101": (0, 30, 0, "2/3"),
        "110": (0, 24, 0, "4/7"), "111": (0, 24, 0, "4/7"),
    }
    defender = {
        "000": (2, 41, 14, "16/21"), "001": (2, 40, 14, "11/14"),
        "010": (2, 48, 14, "13/14"), "011": (1, 47, 7, "20/21"),
        "100": (2, 30, 10, "13/21"), "101": (0, 34, 0, "5/7"),
        "110": (2, 36, 10, "16/21"), "111": (0, 40, 0, "6/7"),
    }
    table = private if context == "conflicted-private" else defender
    return table[screen + share + challenge]


def outcome_prediction(record: dict[str, Any]) -> dict[str, Any]:
    item = record["cell"]
    count, effort, credit, contribution = expected_outcome(item["context"], item["variant"])
    sign = 1 if item["truth"] == "accurate" else -1
    expected = {"accepted_slots": count, "quality": sign * 12 * count,
                "effort": effort, "credit": str(sign * credit),
                "utility": str(sign * (12 * count + credit) - effort),
                "contribution": contribution}
    actual = {metric: record[field] for metric, field in METRICS.items()}
    return {"held": actual == expected, "expected": expected, "actual": actual}


def factorial_contrasts(records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """All finite differences, conditional on every unvaried bit; no averaging."""
    result = []
    for context, truth, order in itertools.product(CONTEXTS, TRUTHS, range(1, 5)):
        for positions in itertools.combinations(range(4), order):
            other = [index for index in range(4) if index not in positions]
            for values in itertools.product("01", repeat=len(other)):
                background = ["-"] * 4
                for index, value in zip(other, values, strict=True):
                    background[index] = value
                terms = []
                totals = dict.fromkeys(METRICS, Fraction())
                hashes = []
                for corner in itertools.product("01", repeat=order):
                    bits = background.copy()
                    for index, value in zip(positions, corner, strict=True):
                        bits[index] = value
                    cid = cell_id({"context": context, "truth": truth, "variant": "".join(bits)})
                    coefficient = (-1) ** (order - sum(map(int, corner)))
                    terms.append({"cell_id": cid, "coefficient": coefficient})
                    row = records[cid]
                    hashes.append(row["action_hash"])
                    for metric, field in METRICS.items():
                        totals[metric] += coefficient * Fraction(row[field])
                result.append({
                    "context": context, "truth": truth,
                    "factors": "".join(FACTORS[i] for i in positions),
                    "background": "".join(background), "terms": terms,
                    "deltas": {key: frac_str(value) for key, value in totals.items()},
                    "actions_equal": hashes[0] == hashes[1] if order == 1 else None,
                })
    return result


def predictions(result: dict[str, Any]) -> list[dict[str, Any]]:
    records = result["episodes"]
    literals = [{"cell_id": cid, **outcome_prediction(record)} for cid, record in records.items()]
    first = result["single_factor_contrasts"]
    interactions = result["interactions"]
    nulls = [r for r in first if (
        r["context"] == "corroborated-private"
        or (r["context"] == "conflicted-ledger" and r["factors"] == "H")
        or (r["context"] != "unread-private" and r["factors"] == "R")
        or (r["context"] == "unread-private" and r["factors"] in "SHC")
        or (r["context"] == "echo-private" and r["factors"] != "S"))]
    interaction_checks = []
    for row in interactions:
        expected = None
        if row["context"] == "conflicted-ledger" and row["factors"] == "SC":
            expected = 24
        if row["context"] == "conflicted-private" and row["factors"] == "HC":
            expected = -24 if row["background"][0] == "0" else 12
        if row["context"] == "conflicted-private" and row["factors"] == "SHC":
            expected = 36
        if expected is not None:
            expected *= 1 if row["truth"] == "accurate" else -1
            interaction_checks.append({
                "context": row["context"], "truth": row["truth"],
                "factors": row["factors"], "background": row["background"],
                "expected_quality": str(expected), "actual_quality": row["deltas"]["quality"],
                "held": row["deltas"]["quality"] == str(expected),
            })
    truth = result["truth_controls"]
    bridges = [r["endpoint_bridge"] for r in records.values() if r["endpoint_bridge"] is not None]
    integrity = result["same_action_integrity"]
    return [
        {"prediction": "P1", "held": all(all(row[key] for key in (
            "actions_equal", "observations_equal", "effort_equal", "contribution_equal",
            "quality_opposite", "credit_opposite")) for row in truth), "checked_pairs": len(truth)},
        {"prediction": "P2", "held": all(row["actions_equal"] for row in bridges),
         "checked_endpoints": len(bridges)},
        {"prediction": "P3", "held": all(row["held"] for row in literals),
         "checked_cells": len(literals), "misses": [row for row in literals if not row["held"]]},
        {"prediction": "P4", "held": all(row["actions_equal"] for row in nulls)
         and all(not row["actions_equal"] for row in first
                 if row["context"] == "echo-private" and row["factors"] == "S"),
         "checked_null_contrasts": len(nulls)},
        {"prediction": "P5", "held": all(row["held"] for row in interaction_checks)
         and all(all(value == "0" for value in row["deltas"].values())
                 for row in interactions if row["context"] == "unread-private"),
         "literal_interaction_checks": interaction_checks},
        {"prediction": "P6", "held": all(row["preserved"] for row in integrity),
         "checked_replays": len(integrity)},
    ]


def _range(rows: list[dict[str, Any]], metric: str) -> str:
    values = [Fraction(row["deltas"][metric]) for row in rows]
    lo, hi = min(values), max(values)
    return frac_str(lo) if lo == hi else f"{frac_str(lo)} to {frac_str(hi)}"


def render_report(result: dict[str, Any]) -> str:
    records = result["episodes"]
    held = [p["prediction"] for p in result["predictions"] if p["held"]]
    misses = [p["prediction"] for p in result["predictions"] if not p["held"]]
    lines = [
        "# Evidence Commons: independent rule component ablations", "",
        "Exploratory, unfrozen, deterministic synthetic experiment for issue #95.",
        "The [design and hand predictions](DESIGN.md) were committed before execution.",
        "The previous quality-safeguards experiment and v1 policies remain unchanged.", "",
        f"**{result['behavioral_episodes']} behavioral episodes, "
        f"{result['fixed_action_episodes']} fixed-action controls, "
        f"{result['verified_replays']} verified ledger replays.** Each episode has 14 rounds.",
        "There are 384 conditional single-component contrasts and 396 conditional interactions.",
        "These counts enumerate a chosen finite design; they are not independent samples.", "",
        "## Prediction audit", "",
        f"Held: {', '.join(held) or 'none'}. Missed: {', '.join(misses) or 'none'}.",
        "All misses, if any, remain in RESULTS.json with the original expected values.", "",
        "| Prediction | Scope | Held |", "|---|---|---|",
    ]
    descriptions = ("Truth action/observation identity and signed scores", "Unchanged v1 endpoints",
                    "Complete hand-derived outcome table", "Structural action nulls",
                    "Literal interactions and probe interaction nulls", "Same-action integrity")
    for row, description in zip(result["predictions"], descriptions, strict=True):
        lines.append(f"| {row['prediction']} | {description} | {row['held']} |")
    lines += [
        "", "## Reading of the executed contrasts", "",
        "S = evidence screen; H = share contradictions; C = challenges; R = require read support",
        "among a claim's citations. All four are independently switched; every contrast holds",
        "the other bits fixed. The quorum, costs and action priority remain the same.", "",
        "All accurate/misleading pairs share their observation and action schedules if P1 holds.",
        "Consequently any reduction in accepted false slots has a matched loss of accepted true",
        "slots. No component acquires a truth signal. Corroborated false consensus remains a",
        "negative control, and source labels do not establish independent information.", "",
        "### Citation access probe (separate from the original corpus contexts)", "",
    ]
    for truth in TRUTHS:
        off = records[cell_id({"context": "unread-private", "truth": truth, "variant": "0000"})]
        on = records[cell_id({"context": "unread-private", "truth": truth, "variant": "0001"})]
        lines.append(
            f"- {truth}: R=0 to R=1 changes quality {off['collective_quality']} to "
            f"{on['collective_quality']}, effort {off['total_effort']} to {on['total_effort']}, "
            f"and total utility {off['total_utility']} to {on['total_utility']}.")
    lines += [
        "", "The peer cites a public item the focal agent has not inspected after exhausting",
        "its inspection budget. R gates that verification even though the proposition passes",
        "the two-source screen. In the full-inspection contexts R's null effects are retained.",
        "", "### Why the other components interact", "",
        "Sharing changes who can inspect the contradiction and how many rounds remain.",
        "Challenges precede verification but do not forbid later verification of the same claim.",
        "The existing quorum counts proposals/verifications, not challenges; verification can",
        "therefore reopen peers' participation. In the defender context a policy also cannot",
        "challenge its own proposal. These are context-dependent paths, not additive safeguards.",
        "", "## Matched single-component effects", "",
        "Each row is eight pairs (every setting of the other three bits). Ranges retain the",
        "conditional effects; no averaging across contexts or truths is used.", "",
        "| Context | Truth | Switch | Action-changing pairs | Quality delta | Effort delta | "
        "Total utility delta |", "|---|---|---|---:|---|---|---|",
    ]
    for context, truth, factor in itertools.product(CONTEXTS, TRUTHS, FACTORS):
        rows = [r for r in result["single_factor_contrasts"]
                if (r["context"], r["truth"], r["factors"]) == (context, truth, factor)]
        lines.append(f"| {context} | {truth} | {factor} | "
                     f"{sum(not r['actions_equal'] for r in rows)}/8 | {_range(rows, 'quality')} | "
                     f"{_range(rows, 'effort')} | {_range(rows, 'utility')} |")
    lines += [
        "", "## Nonzero quality interactions", "",
        "Alternating sums, not regression coefficients or averages. A dash in SHCR marks a",
        "varied bit. Every zero and every effort/credit/utility interaction remains in JSON.", "",
        "| Context | Truth | Factors | Background SHCR | Quality interaction |",
        "|---|---|---|---|---:|",
    ]
    for row in result["interactions"]:
        if row["deltas"]["quality"] != "0":
            lines.append(f"| {row['context']} | {row['truth']} | {row['factors']} | "
                         f"{row['background']} | {row['deltas']['quality']} |")
    lines += ["", "## All component combinations", "",
              "Quality and utility are shown as accurate / misleading. Effort and contribution",
              "are the same across the paired truth worlds. Per-agent data and full typed action",
              "schedules are in [RESULTS.json](RESULTS.json)."]
    for context in CONTEXTS:
        lines += ["", f"### {context}", "",
                  "| SHCR | Accepted slots | Quality | Effort | Contribution | Total utility |",
                  "|---|---:|---|---:|---|---|"]
        for variant in VARIANTS:
            good, bad = (records[cell_id({"context": context, "truth": truth, "variant": variant})]
                         for truth in TRUTHS)
            lines.append(f"| {variant} | {good['accepted_slots']} | "
                         f"{good['collective_quality']} / {bad['collective_quality']} | "
                         f"{good['total_effort']} | {good['contribution_fraction']} | "
                         f"{good['total_utility']} / {bad['total_utility']} |")
    lines += [
        "", "## Integrity and limits", "",
        f"Truth controls: {len(result['truth_controls'])}. Endpoint bridges: "
        f"{sum(r['endpoint_bridge'] is not None for r in records.values())}. "
        f"Fixed-action integrity: "
        f"{sum(r['preserved'] for r in result['same_action_integrity'])}/96.",
        "The aggregate controls replay the accurate world's exact action schedules and test",
        "task/total-utility integrity. They do not estimate a behavioral accountability effect.",
        "No incentive certificate, final weights, live provider or human inference is added.",
        "These six diagnostic contexts do not specify how often any corpus structure occurs.",
        "", "## Reproduce", "", "```bash",
        "python experiments/ec-rule-ablation/ec_rule_ablation.py --out artifacts/ec-ablation-new",
        "python experiments/ec-rule-ablation/ec_rule_ablation.py --check", "```", "",
        "`--out` requires committed clean source and a fresh destination; it saves inputs,",
        "sealed runs, controls and readout. `--check` regenerates and replays every run in a",
        "temporary directory, then byte-compares JSON and Markdown. No provider is called.",
        "[SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json) binds the original execution source.",
        f"Study hash: `{result['study_hash']}`.", "",
    ]
    return "\n".join(lines)
