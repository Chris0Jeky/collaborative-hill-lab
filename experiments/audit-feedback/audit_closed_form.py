"""Independent literal and exact-mixture oracle for the committed DESIGN.

This module uses only the standard library. No engine, policy, episode, replay
or recorded result supplies an expected answer. Intermediate probability rows
are exact reweightings of conditional endpoint cases, not additional runs.
"""

import itertools
from fractions import Fraction
from typing import Any

AGENTS = ("a1", "a2", "a3")
TRUTHS = ("p", "q")
VERDICTS = ("positive", "negative", "unavailable")
TIMINGS = (3, 4, 5, 6)
TRACES = ("A", "B", "C", "D")
ERRORS = ("0", "1/10", "1/2", "1")
ACCURACIES = ("0", "1/2", "3/4", "9/10", "1")
UNAVAILABLE = ("0", "1/2", "1")
TRUTH_VIEWS = ("mixed", "p", "q")
TOKENS = {
    "A": ("I1", "I2", "I3", "P", "V1", "V2", "W", "W"),
    "B": ("I1", "I2", "I3", "W", "W", "W", "W", "W"),
    "C": ("I1", "I2", "I3", "P", "W", "W", "W", "W"),
    "D": ("I1", "I2", "I3", "P", "V1", "W", "W", "W"),
}


def exact_probability(value: str) -> Fraction:
    if not isinstance(value, str):
        raise ValueError("probability must be a canonical rational string")
    try:
        probability = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("invalid probability") from exc
    if not 0 <= probability <= 1 or str(probability) != value:
        raise ValueError("probability must be canonical and in [0,1]")
    return probability


def trace_for(verdict: str | None, timing: int | None) -> str:
    if verdict is None and timing is None:
        return "A"
    if verdict not in VERDICTS or type(timing) is not int or timing not in TIMINGS:
        raise ValueError("verdict/timing is outside the declared grid")
    if verdict != "negative":
        return "A"
    return {3: "B", 4: "C", 5: "D", 6: "A"}[timing]


def endpoint_parameters(truth: str, report: str, verdict: str) -> tuple[str, str]:
    if truth not in TRUTHS or report not in TRUTHS or verdict not in VERDICTS:
        raise ValueError("endpoint is outside the declared grid")
    if verdict == "unavailable":
        return "1", "1"
    correct_verdict = (verdict == "positive") == (truth == report)
    return ("1" if correct_verdict else "0"), "0"


def literal_schedule(trace: str, report: str) -> list[dict[str, Any]]:
    if trace not in TRACES or report not in TRUTHS:
        raise ValueError("schedule is outside the declared grid")
    rows = []
    for round_index, token in enumerate(TOKENS[trace]):
        for index, agent in enumerate(AGENTS):
            action: dict[str, Any]
            if token.startswith("I"):
                action = {"type": "inspect_evidence", "evidence_id": "e" + token[1:]}
            elif token == "P":
                action = {"type": "propose_claim", "slot_id": "s1", "proposition_id": report,
                          "evidence_ids": ["e1", "e2", "e3"]}
            elif token == "V1":
                action = {"type": "verify_claim", "claim_id": ("c2", "c1", "c1")[index]}
            elif token == "V2":
                action = {"type": "verify_claim", "claim_id": ("c3", "c3", "c2")[index]}
            else:
                action = {"type": "withhold"}
            rows.append({"round": round_index, "agent": agent, "action": action})
    return rows


def literal_outcome(trace: str, truth: str, report: str) -> dict[str, Any]:
    if trace not in TRACES or truth not in TRUTHS or report not in TRUTHS:
        raise ValueError("task outcome is outside the declared grid")
    effort, verify, contribution = {
        "A": (8, 0, "3/4"), "B": (3, 2, "3/8"),
        "C": (4, 2, "1/2"), "D": (6, 1, "5/8"),
    }[trace]
    accepted = trace in ("A", "D")
    correct = truth == report
    signed = (1 if correct else -1) if accepted else 0
    briefing: list[dict[str, Any]]
    if accepted:
        briefing = [{"slot_id": "s1", "claim_id": "c1", "proposition_id": report,
                     "proposer": "a1", "correct": correct, "provenance_ok": True,
                     "net_support": 2}]
    else:
        briefing = [{"slot_id": "s1", "claim_id": None}]
    utility = 19 * signed - 3 * effort
    return {
        "briefing": briefing, "budgets": {a: {"inspect": 0, "verify": verify} for a in AGENTS},
        "accepted_slots": int(accepted), "correct_slots": int(accepted and correct),
        "wrong_slots": int(accepted and not correct), "collective_quality": 12 * signed,
        "effort": dict.fromkeys(AGENTS, effort), "total_effort": 3 * effort,
        "individual_credit": dict.fromkeys(AGENTS, str(Fraction(7 * signed, 3))),
        "total_credit": str(7 * signed),
        "utility": dict.fromkeys(AGENTS, str(Fraction(utility, 3))),
        "total_utility": str(utility), "contribution_fraction": contribution,
    }


def _task_metrics(correct: Fraction, wrong: Fraction, effort: Fraction,
                  contribution: Fraction) -> dict[str, str | None]:
    accepted = correct + wrong
    signed = correct - wrong
    return {
        "correct_accepted": str(correct), "wrong_accepted": str(wrong),
        "acceptance": str(accepted), "selective_accuracy": str(correct / accepted)
        if accepted else None, "signed_quality": str(12 * signed), "total_credit": str(7 * signed),
        "total_effort": str(effort), "contribution_fraction": str(contribution),
        "total_utility": str(19 * signed - effort),
    }


def baseline(error: str) -> dict[str, str | None]:
    source_error = exact_probability(error)
    return _task_metrics(1 - source_error, source_error, Fraction(24), Fraction(3, 4))


def expectation(error: str, accuracy: str, unavailable: str,
                timing: int) -> dict[str, str | None]:
    e, a, u = (exact_probability(value) for value in (error, accuracy, unavailable))
    if type(timing) is not int or timing not in TIMINGS:
        raise ValueError("timing is outside the declared grid")
    negative = (1 - u) * ((1 - e) * (1 - a) + e * a)
    if timing in (3, 4):
        correct = (1 - e) * (u + (1 - u) * a)
        wrong = e * (u + (1 - u) * (1 - a))
        accepted = correct + wrong
        if timing == 3:
            effort, contribution = 9 + 15 * accepted, 3 * (1 + accepted) / 8
        else:
            effort, contribution = 12 + 12 * accepted, (2 + accepted) / 4
    else:
        correct, wrong = 1 - e, e
        effort = 24 - 6 * negative if timing == 5 else Fraction(24)
        contribution = Fraction(3, 4) - negative / 8 if timing == 5 else Fraction(3, 4)
    return {**_task_metrics(correct, wrong, effort, contribution),
            "negative_mass": str(negative), "available_correct_mass": str((1 - u) * a),
            "conditional_audit_accuracy": str(a) if u < 1 else None}


def cell_weights(error: str, accuracy: str, unavailable: str,
                 truth_view: str) -> list[dict[str, str]]:
    e, a, u = (exact_probability(value) for value in (error, accuracy, unavailable))
    if truth_view not in TRUTH_VIEWS:
        raise ValueError("truth view is outside the declared grid")
    rows = []
    for truth, report, verdict in itertools.product(TRUTHS, TRUTHS, VERDICTS):
        truth_mass = Fraction(1, 2) if truth_view == "mixed" else Fraction(truth == truth_view)
        source_mass = 1 - e if truth == report else e
        if verdict == "unavailable":
            report_mass = u
        elif (verdict == "positive") == (truth == report):
            report_mass = (1 - u) * a
        else:
            report_mass = (1 - u) * (1 - a)
        rows.append({"truth": truth, "report": report, "verdict": verdict,
                     "weight": str(truth_mass * source_mass * report_mass)})
    return rows


def law_grid() -> list[dict[str, Any]]:
    return [{"source_error": e, "audit_accuracy": a, "unavailable": u,
             "publish_round": timing, "truth_view": view,
             "expected": expectation(e, a, u, timing)}
            for e, a, u, timing, view in itertools.product(
                ERRORS, ACCURACIES, UNAVAILABLE, TIMINGS, TRUTH_VIEWS)]
