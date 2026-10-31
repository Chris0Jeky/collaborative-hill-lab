"""Regenerate a small sealed sample and render it (make lab). Replaces artifacts/lab only."""

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


def main() -> int:
    root = REPO / "artifacts" / "lab"
    shutil.rmtree(root, ignore_errors=True)
    for study, replicates in STUDIES:
        run_study(REPO / study, root, replicates_override=replicates)
    out = root / "console.html"
    text, traces = write_console(root, out, max_detail=2)
    print(text, end="")
    print(f"wrote {out}")
    return 1 if any("broken" in trace for trace in traces) else 0


if __name__ == "__main__":
    raise SystemExit(main())
