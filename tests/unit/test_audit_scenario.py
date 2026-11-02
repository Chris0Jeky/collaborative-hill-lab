"""Audit routing and hash binding preserve the legacy institution shape."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_audit_models import settings_data

from collaborative_hill.domain.institutions import AuditInstitutionConfig, InstitutionConfig
from collaborative_hill.domain.world import audited_evidence_commons
from collaborative_hill.domain.world.audited_evidence_commons import AuditedEvidenceCommonsMechanism
from collaborative_hill.domain.world.evidence_commons import EvidenceCommonsMechanism
from collaborative_hill.experiments.scenario import (
    NarrativeSkin,
    ResolvedScenario,
    ScenarioSpec,
    compile_scenario,
    mechanism_view,
)
from collaborative_hill.experiments.study import validate_study

ROOT = Path(__file__).resolve().parents[2]


def scenario_data():
    return json.loads((ROOT / "studies/001-evidence-commons/scenarios/attr-ledger.json").read_text(
        encoding="utf-8"))


def audited_data():
    data = scenario_data()
    audit = settings_data()
    audit["contract"]["schedule"] = [
        {"slot_id": "s1", "proposition_id": "s1_true", "publish_round": 0},
        {"slot_id": "s1", "proposition_id": "s1_false", "publish_round": 11},
    ]
    data["institution"]["audit"] = audit
    return data


def parse(data):
    return ScenarioSpec.model_validate_json(json.dumps(data))


def test_legacy_institution_dump_and_engine_route_remain_exact():
    spec = parse(scenario_data())
    assert type(spec.institution) is InstitutionConfig
    assert spec.institution.model_dump(mode="json") == {
        "accountability": "attributable", "evidence_topology": "shared_ledger"}
    resolved = compile_scenario(spec, NarrativeSkin(skin_id="plain"))
    mechanism = resolved.build_mechanism()
    assert type(mechanism) is EvidenceCommonsMechanism
    assert mechanism_view(spec)["engine_version"] == 2
    assert "audit" not in mechanism.observe(mechanism.initial_state(), "a1")


def test_audit_subtype_round_trips_without_dropping_hash_bound_fields():
    raw = audited_data()
    spec = parse(raw)
    assert isinstance(spec.institution, AuditInstitutionConfig)
    assert spec.institution.model_dump(mode="json") == raw["institution"]
    assert ScenarioSpec.model_validate(spec.model_dump(mode="python")) == spec
    assert ScenarioSpec.model_validate_json(spec.model_dump_json()) == spec
    resolved = compile_scenario(spec, NarrativeSkin(skin_id="plain"))
    assert ResolvedScenario.model_validate_json(resolved.model_dump_json()) == resolved
    assert isinstance(resolved.build_mechanism(), AuditedEvidenceCommonsMechanism)
    assert mechanism_view(spec)["engine_version"] == 3
    assert mechanism_view(spec)["institution"] == raw["institution"]


@pytest.mark.parametrize("damage", ["null", "missing-slot", "wrong-candidate", "horizon"])
def test_audit_binding_fails_before_any_episode(damage):
    data = audited_data()
    if damage == "null":
        data["institution"]["audit"] = None
    else:
        target = data["institution"]["audit"]["contract"]["schedule"][0]
        if damage == "missing-slot":
            target["slot_id"] = "absent"
        elif damage == "wrong-candidate":
            target["proposition_id"] = "s2_true"
        else:
            target["publish_round"] = data["world"]["params"]["rounds"]
    with pytest.raises(ValueError):
        compile_scenario(parse(data), NarrativeSkin(skin_id="plain"))


def test_audit_cannot_be_silently_ignored_on_nipd_even_through_model_copy():
    raw = {
        "scenario_id": "n", "world": {"kind": "nipd", "mode": "pairwise", "rounds": 3},
        "interaction": {"structure": "pairwise"},
        "cognition": {"agents": [
            {"agent_id": "a1", "policy": {"name": "allc"}},
            {"agent_id": "a2", "policy": {"name": "alld"}},
        ]},
    }
    legacy = parse(raw)
    raw["institution"] = audited_data()["institution"]
    with pytest.raises(ValidationError, match="audit"):
        parse(raw)
    copied = legacy.model_copy(update={"institution": parse(audited_data()).institution})
    with pytest.raises(ValueError, match="audit"):
        compile_scenario(copied, NarrativeSkin(skin_id="plain"))


@pytest.mark.parametrize("field", ["accuracy", "unavailability", "timing", "identity"])
def test_complete_audit_settings_change_only_the_appropriate_hashes(field):
    original = audited_data()
    changed = deepcopy(original)
    audit = changed["institution"]["audit"]
    if field == "accuracy":
        audit["contract"]["accuracy"] = "1/2"
    elif field == "unavailability":
        audit["generation"]["unavailable_probability"] = "1/2"
    elif field == "timing":
        audit["contract"]["schedule"][0]["publish_round"] = 1
    else:
        audit["contract"]["audit_id"] = "other"
    skin = NarrativeSkin(skin_id="plain")
    before, after = (compile_scenario(parse(data), skin) for data in (original, changed))
    assert before.mechanism_hash != after.mechanism_hash
    assert before.scenario_hash != after.scenario_hash
    assert before.narrative_hash == after.narrative_hash
    assert before.evidence_corpus_hash == after.evidence_corpus_hash


def test_only_audited_hash_binds_the_new_engine_version(monkeypatch):
    legacy, audited = parse(scenario_data()), parse(audited_data())
    skin = NarrativeSkin(skin_id="plain")
    legacy_before = compile_scenario(legacy, skin)
    audited_before = compile_scenario(audited, skin)
    monkeypatch.setattr(audited_evidence_commons, "EC_AUDIT_ENGINE_VERSION", 4)
    assert compile_scenario(legacy, skin) == legacy_before
    assert compile_scenario(audited, skin).mechanism_hash != audited_before.mechanism_hash


@pytest.mark.parametrize("path,expected", [
    ("studies/000-legacy-reproduction",
     "5dcde1a9b6c98c576ca71bc03ea65dcc96175b6d8803c4db89e6c56ac8a15e9f"),
    ("studies/001-evidence-commons",
     "a3bffdfcf1715ebd65aa45b469f3e32c720d22633cfc80769b11020bcbd37bbe"),
])
def test_shipped_legacy_study_hash_literals_are_unchanged(path, expected):
    assert validate_study(ROOT / path)["study_hash"] == expected
