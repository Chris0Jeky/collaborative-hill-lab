"""The graph regeneration gate ignores source annotations, never scientific drift."""

import hashlib
import importlib.util
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from collaborative_hill.engine.hashing import content_hash

spec = importlib.util.spec_from_file_location(
    "graph_readout_gate", Path(__file__).resolve().parents[2] / "scripts/check_graph.py")
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def report():
    return {"study_hash": "design", "execution_source": {"local_source_commit": "old"},
            "report_source_sha256": "old-code", "cells": {"ring": {
                "manifest_worktree_dirty": False, "observed_curve": ["1", "1/2"],
                "scores": {"a1": "3/2"}, "terminal_event_hash": "sealed",
                "scenario_hash": "scenario", "replay_verified": True,
            }}}


def test_new_source_annotations_do_not_replace_original_record():
    original = report()
    snapshot = deepcopy(original)
    new = deepcopy(original)
    new["execution_source"]["local_source_commit"] = "new"
    new["report_source_sha256"] = "new-report-code"
    new["cells"]["ring"]["manifest_worktree_dirty"] = True
    gate.verify_readout(original, new)
    assert original == snapshot


@pytest.mark.parametrize("key,value", [
    ("observed_curve", ["1", "1/3"]), ("scores", {"a1": "4/3"}),
    ("terminal_event_hash", "different"), ("scenario_hash", "different"),
    ("replay_verified", False), ("replay_verified", 1),
])
def test_gate_rejects_changed_science_or_seal_identity(key, value):
    original = report()
    changed = deepcopy(original)
    changed["cells"]["ring"][key] = value
    with pytest.raises(ValueError, match="differ from the original"):
        gate.verify_readout(original, changed)


@pytest.fixture
def retained(tmp_path):
    original = Path(__file__).resolve().parents[2] / "experiments/graph-topology"
    for name in ("RESULTS.json", "RESULTS.md", "EXECUTION_SOURCE.json", "SOURCE_PROVENANCE.json"):
        shutil.copy2(original / name, tmp_path / name)
    return tmp_path


def read(directory, name):
    return json.loads((directory / name).read_text(encoding="utf-8"))


def write(directory, name, value):
    (directory / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")


def rebind_bytes(directory):
    """Update only physical byte commitments, so logical-link checks must work."""
    mapping = read(directory, "SOURCE_PROVENANCE.json")
    for name in ("RESULTS.json", "RESULTS.md", "EXECUTION_SOURCE.json"):
        data = (directory / name).read_bytes()
        mapping["original_retained_files"][name] = {
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        }
    write(directory, "SOURCE_PROVENANCE.json", mapping)


def test_original_retention_record_is_verified_without_modification(retained):
    snapshot = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in retained.iterdir()}
    assert gate.verify_retained_records(retained) == read(retained, "RESULTS.json")
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
            for p in retained.iterdir()} == snapshot


@pytest.mark.parametrize("name", ["RESULTS.json", "RESULTS.md", "EXECUTION_SOURCE.json",
                                  "SOURCE_PROVENANCE.json"])
def test_missing_retained_record_is_rejected(retained, name):
    (retained / name).unlink()
    with pytest.raises(ValueError):
        gate.verify_retained_records(retained)


def test_corrupt_retained_source_fails_before_new_execution(retained, monkeypatch):
    # The old gate accepted this missing self-commitment because it never read
    # the standalone original source record. Regeneration cannot repair that.
    (retained / "EXECUTION_SOURCE.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(gate, "EXPERIMENT", retained)
    calls = []

    def regenerate(command, **kwargs):
        calls.append(command)
        artifacts = Path(command[-1])
        artifacts.mkdir()
        write(artifacts, "RESULTS.json", read(retained, "RESULTS.json"))

    monkeypatch.setattr(gate.subprocess, "run", regenerate)
    with pytest.raises(ValueError):
        gate.main()
    assert calls == []


def test_source_self_commitment_is_required_even_when_other_links_are_rebound(retained):
    source = read(retained, "EXECUTION_SOURCE.json")
    source["files"]["requirements-lock.txt"] = "0" * 64
    write(retained, "EXECUTION_SOURCE.json", source)
    original = read(retained, "RESULTS.json")
    original["execution_source"] = source
    write(retained, "RESULTS.json", original)
    mapping = read(retained, "SOURCE_PROVENANCE.json")
    mapping["runtime"]["requirements_lock_sha256"] = "0" * 64
    write(retained, "SOURCE_PROVENANCE.json", mapping)
    rebind_bytes(retained)
    with pytest.raises(ValueError):
        gate.verify_retained_records(retained)


def test_source_domain_cannot_change_with_a_recomputed_self_commitment(retained):
    source = read(retained, "EXECUTION_SOURCE.json")
    source["domain"] = "different-source-contract"
    source["files_sha256"] = content_hash({"domain": source["domain"], "files": source["files"]})
    write(retained, "EXECUTION_SOURCE.json", source)
    original = read(retained, "RESULTS.json")
    original["execution_source"] = source
    write(retained, "RESULTS.json", original)
    mapping = read(retained, "SOURCE_PROVENANCE.json")
    mapping["execution_source_files_sha256"] = source["files_sha256"]
    write(retained, "SOURCE_PROVENANCE.json", mapping)
    rebind_bytes(retained)
    with pytest.raises(ValueError):
        gate.verify_retained_records(retained)


def test_embedded_source_must_match_retained_source_even_with_rebound_bytes(retained):
    original = read(retained, "RESULTS.json")
    original["execution_source"]["scope"] = "different embedded source"
    write(retained, "RESULTS.json", original)
    rebind_bytes(retained)
    with pytest.raises(ValueError):
        gate.verify_retained_records(retained)


def test_report_generator_must_match_historical_source_not_only_mapping(retained):
    original = read(retained, "RESULTS.json")
    original["report_source_sha256"] = "0" * 64
    write(retained, "RESULTS.json", original)
    mapping = read(retained, "SOURCE_PROVENANCE.json")
    mapping["report_generator_source_sha256"] = "0" * 64
    write(retained, "SOURCE_PROVENANCE.json", mapping)
    rebind_bytes(retained)
    with pytest.raises(ValueError):
        gate.verify_retained_records(retained)


def test_original_dirty_annotations_cannot_be_rewritten_consistently(retained):
    source = read(retained, "EXECUTION_SOURCE.json")
    source["worktree_dirty_before_run"] = True
    write(retained, "EXECUTION_SOURCE.json", source)
    original = read(retained, "RESULTS.json")
    original["execution_source"] = source
    for cell in original["cells"].values():
        cell["manifest_worktree_dirty"] = True
    write(retained, "RESULTS.json", original)
    mapping = read(retained, "SOURCE_PROVENANCE.json")
    mapping["worktree_dirty_before_execution"] = True
    mapping["verification"]["all_manifest_worktree_dirty_false"] = False
    write(retained, "SOURCE_PROVENANCE.json", mapping)
    rebind_bytes(retained)
    with pytest.raises(ValueError):
        gate.verify_retained_records(retained)


@pytest.mark.parametrize("keys,value", [
    (("schema_version",), 2), (("domain",), "wrong-contract"),
    (("execution_source_files",), 70), (("execution_source_files_sha256",), "0" * 64),
    (("local_execution_source_commit",), "0" * 40),
    (("local_execution_source_tree",), "0" * 40),
    (("published_source", "tree"), "0" * 40),
    (("study_hash",), "0" * 64), (("report_generator_source_sha256",), "0" * 64),
    (("runtime", "requirements_lock_sha256"), "0" * 64),
    (("verification", "completed_episodes"), 17),
    (("verification", "full_analytical_curves_matched"), 17),
    (("verification", "ledger_events"), 3113),
    (("verification", "rounds"), 143),
    (("verification", "sealed_replays_verified"), 17),
    (("verification", "all_manifest_worktree_dirty_false"), False),
    (("worktree_dirty_before_execution",), True),
    (("original_retained_files", "RESULTS.json", "bytes"), 1),
    (("original_retained_files", "RESULTS.json", "sha256"), "0" * 64),
])
def test_inconsistent_separate_source_mapping_is_rejected(retained, keys, value):
    mapping = read(retained, "SOURCE_PROVENANCE.json")
    target = mapping
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    write(retained, "SOURCE_PROVENANCE.json", mapping)
    with pytest.raises(ValueError):
        gate.verify_retained_records(retained)
