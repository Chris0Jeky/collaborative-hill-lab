"""Cost honesty: a FakeProvider measures no tokens, so both the manifest and the
operational metrics report None for tokens/cost — never a fabricated number."""

import json

from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.study import run_study
from collaborative_hill.metrics.operations import operational_metrics

# One abstain response per call — enough for any round under llm_fake.
_ABSTAIN_SCRIPT = json.dumps(['{"action":{"type":"abstain"}}'])

EC_SCENARIO = {
    "scenario_id": "sc-ec",
    "world": {"kind": "evidence_commons",
              "slots": {"s1": ["p1a", "p1b"]},
              "true_propositions": {"s1": "p1a"},
              "params": {"rounds": 2}},
    "information": {"evidence": [
        {"evidence_id": "e1", "source_id": "src1", "slot_id": "s1",
         "proposition_id": "p1a", "stance": "supports", "truth_aligned": True,
         "initial_holders": ["a1"]}]},
    "interaction": {"structure": "commons"},
    "cognition": {"agents": [
        {"agent_id": a, "policy": {"name": "llm_fake", "params": {"script": _ABSTAIN_SCRIPT}}}
        for a in ("a1", "a2", "a3")]},
}


def _write_llm_study(study_dir):
    (study_dir / "scenarios").mkdir(parents=True)
    (study_dir / "skins").mkdir(parents=True)
    (study_dir / "scenarios" / "sc.json").write_text(json.dumps(EC_SCENARIO))
    (study_dir / "skins" / "plain.json").write_text(json.dumps({"skin_id": "plain"}))
    (study_dir / "study.json").write_text(json.dumps({
        "study_id": "study-ec", "seed": 1, "replicates": 1,
        "conditions": [{"condition_id": "c0", "scenario": "scenarios/sc.json",
                        "skin": "skins/plain.json"}],
    }))


def test_llm_fake_run_reports_no_tokens_or_cost(tmp_path):
    study_dir = tmp_path / "study"
    _write_llm_study(study_dir)
    arts = tmp_path / "arts"
    run_study(study_dir, arts)

    manifest_path = next(arts.glob("**/manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Manifest: measured nothing -> None, and a fake provider is recorded honestly.
    assert manifest["input_tokens"] is None
    assert manifest["output_tokens"] is None
    assert manifest["cost_usd"] is None
    assert manifest["pricing_table_version"] is None
    assert set(manifest["providers"].values()) == {"fake-provider/fake-model-1"}

    # Operational metrics propagate the None straight through (never invent).
    events = FileEventStore(RunPaths(manifest_path.parent).events).load_all(verify=True)
    ops = operational_metrics(events, manifest)
    assert ops["input_tokens"] is None
    assert ops["output_tokens"] is None
    assert ops["cost_usd"] is None
