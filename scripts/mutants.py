"""Mutation sampler (make mutants): would the tests notice if the science were wrong?

Applies one token-level change at a time to a copy of the package and runs the
tests the import graph selects for that file. A surviving mutant is either a
real test gap or an equivalent change: triage it, do not trust the count blindly.
The sample is reproducible from --seed. This is a development probe, not a gate.
"""

import argparse
import io
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import tokenize
from pathlib import Path

import quick

REPO = quick.REPO
FAST_TESTS = ("tests/unit/", "tests/property/", "tests/metamorphic/")
DEFAULT_TARGETS = (
    "src/collaborative_hill/domain/world/nipd.py",
    "src/collaborative_hill/domain/world/graph_nipd.py",
    "src/collaborative_hill/domain/world/evidence_commons.py",
    "src/collaborative_hill/agents/scripted/nipd_policies.py",
    "src/collaborative_hill/agents/scripted/graph_nipd_policies.py",
    "src/collaborative_hill/agents/scripted/ec_policies.py",
    "src/collaborative_hill/engine/hashing.py",
    "src/collaborative_hill/engine/events.py",
    "src/collaborative_hill/engine/seeds.py",
    "src/collaborative_hill/metrics/cooperation.py",
    "src/collaborative_hill/metrics/epistemics.py",
    "src/collaborative_hill/metrics/distribution.py",
)
SWAPS = {
    "+": "-", "-": "+", "*": "+", "/": "*", "//": "*", "%": "*",
    "<": "<=", "<=": "<", ">": ">=", ">=": ">", "==": "!=", "!=": "==",
    "and": "or", "or": "and", "True": "False", "False": "True", "not": "",
    "0": "1", "1": "2", "2": "3",
}
AFTER_STAR_SYNTAX = {"(", ",", "[", "{", "lambda", ":", "=", "print"}


def candidates(source: str) -> list[tuple[int, int, int, str, str]]:
    """Every (line, start, end, old, new) token swap outside strings and comments."""
    found = []
    previous = ""
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.OP, tokenize.NAME, tokenize.NUMBER) \
                and token.string in SWAPS \
                and not (token.string == "*" and previous in AFTER_STAR_SYNTAX):
            found.append((token.start[0], token.start[1], token.end[1],
                          token.string, SWAPS[token.string]))
        if token.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT):
            previous = token.string
    return found


def apply(source: str, mutation: tuple[int, int, int, str, str]) -> str:
    line, start, end, _, new = mutation
    lines = source.splitlines(keepends=True)
    text = lines[line - 1]
    lines[line - 1] = text[:start] + new + text[end:]
    return "".join(lines)


def tests_for(target: str) -> list[str]:
    tests, _, _ = quick.plan([target])
    return [test for test in tests if test.startswith(FAST_TESTS)]


def run_mutant(overlay: Path, target: str, mutated: str, tests: list[str],
               timeout: int) -> str:
    path = overlay / target
    original = path.read_bytes()
    path.write_text(mutated, encoding="utf-8", newline="\n")
    env = {**os.environ, "PYTHONPATH": str(overlay / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    command = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *tests]
    try:
        done = subprocess.run(command, cwd=REPO, env=env, capture_output=True, timeout=timeout,
                              check=False)
    except subprocess.TimeoutExpired:
        return "killed (timeout)"
    finally:
        path.write_bytes(original)
    # pytest exit 2 means collection failed, typically an import crash: still detected.
    return "survived" if done.returncode == 0 else "killed"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", default=list(DEFAULT_TARGETS))
    parser.add_argument("--per-file", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    for target in args.targets:
        # Relative src/ paths only: the mutant must land in the overlay, never the checkout.
        if not target.startswith("src/") or Path(target).is_absolute() or ".." in target:
            parser.error(f"target must be a relative src/ path: {target}")
    rng = random.Random(args.seed)
    survivors = killed = 0
    with tempfile.TemporaryDirectory(prefix="chl-mutants-") as temp:
        overlay = Path(temp)
        shutil.copytree(REPO / "src", overlay / "src",
                        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
        # A red baseline would make every mutant look killed.
        env = {**os.environ, "PYTHONPATH": str(overlay / "src")}
        baseline = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-p",
                                   "no:cacheprovider", *FAST_TESTS], cwd=REPO, env=env,
                                  capture_output=True, check=False)
        if baseline.returncode != 0:
            print(baseline.stdout.decode(errors="replace")[-2000:])
            print("baseline tests are not green; mutation results would be meaningless")
            return 2
        for target in args.targets:
            source = (REPO / target).read_text(encoding="utf-8")
            options = candidates(source)
            sample = rng.sample(options, min(args.per_file, len(options)))
            tests = tests_for(target)
            print(f"{target}: {len(sample)} of {len(options)} sites, "
                  f"{len(tests)} test files", flush=True)
            if not tests:  # Bare pytest would fall back to every configured test path.
                print("  no fast tests reach this file: every mutant is an unmeasured gap")
                continue
            for mutation in sorted(sample):
                started = time.monotonic()
                verdict = run_mutant(overlay, target, apply(source, mutation), tests,
                                     args.timeout)
                survivors += verdict == "survived"
                killed += verdict != "survived"
                line, _, _, old, new = mutation
                text = source.splitlines()[line - 1].strip()
                print(f"  {verdict:<16} {target.rsplit('/', 1)[-1]}:{line} {old!r} -> {new!r}"
                      f" | {text[:70]} ({time.monotonic() - started:.0f}s)", flush=True)
    print(f"mutants: {killed} killed, {survivors} survived")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
