"""The opt-in extension must keep pre-existing scientific identities and bytes.

Goldens were captured before implementation, with package/study sources verified
equal to GitHub main e1f8f119. These protect compatibility, not new audit behavior.
"""

import json
from pathlib import Path

import pytest

from collaborative_hill.engine.hashing import sha256_hex
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.store import RunPaths
from collaborative_hill.experiments.scenario import NarrativeSkin, ScenarioSpec, compile_scenario
from collaborative_hill.experiments.study import build_policies, load_study, study_hash

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads(
    (ROOT / "tests/fixtures/audit_legacy_baseline.json").read_text(encoding="utf-8")
)
pytestmark = pytest.mark.metamorphic


@pytest.mark.parametrize("directory", sorted(GOLDEN["studies"]))
def test_legacy_studies_keep_hashes_and_exact_model_serialization(directory):
    expected = GOLDEN["studies"][directory]
    study, resolved = load_study(ROOT / directory)
    assert study_hash(study, resolved) == expected["study_hash"]
    assert set(resolved) == set(expected["conditions"])
    for name, scenario in resolved.items():
        actual = {field: getattr(scenario, field) for field in (
            "scenario_hash", "mechanism_hash", "narrative_hash", "evidence_corpus_hash",
        )}
        actual.update(spec_json_sha256=sha256_hex(scenario.spec.model_dump_json()),
                      resolved_json_sha256=sha256_hex(scenario.model_dump_json()))
        assert actual == expected["conditions"][name], (directory, name)
        assert set(scenario.spec.institution.model_dump()) == {
            "accountability", "evidence_topology",
        }


@pytest.mark.parametrize("name", sorted(GOLDEN["runs"]))
def test_legacy_mechanisms_reproduce_original_ledger_bytes(tmp_path, name):
    expected = GOLDEN["runs"][name]
    resolved = compile_scenario(ScenarioSpec.model_validate(expected["spec"]),
                                NarrativeSkin.model_validate(expected["skin"]))
    config = RunConfig.model_validate(expected["config"])
    with RunPaths(tmp_path / name).reserve() as paths:
        result = run_episode(mechanism=resolved.build_mechanism(),
                             policies=build_policies(resolved), config=config, paths=paths)
    assert result.model_dump(mode="json") == expected["result"]
    assert sha256_hex(paths.events.read_bytes()) == expected["ledger_sha256"]
