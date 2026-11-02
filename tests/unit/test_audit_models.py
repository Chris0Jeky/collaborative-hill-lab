"""Exact audit law and released reports, without executing an audited episode."""

import importlib.util
import json
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from collaborative_hill.domain.audit import (
    AuditConfig,
    AuditFinding,
    AuditMechanismConfig,
    AuditTarget,
    audit_seed_key,
    project_published_audit,
    sample_audit_finding,
)

EXPERIMENT = Path(__file__).resolve().parents[2] / "experiments/noisy-corpus"
FIXTURE = json.loads((EXPERIMENT / "AUDIT_FIXTURE.json").read_text(encoding="utf-8"))


def settings_data(*, accuracy="3/4", unavailable="1/3"):
    contract = deepcopy(FIXTURE["config"])
    contract["accuracy"] = accuracy
    return {
        "contract": contract,
        "generation": {
            "generator_version": "ec-audit-generator@1",
            "unavailable_probability": unavailable,
            "draw_dependence": "independent-per-target",
            "unavailable_dependence": "independent-of-truth-source-errors-and-correctness",
        },
    }


def settings(**kwargs):
    return AuditMechanismConfig.model_validate_json(json.dumps(settings_data(**kwargs)))


def findings():
    return tuple(AuditFinding.model_validate(item) for item in FIXTURE["findings"])


class LiteralDraw:
    """Independent finite oracle: supply an integer in the sampler's exact range."""

    def __init__(self, value, denominator):
        self.value = value
        self.denominator = denominator
        self.calls = 0

    def randrange(self, stop):
        assert stop == self.denominator
        assert 0 <= self.value < stop
        self.calls += 1
        return self.value


class NoDraw:
    def randrange(self, stop):
        pytest.fail("unavailable reports must not need a verdict draw")


def test_public_contract_and_every_released_envelope_match_original_foundation():
    module_spec = importlib.util.spec_from_file_location(
        "audit_foundation_reference", EXPERIMENT / "audit_contract.py")
    assert module_spec is not None and module_spec.loader is not None
    reference = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = reference
    module_spec.loader.exec_module(reference)
    old = reference.AuditConfig.model_validate_json(json.dumps(FIXTURE["config"]))
    old_findings = tuple(reference.AuditFinding.model_validate(item)
                         for item in FIXTURE["findings"])
    config = settings().contract
    assert config.model_dump(mode="json") == FIXTURE["config"]
    assert config.contract_hash() == old.contract_hash()
    for text_round, verdicts in FIXTURE["expected_public_verdicts_by_round"].items():
        rnd = int(text_round)
        released = tuple(item for item in findings() if item.publish_round <= rnd)
        result = project_published_audit(config, released, rnd).model_dump(mode="json")
        assert result == reference.project_audit(old, old_findings, rnd).model_dump(mode="json")
        assert [item["verdict"] for item in result["reports"]] == verdicts
        assert set(result) == {"contract_version", "audit_id", "contract_hash", "reports"}
        assert all(set(item) == {"slot_id", "proposition_id", "publish_round", "verdict"}
                   for item in result["reports"])


def test_python_tuples_and_json_arrays_are_explicit_strict_input_paths():
    config = settings()
    assert AuditMechanismConfig.model_validate(config.model_dump(mode="python")) == config
    assert AuditMechanismConfig.model_validate_json(config.model_dump_json()) == config
    assert isinstance(config.contract.schedule, tuple)
    # A Python list is not silently turned into the strict tuple contract.
    with pytest.raises(ValidationError, match="tuple"):
        AuditMechanismConfig.model_validate(config.model_dump(mode="json"))
    with pytest.raises(ValidationError, match="frozen"):
        config.contract.accuracy = "1"


@pytest.mark.parametrize("field,value", [
    ("unavailable_probability", 0), ("unavailable_probability", True),
    ("unavailable_probability", 0.5), ("unavailable_probability", "0.5"),
    ("unavailable_probability", "2/4"), ("unavailable_probability", "-1/4"),
    ("unavailable_probability", "5/4"), ("unavailable_probability", "1/0"),
    ("generator_version", "future"), ("draw_dependence", "shared-error"),
    ("unavailable_dependence", "truth-dependent"), ("extra", 1),
])
def test_generation_law_rejects_undeclared_or_coerced_inputs(field, value):
    data = settings_data()
    data["generation"][field] = value
    with pytest.raises(ValidationError):
        AuditMechanismConfig.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("field,value", [
    ("accuracy", True), ("accuracy", 0.75), ("accuracy", "0.75"), ("accuracy", "6/8"),
    ("audit_id", "  "), ("contract_version", "ec-audit-observation@2"),
    ("dependence", "empirical-independence"), ("true_propositions", {"s1": "p"}),
])
def test_public_contract_retains_strict_values_and_allowlist(field, value):
    data = settings_data()
    data["contract"][field] = value
    with pytest.raises(ValidationError):
        AuditMechanismConfig.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("value", [-1, True, 2.0, "2"])
def test_scheduled_round_is_a_strict_nonnegative_integer(value):
    data = settings_data()
    data["contract"]["schedule"][0]["publish_round"] = value
    with pytest.raises(ValidationError):
        AuditMechanismConfig.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("damage", ["empty", "duplicate", "rescheduled"])
def test_schedule_requires_nonempty_unique_candidate_targets(damage):
    data = settings_data()
    if damage == "empty":
        data["contract"]["schedule"] = []
    else:
        duplicate = deepcopy(data["contract"]["schedule"][0])
        if damage == "rescheduled":
            duplicate["publish_round"] += 1
        data["contract"]["schedule"].append(duplicate)
    with pytest.raises(ValidationError):
        AuditMechanismConfig.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("value", ["0", "1/2", "1"])
def test_canonical_probability_boundaries(value):
    config = settings(accuracy=value, unavailable=value)
    assert config.contract.accuracy == value
    assert config.generation.unavailable_probability == value


@pytest.mark.parametrize("field", ["audit_id", "slot_id", "proposition_id"])
def test_integrated_settings_reject_seed_separator_before_world_execution(field):
    data = settings_data()
    if field == "audit_id":
        data["contract"][field] = "a\x1fb"
    else:
        data["contract"]["schedule"][0][field] = "a\x1fb"
    # The public foundation's schema is unchanged; integration adds seed validation.
    AuditConfig.model_validate_json(json.dumps(data["contract"]))
    with pytest.raises(ValidationError, match="reserved separator"):
        AuditMechanismConfig.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("slots,rounds", [
    ({"s2": ("p", "q")}, 5), ({"s1": ("p", "r")}, 5),
    ({"s1": ("p", "q")}, 4), ({"s1": ("p", "q")}, 0),
    ({"s1": ("p", "q")}, True), ({"s1": ("p", "q")}, 5.0),
])
def test_candidate_and_horizon_binding_rejects_invalid_world(slots, rounds):
    with pytest.raises(ValueError):
        settings().validate_world(slots, rounds)


def test_candidate_and_horizon_binding_accepts_last_observable_round():
    settings().validate_world({"s1": ("p", "q")}, 5)


@pytest.mark.parametrize("truth,expected", [
    (True, {"positive": 6, "negative": 2, "unavailable": 4}),
    (False, {"positive": 2, "negative": 6, "unavailable": 4}),
])
def test_exact_joint_draw_enumeration_matches_hand_derived_law(truth, expected):
    # u=1/3 and a=3/4: twelve equally weighted integer pairs. Expected counts
    # are literal, independently derived from the stated law, not this sampler.
    config = settings()
    target = config.contract.schedule[0]
    before = config.model_dump(mode="json")
    counts = Counter()
    for availability in range(3):
        for verdict in range(4):
            u_rng, a_rng = LiteralDraw(availability, 3), LiteralDraw(verdict, 4)
            finding = sample_audit_finding(
                config, target, target_is_true=truth,
                availability_rng=u_rng, verdict_rng=a_rng,
            )
            counts[finding.verdict] += 1
            assert finding.key() == target.key()
            assert u_rng.calls == 1
            assert a_rng.calls == (0 if finding.verdict == "unavailable" else 1)
    assert counts == expected
    assert config.model_dump(mode="json") == before


@pytest.mark.parametrize("accuracy,truth,expected", [
    ("1", True, "positive"), ("1", False, "negative"),
    ("0", True, "negative"), ("0", False, "positive"),
])
def test_perfect_and_inverted_oracles_are_explicit_assumptions(accuracy, truth, expected):
    config = settings(accuracy=accuracy, unavailable="0")
    finding = sample_audit_finding(
        config, config.contract.schedule[0], target_is_true=truth,
        availability_rng=LiteralDraw(0, 1), verdict_rng=LiteralDraw(0, 1),
    )
    assert finding.verdict == expected


@pytest.mark.parametrize("truth", [True, False])
def test_total_unavailability_is_an_explicit_report_without_a_verdict_draw(truth):
    config = settings(unavailable="1")
    finding = sample_audit_finding(
        config, config.contract.schedule[0], target_is_true=truth,
        availability_rng=LiteralDraw(0, 1), verdict_rng=NoDraw(),
    )
    assert finding.verdict == "unavailable"


@pytest.mark.parametrize("truth", [0, 1, "true", None])
def test_trusted_sampler_does_not_coerce_its_truth_input(truth):
    config = settings()
    with pytest.raises(ValueError, match="bool"):
        sample_audit_finding(config, config.contract.schedule[0], target_is_true=truth,
                            availability_rng=NoDraw(), verdict_rng=NoDraw())


def test_sampler_rejects_unscheduled_target_without_consuming_randomness():
    config = settings()
    target = AuditTarget(slot_id="s1", proposition_id="p", publish_round=3)
    with pytest.raises(ValueError, match="scheduled"):
        sample_audit_finding(config, target, target_is_true=True,
                            availability_rng=NoDraw(), verdict_rng=NoDraw())


def test_seed_keys_have_literal_domains_and_do_not_include_timing_or_other_targets():
    config = settings()
    target = config.contract.schedule[0]
    expected = ("ec-audit-generator@1", "ec-audit-observation@1", "toy-audit", "s1", "p")
    assert audit_seed_key(config, target, "availability") == (*expected, "availability")
    assert audit_seed_key(config, target, "verdict") == (*expected, "verdict")
    data = settings_data(accuracy="1/2", unavailable="1/2")
    data["contract"]["schedule"][0]["publish_round"] = 3
    data["contract"]["schedule"].append(
        {"slot_id": "s2", "proposition_id": "r", "publish_round": 0})
    data["contract"]["schedule"].reverse()
    changed = AuditMechanismConfig.model_validate_json(json.dumps(data))
    moved = next(t for t in changed.contract.schedule if t.proposition_id == "p")
    assert audit_seed_key(changed, moved, "verdict") == (*expected, "verdict")
    with pytest.raises(ValueError, match="purpose"):
        audit_seed_key(config, target, "unknown")


@pytest.mark.parametrize("damage", ["missing", "duplicate", "future", "unknown", "wrong-round"])
def test_released_projection_requires_exact_due_prefix(damage):
    config = settings().contract
    q, p = findings()
    supplied = (p,)
    if damage == "missing":
        supplied = ()
    elif damage == "duplicate":
        supplied = (p, p)
    elif damage == "future":
        supplied = (p, q)
    elif damage == "unknown":
        supplied = (p.model_copy(update={"proposition_id": "r"}),)
    elif damage == "wrong-round":
        supplied = (p.model_copy(update={"publish_round": 1}),)
    with pytest.raises(ValueError, match="published"):
        project_published_audit(config, supplied, 2)


@pytest.mark.parametrize("rnd", [-1, True, 2.0, "2", None])
def test_released_projection_round_is_strict(rnd):
    with pytest.raises(ValueError, match="nonnegative integer"):
        project_published_audit(settings().contract, (), rnd)
