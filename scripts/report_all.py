"""Generate run + study reports for everything under artifacts/ (make report)."""

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.reporting import run_report, study_report  # noqa: E402


def main() -> int:
    artifacts = REPO / "artifacts"
    study_dirs = sorted(p for p in artifacts.iterdir() if p.is_dir())
    if not study_dirs:
        print("no artifacts found")
        return 1
    for study_dir in study_dirs:
        for run_dir in sorted(p.parent for p in study_dir.glob("*/*/events.jsonl")):
            run_report(run_dir)
        out = study_report(study_dir)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
