"""run_study writes an honest RunManifest: hashes match the resolved scenario,
seed_root/policies/status are exact, dependency lock hashes only a real file,
and token/cost fields stay None for non-metered (scripted / FakeProvider) runs.
"""

import json
import sys

from collaborative_hill.engine.hashing import sha256_hex
from collaborative_hill.experiments.manifests import lock_hash
from collaborative_hill.experiments.scenario import (
    NarrativeSkin,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import _find_repo_root, run_study

SCENARIO = {
    "scenario_id": "sc-nipd",
    "world": {"kind": "nipd", "mode": "neighbourhood", "rounds": 3},
    "interaction": {"structure": "neighbourhood"},
    "cognition": {"agents": [
        {"agent_id": "a1", "policy": {"name": "allc"}},
        {"agent_id": "a2", "policy": {"name": "alld"}},
        {"agent_id": "a3", "policy": {"name": "allc"}},
    ]},
}
SKIN = {"skin_id": "plain"}


def _write_study(study_dir, *, with_lock=False):
    (study_dir / "scenarios").mkdir(parents=True)
    (study_dir / "skins").mkdir(parents=True)
    (study_dir / "scenarios" / "sc.json").write_text(json.dumps(SCENARIO))
    (study_dir / "skins" / "plain.json").write_text(json.dumps(SKIN))
    (study_dir / "study.json").write_text(json.dumps({
        "study_id": "study-x", "seed": 42, "replicates": 1,
        "conditions": [{"condition_id": "c0", "scenario": "scenarios/sc.json",
                        "skin": "skins/plain.json"}],
    }))
    if with_lock:
        (study_dir / "requirements-lock.txt").write_text("pinned==1.0.0\n")


def _run_and_load_manifest(tmp_path, *, with_lock=False):
    study_dir = tmp_path / "study"
    _write_study(study_dir, with_lock=with_lock)
    arts = tmp_path / "arts"
    results = run_study(study_dir, arts)
    assert len(results) == 1 and results[0].status == "completed"
    manifests = list(arts.glob("**/manifest.json"))
    assert len(manifests) == 1
    return json.loads(manifests[0].read_text(encoding="utf-8")), study_dir


def test_manifest_hashes_match_resolved_scenario(tmp_path):
    manifest, _study = _run_and_load_manifest(tmp_path)
    resolved = compile_scenario(ScenarioSpec.model_validate(SCENARIO),
                                NarrativeSkin.model_validate(SKIN))
    assert manifest["scenario_hash"] == resolved.scenario_hash
    assert manifest["mechanism_hash"] == resolved.mechanism_hash
    assert manifest["narrative_hash"] == resolved.narrative_hash
    assert manifest["evidence_corpus_hash"] == resolved.evidence_corpus_hash


def test_manifest_seed_policies_status_python(tmp_path):
    manifest, _study = _run_and_load_manifest(tmp_path)
    assert manifest["seed_root"] == [42, "c0", 0]
    assert manifest["status"] == "completed"
    assert manifest["policies"] == {
        "a1": "allc[neighbourhood]@1",
        "a2": "alld[neighbourhood]@1",
        "a3": "allc[neighbourhood]@1",
    }
    assert manifest["python_version"] == sys.version.split()[0]
    assert manifest["condition_id"] == "c0"
    assert manifest["replicate"] == 0


def test_lock_hash_present_and_absent(tmp_path):
    # Directly exercise the "when present" semantics, decoupled from repo-root
    # discovery: hash of the file iff it exists, else None (never fabricated).
    empty = tmp_path / "no_lock"
    empty.mkdir()
    assert lock_hash(empty) is None
    present = tmp_path / "with_lock"
    present.mkdir()
    (present / "requirements-lock.txt").write_text("pinned==1.0.0\n")
    lock_bytes = (present / "requirements-lock.txt").read_bytes()
    assert lock_hash(present) == sha256_hex(lock_bytes)


def test_manifest_dependency_lock_is_faithful_to_resolver(tmp_path):
    # The manifest must record exactly what lock_hash(resolved_repo_root) yields
    # — whatever it is on this machine — never an invented value.
    manifest, study_dir = _run_and_load_manifest(tmp_path)
    expected = lock_hash(_find_repo_root(study_dir))
    assert manifest["dependency_lock_sha256"] == expected


def test_manifest_tokens_and_cost_none_for_scripted(tmp_path):
    manifest, _study = _run_and_load_manifest(tmp_path)
    assert manifest["input_tokens"] is None
    assert manifest["output_tokens"] is None
    assert manifest["cost_usd"] is None
    assert manifest["providers"] == {}  # no LLM policies in a scripted run
