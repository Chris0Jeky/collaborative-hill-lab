"""Canonical graph controls and exact sealed readout; no providers or inference."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.domain.world.graph_nipd import UndirectedGraph  # noqa: E402
from collaborative_hill.engine.events import EventType  # noqa: E402
from collaborative_hill.engine.hashing import canonical_json, content_hash, frac_str  # noqa: E402
from collaborative_hill.engine.replay import load_run, replay_run  # noqa: E402
from collaborative_hill.engine.seeds import LEGACY_SEED_PROTOCOL  # noqa: E402
from collaborative_hill.experiments.manifests import git_provenance  # noqa: E402
from collaborative_hill.experiments.scenario import (  # noqa: E402
    AgentSpec,
    CognitionPlane,
    GraphNIPDWorld,
    InteractionPlane,
    NarrativeSkin,
    PolicySpec,
    ScenarioSpec,
)
from collaborative_hill.experiments.study import (  # noqa: E402
    ConditionSpec,
    StudySpec,
    build_policies,
    load_study,
    run_study,
    study_hash,
)

AGENTS = ("a1", "a2", "a3", "a4", "a5")
ROUNDS = 8
SEED = 20261029
POLICIES = {"targeted": "tft_pairwise", "linked": "tft_linked", "quorum": "tft_threshold"}
SOURCE_DOMAIN = "chl.graph-topology.source-files.v1"


@dataclass(frozen=True)
class Cell:
    topology: str
    defector: str
    policy: str

    @property
    def condition_id(self) -> str:
        return f"{self.topology}-d-{self.defector}-{self.policy}"

    @property
    def mode(self) -> Literal["pairwise", "neighbourhood"]:
        return "neighbourhood" if self.policy == "quorum" else "pairwise"


def cells() -> tuple[Cell, ...]:
    return tuple(Cell(topology, defector, policy)
                 for topology in ("complete", "ring", "star")
                 for defector in ("a1", "a2") for policy in POLICIES)


def adjacency(topology: str) -> dict[str, tuple[str, ...]]:
    if topology == "complete":
        return {a: tuple(b for b in AGENTS if b != a) for a in AGENTS}
    if topology == "ring":
        return {a: (AGENTS[(i - 1) % 5], AGENTS[(i + 1) % 5]) for i, a in enumerate(AGENTS)}
    if topology == "star":
        return {a: AGENTS[1:] if a == "a1" else ("a1",) for a in AGENTS}
    raise ValueError(f"unknown topology: {topology}")


def expected_curve(cell: Cell) -> list[str]:
    """Literal eight-round predictions committed in the design before execution."""
    if cell.policy == "quorum":
        return (["4/5"] + ["0"] * 7 if (cell.topology, cell.defector) == ("star", "a1")
                else ["4/5"] * 8)
    if cell.topology == "star":
        if cell.defector == "a1":
            return ["1/2"] + ["0"] * 7
        return (["7/8"] + ["3/4"] * 7 if cell.policy == "targeted"
                else ["7/8", "3/8"] + ["0"] * 6)
    if cell.policy == "targeted":
        return ["4/5"] + ["3/5"] * 7
    return (["4/5", "2/5"] + ["0"] * 6 if cell.topology == "ring"
            else ["4/5"] + ["0"] * 7)


def _scenario(cell: Cell) -> ScenarioSpec:
    params: dict[str, int | str | bool] = {"epsilon": "0"}
    if cell.policy == "quorum":
        params.update(threshold_num=1, threshold_den=2)
    agents = tuple(AgentSpec(
        agent_id=a, policy=PolicySpec(name="alld" if a == cell.defector else POLICIES[cell.policy],
                                     params={} if a == cell.defector else params),
    ) for a in AGENTS)
    return ScenarioSpec(
        scenario_id=cell.condition_id,
        description="Fixed N=5, one AllD, explicit placement, mean edge payoff, no exploration.",
        world=GraphNIPDWorld(mode=cell.mode, rounds=ROUNDS, payoff_aggregation="mean"),
        interaction=InteractionPlane(structure=cell.mode,
                                     graph=UndirectedGraph(adjacency=adjacency(cell.topology))),
        cognition=CognitionPlane(agents=agents),
    )


def _json_bytes(value: Any) -> bytes:
    canonical_json(value)  # reject floats recursively before producing a readable artifact
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def canonical_files() -> dict[str, bytes]:
    conditions = tuple(ConditionSpec(condition_id=c.condition_id,
                                     scenario=f"scenarios/{c.condition_id}.json", skin="skin.json")
                       for c in cells())
    spec = StudySpec(study_id="graph-topology-v1", seed=SEED, replicates=1,
                     checkpoint_every=2, conditions=conditions)
    files = {"study.json": _json_bytes(spec.model_dump(mode="json")),
             "skin.json": _json_bytes(NarrativeSkin(skin_id="graph-plain").model_dump(mode="json"))}
    files.update({f"scenarios/{c.condition_id}.json":
                  _json_bytes(_scenario(c).model_dump(mode="json")) for c in cells()})
    return files


def _preflight(files: dict[Path, bytes]) -> None:
    for path, data in files.items():
        if path.is_symlink():
            raise ValueError(f"output is a symbolic link: {path}")
        for ancestor in path.parents:
            if ancestor.is_symlink() or (ancestor.exists() and not ancestor.is_dir()):
                raise ValueError(f"output ancestor is not an ordinary directory: {ancestor}")
        if path.exists() and (not path.is_file() or path.read_bytes() != data):
            raise ValueError(f"refusing to replace different existing output: {path}")


def _write_files(files: dict[Path, bytes]) -> None:
    _preflight(files)
    for path, data in files.items():
        if path.exists():
            continue  # byte-identical no-op; preserve the original mtime
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)


def generate(directory: Path, *, check: bool = False) -> None:
    directory = Path(directory)
    lock = directory / "study.lock.json"
    if lock.exists() or lock.is_symlink():
        raise ValueError("graph controls are unfrozen; do not regenerate a frozen fixture")
    files = {directory / name: data for name, data in canonical_files().items()}
    if check:
        _preflight(files)
        missing = [str(path) for path in files if not path.is_file()]
        if missing:
            raise ValueError(f"missing canonical graph inputs: {missing}")
    else:
        _write_files(files)


def _source_record(directory: Path) -> dict[str, Any]:
    paths = [*sorted((REPO / "src").rglob("*.py")), REPO / "pyproject.toml",
             REPO / "requirements-lock.txt", Path(__file__), HERE / "README.md"]
    files = {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in paths}
    files.update({f"experiments/graph-topology/{name}":
                  hashlib.sha256((directory / name).read_bytes()).hexdigest()
                  for name in canonical_files()})
    commit, dirty = git_provenance(REPO)
    tree = None
    if commit is not None and dirty is False:
        result = subprocess.run(["git", "rev-parse", f"{commit}^{{tree}}"], cwd=REPO,
                                capture_output=True, text=True, check=False, timeout=10)
        if result.returncode == 0:
            tree = result.stdout.strip()
    return {
        "schema_version": 1, "domain": SOURCE_DOMAIN,
        "commit_kind": "local_source_checkout; remote GitHub identity is not asserted",
        "local_source_commit": commit, "clean_local_source_tree": tree,
        "worktree_dirty_before_run": dirty,
        "scope": "Package Python, dependencies, experiment program/design and canonical inputs.",
        "files": files, "files_sha256": content_hash({"domain": SOURCE_DOMAIN, "files": files}),
    }


def execute(directory: Path, artifacts: Path) -> None:
    generate(directory, check=True)
    artifacts = Path(artifacts)
    if artifacts.is_symlink() or (artifacts.exists()
                                 and (not artifacts.is_dir() or any(artifacts.iterdir()))):
        raise ValueError("execution requires a fresh artifact root")
    source = _source_record(directory)
    _write_files({artifacts / "EXECUTION_SOURCE.json": _json_bytes(source)})
    results = run_study(directory, artifacts)
    if len(results) != len(cells()) or any(r.status != "completed" for r in results):
        raise ValueError("graph execution incomplete; retain failed artifacts for diagnosis")


def _read_source(artifacts: Path) -> dict[str, Any]:
    source = json.loads((artifacts / "EXECUTION_SOURCE.json").read_text(encoding="utf-8"))
    required = {"schema_version", "domain", "commit_kind", "local_source_commit",
                "clean_local_source_tree", "worktree_dirty_before_run", "scope",
                "files", "files_sha256"}
    if (not isinstance(source, dict) or not required.issubset(source)
            or source.get("domain") != SOURCE_DOMAIN
            or type(source["schema_version"]) is not int or source["schema_version"] != 1):
        raise ValueError("invalid graph execution source record")
    canonical_json(source)
    files = source.get("files")
    if (not isinstance(files, dict) or "requirements-lock.txt" not in files
            or any(not isinstance(v, str) or re.fullmatch(r"[0-9a-f]{64}", v) is None
                   for v in files.values())
            or source["files_sha256"] != content_hash({"domain": SOURCE_DOMAIN, "files": files})):
        raise ValueError("invalid execution source file commitment")
    for name, data in canonical_files().items():
        if files.get(f"experiments/graph-topology/{name}") != hashlib.sha256(data).hexdigest():
            raise ValueError("execution source input commitments do not match the graph design")
    return source


def collect_report(directory: Path, artifacts: Path) -> dict[str, Any]:
    """Bind every completed run to this design and independently replay all 18."""
    generate(directory, check=True)
    artifacts = Path(artifacts)
    source = _read_source(artifacts)
    spec, resolved = load_study(directory)
    expected_hash = study_hash(spec, resolved)
    root = artifacts / f"DRAFT-{expected_hash[:12]}"
    expected = {root / c.condition_id / f"{c.condition_id}-r000" for c in cells()}
    if ({p.parent for p in artifacts.rglob("manifest.json")} != expected
            or {p.parent for p in artifacts.rglob("events.jsonl")} != expected):
        raise ValueError("missing, extra or misplaced graph run artifacts")
    records: dict[str, Any] = {}
    for cell in cells():
        cid = cell.condition_id
        run = root / cid / f"{cid}-r000"
        events, actual, manifest = load_run(run)
        identity = {
            "study_id": spec.study_id, "study_hash": expected_hash, "study_frozen": False,
            "condition_id": cid, "replicate": 0, "run_id": f"{cid}-r000", "status": "completed",
            "seed_root": [SEED, cid, 0], "seed_protocol": LEGACY_SEED_PROTOCOL,
            "policy_seed_root": None, "scenario_block": None,
            "code_commit": source.get("local_source_commit"),
            "dependency_lock_sha256": source["files"]["requirements-lock.txt"],
            "policies": {a: p.policy_id for a, p in build_policies(resolved[cid]).items()},
        }
        if actual != resolved[cid] or any(manifest.get(k) != v for k, v in identity.items()):
            raise ValueError(f"graph run identity mismatch: {cid}")
        if events[-1].event_type != EventType.RUN_COMPLETED or not replay_run(run).chains_match:
            raise ValueError(f"graph run is not independently replayable: {cid}")
        transitions = [e.payload for e in events if e.event_type == EventType.WORLD_TRANSITIONED]
        if [p["round"] for p in transitions] != list(range(ROUNDS)):
            raise ValueError(f"incomplete graph trajectory: {cid}")
        observed = [frac_str(Fraction(p["cooperative_votes"], p["total_votes"]))
                    for p in transitions]
        prediction = expected_curve(cell)
        records[cid] = {
            "topology": cell.topology, "defector": cell.defector, "policy": cell.policy,
            "mode": cell.mode,
            "degree_by_agent": {a: len(n) for a, n in adjacency(cell.topology).items()},
            "replicate": 0, "run_id": manifest["run_id"], "seed_root": manifest["seed_root"],
            "scenario_hash": actual.scenario_hash, "mechanism_hash": actual.mechanism_hash,
            "terminal_event_hash": events[-1].event_hash, "event_count": len(events),
            "manifest_worktree_dirty": manifest.get("worktree_dirty"),
            "replay_verified": True, "analytical_curve": prediction, "observed_curve": observed,
            "analytical_curve_match": prediction == observed,
            "cooperative_votes": [p["cooperative_votes"] for p in transitions],
            "eligible_votes": [p["total_votes"] for p in transitions],
            "mean_cooperation": frac_str(sum(map(Fraction, observed), Fraction(0)) / ROUNDS),
            "final_round_cooperation": observed[-1], "scores": events[-1].payload["scores"],
        }
    return {
        "report_version": "graph_topology@1", "status": "unfrozen_exploratory_controls",
        "report_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "study_hash": expected_hash, "episode_count": len(records), "rounds": ROUNDS,
        "population_size": 5, "fixed_defectors": 1, "payoff_aggregation": "mean",
        "seed": SEED, "seed_protocol": LEGACY_SEED_PROTOCOL,
        "unit_of_analysis": "one deterministic episode per condition; no inferential replication",
        "matching_analytical_curves": sum(r["analytical_curve_match"] for r in records.values()),
        "execution_source": source, "cells": records,
    }


def render_markdown(report: dict[str, Any]) -> str:
    source = report["execution_source"]
    lines = [
        "# Graph topology — exact deterministic readout", "",
        "**Executed, unfrozen exploratory controls; scripted agents only.**",
        f"{report['matching_analytical_curves']}/{report['episode_count']} complete cooperation "
        "curves match the local pre-execution predictions. Every original sealed run was "
        "independently replayed for this report.", "",
        "N=5, one AllD, eight rounds t=0,…,7, zero exploration, and mean incident-edge "
        "payoff are fixed. Each row is one deterministic episode. Symmetry controls "
        "and regeneration checks add no independent outcome information.", "",
        "## Measured outcomes", "",
        "All entries are exact fractions. The JSON retains full predicted/measured "
        "curves, eligible vote counts, agent degrees, seed identities and terminal commitments.",
        "",
        "| Topology | AllD seat | Reciprocator policy | Mean cooperation | Final round | "
        "Cumulative mean-edge scores (a1, a2, a3, a4, a5) | Prediction match |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for cell in cells():
        record = report["cells"][cell.condition_id]
        scores = ", ".join(record["scores"][a] for a in AGENTS)
        lines.append(f"| {cell.topology} | {cell.defector} | {cell.policy} | "
                     f"{record['mean_cooperation']} | {record['final_round_cooperation']} | "
                     f"{scores} | {record['analytical_curve_match']} |")
    lines.extend([
        "", "## Interpretation and boundaries", "",
        "Compare topologies within a fixed policy and defector-seat condition. The star "
        "has hub a1 and leaf a2; moving AllD changes policy placement. Targeted, linked "
        "and quorum TFT also differ in action/observation rules. Pairwise rates count "
        "directed edge votes and weight agents by degree; neighbourhood rates count "
        "one vote per positive-degree agent. The different star first-round rates "
        "already reflect AllD's degree before any reciprocal response.", "",
        "This experiment fixes mean payoff in both modes. Legacy complete-graph "
        "equivalence separately uses pairwise/sum and neighbourhood/mean; the complete "
        "pairwise mean scores here equal legacy summed scores divided by four.", "",
        "No uncertainty interval, p-value, population-size causal effect, human/LLM "
        "response or sparse-graph count-state pTFT model is inferred. Analytical "
        "predictions remain distinct from measured outcomes, including any mismatch.", "",
        "## Execution provenance", "",
        f"- Study content hash: `{report['study_hash']}`; unfrozen.",
        f"- Local execution checkout: `{source['local_source_commit']}`.",
        f"- Clean local tree commitment, when available: `{source['clean_local_source_tree']}`.",
        f"- Worktree dirty before execution: `{source['worktree_dirty_before_run']}`.",
        f"- Execution file commitment: `{source['files_sha256']}` "
        f"over {len(source['files'])} named source/input files.",
        f"- Report generator source SHA-256: `{report['report_source_sha256']}`.",
        "", "Commit identifiers above describe local source identity; no published GitHub "
        "revision or external preregistration timestamp is asserted. The execution "
        "source record was captured before running; per-run manifests preserve their "
        "own dirty flags. The source commitment and hash-linked ledgers establish "
        "consistency relative to retained evidence, not independent authenticity.", "",
        "Original ledgers and EXECUTION_SOURCE.json are generated artifacts. Rebuilding "
        "this readout requires those artifacts; running newer source is a new execution. "
        "Use graph_experiment.py --report-from <artifact-root> --output <fresh-prefix>.", "",
    ])
    return "\n".join(lines)


def write_report(report: dict[str, Any], prefix: Path) -> None:
    _write_files({prefix.with_suffix(".json"): _json_bytes(report),
                  prefix.with_suffix(".md"): render_markdown(report).encode("utf-8")})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate", type=Path, nargs="?", const=HERE, metavar="DIRECTORY")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--report-from", type=Path, metavar="ARTIFACTS")
    parser.add_argument("--study-dir", type=Path, default=HERE)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/graph-topology"))
    parser.add_argument("--output", type=Path, help="output prefix for --report-from only")
    args = parser.parse_args()
    if args.output is not None and args.report_from is None:
        parser.error("--output applies only to --report-from; --run writes <artifacts>/RESULTS")
    try:
        if args.generate is not None:
            generate(args.generate)
            print("Generated 18 unfrozen deterministic graph conditions")
        elif args.check:
            generate(args.study_dir, check=True)
            print("Canonical graph fixture verified: 18 conditions x 1 episode x 8 rounds")
        else:
            artifacts = args.report_from if args.report_from is not None else args.artifacts
            prefix = args.output or artifacts / "RESULTS"
            if args.run:
                # Refuse an occupied report destination before running any episodes.
                _preflight({prefix.with_suffix(".json"): b"", prefix.with_suffix(".md"): b""})
                if any(prefix.with_suffix(suffix).exists() for suffix in (".json", ".md")):
                    raise ValueError("new execution requires fresh report destinations")
                execute(args.study_dir, artifacts)
            report = collect_report(args.study_dir, artifacts)
            write_report(report, prefix)
            print(f"{report['matching_analytical_curves']}/18 full curves match; "
                  "18 sealed runs replayed; exact readout written")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
