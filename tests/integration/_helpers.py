"""Shared constants and helpers for the integration suite.

Integration tests drive the *shipped* studies end to end — through the public
Python API (``run_study``, ``run_report`` …) and through the ``chl`` CLI as a
subprocess — and assert on the sealed artifacts. Everything is written under a
pytest ``tmp_path``; nothing here mutates the repo's own ``artifacts/`` tree.

Imported as a sibling module (``from ._helpers import …``), mirroring the
metamorphic suite's convention.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# tests/integration/_helpers.py -> repo root is three parents up.
REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_000 = REPO_ROOT / "studies" / "000-legacy-reproduction"
STUDY_001 = REPO_ROOT / "studies" / "001-evidence-commons"


def find_run_dirs(artifacts_root: Path) -> list[Path]:
    """Every materialised run directory (one containing ``events.jsonl``)."""
    return sorted(p.parent for p in Path(artifacts_root).rglob("events.jsonl"))


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke ``python -m collaborative_hill.cli <args>`` with the venv python.

    Uses ``sys.executable`` so the subprocess is the exact interpreter running
    the suite (the project venv), and runs from the repo root.
    """
    return subprocess.run(
        [sys.executable, "-m", "collaborative_hill.cli", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
