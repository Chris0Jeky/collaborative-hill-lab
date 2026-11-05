"""Offline discovery and execution recipes for the research shipped in this checkout.

This catalog describes existing designs. Listing or planning never runs a simulation,
changes a source artifact, freezes a study, or enables provider requests. Execution
delegates to the original entry points so their evidence/provenance checks still apply.
"""

import os
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

Kind = Literal["study", "experiment", "analysis", "archive"]
Steps = tuple[tuple[str, ...], ...]
CLI = ("-m", "collaborative_hill.cli")


@dataclass(frozen=True)
class CatalogEntry:
    experiment_id: str
    title: str
    kind: Kind
    source: str
    question: str
    evidence: str
    readouts: tuple[str, ...]
    run_steps: Steps = ()
    check_steps: Steps = ()
    check_scope: str = ""
    clean_source_required: bool = False
    notes: str = ""
    study_specs: tuple[str, ...] = ()


def _pack(
    identifier: str, title: str, script: str, question: str, evidence: str,
    *, clean: bool = False,
) -> CatalogEntry:
    source = f"experiments/{identifier}"
    runner = f"{source}/{script}.py"
    return CatalogEntry(
        identifier, title, "experiment", source, question, evidence,
        (f"{source}/DESIGN.md", f"{source}/RESULTS.md"),
        ((runner, "--out", "{out}"),), ((runner, "--check"),),
        "Re-execute the declared synthetic design in temporary storage and compare readout bytes.",
        clean_source_required=clean,
    )


CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        "study-000", "Legacy reproduction and strategy controls", "study",
        "studies/000-legacy-reproduction",
        "Which legacy Hill/Valley effects depend on strategy as well as interaction structure?",
        "Unfrozen scripted reproduction; exact replication of historical unseeded CSVs "
        "is not claimed.",
        ("studies/000-legacy-reproduction/README.md",),
        ((*CLI, "run", "studies/000-legacy-reproduction", "--artifacts", "{out}"),
         ("studies/000-legacy-reproduction/generate_report.py", "--artifacts", "{out}",
          "--out", "{out}/REPORT.md")),
        ((*CLI, "study", "validate", "studies/000-legacy-reproduction"),),
        "Validate the declared study and compiled scenarios; this does not rerun its episodes.",
        study_specs=("studies/000-legacy-reproduction/study.json",),
    ),
    CatalogEntry(
        "study-001", "Evidence Commons foundation", "study", "studies/001-evidence-commons",
        "How do accountability and evidence access change finite scripted incentives?",
        "Unfrozen synthetic study. C1 and intervention integrity pass; C2 fails, "
        "so no dilemma certificate.",
        ("studies/001-evidence-commons/README.md",
         "studies/001-evidence-commons/MECHANISM_CERTIFICATE.md"),
        ((*CLI, "run", "studies/001-evidence-commons", "--artifacts", "{out}"),),
        ((*CLI, "study", "validate", "studies/001-evidence-commons"),),
        "Validate the declared study and compiled scenarios; this does not rerun its episodes.",
        notes="The historical certificate generator writes into the source study, so this wrapper "
              "runs sealed episodes only. Inspect the fresh output with chl lab or chl monitor.",
        study_specs=("studies/001-evidence-commons/study.json",),
    ),
    CatalogEntry(
        "study-002", "NIPD sensitivity and exact benchmark", "study",
        "studies/002-nipd-sensitivity",
        "How sensitive is complete-population reciprocity to policy and population choices?",
        "Unfrozen synthetic deterministic/stochastic components, with a separate exact benchmark.",
        ("studies/002-nipd-sensitivity/README.md", "studies/002-nipd-sensitivity/RESULTS.md"),
        (("studies/002-nipd-sensitivity/run_study.py", "--artifacts", "{out}"),
         ("studies/002-nipd-sensitivity/generate_report.py", "--artifacts", "{out}",
          "--output", "{out}/REPORT")),
        (("studies/002-nipd-sensitivity/generate_study.py", "--check"),
         ("studies/002-nipd-sensitivity/generate_exact_benchmark.py", "--check")),
        "Regenerate declared inputs and the exact analytical benchmark; not a stochastic rerun.",
        notes="Runs deterministic and stochastic components at their declared replicate counts.",
        study_specs=("studies/002-nipd-sensitivity/study.json",
                     "studies/002-nipd-sensitivity/stochastic/study.json"),
    ),
    CatalogEntry(
        "incentive-atlas", "Finite incentive atlas", "experiment", "experiments/incentive-atlas",
        "Where do finite-strategy inequalities hold as benefit and attribution credit vary?",
        "Exact finite-strategy analysis checked against 224 synthetic engine episodes; "
        "no behavioral effect.",
        ("experiments/incentive-atlas/README.md",),
        (("experiments/incentive-atlas/atlas.py", "--out", "{out}"),),
        (("scripts/check_atlas.py",),),
        "Build in temporary storage and check exact inequalities against engine episodes.",
    ),
    _pack(
        "responsive-commons", "Contribution-history sensitivity", "responsive_commons",
        "When does a declared history-responsive policy change contributions?",
        "Synthetic scripted sensitivity with finite incentives and fixed-action controls.",
    ),
    _pack(
        "quality-safeguards", "Skeptical quality safeguards", "quality_safeguards",
        "Can a skeptical rule distinguish independent support from repeated misinformation?",
        "Synthetic scripted rules, truth negative controls and fixed-action controls.", clean=True,
    ),
    _pack(
        "ec-rule-ablation", "Evidence Commons rule ablation", "ec_rule_ablation",
        "Which components and interactions of the skeptical rule account for its behavior?",
        "Synthetic four-component factorial with literal predictions and fixed-action controls.",
        clean=True,
    ),
    _pack(
        "noisy-corpus", "Noisy evidence corpus", "noisy_corpus",
        "How do source noise, dependence and label changes affect scripted evidence review?",
        "Exact synthetic source models and label controls; audit contract here is observational.",
        clean=True,
    ),
    _pack(
        "audit-feedback", "Released audits and decision feedback", "audit_feedback",
        "When does a negative audit change a scripted decision, and with what quality cost?",
        "76 synthetic runs, literal controls and exact-law checks; no live model or human data.",
        clean=True,
    ),
    CatalogEntry(
        "sparse-ptft", "Exact sparse-graph pTFT", "analysis", "experiments/sparse-ptft",
        "Which labeled graph states are needed to predict probabilistic reciprocity exactly?",
        "Exact finite-state calculation with an independent history oracle; no sampled episodes.",
        ("experiments/sparse-ptft/DESIGN.md", "experiments/sparse-ptft/EXACT.md"),
        check_steps=(("experiments/sparse-ptft/generate.py", "--check"),),
        check_scope="Recompute exact results and compare the retained JSON/Markdown bytes.",
        notes="No fresh-output interface is shipped. Use check to preserve original results.",
    ),
    CatalogEntry(
        "graph-topology", "Graph topology and agent placement", "experiment",
        "experiments/graph-topology",
        "How do local interaction graphs and defector placement change deterministic curves?",
        "18 synthetic eight-round conditions with hand-derived curves and replay checks.",
        ("experiments/graph-topology/README.md", "experiments/graph-topology/RESULTS.md"),
        (("experiments/graph-topology/graph_experiment.py", "--run", "--artifacts", "{out}"),),
        (("experiments/graph-topology/graph_experiment.py", "--check"),
         ("scripts/check_graph.py",)),
        "Check canonical inputs, rerun graph controls and verify retained provenance consistency.",
        notes="The runner records source cleanliness; a dirty run is not original clean evidence.",
        study_specs=("experiments/graph-topology/study.json",),
    ),
    CatalogEntry(
        "legacy-audit", "Historical NPDL source audit", "archive",
        "docs/research/_discovery/legacy-code-audit.md",
        "Which older engines, reporting defects and strategy confounds informed this lab?",
        "Historical source audit. The external legacy engines are not shipped or runnable here.",
        ("docs/research/_discovery/legacy-code-audit.md",),
        notes="Use study-000 for the maintained reproduction and deconfounding experiments.",
    ),
)


def repository_root() -> Path:
    root = Path(__file__).resolve().parents[3]
    if not (root / "pyproject.toml").is_file() or not (root / "studies").is_dir():
        raise ValueError("experiment recipes require this repository's editable source checkout")
    return root


def validate_catalog(root: Path) -> None:
    """Fail visibly for stale paths or a new experiment/study missing from discovery."""
    identifiers = [entry.experiment_id for entry in CATALOG]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate experiment ID in catalog")
    sources = {entry.source for entry in CATALOG}
    for parent in ("studies", "experiments"):
        shipped = {p.relative_to(root).as_posix() for p in (root / parent).iterdir()
                   if p.is_dir() and not p.name.startswith((".", "__"))}
        missing = shipped - sources
        if missing:
            raise ValueError(f"uncataloged {parent}: {', '.join(sorted(missing))}")
    for entry in CATALOG:
        paths = {entry.source, *entry.readouts, *entry.study_specs}
        paths.update(arg for step in (*entry.run_steps, *entry.check_steps) for arg in step
                     if arg.endswith(".py") and "{out}" not in arg)
        for relative in paths:
            path = root / relative
            if not path.exists() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(
                    f"{entry.experiment_id}: missing or external catalog path {relative}")


def get_entry(identifier: str) -> CatalogEntry:
    for entry in CATALOG:
        if entry.experiment_id == identifier:
            return entry
    raise ValueError(f"unknown experiment {identifier!r}; use chl catalog for available IDs")


def catalog_data(root: Path) -> dict[str, Any]:
    validate_catalog(root)
    return {
        "schema_version": 1,
        "evidence_scope": "Synthetic scripted populations and exact analysis; "
                          "no live LLM/human results.",
        "entries": [asdict(entry) for entry in CATALOG],
    }


def validate_output(root: Path, output: Path) -> Path:
    """Preflight without creating anything; resolve aliases before protecting source/run trees."""
    if output.exists() or output.is_symlink():
        raise ValueError(f"output already exists: {output}; choose a new directory")
    resolved = output.resolve()
    source = root.resolve()
    if resolved.is_relative_to(source):
        relative = resolved.relative_to(source)
        if len(relative.parts) < 2 or relative.parts[0] != "artifacts":
            raise ValueError("outputs inside this checkout must be under artifacts/<new-directory>")
    for parent in resolved.parents:
        if (parent / "events.jsonl").exists() or (parent / "manifest.json").exists():
            raise ValueError("output must not be inside an existing evidence run")
    return resolved


def experiment_plan(
    root: Path, identifier: str, *, output: Path | None = None, check: bool = False,
) -> dict[str, Any]:
    validate_catalog(root)
    entry = get_entry(identifier)
    mode = "check" if check or not entry.run_steps else "run"
    steps = entry.check_steps if mode == "check" else entry.run_steps
    if not steps:
        raise ValueError(f"{identifier} is an archived reference with no executable recipe")
    if mode == "check" and output is not None:
        raise ValueError("checks use temporary storage or read-only comparison; omit --out")
    destination = None
    if mode == "run":
        candidate = output if output is not None else root / "artifacts" / f"{identifier}-new"
        destination = validate_output(root, candidate)
    commands = [[sys.executable, *(part.replace("{out}", str(destination)) for part in step)]
                for step in steps]
    return {
        "schema_version": 1, "experiment_id": identifier, "operation": mode,
        "cwd": str(root.resolve()), "commands": commands,
        "output": str(destination) if destination is not None else None,
        "evidence": entry.evidence,
        "scope": entry.check_scope if mode == "check" else "Execute the shipped declared design.",
        "clean_source_required": mode == "run" and entry.clean_source_required,
        "provider_requests": False, "writes_source_artifacts": False,
        "notes": entry.notes,
    }


def render_plan(plan: dict[str, Any]) -> str:
    lines = [f"{plan['experiment_id']} — {plan['operation']}", plan["scope"],
             f"Evidence: {plan['evidence']}", f"Working directory: {plan['cwd']}"]
    if plan["clean_source_required"]:
        lines.append("Requires a clean committed checkout; the original runner enforces this.")
    if plan["notes"]:
        lines.append(plan["notes"])
    formatter = subprocess.list2cmdline if os.name == "nt" else shlex.join
    lines.extend(formatter(command) for command in plan["commands"])
    return "\n".join(lines) + "\n"


def execute_experiment(
    root: Path, identifier: str, *, output: Path | None = None, check: bool = False,
) -> int:
    """Delegate argv directly, stop on first failure, and retain all partial evidence."""
    entry = get_entry(identifier)
    if not check and not entry.run_steps:
        raise ValueError(
            f"{identifier} has no run recipe; inspect its catalog check/reference entry")
    if not check and output is None:
        raise ValueError("run requires an explicit --out new-directory")
    plan = experiment_plan(root, identifier, output=output, check=check)
    # Child modules must come from the same checkout even when launched elsewhere or
    # through an interpreter whose editable installation points to another worktree.
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root / "src") + os.pathsep + environment.get("PYTHONPATH", "")
    for command in plan["commands"]:
        completed = subprocess.run(command, cwd=root, env=environment, shell=False, check=False)
        if completed.returncode:
            return completed.returncode if completed.returncode > 0 else 1
    return 0
