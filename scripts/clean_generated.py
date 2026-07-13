"""Remove generated artifacts (make clean-generated). Studies and source are never touched."""

import shutil
from pathlib import Path

REPO = Path(__file__).parent.parent


def main() -> int:
    artifacts = REPO / "artifacts"
    removed = 0
    if artifacts.exists():
        for child in artifacts.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
                removed += 1
    for cache in (REPO / ".pytest_cache", REPO / ".ruff_cache", REPO / ".hypothesis"):
        if cache.exists():
            shutil.rmtree(cache, ignore_errors=True)
    print(f"removed {removed} artifact tree(s); caches cleared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
