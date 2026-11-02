"""Independent hand-derived oracle for DESIGN.md; no engine/policy/model imports.

The experiment calculates expectations by weighting sealed events. This module
instead uses the declared closed forms and literal round schedule.
"""

from fractions import Fraction
from typing import Any


def acceptance_probabilities(model: str, rule: str, labels: str,
                             error: Fraction) -> tuple[Fraction, Fraction]:
    if rule == "skeptical" and labels == "collapsed":
        return Fraction(0), Fraction(0)
    if rule == "skeptical" and model == "independent":
        return (1 - error) ** 3, error ** 3
    return 1 - error, error


def expected_metrics(model: str, rule: str, labels: str,
                     error: Fraction) -> dict[str, str | None]:
    correct, wrong = acceptance_probabilities(model, rule, labels, error)
    accepted, signed = correct + wrong, correct - wrong
    return {
        "correct_probability": str(correct),
        "wrong_probability": str(wrong),
        "accepted_probability": str(accepted),
        "abstention_probability": str(1 - accepted),
        "selective_accuracy": str(correct / accepted) if accepted else None,
        "expected_quality": str(12 * signed),
        "expected_effort": str(9 + 15 * accepted),
        "expected_contribution": str(Fraction(3, 8) * (1 + accepted)),
        "expected_total_credit": str(7 * signed),
        "expected_total_utility": str(19 * signed - 9 - 15 * accepted),
    }


def action_schedule(reports: str, rule: str, labels: str) -> list[dict[str, Any]]:
    accepted = rule == "conditional" or (labels == "distinct" and len(set(reports)) == 1)
    citations = [f"e{index}" for index, report in enumerate(reports, 1) if report == reports[0]]
    result = []
    for rnd in range(8):
        for index, agent in enumerate(("a1", "a2", "a3")):
            action: dict[str, Any] = {"type": "withhold"}
            if rnd < 3:
                action = {"type": "inspect_evidence", "evidence_id": ("e1", "e2", "e3")[rnd]}
            elif accepted and rnd == 3:
                action = {"type": "propose_claim", "slot_id": "s1",
                          "proposition_id": reports[0], "evidence_ids": citations}
            elif accepted and rnd in (4, 5):
                target = (("c2", "c1", "c1"), ("c3", "c3", "c2"))[rnd - 4][index]
                action = {"type": "verify_claim", "claim_id": target}
            result.append({"round": rnd, "agent": agent, "action": action})
    return result


def episode_metrics(truth: str, reports: str, rule: str, labels: str,
                    accountability: str) -> dict[str, Any]:
    """Literal accepted/rejected payoffs, separate from the weighted formulas."""
    accepted = rule == "conditional" or (labels == "distinct" and len(set(reports)) == 1)
    if not accepted:
        return {"correct_slots": 0, "wrong_slots": 0, "collective_quality": 0,
                "total_effort": 9, "contribution_fraction": "3/8", "total_credit": "0",
                "total_utility": "-9", "utility": dict.fromkeys(("a1", "a2", "a3"), "-3")}
    correct = truth == reports[0]
    if accountability == "aggregate":
        utilities = ("-5/3",) * 3 if correct else ("-43/3",) * 3
    else:
        utilities = ("-1", "-2", "-2") if correct else ("-15", "-14", "-14")
    return {"correct_slots": int(correct), "wrong_slots": int(not correct),
            "collective_quality": 12 if correct else -12, "total_effort": 24,
            "contribution_fraction": "3/4", "total_credit": "7" if correct else "-7",
            "total_utility": "-5" if correct else "-43",
            "utility": dict(zip(("a1", "a2", "a3"), utilities, strict=True))}
