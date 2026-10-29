"""Generate/check both unfrozen Study 002 components from their canonical design."""

import argparse
from pathlib import Path

from study002_model import STUDY_DIR, generate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=STUDY_DIR)
    parser.add_argument("--check", action="store_true", help="compare bytes without writing")
    args = parser.parse_args()
    try:
        generate(args.output, check=args.check)
    except ValueError as exc:
        parser.error(str(exc))
    print("Study 002 canonical inputs verified" if args.check else
          "Study 002 generated: 29 deterministic x 1 + 6 stochastic x 32; unfrozen")


if __name__ == "__main__":
    main()
