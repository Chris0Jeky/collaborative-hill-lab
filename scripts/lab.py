"""Regenerate sealed demonstration samples. Replaces artifacts/lab only, never original evidence."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.experiments.study import run_study  # noqa: E402
from collaborative_hill.reporting.lab import write_console  # noqa: E402

STUDIES = (
    ("studies/000-legacy-reproduction", 2),
    ("studies/001-evidence-commons", 2),
    ("experiments/graph-topology", 1),
)
SENSITIVITY_SAMPLES = (
    ("studies/002-nipd-sensitivity", "nb-n3-m2-q1-2"),
    ("studies/002-nipd-sensitivity/stochastic", "nb-n3-m2-ptft-include"),
)


def audit_samples(root: Path) -> list[str]:
    """Use three already declared audit cells to illustrate released feedback, not a new study."""
    script = REPO / "experiments/audit-feedback/audit_feedback.py"
    spec = importlib.util.spec_from_file_location("lab_audit_feedback", script)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load shipped audit-feedback demo source")
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)
    destination = root / "audit-feedback-demo"
    declaration, resolved = experiment.write_inputs(destination / "inputs")
    selected = [cell for cell in experiment.cells()
                if cell["kind"] == "audited_behavior" and cell["truth"] == "p"
                and cell["report"] == "q" and cell["publish_round"] == 3]
    identifiers = []
    for cell in selected:
        identifier = experiment.cell_id(cell)
        experiment.run_cell(cell, resolved[identifier], destination / "runs" / identifier,
                            declaration["design_hash"])
        identifiers.append(identifier)
    experiment.write_json(destination / "DEMO.json", {
        "schema_version": 1,
        "purpose": "Three declared audit cells for visual inspection; incomplete design sample.",
        "full_experiment": False,
        "selected_cells": identifiers,
        "full_run_command": "chl experiment run audit-feedback --out artifacts/audit-new",
    })
    return identifiers


def main() -> int:
    root = REPO / "artifacts" / "lab"
    shutil.rmtree(root, ignore_errors=True)
    failed = False
    for study, replicates in STUDIES:
        results = run_study(REPO / study, root, replicates_override=replicates)
        failed |= any(result.status != "completed" for result in results)
    for study, condition in SENSITIVITY_SAMPLES:
        results = run_study(REPO / study, root, only_condition=condition, replicates_override=1)
        failed |= any(result.status != "completed" for result in results)
    selected = audit_samples(root)
    (root / "DEMO.json").write_text(json.dumps({
        "schema_version": 1,
        "purpose": "Synthetic samples for visual inspection; not complete research designs.",
        "full_experiments": False,
        "study002_conditions": [condition for _, condition in SENSITIVITY_SAMPLES],
        "audit_feedback_cells": selected,
        "catalog_command": "chl catalog",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    out = root / "console.html"
    text, traces = write_console(root, out, max_detail=2)
    print(text, end="")
    print(f"wrote {out}")
    return 1 if failed or any(
        "broken" in trace or trace.get("status") != "completed" for trace in traces
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
