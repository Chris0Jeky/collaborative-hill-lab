"""Run an offline parent -> child -> grandchild tutorial in a fresh directory.

    python scripts/counterfactual_demo.py --out artifacts/counterfactual-demo

Uses one existing condition from each shipped study without changing/fixing its
scientific inputs. No model provider calls, freezes, external services or costs.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.agents.scripted.ec_policies import build_ec_policy  # noqa: E402
from collaborative_hill.agents.scripted.nipd_policies import AllDPolicy  # noqa: E402
from collaborative_hill.engine.branching import branch_run  # noqa: E402
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths  # noqa: E402
from collaborative_hill.experiments.study import run_study  # noqa: E402
from collaborative_hill.reporting.comparison import compare_runs  # noqa: E402


def demonstrate(study: Path, condition: str, output: Path, policy: Any) -> dict[str, Any]:
    results = run_study(study, output / "runs", only_condition=condition, replicates_override=1)
    if len(results) != 1 or results[0].status != "completed":
        raise ValueError("demonstration parent did not complete")
    manifests = list((output / "runs").rglob("manifest.json"))
    if len(manifests) != 1:
        raise ValueError("expected exactly one parent manifest")
    parent = manifests[0].parent
    child, grandchild = output / "child", output / "grandchild"
    for source, target in ((parent, child), (child, grandchild)):
        fork = FileCheckpointStore(RunPaths(source).checkpoints).list_seqs()[0]
        result, _ = branch_run(
            parent_dir=source, fork_seq=fork, child_dir=target,
            child_run_id=f"{condition}-{target.name}", policy_overrides={"a3": policy},
        )
        if result.status != "completed":
            raise ValueError(f"demonstration {target.name} failed: {result.failure_reason}")
    directories = {"parent": parent, "child": child, "grandchild": grandchild}
    first = compare_runs(parent, child, verify_replay=True)
    second = compare_runs(child, grandchild, verify_replay=True)
    replays = {"parent": first["replay_reports"]["left"],
               "child": first["replay_reports"]["right"],
               "grandchild": second["replay_reports"]["right"]}
    if not all(report["chains_match"] for report in replays.values()):
        raise ValueError("a demonstration replay did not reproduce its chain")
    return {
        "condition": condition,
        "directories": {name: str(directory.relative_to(output))
                        for name, directory in directories.items()},
        "replays": replays,
        "parent_to_child": first,
        "child_to_grandchild": second,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Fresh output directory")
    args = parser.parse_args()
    output: Path = args.out
    try:
        # Exclusive creation protects previous artifacts, even an empty directory.
        output.mkdir(parents=True, exist_ok=False)
        mechanisms = {
            "nipd": demonstrate(REPO / "studies/000-legacy-reproduction", "pw-3tft",
                                output / "nipd", AllDPolicy("pairwise")),
            "evidence_commons": demonstrate(
                REPO / "studies/001-evidence-commons", "attr-ledger",
                output / "evidence_commons", build_ec_policy("ec_contributor", {}),
            ),
        }
        summary = {"schema_version": 1, "scope": "offline_counterfactual_demonstration",
                   "mechanisms": mechanisms}
        (output / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        lines = ["# Offline counterfactual demonstration", "",
                 "Six sealed runs, replayed from recorded actions. No study inputs were changed.",
                 "These single-episode differences are descriptive, not statistical findings.", "",
                 "| Mechanism | Agent | Full-episode utility change (child - parent) |",
                 "|---|---|---|"]
        for name, entry in mechanisms.items():
            for agent, delta in entry["parent_to_child"]["utility_delta"].items():
                lines.append(f"| {name} | {agent} | {delta} |")
        lines.extend(["", "Inspect `summary.json` for paths, replay proofs and action differences.",
                      "Nested branches explicitly resupply the inherited non-original policy.",
                      "The second branch retains that policy; a new run ID alone changes hashes,",
                      "not actions. Utilities cover the entire episode,",
                      "including the common prefix."])
        (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Verified six sealed runs; comparison summary: {output / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
