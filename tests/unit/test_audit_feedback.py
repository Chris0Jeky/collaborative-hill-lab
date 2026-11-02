"""Literal audit-feedback predictions, independent of any executed episode."""

import importlib.util
import itertools
from fractions import Fraction
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2] / "experiments/audit-feedback/audit_closed_form.py"
SPEC = importlib.util.spec_from_file_location("audit_closed_form", PATH)
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


@pytest.mark.parametrize("verdict,timing,trace", [
    ("positive", 3, "A"), ("positive", 4, "A"), ("positive", 5, "A"),
    ("positive", 6, "A"), ("unavailable", 3, "A"), ("unavailable", 4, "A"),
    ("unavailable", 5, "A"), ("unavailable", 6, "A"),
    ("negative", 3, "B"), ("negative", 4, "C"), ("negative", 5, "D"),
    ("negative", 6, "A"), (None, None, "A"),
])
def test_timing_table_is_literal(verdict, timing, trace):
    assert oracle.trace_for(verdict, timing) == trace


@pytest.mark.parametrize("trace,types", [
    ("A", ["inspect_evidence"] * 3 + ["propose_claim", "verify_claim", "verify_claim"]
     + ["withhold"] * 2),
    ("B", ["inspect_evidence"] * 3 + ["withhold"] * 5),
    ("C", ["inspect_evidence"] * 3 + ["propose_claim"] + ["withhold"] * 4),
    ("D", ["inspect_evidence"] * 3 + ["propose_claim", "verify_claim"] + ["withhold"] * 3),
])
def test_literal_schedule_has_explicit_citations_and_other_agent_claims(trace, types):
    rows = oracle.literal_schedule(trace, "q")
    assert [(r["round"], r["agent"]) for r in rows] == list(
        itertools.product(range(8), ("a1", "a2", "a3")))
    for agent in ("a1", "a2", "a3"):
        actions = [row["action"] for row in rows if row["agent"] == agent]
        assert [a["type"] for a in actions] == types
        assert actions[:3] == [
            {"type": "inspect_evidence", "evidence_id": "e1"},
            {"type": "inspect_evidence", "evidence_id": "e2"},
            {"type": "inspect_evidence", "evidence_id": "e3"},
        ]
        if trace != "B":
            assert actions[3] == {"type": "propose_claim", "slot_id": "s1",
                                  "proposition_id": "q", "evidence_ids": ["e1", "e2", "e3"]}
    if trace in ("A", "D"):
        assert [r["action"]["claim_id"] for r in rows if r["round"] == 4] == ["c2", "c1", "c1"]
    if trace == "A":
        assert [r["action"]["claim_id"] for r in rows if r["round"] == 5] == ["c3", "c3", "c2"]


@pytest.mark.parametrize("trace,effort,verify,contribution,good,bad", [
    ("A", 8, 0, "3/4", "-5", "-43"),
    ("B", 3, 2, "3/8", "-9", "-9"),
    ("C", 4, 2, "1/2", "-12", "-12"),
    ("D", 6, 1, "5/8", "1", "-37"),
])
def test_task_oracle_matches_hand_derived_totals(trace, effort, verify, contribution, good, bad):
    for truth, utility in (("p", good), ("q", bad)):
        row = oracle.literal_outcome(trace, truth, "p")
        assert row["effort"] == dict.fromkeys(("a1", "a2", "a3"), effort)
        assert row["budgets"] == {a: {"inspect": 0, "verify": verify} for a in ("a1", "a2", "a3")}
        assert row["contribution_fraction"] == contribution
        assert row["total_effort"] == 3 * effort
        assert row["total_utility"] == utility
        assert row["utility"] == dict.fromkeys(("a1", "a2", "a3"), str(Fraction(utility) / 3))
        if trace in ("A", "D"):
            assert row["briefing"] == [{"slot_id": "s1", "claim_id": "c1",
                "proposition_id": "p", "proposer": "a1", "correct": truth == "p",
                "provenance_ok": True, "net_support": 2}]
            assert row["collective_quality"] == (12 if truth == "p" else -12)
            assert row["total_credit"] == ("7" if truth == "p" else "-7")
        else:
            assert row["briefing"] == [{"slot_id": "s1", "claim_id": None}]
            assert row["collective_quality"] == 0
            assert row["total_credit"] == "0"


@pytest.mark.parametrize("truth,report,positive,negative", [
    ("p", "p", "1", "0"), ("q", "q", "1", "0"),
    ("p", "q", "0", "1"), ("q", "p", "0", "1"),
])
def test_endpoint_parameters_encode_requested_verdict_without_seed_search(truth, report,
                                                                        positive, negative):
    assert oracle.endpoint_parameters(truth, report, "positive") == (positive, "0")
    assert oracle.endpoint_parameters(truth, report, "negative") == (negative, "0")
    assert oracle.endpoint_parameters(truth, report, "unavailable") == ("1", "1")


@pytest.mark.parametrize("accuracy,acceptance,selective,quality,utility", [
    ("0", "1/10", "0", "-6/5", "-62/5"),
    ("1/2", "1/2", "9/10", "24/5", "-89/10"),
    ("3/4", "7/10", "27/28", "39/5", "-143/20"),
    ("9/10", "41/50", "81/82", "48/5", "-61/10"),
    ("1", "9/10", "1", "54/5", "-27/5"),
])
def test_hand_calculated_nontrivial_rows(accuracy, acceptance, selective, quality, utility):
    row = oracle.expectation("1/10", accuracy, "0", 3)
    assert row["acceptance"] == acceptance
    assert row["selective_accuracy"] == selective
    assert row["signed_quality"] == quality
    assert row["total_utility"] == utility


def test_declared_tradeoff_zero_and_late_timing_cases():
    baseline = oracle.baseline("1/10")
    assert baseline == {"correct_accepted": "9/10", "wrong_accepted": "1/10",
        "acceptance": "1", "selective_accuracy": "9/10", "signed_quality": "48/5",
        "total_credit": "28/5", "total_effort": "24", "contribution_fraction": "3/4",
        "total_utility": "-44/5"}
    early = oracle.expectation("1/10", "3/4", "0", 3)
    assert Fraction(early["selective_accuracy"]) > Fraction(baseline["selective_accuracy"])
    assert Fraction(early["acceptance"]) < Fraction(baseline["acceptance"])
    assert Fraction(early["signed_quality"]) < Fraction(baseline["signed_quality"])
    assert oracle.expectation("1/10", "9/10", "0", 3)["signed_quality"] == "48/5"
    late = oracle.expectation("1/10", "3/4", "0", 5)
    assert late["signed_quality"] == "48/5"
    assert late["total_effort"] == "111/5"
    assert late["total_utility"] == "-7"
    assert late["contribution_fraction"] == "57/80"
    for timing in (3, 4, 5, 6):
        unavailable = oracle.expectation("1/10", "0", "1", timing)
        assert {key: unavailable[key] for key in baseline} == baseline
        assert unavailable["conditional_audit_accuracy"] is None
        assert unavailable["available_correct_mass"] == "0"
    null = oracle.expectation("1/10", "0", "0", 6)
    assert {key: null[key] for key in baseline} == baseline


@pytest.mark.parametrize("error,accuracy", [("0", "0"), ("1", "1")])
@pytest.mark.parametrize("timing", [3, 4])
def test_zero_acceptance_has_undefined_selective_accuracy(error, accuracy, timing):
    row = oracle.expectation(error, accuracy, "0", timing)
    assert row["acceptance"] == "0"
    assert row["selective_accuracy"] is None
    assert row["signed_quality"] == "0"


def test_all_720_rows_against_separate_finite_world_enumeration():
    grid = oracle.law_grid()
    assert len(grid) == 720
    assert len({(r["source_error"], r["audit_accuracy"], r["unavailable"],
                 r["publish_round"], r["truth_view"]) for r in grid}) == 720
    for row in grid:
        error, accuracy, unavailable = map(Fraction,
            (row["source_error"], row["audit_accuracy"], row["unavailable"]))
        weights = oracle.cell_weights(row["source_error"], row["audit_accuracy"],
                                      row["unavailable"], row["truth_view"])
        assert len(weights) == 12  # Includes every zero-mass cell.
        assert sum(Fraction(r["weight"]) for r in weights) == 1
        wrong_source = available_correct = unavailable_mass = negative_mass = Fraction()
        totals = dict.fromkeys(("correct_accepted", "wrong_accepted", "total_effort",
                               "contribution_fraction"), Fraction())
        for cell in weights:
            mass = Fraction(cell["weight"])
            correct = cell["truth"] == cell["report"]
            expected_truth_mass = (Fraction(1, 2) if row["truth_view"] == "mixed"
                                   else Fraction(cell["truth"] == row["truth_view"]))
            expected_source_mass = 1 - error if correct else error
            verdict = cell["verdict"]
            conditional = (unavailable if verdict == "unavailable" else
                           (1 - unavailable) * (accuracy if
                            (verdict == "positive") == correct else 1 - accuracy))
            assert mass == expected_truth_mass * expected_source_mass * conditional
            wrong_source += mass * (not correct)
            unavailable_mass += mass * (verdict == "unavailable")
            available_correct += mass * (verdict != "unavailable"
                                         and (verdict == "positive") == correct)
            negative_mass += mass * (verdict == "negative")
            # A separately literal task table, never the production schedule/oracle.
            if verdict == "negative" and row["publish_round"] == 3:
                accepted, effort, contribution = False, 9, Fraction(3, 8)
            elif verdict == "negative" and row["publish_round"] == 4:
                accepted, effort, contribution = False, 12, Fraction(1, 2)
            elif verdict == "negative" and row["publish_round"] == 5:
                accepted, effort, contribution = True, 18, Fraction(5, 8)
            else:
                accepted, effort, contribution = True, 24, Fraction(3, 4)
            totals["correct_accepted"] += mass * (accepted and correct)
            totals["wrong_accepted"] += mass * (accepted and not correct)
            totals["total_effort"] += mass * effort
            totals["contribution_fraction"] += mass * contribution
        assert wrong_source == error
        assert unavailable_mass == unavailable
        assert available_correct == (1 - unavailable) * accuracy
        expected = row["expected"]
        assert expected == oracle.expectation(row["source_error"], row["audit_accuracy"],
                                              row["unavailable"], row["publish_round"])
        assert expected["conditional_audit_accuracy"] == (None if unavailable == 1
                                                          else str(accuracy))
        assert expected["available_correct_mass"] == str(available_correct)
        assert expected["negative_mass"] == str(negative_mass)
        for key, value in totals.items():
            assert expected[key] == str(value)
        accepted = totals["correct_accepted"] + totals["wrong_accepted"]
        signed = totals["correct_accepted"] - totals["wrong_accepted"]
        assert expected["acceptance"] == str(accepted)
        assert expected["selective_accuracy"] == (str(totals["correct_accepted"] / accepted)
                                                  if accepted else None)
        assert expected["signed_quality"] == str(12 * signed)
        assert expected["total_credit"] == str(7 * signed)
        assert expected["total_utility"] == str(19 * signed - totals["total_effort"])


@pytest.mark.parametrize("bad", [True, 0.5, "0.5", "01/2", "2/4", "-1/2", "3/2", "nan", None])
def test_probability_boundary_never_coerces_bad_scalars(bad):
    for position in range(3):
        params = ["1/10", "3/4", "1/2"]
        params[position] = bad
        with pytest.raises(ValueError, match="probability"):
            oracle.expectation(*params, 3)


@pytest.mark.parametrize("verdict,timing", [(None, 3), ("positive", None), ("future", 3),
                                          ("negative", True), ("negative", 3.0), ("negative", 7)])
def test_out_of_design_trace_is_rejected(verdict, timing):
    with pytest.raises(ValueError, match="declared"):
        oracle.trace_for(verdict, timing)


def test_unknown_source_truth_trace_or_view_is_rejected():
    for args in (("A", "p", "z"), ("A", "z", "q"), ("Z", "p", "q")):
        with pytest.raises(ValueError, match="declared"):
            oracle.literal_outcome(*args)
    with pytest.raises(ValueError, match="declared"):
        oracle.cell_weights("0", "1", "0", "unknown")
