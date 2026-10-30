"""Change-aware gate (make quick): run only what the current diff can affect.

Selection follows a static import graph plus path mentions, so it stays current
without a maintained table. A file nothing can classify selects everything, and
CI still runs the complete gate on the exact commit: quick is for feedback speed,
never for merge evidence. Gate entry points are read from the Makefile.
"""

import ast
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACKAGE = "collaborative_hill"
PY_ROOTS = ("src", "tests", "scripts", "studies", "experiments")
GATE = re.compile(r"^(check-[\w-]+|validate|acceptance):\s*$")
SCRIPT = re.compile(r"[\w./-]+\.py|studies/[\w./-]+|experiments/[\w./-]+")
MODULE_STRING = re.compile(rf"{PACKAGE}(?:\.\w+)+")
NO_EFFECT = re.compile(r"^(docs/|LICENSE|LICENSES/|\.hosting/|\.claude/|\.codex/|\.agent-harness/)"
                       r"|^[A-Z_]+\.md$|^CITATION\.cff$")
ALWAYS_FULL = ("Makefile", "pyproject.toml", "requirements-lock.txt", ".gitattributes")


def _git(*args: str) -> list[str]:
    done = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True)
    return done.stdout.splitlines()


def changed_files(base: str) -> list[str]:
    merge_base = _git("merge-base", base, "HEAD")[0]
    tracked = _git("diff", "--name-only", merge_base)
    untracked = _git("ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked + untracked))


def python_files() -> list[Path]:
    return [path for root in PY_ROOTS for path in (REPO / root).rglob("*.py")]


def module_name(path: Path) -> str | None:
    parts = path.relative_to(REPO).with_suffix("").parts
    if parts[0] != "src":
        return None
    parts = parts[1:-1] if parts[-1] == "__init__" else parts[1:]
    return ".".join(parts)


def dependencies(path: Path, modules: dict[str, Path]) -> set[Path]:
    """Repository files this file imports, or names as a module string for a subprocess."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_bytes())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.update(MODULE_STRING.findall(node.value))
    found = {modules[name] for name in names if name in modules}
    # Studies and experiments import sibling helper modules by bare name.
    found.update(sibling for name in names
                 if "." not in name and (sibling := path.with_name(f"{name}.py")).exists())
    return found


def affected(changed: set[Path], graph: dict[Path, set[Path]]) -> set[Path]:
    closure = set(changed)
    grew = True
    while grew:
        grew = False
        for path, deps in graph.items():
            if path not in closure and deps & closure:
                closure.add(path)
                grew = True
    return closure


def makefile_gates() -> dict[str, list[str]]:
    gates: dict[str, list[str]] = {}
    current = None
    for line in (REPO / "Makefile").read_text(encoding="utf-8").splitlines():
        match = GATE.match(line)
        if match:
            current = match.group(1)
            gates[current] = []
        elif line.startswith("\t") and current:
            gates[current] += SCRIPT.findall(line)
        elif line.strip():
            current = None
    return gates


def _gate_files(paths: list[str]) -> set[Path]:
    files: set[Path] = set()
    for name in paths:
        if "*" in name:
            files.update(REPO.glob(name))
        elif (REPO / name).is_dir():
            files.update((REPO / name).rglob("*.py"))
        elif (REPO / name).exists():
            files.add(REPO / name)
    return files


def plan(changed: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Return (test paths, make gates, reasons). ``tests/`` means the complete suite."""
    relevant = [name for name in changed if not NO_EFFECT.search(name)]
    reasons = [f"full: {name}" for name in relevant if name in ALWAYS_FULL]
    reasons += [f"full: unclassified {name}" for name in relevant
                if not name.startswith((*PY_ROOTS, ".github/")) and name not in ALWAYS_FULL]
    gates = makefile_gates()
    if reasons:
        return ["tests/"], list(gates), reasons
    files = python_files()
    modules = {name: path for path in files if (name := module_name(path))}
    graph = {path: dependencies(path, modules) for path in files}
    closure = affected({REPO / name for name in relevant if name.endswith(".py")}, graph)
    data_roots = {"/".join(name.split("/")[:2]) for name in relevant
                  if name.startswith(("studies/", "experiments/"))}
    selected_gates = [gate for gate, entries in gates.items()
                      if closure & _gate_files(entries)
                      or any(root in entry for root in data_roots for entry in entries)]
    tokens = {root.split("/")[1] for root in data_roots}
    tokens.update(Path(name).stem for name in relevant if name.startswith("scripts/"))
    tests = [path.relative_to(REPO).as_posix()
             for path in sorted((REPO / "tests").rglob("test_*.py"))
             if path in closure or any(token in path.read_text(encoding="utf-8")
                                       for token in tokens)]
    return tests, selected_gates, reasons


def main() -> int:
    only_plan = "--plan" in sys.argv
    base = next((arg for arg in sys.argv[1:] if not arg.startswith("-")), "origin/main")
    changed = changed_files(base)
    tests, gates, reasons = plan(changed)
    print(f"changed {len(changed)} files against {base}")
    for reason in reasons:
        print(f"  {reason}")
    print(f"tests: {'complete suite' if tests == ['tests/'] else len(tests)}; "
          f"gates: {' '.join(gates) or 'none'}")
    if only_plan:
        for test in tests:
            print(f"  {test}")
        return 0
    python = sys.executable
    lint = [name for name in changed if name.endswith(".py") and (REPO / name).exists()]
    commands: list[list[str]] = []
    if lint:
        commands.append([python, "-m", "ruff", "check", *lint])
    if any(name.startswith("src/") for name in lint):
        commands.append([python, "-m", "mypy"])
    if tests:
        commands.append([python, "-m", "pytest", "-x", "-q", *tests])
    commands += [["make", f"PY={python}", gate] for gate in gates]
    started = time.monotonic()
    for command in commands:
        step = time.monotonic()
        label = " ".join(command[2:5] if command[0] == python else command[2:])
        code = subprocess.run(command, cwd=REPO, check=False).returncode
        print(f"[{'pass' if code == 0 else 'FAIL'} {time.monotonic() - step:5.1f}s] {label}")
        if code:
            return code
    print(f"quick: green in {time.monotonic() - started:.1f}s; CI still runs the complete gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
