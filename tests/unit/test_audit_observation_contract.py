"""Public projection foundation only; this does not claim engine audit integration."""

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

EXPERIMENT = Path(__file__).resolve().parents[2] / "experiments/noisy-corpus"
spec = importlib.util.spec_from_file_location("audit_contract", EXPERIMENT / "audit_contract.py")
assert spec is not None and spec.loader is not None
contract = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = contract
spec.loader.exec_module(contract)
FIXTURE = json.loads((EXPERIMENT / "AUDIT_FIXTURE.json").read_text(encoding="utf-8"))


def parse_config(value=None):
    return contract.AuditConfig.model_validate_json(json.dumps(value or FIXTURE["config"]))


def parse_findings(values=None):
    return tuple(contract.AuditFinding.model_validate_json(json.dumps(value))
                 for value in (values if values is not None else FIXTURE["findings"]))


def test_literal_timing_fixture_and_report_allowlist():
    config, findings = parse_config(), parse_findings()
    for rnd, expected in FIXTURE["expected_public_verdicts_by_round"].items():
        envelope = contract.project_audit(config, findings, int(rnd)).model_dump(mode="json")
        assert set(envelope) == {"contract_version", "audit_id", "contract_hash", "reports"}
        assert envelope["contract_version"] == "ec-audit-observation@1"
        assert [item["verdict"] for item in envelope["reports"]] == expected
        for item in envelope["reports"]:
            assert set(item) == {"slot_id", "proposition_id", "publish_round", "verdict"}
            assert item["publish_round"] <= int(rnd)
        assert not contract.has_hidden_fields(envelope)


def test_wrong_verdict_remains_wrong_and_unavailability_is_not_a_negative():
    # The projector has no truth input and must not "repair" supplied findings.
    findings = deepcopy(FIXTURE["findings"])
    findings[1]["verdict"] = "negative"
    result = contract.project_audit(parse_config(), parse_findings(findings), 4)
    assert [item.verdict for item in result.reports] == ["negative", "unavailable"]


def test_projection_order_is_deterministic_and_input_is_immutable():
    config, findings = parse_config(), parse_findings()
    original = config.model_dump(mode="json")
    projected = contract.project_audit(config, findings, 4)
    assert projected == contract.project_audit(config, tuple(reversed(findings)), 4)
    assert config.model_dump(mode="json") == original
    with pytest.raises(ValidationError):
        config.accuracy = "1"


def test_pure_augmentation_preserves_base_observation_and_nested_content():
    base = {"mechanism": "evidence_commons", "round": 2, "self_id": "a1",
            "my_budgets": {"inspect": 3}, "claims": []}
    before = deepcopy(base)
    augmented = contract.with_audit(base, parse_config(), parse_findings())
    assert base == before
    assert {key: value for key, value in augmented.items() if key != "audit"} == before
    augmented["my_budgets"]["inspect"] = 0
    assert base == before
    second_agent = contract.with_audit({**base, "self_id": "a2"}, parse_config(), parse_findings())
    assert augmented["audit"] == second_agent["audit"]


@pytest.mark.parametrize("field,value", [
    ("accuracy", 1), ("accuracy", True), ("accuracy", 0.75), ("accuracy", "0.75"),
    ("accuracy", "6/8"), ("accuracy", "-1/4"), ("accuracy", "5/4"), ("accuracy", "1/0"),
    ("contract_version", "ec-audit-observation@2"), ("audit_id", ""), ("audit_id", "  "),
    ("visibility", "private"), ("oracle_kind", "live-verifier"),
    ("dependence", "unknown"), ("selection", "claims-selected-after-the-fact"),
    ("accuracy_semantics", "empirically-measured"), ("unavailable_semantics", "negative"),
    ("unexpected", "value"), ("true_propositions", {"s1": "p"}), ("truth_aligned", True),
])
def test_configuration_rejects_unknown_fields_versions_and_unsupported_assumptions(field, value):
    data = deepcopy(FIXTURE["config"])
    data[field] = value
    with pytest.raises(ValidationError):
        parse_config(data)


@pytest.mark.parametrize("value", ["0", "1/2", "1"])
def test_exact_accuracy_boundaries_are_declared_not_measured(value):
    data = deepcopy(FIXTURE["config"])
    data["accuracy"] = value
    assert parse_config(data).accuracy == value


@pytest.mark.parametrize("field,value", [
    ("publish_round", -1), ("publish_round", 1.0), ("publish_round", True),
    ("publish_round", "2"), ("slot_id", ""), ("slot_id", 1), ("proposition_id", " "),
    ("truth_aligned", True),
])
def test_target_validation_is_strict(field, value):
    data = deepcopy(FIXTURE["config"])
    data["schedule"][0][field] = value
    with pytest.raises(ValidationError):
        parse_config(data)


def test_empty_or_duplicate_targets_including_rescheduled_target_are_invalid():
    empty = deepcopy(FIXTURE["config"])
    empty["schedule"] = []
    with pytest.raises(ValidationError):
        parse_config(empty)
    duplicate = deepcopy(FIXTURE["config"])
    duplicate["schedule"][1] = {**duplicate["schedule"][0], "publish_round": 5}
    with pytest.raises(ValidationError):
        parse_config(duplicate)


@pytest.mark.parametrize("modification", ["missing", "duplicate", "unknown", "wrong_round"])
def test_findings_cover_exactly_the_fixed_schedule_even_before_publication(modification):
    values = deepcopy(FIXTURE["findings"])
    if modification == "missing":
        values.pop()
    elif modification == "duplicate":
        values[1] = values[0]
    elif modification == "unknown":
        values[0]["slot_id"] = "unscheduled"
    else:
        values[0]["publish_round"] = 99
    with pytest.raises(ValueError, match="exactly once"):
        contract.project_audit(parse_config(), parse_findings(values), 0)


@pytest.mark.parametrize("field,value", [
    ("verdict", "true"), ("verdict", True), ("verdict", ""),
    ("true_propositions", {"s1": "p"}), ("truth_aligned", True), ("score", 12),
])
def test_findings_allow_only_versioned_public_fields(field, value):
    data = deepcopy(FIXTURE["findings"][0])
    data[field] = value
    with pytest.raises(ValidationError):
        parse_findings([data])


@pytest.mark.parametrize("rnd", [-1, True, 2.0, "2", None])
def test_observed_round_never_coerces(rnd):
    with pytest.raises(ValueError, match="nonnegative integer"):
        contract.project_audit(parse_config(), parse_findings(), rnd)


@pytest.mark.parametrize("field,value", [
    ("accuracy", "1/2"), ("audit_id", "different-audit"), ("schedule", [
        {"slot_id": "s1", "proposition_id": "p", "publish_round": 3},
        {"slot_id": "s1", "proposition_id": "q", "publish_round": 4}]),
])
def test_contract_hash_binds_accuracy_identity_and_timing(field, value):
    data = deepcopy(FIXTURE["config"])
    data[field] = value
    assert parse_config(data).contract_hash() != parse_config().contract_hash()


@pytest.mark.parametrize("extra", [
    {"audit": {}}, {"true_propositions": {"s1": "p"}}, {"nested": [{"truth_aligned": True}]},
])
def test_augmentation_rejects_collision_and_nested_hidden_field_keys(extra):
    with pytest.raises(ValueError, match="collision or hidden"):
        contract.with_audit({"mechanism": "evidence_commons", "round": 2, **extra},
                            parse_config(), parse_findings())
