"""Independent arithmetic/design checks for the responsive EC enumeration."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / (
    "experiments/responsive-commons/responsive_commons.py")
spec = importlib.util.spec_from_file_location("responsive_experiment", MODULE_PATH)
assert spec is not None and spec.loader is not None
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


def test_declared_full_cross_and_pairing_blocks():
    study, resolved = experiment.design()
    assert len(study.conditions) == len(resolved) == 320
    assert study.replicates == 1
    assert study.seed_protocol == "paired-policy-v2"
    blocks = {condition.scenario_block for condition in study.conditions}
    assert len(blocks) == 80
    for block in blocks:
        members = [c for c in study.conditions if c.scenario_block == block]
        institutions = {(
            resolved[c.condition_id].spec.institution.accountability,
            resolved[c.condition_id].spec.institution.evidence_topology,
        ) for c in members}
        assert institutions == {("aggregate", "private"), ("aggregate", "shared_ledger"),
                                ("attributable", "private"),
                                ("attributable", "shared_ledger")}


def effort_only_profiles():
    # Literal synthetic game: each active player pays one, everyone else zero.
    # Every C->F deviation gains one; total CCC is -3 versus zero at FFF.
    return {profile: {"utility": {agent: "-1" if active == "C" else "0"
                                   for agent, active in zip(experiment.AGENTS, profile,
                                                            strict=True)},
                      "total_utility": str(-profile.count("C"))}
            for profile in experiment.PROFILES}


def test_strict_certificate_and_all_twelve_deviations():
    result = experiment.certificate(effort_only_profiles())
    assert result["c1"] is True
    assert result["c2"] is False
    assert result["finite_strategy_dilemma"] is False
    assert result["ccc_minus_fff_total_utility"] == "-3"
    deviations = result["active_to_freerider_deviations"]
    assert len(deviations) == 12
    assert {d["gain"] for d in deviations} == {"1"}
    for deviation in deviations:
        index = experiment.AGENTS.index(deviation["agent"])
        assert deviation["from"][index] == "C"
        assert deviation["to"][index] == "F"
        assert sum(a != b for a, b in zip(deviation["from"], deviation["to"], strict=True)) == 1


def test_certificate_keeps_zero_boundary_strict():
    profiles = {p: {"utility": dict.fromkeys(experiment.AGENTS, "0"), "total_utility": "0"}
                for p in experiment.PROFILES}
    result = experiment.certificate(profiles)
    assert result["c1"] is result["c2"] is result["finite_strategy_dilemma"] is False


def test_certificate_rejects_missing_profile():
    profiles = effort_only_profiles()
    del profiles["CFC"]
    with pytest.raises(ValueError, match="all eight"):
        experiment.certificate(profiles)


def test_task_integrity_allows_credit_redistribution_but_detects_task_changes():
    source = {"action_hash": "actions", "briefing": [{"claim_id": None}],
              "effort": {"a1": 1, "a2": 0}, "collective_quality": 0,
              "total_utility": "-1", "individual_credit": {"a1": "0", "a2": "0"}}
    target = deepcopy(source)
    target["individual_credit"] = {"a1": "2", "a2": "-2"}
    assert all(experiment.task_integrity(source, target).values())
    target["total_utility"] = "1"
    assert experiment.task_integrity(source, target)["total_utility"] is False


def test_existing_output_is_not_rewritten(tmp_path):
    output = tmp_path / "record"
    output.mkdir()
    sentinel = output / "original.txt"
    sentinel.write_text("retain original evidence", encoding="utf-8")
    with pytest.raises(FileExistsError):
        experiment.execute(output)
    assert sentinel.read_text(encoding="utf-8") == "retain original evidence"
    assert list(output.iterdir()) == [sentinel]


def test_all_freerider_sealed_episode_is_exact_zero(tmp_path):
    study, resolved = experiment.write_inputs(tmp_path / "inputs")
    cell = {"corpus": "misleading", "topology": "private", "accountability": "aggregate",
            "rule": "all-5", "profile": "FFF"}
    cid = experiment.cell_id(cell)
    experiment.run_study(tmp_path / "inputs", tmp_path / "runs", only_condition=cid)
    path = experiment.run_path(tmp_path, experiment.study_hash(study, resolved), cid)
    record = experiment.episode_record(path, resolved[cid])
    assert record["action_counts"] == {"withhold": 36}
    assert record["contribution_fraction"] == "0"
    assert record["total_utility"] == "0"
    assert record["collective_quality"] == record["correct_slots"] == record["wrong_slots"] == 0
    assert record["effort"] == {"a1": 0, "a2": 0, "a3": 0}
    assert experiment.replay_run(path).chains_match
    # A consistent ledger cannot silently become a different declared replicate.
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["replicate"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected manifest replicate"):
        experiment.episode_record(path, resolved[cid], expected_manifest={"replicate": 0})


@pytest.mark.parametrize("corpus,topology,quality,total_utility,contributions", [
    ("accurate", "shared_ledger", 24, "2", "3/4"),
    ("accurate", "private", 24, "-1", "5/6"),
    ("misleading", "shared_ledger", -24, "-74", "3/4"),
    ("misleading", "private", -24, "-77", "5/6"),
])
def test_hand_derived_all_peer_quorum_trace(
        tmp_path, corpus, topology, quality, total_utility, contributions):
    # Under shared visibility, rounds0..2 inspect, 3..5 propose, 6..8 verify.
    # Private visibility inserts one share round. Three verifications per actor
    # support only the first two slots (earliest duplicated claims): |Q|=24,
    # proposer+verifier credits total +/-14, total effort36 shared or39 private.
    # Anonymous all-peer quorum stops at round5: effort15, no accepted claims.
    study, resolved = experiment.write_inputs(tmp_path / "inputs")
    digest = experiment.study_hash(study, resolved)
    for accountability in ("aggregate", "attributable"):
        cell = {"corpus": corpus, "topology": topology, "accountability": accountability,
                "rule": "all-5", "profile": "CCC"}
        cid = experiment.cell_id(cell)
        experiment.run_study(tmp_path / "inputs", tmp_path / "runs", only_condition=cid)
        record = experiment.episode_record(experiment.run_path(tmp_path, digest, cid),
                                            resolved[cid])
        if accountability == "aggregate":
            assert record["collective_quality"] == 0
            assert record["total_utility"] == "-15"
            assert record["contribution_fraction"] == "5/12"
        else:
            assert record["collective_quality"] == quality
            assert record["total_utility"] == total_utility
            assert record["contribution_fraction"] == contributions
