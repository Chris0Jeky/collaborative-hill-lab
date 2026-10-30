"""Generate a deterministic exact readout; never execute stochastic episodes."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from sparse_ptft_exact import MAX_AGENTS, MAX_ROUNDS, MAX_STATES, GraphPTFT

from collaborative_hill.engine.hashing import canonical_json, frac_str

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROUNDS = 8
SOURCES = (
    "experiments/sparse-ptft/sparse_ptft_exact.py", "experiments/sparse-ptft/generate.py",
    "experiments/sparse-ptft/DESIGN.md", "tests/unit/test_sparse_ptft.py",
    "tests/unit/_sparse_ptft_oracle.py", "src/collaborative_hill/domain/world/graph_nipd.py",
    "src/collaborative_hill/agents/scripted/graph_nipd_policies.py",
    "src/collaborative_hill/engine/hashing.py", "docs/adr/0011-versioned-graph-nipd.md",
    "studies/002-nipd-sensitivity/study002_markov.py", "requirements-lock.txt",
)


def cells() -> dict[str, GraphPTFT]:
    complete3 = {a: tuple(b for b in "abc" if b != a) for a in "abc"}
    complete5 = {a: tuple(b for b in "abcde" if b != a) for a in "abcde"}
    cycle: dict[str, tuple[str, ...]] = {
        "a": ("b", "d"), "b": ("a", "c"), "c": ("b", "d"), "d": ("a", "c")}
    star: dict[str, tuple[str, ...]] = {"a": ("b", "c", "d"), "b": ("a",), "c": ("a",), "d": ("a",)}
    designs = (
        ("complete3-m2", complete3, ("c",)),
        ("complete5-m4", complete5, ("e",)),
        ("complete5-m3", complete5, ("d", "e")),
        ("cycle4-m3", cycle, ("d",)),
        ("star4-hub-alld", star, ("a",)),
        ("star4-leaf-alld", star, ("d",)),
        ("cycle4-all-ptft", cycle, ()),
        ("cycle4-all-alld", cycle, ("a", "b", "c", "d")),
    )
    return {f"{name}-{rule}": GraphPTFT(graph, fixed, rule)
            for name, graph, fixed in designs for rule in ("include_self", "exclude_self")}


def _verify_complete(model: GraphPTFT, record: dict[str, Any]) -> None:
    spec = importlib.util.spec_from_file_location(
        "sparse_complete_reference", REPO / "studies/002-nipd-sensitivity/study002_markov.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the complete-graph reference")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    n, m = len(model.agents), len(model.dynamic_agents)
    if model.count_projection() != module.transition_matrix(n, m, model.denominator):
        raise ValueError("complete-graph transition projection differs from Study 002")
    reference = module.benchmark(n, m, model.denominator, rounds=ROUNDS)
    for key in ("cooperation_by_round", "expected_cooperators_by_round",
                "expected_squared_cooperators_by_round", "mean_cooperation",
                "variance_mean_cooperation", "variance_terms", "absorption_by_round"):
        if record[key] != reference[key]:
            raise ValueError(f"complete-graph {key} differs from Study 002")


def build_report() -> dict[str, Any]:
    records = {}
    for name, model in cells().items():
        record = model.benchmark(ROUNDS)
        try:
            model.count_projection()
            record["count_projection"] = "strong_lumpability_verified"
        except ValueError:
            record["count_projection"] = "rejected_not_lumpable"
        record["complete_reference_matched"] = None
        if name.startswith("complete"):
            _verify_complete(model, record)
            record["complete_reference_matched"] = True
        records[name] = record
    cycle = cells()["cycle4-m3-exclude_self"]
    matrix = cycle.transition_matrix()
    witnesses = []
    for state in ((1, 1, 0, 0), (1, 0, 1, 0)):
        row = matrix[cycle.states.index(state)]
        witnesses.append({
            "state": list(state),
            "actor_probabilities": [frac_str(p) for p in cycle.probabilities(state)],
            "next_count_pmf": [frac_str(sum(
                p for following, p in zip(cycle.states, row, strict=True)
                if sum(following) == k)) for k in range(4)],
        })
    report = {
        "schema_version": 1, "analysis_version": "sparse_ptft_readout@1",
        "status": "offline_exact_analytical_extension", "rounds": ROUNDS,
        "limits": {"vertices": MAX_AGENTS, "labeled_states": MAX_STATES, "rounds": MAX_ROUNDS},
        "source_files_sha256": {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
                                for p in SOURCES},
        "model_assumption": "Independent ideal rational Bernoulli; not finite-precision PRNG",
        "cooperation_denominator": "all vertices; connected neighborhood broadcast",
        "payoff_normalization": "not evaluated; sum/mean do not enter this policy",
        "stochastic_samples": None, "sample_minus_exact_discrepancies": None,
        "four_cycle_non_lumpability": witnesses, "cells": records,
    }
    canonical_json(report)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Sparse pTFT — exact labeled-state readout", "",
        "Offline analytical extension; no stochastic episodes or measured discrepancies.", "",
        "Sixteen declared cells, eight observed rounds t=0,...,7, zero exploration.",
        "All pTFT actors start C; fixed AllD actors stay D. Every entry is an exact fraction.",
        "Cooperation weights vertices equally, including AllD, and includes the initial round.", "",
        "| Condition | E[mean cooperation] | Var(mean cooperation) | P(first all-D <= 7) |",
        "|---|---:|---:|---:|",
    ]
    for name, cell in report["cells"].items():
        lines.append(f"| {name} | {cell['mean_cooperation']} | "
                     f"{cell['variance_mean_cooperation']} | "
                     f"{cell['absorption_probability_by_last_round']} |")
    lines.extend([
        "", "Variance includes all cross-time covariance. EXACT.json retains every transition",
        "row, labeled state, expected trajectory, covariance contribution and first-all-D mass.",
        "Its restricted hitting time is E[min(T0,7)], not an eventual mean absorption time.", "",
        "## Controls and boundaries", "",
        "All six complete-graph controls match the existing Study 002 count benchmark exactly",
        "for transitions, finite-horizon first/second moments, covariance-aware variance and",
        "first-all-D probabilities under matched denominators and this eight-round horizon.",
        "Sparse count projections are checked against every labeled state and rejected when",
        "strong lumpability fails. The four-cycle witness is retained in EXACT.json and tests.", "",
        "On the four-cycle with d fixed D, (1,1,0,0) gives next-count PMF",
        "(1/8,3/8,3/8,1/8); (1,0,1,0) gives (0,1,0,0). Both start with two C.", "",
        "Star hub/leaf placements change which actor is fixed AllD; they are separate design",
        "conditions, not repetitions. Structure, population composition, placement and the",
        "self-inclusion convention must remain explicit. No payoff outcome is inferred.", "",
        "The rational independent Bernoulli assumption is idealized. The simulator retains",
        "binary-float thresholds and finite-precision RNG draws. Real-observation tests find",
        "the same local probability formula up to that explicitly acknowledged rounding.", "",
        "No general topology ranking, eventual absorption theorem, human/LLM inference,",
        "sampling uncertainty interval or new study freeze is supported by this readout.", "",
        "## Source and regeneration", "",
        "DESIGN.md declares the graphs, initialization, limits and moment recurrences.",
        "EXACT.json records SHA-256 source commitments without timestamps or floats.",
        "These establish consistency, not external publication or historical authenticity.",
        "Existing Study 002 and graph execution provenance/readouts remain untouched.", "",
        "Run with PYTHONPATH=src: python experiments/sparse-ptft/generate.py --check",
        "or make check-sparse-ptft. Check mode byte-compares both outputs without writing.", "",
    ])
    return "\n".join(lines)


def generate(directory: Path = HERE, *, check: bool = False) -> None:
    report = build_report()
    outputs = {
        directory / "EXACT.json": (json.dumps(report, indent=2, sort_keys=True) + "\n").encode(),
        directory / "EXACT.md": render_markdown(report).encode(),
    }
    for path, data in outputs.items():
        if not path.exists():
            if check:
                raise ValueError(f"missing exact readout: {path}")
        elif path.read_bytes() != data:
            if check:
                raise ValueError(f"exact readout differs: {path}")
            raise ValueError(f"refusing to overwrite divergent exact readout: {path}")
    if not check:
        directory.mkdir(parents=True, exist_ok=True)
        for path, data in outputs.items():
            if not path.exists():
                path.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=args.check)
    print("Verified exact sparse pTFT JSON/Markdown bytes." if args.check
          else "Generated exact sparse pTFT JSON/Markdown (no episodes).")


if __name__ == "__main__":
    main()
