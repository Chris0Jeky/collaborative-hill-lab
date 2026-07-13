"""One-shot: add the TFT-E + AllC conditions to Study 000 (erratum fix).

Kept in the study directory as a record of the design change; safe to re-run
(idempotent). See README 'Prediction-encoding erratum'.
"""

import sys
from pathlib import Path

STUDY_DIR = Path(__file__).parent
REPO = STUDY_DIR.parent.parent
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.experiments.scenario import (  # noqa: E402
    NarrativeSkin,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import ConditionSpec, StudySpec  # noqa: E402

TFTE = {"name": "tft_pairwise", "params": {"epsilon": "1/10"}}
PTFTE = {"name": "ptft", "params": {"denominator": "include_self", "epsilon": "1/10"}}
ALLC = {"name": "allc"}

NEW = {
    "pw-2tfte-allc": ("pairwise", [TFTE, TFTE, ALLC]),
    "nb-2ptfte-allc-incself": ("neighbourhood", [PTFTE, PTFTE, ALLC]),
}


def main() -> None:
    skin = NarrativeSkin.model_validate_json(
        (STUDY_DIR / "skins/plain.json").read_text(encoding="utf-8")
    )
    study = StudySpec.model_validate_json(
        (STUDY_DIR / "study.json").read_text(encoding="utf-8")
    )
    existing = {c.condition_id for c in study.conditions}
    added = []
    for cid, (mode, policies) in NEW.items():
        spec = ScenarioSpec.model_validate({
            "scenario_id": f"000-{cid}",
            "description": f"Legacy reproduction condition {cid} (erratum addition)",
            "world": {"kind": "nipd", "mode": mode, "rounds": 50},
            "interaction": {"structure": mode},
            "cognition": {"agents": [
                {"agent_id": f"a{i+1}", "policy": p} for i, p in enumerate(policies)
            ]},
        })
        compile_scenario(spec, skin)
        (STUDY_DIR / f"scenarios/{cid}.json").write_text(
            spec.model_dump_json(indent=2), encoding="utf-8"
        )
        if cid not in existing:
            added.append(ConditionSpec(
                condition_id=cid, scenario=f"scenarios/{cid}.json", skin="skins/plain.json"
            ))
    if added:
        study = study.model_copy(update={"conditions": tuple([*study.conditions, *added])})
        (STUDY_DIR / "study.json").write_text(study.model_dump_json(indent=2), encoding="utf-8")
    print(f"conditions now: {len(study.conditions)} (added {len(added)})")


if __name__ == "__main__":
    main()
