"""Unfrozen, finite-strategy incentive atlas. Run from any working directory."""

import argparse
import itertools
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.engine.events import EventType  # noqa: E402
from collaborative_hill.engine.hashing import content_hash, frac_str, sha256_hex  # noqa: E402
from collaborative_hill.engine.replay import replay_run  # noqa: E402
from collaborative_hill.engine.runner import RunConfig, run_episode  # noqa: E402
from collaborative_hill.engine.store import FileEventStore, RunPaths  # noqa: E402
from collaborative_hill.experiments.manifests import (  # noqa: E402
    RunManifest,
    environment_provenance,
    write_manifest,
)
from collaborative_hill.experiments.scenario import (  # noqa: E402
    NarrativeSkin,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import build_policies, validate_study  # noqa: E402

AGENTS = ("a1", "a2", "a3")
PROFILES = tuple("".join(p) for p in itertools.product("CF", repeat=3))
CELLS = {
    "aggregate/private": "agg-priv",
    "aggregate/shared_ledger": "agg-ledger",
    "attributable/private": "attr-priv",
    "attributable/shared_ledger": "attr-ledger",
}
STUDIES = ("000-legacy-reproduction", "001-evidence-commons")
Vector = tuple[Fraction, Fraction, Fraction]
ZERO: Vector = (Fraction(0), Fraction(0), Fraction(0))
# Deliberate probes, not a grid: negative, two C2 boundaries, interior with both
# denominators, and an attributable all-C deviation boundary / high-credit case.
PROBES = ((0, 0), ("31/2", 1), (32, 1), ("109/3", "1/2"), (3, 4), (0, 7))
DESIGNS = ((40, 0), (33, 1), (12, 4), (0, 7))


def point(b: Any, r: Any) -> tuple[Fraction, Fraction]:
    if any(isinstance(x, bool) or not isinstance(x, int | str | Fraction) for x in (b, r)):
        raise ValueError("use exact integer or rational strings, never floats")
    values = (Fraction(b), Fraction(r))
    if min(values) < 0:
        raise ValueError("the atlas domain is b >= 0, r >= 0")
    return values


def value(vector: Vector, b: Fraction, r: Fraction) -> Fraction:
    return vector[0] * b + vector[1] * r + vector[2]


def subtract(left: Vector, right: Vector) -> Vector:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def total(vectors: dict[str, Vector]) -> Vector:
    return (sum((v[0] for v in vectors.values()), Fraction(0)),
            sum((v[1] for v in vectors.values()), Fraction(0)),
            sum((v[2] for v in vectors.values()), Fraction(0)))


def coefficients(summary: dict[str, Any]) -> dict[str, Vector]:
    """Per-agent (b, r, constant) coefficients from the (12, 1) sealed summary."""
    correct = sum(entry.get("correct") is True for entry in summary["briefing"])
    wrong = sum(entry.get("correct") is False for entry in summary["briefing"])
    return {
        agent: (Fraction(correct, 3), Fraction(summary["individual_credit"][agent]),
                -4 * wrong - Fraction(effort))
        for agent, effort in summary["effort"].items()
    }


def encode(vector: Vector) -> list[str]:
    return [frac_str(x) for x in vector]


def decode(vector: list[str]) -> Vector:
    a, b, c = map(Fraction, vector)
    return a, b, c


def run_profile(root: Path, cell: str, profile: str,
                b: Fraction, r: Fraction) -> dict[str, Any]:
    """Run integer-unit engine episodes; normalize monetary results by scale."""
    b, r = point(b, r)
    if cell not in CELLS or profile not in PROFILES:
        raise ValueError("unknown institution or profile")
    scale = math.lcm(b.denominator, r.denominator)
    source = REPO / "studies/001-evidence-commons/scenarios" / f"{CELLS[cell]}.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    params = raw["world"]["params"]
    for name in params:
        if name.startswith(("cost_", "penalty_", "credit_")):
            params[name] *= scale
            if name.startswith("credit_"):
                params[name] = int(params[name] * r)
    params["benefit_correct_slot"] = int(b * scale)
    for agent, strategy in zip(raw["cognition"]["agents"], profile, strict=True):
        agent["policy"] = {"name": "ec_contributor" if strategy == "C" else "ec_freerider"}
    raw["scenario_id"] = f"atlas-{CELLS[cell]}-{profile}"
    resolved = compile_scenario(ScenarioSpec.model_validate(raw),
                                NarrativeSkin(skin_id="atlas-plain", title="Incentive atlas"))
    policies = build_policies(resolved)
    env = environment_provenance()
    run_id = raw["scenario_id"]
    config = RunConfig(study_id="unfrozen-incentive-atlas", run_id=run_id,
                       seed_root=(0, run_id, 0))
    with RunPaths(root / run_id).reserve() as paths:
        (paths.root / "scenario.resolved.json").write_text(
            resolved.model_dump_json(indent=2), encoding="utf-8", newline="\n")
        result = run_episode(mechanism=resolved.build_mechanism(), policies=policies,
                             config=config, paths=paths)
        if result.status != "completed":
            raise RuntimeError(result.failure_reason)
        write_manifest(RunManifest(
            study_id=config.study_id, condition_id=CELLS[cell], run_id=run_id, replicate=0,
            scenario_hash=resolved.scenario_hash, mechanism_hash=resolved.mechanism_hash,
            narrative_hash=resolved.narrative_hash,
            evidence_corpus_hash=resolved.evidence_corpus_hash,
            institution=resolved.spec.institution.model_dump(mode="json"),
            policies={a: p.policy_id for a, p in policies.items()},
            seed_root=list(config.seed_root),
            status=result.status, event_count=result.event_count,
            final_event_hash=result.final_event_hash,
            python_version=env["python_version"], platform=env["platform"],
        ), paths.manifest)
    events = FileEventStore(paths.events).load_all(verify=True)
    if events[-1].event_type != EventType.RUN_COMPLETED:
        raise ValueError("coefficient extraction requires a completed seal")
    summary = events[-1].payload
    # These labels are retained exactly; monetary totals alone are normalized.
    normalized = {"briefing": summary["briefing"]}
    for key in ("utility", "individual_credit", "effort"):
        normalized[key] = {a: frac_str(Fraction(x) / scale) for a, x in summary[key].items()}
    normalized["collective_quality"] = frac_str(Fraction(summary["collective_quality"], scale))
    actions = [[event.logical_time, event.payload] for event in events
               if event.event_type == EventType.ACTION_ACCEPTED]
    return {"summary": normalized, "action_hash": content_hash(actions),
            "seal_hash": events[-1].event_hash, "integer_scale": scale}


def collect(root: Path, b: Any = 12, r: Any = 1) -> dict[str, dict[str, Any]]:
    b, r = point(b, r)
    return {cell: {profile: run_profile(root, cell, profile, b, r) for profile in PROFILES}
            for cell in CELLS}


def derive(baseline: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cells = {}
    for cell, profiles in baseline.items():
        payoffs = {p: coefficients(record["summary"]) for p, record in profiles.items()}
        deviations: list[dict[str, Any]] = []
        for profile in PROFILES:
            for i, agent in enumerate(AGENTS):
                if profile[i] == "C":
                    target = profile[:i] + "F" + profile[i + 1:]
                    deviations.append({"from": profile, "to": target, "agent": agent,
                                       "gain": encode(subtract(payoffs[target][agent],
                                                               payoffs[profile][agent]))})
        uniform = next((d for d in deviations if d["from"] == "CFF"), None)
        if uniform is None or decode(uniform["gain"])[:2] != ZERO[:2] or \
                Fraction(uniform["gain"][2]) <= 0:
            raise ValueError("uniform C1 witness changed; revise the atlas proof")
        cells[cell] = {
            "payoffs": {p: {a: encode(v) for a, v in agents.items()}
                        for p, agents in payoffs.items()},
            "deviations": deviations,
            "c1_uniform_witness": uniform,
            "c2_difference": encode(subtract(total(payoffs["CCC"]), total(payoffs["FFF"]))),
        }
    c3 = []
    for topology in ("private", "shared_ledger"):
        agg, att = f"aggregate/{topology}", f"attributable/{topology}"
        for profile in PROFILES:
            left, right = baseline[agg][profile], baseline[att][profile]
            if (left["action_hash"] != right["action_hash"]
                    or left["summary"]["briefing"] != right["summary"]["briefing"]
                    or total(coefficients(left["summary"])) !=
                    total(coefficients(right["summary"]))):
                c3.append({"topology": topology, "profile": profile})
    if c3:
        raise ValueError(f"C3 invariance failed: {c3}")
    return {"schema": "incentive-atlas-v1", "status": "exploratory-unfrozen",
            "coefficient_order": ["b", "r", "constant"], "domain": "b >= 0, r >= 0 (rational)",
            "c1": "exists a unilateral C->F gain > 0", "c2": "sum U(CCC)-sum U(FFF) > 0",
            "admissible": "C1 AND C2; all-institution region is intersection over cells",
            "cells": cells, "c3_violations": c3}


def evaluate(atlas: dict[str, Any], benefit: Any, credit: Any) -> dict[str, Any]:
    b, r = point(benefit, credit)
    result: dict[str, Any] = {"b": frac_str(b), "r": frac_str(r), "cells": {}}
    for cell, data in atlas["cells"].items():
        gains = [{**d, "value": frac_str(value(decode(d["gain"]), b, r))}
                 for d in data["deviations"]]
        profitable = [d for d in gains if Fraction(d["value"]) > 0]
        delta = value(decode(data["c2_difference"]), b, r)
        utilities = {p: {a: frac_str(value(decode(v), b, r)) for a, v in agents.items()}
                     for p, agents in data["payoffs"].items() if p in ("CCC", "FFF")}
        result["cells"][cell] = {
            "c1": bool(profitable), "c2": delta > 0, "admissible": bool(profitable) and delta > 0,
            "c2_difference": frac_str(delta), "ccc_utilities": utilities["CCC"],
            "profitable_deviations": profitable,
            "ccc_deviations": [d for d in gains if d["from"] == "CCC"],
            "failed_conditions": ([] if profitable else ["C1"]) + ([] if delta > 0 else ["C2"]),
            "failure_witnesses": {
                "C1": None if profitable else gains,
                "C2": None if delta > 0 else {"CCC": utilities["CCC"], "FFF": utilities["FFF"]},
            },
        }
    return result


def verify_point(atlas: dict[str, Any], baseline: dict[str, Any], fresh: dict[str, Any],
                 benefit: Any, credit: Any) -> None:
    b, r = point(benefit, credit)
    for cell in CELLS:
        for profile in PROFILES:
            old, new = baseline[cell][profile], fresh[cell][profile]
            if old["action_hash"] != new["action_hash"] or \
                    old["summary"]["briefing"] != new["summary"]["briefing"]:
                raise ValueError(f"behavior changed: {cell}/{profile}")
            predicted = {a: frac_str(value(decode(v), b, r)) for a, v in
                         atlas["cells"][cell]["payoffs"][profile].items()}
            if predicted != new["summary"]["utility"]:
                raise ValueError(f"payoff mismatch: {cell}/{profile}: {predicted}")


def study_snapshot() -> dict[str, Any]:
    """Byte commitments for every original input and lock, not generated reports."""
    snapshot = {}
    for name in STUDIES:
        folder = REPO / "studies" / name
        paths = sorted(folder.rglob("*.json"))
        snapshot[name] = {
            "validation": validate_study(folder),
            "input_sha256": {p.relative_to(REPO).as_posix(): sha256_hex(p.read_bytes())
                             for p in paths},
        }
    return snapshot


def report(atlas: dict[str, Any]) -> str:
    lines = ["# Exact incentive-region atlas", "", "Exploratory, unfrozen; no selected default.",
             "b >= 0 is the correct-slot collective benefit; r >= 0 scales signed proposer",
             "(+3/-3) and verifier (+2/-2) credits. Wrong-slot penalty stays 12; effort costs",
             "stay 1/1/1/2/1 for inspect/share/propose/verify/challenge. Strategies are the",
             "three labelled agents' eight ordered contributor (C) / freerider (F) profiles.", "",
             "C1 requires at least one profitable C-to-F switch. C2 requires greater total",
             "utility at CCC than FFF. Admissibility requires both; equality fails.", "",
             "| Institution | C1 witness: CFF -> FFF, a1 gain | C2 / admissible half-plane |",
             "|---|---:|---|" ]
    for cell, data in atlas["cells"].items():
        x, y, z = decode(data["c2_difference"])
        lines.append(f"| {cell} | {data['c1_uniform_witness']['gain'][2]} | "
                     f"{frac_str(x)} b + {frac_str(y)} r > {frac_str(-z)} |")
    lines += ["", "C1 holds throughout the domain. C2's failed half-plane has the",
              "explicit witness CCC versus FFF. The JSON retains all 48 deviation inequalities,",
              "all 32 payoff vectors, exact queried gains and failed-condition witnesses.", "",
              "| (b,r) | Private total U(CCC) | Shared total U(CCC) | "
              "Attributable private U(a1,a2,a3) | Profitable CCC exits (private/shared) |",
              "|---|---:|---:|---|---|" ]
    for b, r in DESIGNS:
        cells = evaluate(atlas, b, r)["cells"]
        private, shared = cells["attributable/private"], cells["attributable/shared_ledger"]
        counts = [sum(Fraction(d["value"]) > 0 for d in row["ccc_deviations"])
                  for row in (private, shared)]
        lines.append(f"| ({b},{r}) | {private['c2_difference']} | {shared['c2_difference']} | "
                     f"{', '.join(private['ccc_utilities'].values())} | {counts[0]}/{counts[1]} |")
    lines += ["", "Credits are added to total utility, not funded by a fixed budget. C2 is a",
              "sum comparison, not a Pareto or equilibrium guarantee. Strong credit can remove",
              "profitable exits from CCC while the weak existential C1 remains true.", "",
              "The scripted personas do not respond to attribution or rewards. This atlas",
              "does not show behavioral improvement, human/LLM effects, statistical power,",
              "a theorem over all strategies, or a published finding. See the experiment README",
              "for the parameter definition, hand derivation and coefficient-reuse proof.", ""]
    return "\n".join(lines)


def write_json(path: Path, data: Any) -> None:
    # Validate the entire artifact's exact representation before writing.
    content_hash(data)
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def build(output: Path) -> dict[str, Any]:
    before = study_snapshot()
    if output.resolve().is_relative_to((REPO / "studies").resolve()):
        raise ValueError("experiment outputs must be outside the original studies tree")
    output.mkdir(parents=True, exist_ok=False)
    baseline = collect(output / "baseline")
    atlas = derive(baseline)
    verify_point(atlas, baseline, baseline, 12, 1)
    checks = []
    for i, (b, r) in enumerate(PROBES):
        root = output / f"probe-{i}"
        fresh = collect(root, b, r)
        verify_point(atlas, baseline, fresh, b, r)
        # One replay per point checks standard manifest/ledger interoperability.
        replay = replay_run(root / "atlas-attr-priv-FCC")
        if not replay.chains_match:
            raise ValueError(f"replay mismatch: {replay}")
        checks.append({"point": [str(b), str(r)], "profiles": 32,
                       "replay": replay.model_dump(mode="json"),
                       "seals": {c: {p: v["seal_hash"] for p, v in rows.items()}
                                 for c, rows in fresh.items()}})
    if before != study_snapshot():
        raise ValueError("original study inputs or freeze states changed during experiment")
    atlas["studies"] = before
    atlas["baseline"] = baseline
    atlas["checks"] = checks
    atlas["examples"] = [evaluate(atlas, b, r) for b, r in ((12, 1), *PROBES, *DESIGNS)]
    source_paths = sorted((REPO / "src").rglob("*.py")) + [Path(__file__).resolve()]
    atlas["source_sha256"] = {p.relative_to(REPO).as_posix(): sha256_hex(p.read_bytes())
                              for p in source_paths}
    write_json(output / "atlas.json", atlas)
    (output / "REPORT.md").write_text(report(atlas), encoding="utf-8", newline="\n")
    return atlas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="new output directory (224 small engine episodes)")
    parser.add_argument("--atlas", type=Path, help="previous atlas.json for an exact point query")
    parser.add_argument("--point", nargs=2, metavar=("B", "R"))
    args = parser.parse_args()
    if args.atlas:
        if args.out or not args.point:
            parser.error("--atlas requires --point and cannot be combined with --out")
        atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    elif args.out:
        atlas = build(args.out)
        output_file = args.out / "atlas.json"
        print(f"wrote {output_file}; sha256={sha256_hex(output_file.read_bytes())}")
    else:
        parser.error("use --out NEW_DIRECTORY, or --atlas FILE --point B R")
    if args.point:
        print(json.dumps(evaluate(atlas, *args.point), indent=2))


if __name__ == "__main__":
    main()
