"""Exercise the offline atlas CLI with fresh, automatically cleaned artifacts."""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="chl-atlas-") as temporary:
        subprocess.run(
            [sys.executable, str(REPO / "experiments/incentive-atlas/atlas.py"),
             "--out", str(Path(temporary) / "atlas")],
            cwd=REPO,
            check=True,
        )


if __name__ == "__main__":
    main()
