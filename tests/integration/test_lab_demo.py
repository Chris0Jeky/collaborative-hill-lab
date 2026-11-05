"""The bounded lab demo uses declared audit cells and labels its incomplete evidence clearly."""

import importlib.util
import json
from pathlib import Path

from collaborative_hill.engine.replay import load_run, replay_run

REPO = Path(__file__).resolve().parents[2]


def test_audit_demo_has_three_sealed_replayable_cases_and_explicit_scope(tmp_path):
    spec = importlib.util.spec_from_file_location("lab_demo", REPO / "scripts/lab.py")
    assert spec is not None and spec.loader is not None
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    selected = demo.audit_samples(tmp_path)
    assert set(selected) == {
        "behavior-tp-rq-positive-3", "behavior-tp-rq-negative-3",
        "behavior-tp-rq-unavailable-3",
    }
    root = tmp_path / "audit-feedback-demo"
    marker = json.loads((root / "DEMO.json").read_text(encoding="utf-8"))
    assert marker["full_experiment"] is False
    assert set(marker["selected_cells"]) == set(selected)
    assert len(list(root.rglob("events.jsonl"))) == 3
    for identifier in selected:
        run = root / "runs" / identifier
        _, _, manifest = load_run(run)
        assert manifest["status"] == "completed"
        assert manifest["condition_id"] == identifier
        assert replay_run(run).chains_match
