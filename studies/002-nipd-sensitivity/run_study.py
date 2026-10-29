"""Run both Study 002 components with their declared, different repeat counts."""

import argparse
from pathlib import Path

from study002_model import STUDY_DIR, generate

from collaborative_hill.experiments.study import load_study, run_study


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/study-002"))
    parser.add_argument("--study-dir", type=Path, default=STUDY_DIR)
    parser.add_argument("--plan", action="store_true",
                        help="validate and print plan without running")
    args = parser.parse_args()
    try:
        generate(args.study_dir, check=True)
        sources = [args.study_dir, args.study_dir / "stochastic"]
        for source in sources:
            if (source / "study.lock.json").exists():
                raise ValueError("this draft runner requires unfrozen components")
        specs = [load_study(source)[0] for source in sources]
        counts = [len(spec.conditions) * spec.replicates for spec in specs]
        print(f"Study 002: {counts[0]} deterministic + {counts[1]} stochastic episodes; "
              "50 rounds each; independent seed paths; unfrozen", flush=True)
        if args.plan:
            return
        if args.artifacts.exists() and any(args.artifacts.iterdir()):
            raise ValueError("choose a fresh artifacts directory; existing results are preserved")
        for source, spec in zip(sources, specs, strict=True):
            print(f"Running {spec.study_id} ({spec.replicates} episode(s) per cell)", flush=True)
            results = run_study(source, args.artifacts)
            if any(result.status != "completed" for result in results):
                raise ValueError("a run failed; inspect sealed artifacts; no episode was replaced")
        print(f"Completed {sum(counts)} sealed episodes; generate_report.py produces the readout")
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
