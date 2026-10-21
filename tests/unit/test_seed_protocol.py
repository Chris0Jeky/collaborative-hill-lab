"""Protocol/block identity is explicit, validated, and frozen into the study hash."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from collaborative_hill.engine.runner import RunConfig
from collaborative_hill.experiments.manifests import RunManifest
from collaborative_hill.experiments.study import StudySpec, load_study, study_hash

LEGACY = "legacy-independent-v1"
PAIRED = "paired-policy-v2"
STUDY_001 = Path(__file__).resolve().parents[2] / "studies/001-evidence-commons"


def _study_data(protocol=None, block=None):
    data = {
        "study_id": "s", "seed": 7,
        "conditions": [{"condition_id": "c", "scenario": "c.json", "skin": "skin.json"}],
    }
    if protocol is not None:
        data["seed_protocol"] = protocol
    if block is not None:
        data["conditions"][0]["scenario_block"] = block
    return data


@pytest.mark.parametrize(("protocol", "block"), [
    ("unknown", None), (PAIRED, None), (LEGACY, "shared"),
    (PAIRED, ""), (PAIRED, "  "), (PAIRED, "a\x1fb"),
])
def test_study_rejects_ambiguous_or_invalid_pairing(protocol, block):
    with pytest.raises(ValidationError):
        StudySpec.model_validate(_study_data(protocol, block))


def test_missing_protocol_is_explicitly_legacy_independent():
    assert StudySpec.model_validate(_study_data()).seed_protocol == LEGACY
    assert RunConfig(study_id="s", run_id="r", seed_root=(7, "c", 0)).seed_protocol == LEGACY


def test_protocol_and_block_changes_have_new_study_hashes():
    legacy, resolved = load_study(STUDY_001)
    old_hash = study_hash(legacy, resolved)
    assert study_hash(legacy.model_copy(update={"seed_protocol": LEGACY}), resolved) == old_hash
    data = legacy.model_dump(mode="json")
    data["seed_protocol"] = PAIRED
    for condition in data["conditions"]:
        condition["scenario_block"] = "block-a"
    paired = StudySpec.model_validate(data)
    paired_hash = study_hash(paired, resolved)
    assert paired_hash != old_hash
    data["conditions"][0]["scenario_block"] = "block-b"
    assert study_hash(StudySpec.model_validate(data), resolved) not in {old_hash, paired_hash}


@pytest.mark.parametrize("metadata", [
    {"seed_protocol": "unknown"},
    {"seed_protocol": PAIRED},
    {"seed_protocol": PAIRED, "policy_seed_root": [7, "block"]},
    {"seed_protocol": PAIRED, "policy_seed_root": [], "scenario_block": "block"},
    {"seed_protocol": PAIRED, "policy_seed_root": [7], "scenario_block": ""},
    {"seed_protocol": LEGACY, "policy_seed_root": [7]},
    {"seed_protocol": LEGACY, "scenario_block": "block"},
])
def test_run_config_and_manifest_reject_ambiguous_seed_metadata(metadata):
    config = {"study_id": "s", "run_id": "r", "seed_root": [7, "c", 0], **metadata}
    with pytest.raises(ValidationError):
        RunConfig.model_validate(config)
    with pytest.raises(ValidationError):
        RunManifest.model_validate({
            **config, "condition_id": "c", "replicate": 0, "institution": {},
            "scenario_hash": "s", "mechanism_hash": "m", "narrative_hash": "n",
            "evidence_corpus_hash": "e",
        })
