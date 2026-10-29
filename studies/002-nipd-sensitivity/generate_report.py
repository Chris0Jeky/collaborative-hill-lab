"""Deterministic Study 002 report from complete, identity-bound sealed episodes."""

import argparse
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from study002_model import (
    BOOTSTRAP_SAMPLES,
    ROUNDS,
    SEED,
    STUDY_DIR,
    WINDOW,
    Condition,
    conditions,
    generate,
    generated_files,
    predict,
)

from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.hashing import canonical_json, frac_str
from collaborative_hill.engine.replay import load_run
from collaborative_hill.engine.seeds import study_seed_roots
from collaborative_hill.experiments.scenario import ResolvedScenario
from collaborative_hill.experiments.study import (
    StudySpec,
    build_policies,
    load_study,
    study_hash,
)
from collaborative_hill.reporting.analysis_stats import bootstrap_means, interval, mean


def read_episode(directory: Path, condition: Condition, spec: StudySpec,
                 resolved: dict[str, ResolvedScenario]) -> dict[str, Any]:
    """Bind ledger, manifest, seeds and policies to this declared design before scoring."""
    events, archived, manifest = load_run(directory)
    cid = condition.condition_id
    replicate = manifest.get("replicate")
    if type(replicate) is not int or not 0 <= replicate < spec.replicates:
        raise ValueError("invalid declared replicate")
    seed, policy_seed = study_seed_roots(
        spec.seed, cid, replicate, protocol=spec.seed_protocol, scenario_block=None,
    )
    expected = {
        "study_id": spec.study_id, "study_hash": study_hash(spec, resolved),
        "study_frozen": False, "condition_id": cid, "replicate": replicate,
        "run_id": f"{cid}-r{replicate:03d}", "seed_root": list(seed),
        "policy_seed_root": list(policy_seed) if policy_seed else None,
        "seed_protocol": spec.seed_protocol, "scenario_block": None,
        "checkpoint_every": spec.checkpoint_every,
        "invalid_action_policy": spec.invalid_action_policy,
        "policies": {a: p.policy_id for a, p in build_policies(resolved[cid]).items()},
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("episode identity does not match the declared study, policy or seed")
    if (archived.scenario_hash != resolved[cid].scenario_hash or manifest.get("parent_run")
            or directory.parent.name != cid or directory.name != expected["run_id"]):
        raise ValueError("episode scenario or directory identity mismatch")
    if manifest["status"] != "completed":
        raise ValueError("failed episode; incomplete design cannot be silently analyzed")
    transitions = [e.payload for e in events if e.event_type == EventType.WORLD_TRANSITIONED]
    n = condition.n_agents
    total = n * (n - 1) if condition.mode == "pairwise" else n
    if (len(transitions) != ROUNDS or [t["round"] for t in transitions] != list(range(ROUNDS))
            or any(t["mode"] != condition.mode or t["total_votes"] != total
                   for t in transitions)):
        raise ValueError("transitions do not match the declared horizon or vote denominator")
    votes = [t["cooperative_votes"] for t in transitions]
    if any(type(v) is not int or not 0 <= v <= total for v in votes):
        raise ValueError("invalid cooperation count")
    curve = [Fraction(v, total) for v in votes]
    first_zero = next((t for t, v in enumerate(votes) if v == 0), None)
    if first_zero is not None and any(votes[first_zero:]):
        raise ValueError("unexpected recovery from all-D in a zero-exploration condition")
    return {
        "condition_id": cid, "replicate": replicate, "run_id": expected["run_id"],
        "seed_root": list(seed), "final_event_hash": events[-1].event_hash,
        "code_commit": manifest.get("code_commit"),
        "worktree_dirty": manifest.get("worktree_dirty"),
        "dependency_lock_sha256": manifest.get("dependency_lock_sha256"),
        "cooperation_by_round": [frac_str(c) for c in curve],
        "mean_cooperation": frac_str(mean(curve)),
        "final_window_cooperation": frac_str(mean(curve[-WINDOW:])),
        "first_all_d_round": first_zero,
        "scores": events[-1].payload["scores"],
    }


def describe(values: list[Fraction], *, scope: str, samples: int) -> dict[str, Any]:
    if samples < 2:
        raise ValueError("bootstrap samples must be >= 2")
    if not values:
        raise ValueError("an episode sample cannot be empty")
    average = mean(values)
    degenerate = len(set(values)) == 1
    variance = (sum(((v - average) * (v - average) for v in values), Fraction())
                / (len(values) - 1)
                if len(values) > 1 else None)
    return {
        "episodes": len(values), "mean": frac_str(average),
        "sample_variance": frac_str(variance) if variance is not None else None,
        "ci95": (interval(bootstrap_means(values, seed=SEED, samples=samples, scope=scope))
                 if not degenerate else None),
        "uncertainty_note": "zero_observed_between_episode_variance" if degenerate else None,
    }


def collect_component(source: Path, artifacts: Path) -> tuple[str, list[dict[str, Any]]]:
    spec, resolved = load_study(source)
    digest = study_hash(spec, resolved)
    root = artifacts / f"DRAFT-{digest[:12]}"
    expected = {root / c.condition_id / f"{c.condition_id}-r{r:03d}"
                for c in spec.conditions for r in range(spec.replicates)}
    actual = {p for p in root.glob("*/*") if p.is_dir()}
    if actual != expected:
        raise ValueError(f"incomplete or extra episodes in {spec.study_id}: "
                         f"missing={len(expected-actual)}, extra={len(actual-expected)}")
    catalog = {c.condition_id: c for c in conditions()}
    return digest, [read_episode(path, catalog[path.parent.name], spec, resolved)
                    for path in sorted(expected)]


def _stochastic_cell(condition: Condition, rows: list[dict[str, Any]],
                     samples: int) -> dict[str, Any]:
    cid = condition.condition_id
    curve = [mean([Fraction(row["cooperation_by_round"][t]) for row in rows])
             for t in range(ROUNDS)]
    outcomes = {metric: describe([Fraction(row[metric]) for row in rows],
                                scope=f"study002/{cid}/{metric}", samples=samples)
                for metric in ("mean_cooperation", "final_window_cooperation")}
    return {
        "analytical_expectation": predict(condition),
        "measured": {**outcomes,
                     "mean_cooperation_by_round": [frac_str(c) for c in curve],
                     "absorbed_by_round_49": sum(row["first_all_d_round"] is not None
                                                 for row in rows),
                     "censored_at_50": sum(row["first_all_d_round"] is None for row in rows)},
    }


def _denominator_contrast(include: list[dict[str, Any]], exclude: list[dict[str, Any]],
                          n: int, m: int, samples: int) -> dict[str, Any]:
    a = [Fraction(row["mean_cooperation"]) for row in include]
    b = [Fraction(row["mean_cooperation"]) for row in exclude]
    variable = len(set(a)) > 1 and len(set(b)) > 1
    draws = []
    if variable:
        # Separate scopes are essential: this is independent, not paired, resampling.
        da = bootstrap_means(a, seed=SEED, samples=samples, scope=f"study002/n{n}m{m}/include")
        db = bootstrap_means(b, seed=SEED, samples=samples, scope=f"study002/n{n}m{m}/exclude")
        draws = [x - y for x, y in zip(da, db, strict=True)]
    catalog = {c.condition_id: c for c in conditions()}
    pa = predict(catalog[f"nb-n{n}-m{m}-ptft-include"])
    pb = predict(catalog[f"nb-n{n}-m{m}-ptft-exclude"])
    return {
        "contrast": "include_self minus exclude_self; episode mean cooperation",
        "analytical_expected_difference": frac_str(
            Fraction(pa["mean_cooperation"]) - Fraction(pb["mean_cooperation"])),
        "measured_difference": frac_str(mean(a) - mean(b)),
        "ci95": interval(draws) if draws else None,
        "uncertainty_note": None if variable else "zero_between_episode_variance_in_a_cell",
        "episodes_include": len(a), "episodes_exclude": len(b),
        "resampling": "independent whole episodes; exploratory percentile bootstrap",
    }


def analyze(artifacts: Path, *, study_dir: Path = STUDY_DIR,
            samples: int = BOOTSTRAP_SAMPLES) -> dict[str, Any]:
    """Read-only full-design analysis. No replacement runs or outcome exclusions."""
    if samples < 2:
        raise ValueError("bootstrap samples must be >= 2")
    generate(study_dir, check=True)
    hashes, rows = {}, []
    for component, source in (("deterministic", study_dir),
                              ("stochastic", study_dir / "stochastic")):
        hashes[component], collected = collect_component(source, artifacts)
        rows.extend(collected)
    expected_roots = {f"DRAFT-{digest[:12]}" for digest in hashes.values()}
    if {p.name for p in artifacts.glob("DRAFT-*")} != expected_roots:
        raise ValueError("extra study artifacts; choose the root containing only Study 002")
    by_condition = {c.condition_id: [row for row in rows if row["condition_id"] == c.condition_id]
                    for c in conditions()}
    deterministic, stochastic = {}, {}
    for condition in conditions():
        cid = condition.condition_id
        cell = by_condition[cid]
        if condition.deterministic:
            prediction = predict(condition)
            row = cell[0]
            deterministic[cid] = {
                "episodes": 1,
                "analytical_prediction": {k: v for k, v in prediction.items()
                                          if k != "cooperation_by_round"},
                "measured": {k: row[k] for k in ("mean_cooperation", "final_window_cooperation",
                                                "scores", "first_all_d_round")},
                "exact_trajectory_match": row["cooperation_by_round"]
                == prediction["cooperation_by_round"],
                "exact_scores_match": row["scores"] == prediction["scores"],
            }
        else:
            stochastic[cid] = _stochastic_cell(condition, cell, samples)
    contrasts = {f"n{n}-m{m}": _denominator_contrast(
        by_condition[f"nb-n{n}-m{m}-ptft-include"],
        by_condition[f"nb-n{n}-m{m}-ptft-exclude"], n, m, samples,
    ) for n, m in ((3, 2), (5, 4), (5, 3))}
    return {
        "schema_version": 1, "status": "unfrozen_exploratory_draft",
        "analysis_version": "study002@1", "study_hashes": hashes,
        "unit_of_analysis": "independently seeded whole episode",
        "seed_protocol": "legacy-independent-v1", "seed": SEED,
        "rounds": ROUNDS, "final_window": WINDOW,
        "bootstrap_samples": samples, "bootstrap_seed": SEED,
        "episode_count": len(rows),
        "code_commits": sorted({row["code_commit"] for row in rows if row["code_commit"]}),
        "any_worktree_dirty": any(row["worktree_dirty"] for row in rows),
        "dependency_lock_hashes": sorted({row["dependency_lock_sha256"] for row in rows
                                          if row["dependency_lock_sha256"]}),
        "deterministic": deterministic, "stochastic": stochastic,
        "denominator_contrasts": contrasts,
        "episodes": [{k: v for k, v in row.items()
                      if k not in {"cooperation_by_round", "scores", "code_commit",
                                   "worktree_dirty", "dependency_lock_sha256"}}
                     for row in rows],
    }


def _decimal(value: str) -> str:
    # Display only; the authoritative JSON remains exact and contains no floats.
    return f"{float(Fraction(value)):.6g}"


def _ci(value: list[str] | None) -> str:
    return f"[{_decimal(value[0])}, {_decimal(value[1])}]" if value else "withheld (zero variance)"


def render_markdown(report: dict[str, Any]) -> str:
    deterministic = report["deterministic"]
    matched = sum(row["exact_trajectory_match"] and row["exact_scores_match"]
                  for row in deterministic.values())
    lines = [
        "# Study 002 — measured draft results", "",
        "**Unfrozen exploratory simulation; no confirmatory or human-behavior claim.**", "",
        f"{report['episode_count']} sealed episodes: 29 deterministic controls (one each) and "
        "six stochastic cells (32 independent episodes each). "
        "Fifty rounds, final ten-round window.",
        "", "## Provenance", "",
        *[f"- {component} study hash: `{digest}`"
          for component, digest in report["study_hashes"].items()],
        f"- Run code commits: {', '.join(report['code_commits'])}; "
        f"any dirty run worktree: {report['any_worktree_dirty']}.",
        f"- Independent seed protocol: `{report['seed_protocol']}`; seed {report['seed']}.",
        "- The accompanying JSON retains exact fractions, every terminal event hash, "
        "per-episode outcomes, analytical curves and measured mean curves.", "",
        "## Deterministic predictions versus measured results", "",
        f"**{matched}/{len(deterministic)} complete cooperation trajectories and terminal "
        "score vectors match their pre-execution analytical predictions exactly.** "
        "One run per cell supplies an algorithm check, not inferential replication.", "",
        "| Condition | Expected mean | Measured mean | Expected final | Measured final | "
        "Path / scores exact |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for cid, row in deterministic.items():
        p, measured = row["analytical_prediction"], row["measured"]
        lines.append(f"| {cid} | {p['mean_cooperation']} | {measured['mean_cooperation']} | "
                     f"{p['final_window_cooperation']} | {measured['final_window_cooperation']} | "
                     f"{row['exact_trajectory_match']} / {row['exact_scores_match']} |")
    lines += [
        "", "## pTFT: analytical expectations and independent-episode measurements", "",
        "Expected values are closed-form mathematical predictions. Measured values are sample "
        "means from sealed runs. Equality is not required; no outcomes were tuned toward the "
        "predictions. Displayed decimals are approximations of the exact JSON fractions.", "",
        "| Condition | n | Expected mean | Measured mean | 95% bootstrap interval | "
        "Observed sample variance | All-D by t=49 |",
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for cid, row in report["stochastic"].items():
        measured, expected = row["measured"], row["analytical_expectation"]
        average = measured["mean_cooperation"]
        lines.append(f"| {cid} | {average['episodes']} | "
                     f"{_decimal(expected['mean_cooperation'])} | "
                     f"{_decimal(average['mean'])} | {_ci(average['ci95'])} | "
                     f"{_decimal(average['sample_variance'])} | "
                     f"{measured['absorbed_by_round_49']}/{average['episodes']} |")
    lines += [
        "", "| Condition | Expected final-window mean | Measured final-window mean | "
        "95% bootstrap interval |",
        "|---|---:|---:|---|",
    ]
    for cid, row in report["stochastic"].items():
        measured = row["measured"]["final_window_cooperation"]
        lines.append(f"| {cid} | "
                     f"{_decimal(row['analytical_expectation']['final_window_cooperation'])} | "
                     f"{_decimal(measured['mean'])} | {_ci(measured['ci95'])} |")
    lines += [
        "", "## Denominator sensitivity contrasts", "",
        "Each contrast is include-self minus exclude-self in episode mean cooperation. "
        "The cells are independently seeded; resampling is independent across them.", "",
        "| Population | Analytical expected difference | Measured difference | "
        "95% bootstrap interval |",
        "|---|---:|---:|---|",
    ]
    for population, row in report["denominator_contrasts"].items():
        lines.append(f"| {population} | {_decimal(row['analytical_expected_difference'])} | "
                     f"{_decimal(row['measured_difference'])} | {_ci(row['ci95'])} |")
    lines += [
        "", "## Interpretation and limits", "",
        "The quorum model predicts an inclusive boundary at (m−1)/(N−1): 1/2 for "
        "N=3,m=2, 3/4 for N=5,m=4, and 1/2 again for N=5,m=3. The table reports the "
        "actual agreement checks; increasing N while retaining one AllD also changes "
        "the defector fraction. The two-AllD control makes this composition dependence explicit.",
        "",
        "For pTFT, the exact decay factor is m/N with self included and (m−1)/(N−1) "
        "with self excluded. Include-self has the larger expected finite-horizon cooperation. "
        "A positive expected final-window rate can coexist with an observed all-zero final "
        "window in 32 episodes. Observed absorption is finite-horizon evidence; the "
        "almost-sure eventual-absorption claim comes from the finite-chain argument in README.md.",
        "",
        "The analytical fractions describe the rational Bernoulli model. The unchanged pTFT "
        "policy compares finite-precision PRNG draws with binary floating-point ratios; it "
        "is not an exact rational Bernoulli sampler. Scenario hashes and replay remain exact.",
        "",
        f"Intervals use {report['bootstrap_samples']} whole-episode percentile bootstrap draws "
        f"with seed {report['bootstrap_seed']} and type-7 endpoints. They describe exploratory "
        "Monte Carlo uncertainty, with no p-values or confirmatory significance labels. "
        "Zero observed between-episode variance suppresses an interval; it does not make "
        "the population outcome certain. Turns, votes and agents are not extra replicates.",
        "",
        "Targeted and linked pairwise TFT, quorum TFT and pTFT differ in policy and "
        "observations. This draft therefore narrows a strategy/structure claim; it does not "
        "identify a structure-only causal effect. Raw pairwise and neighbourhood payoff "
        "scales differ. No new claim about people, LLM behavior, or a confirmed population-size "
        "effect follows. Studies 000 and 001 and all mechanism/policy semantics remain unchanged.",
        "",
    ]
    return "\n".join(lines)


def validate_output(output: Path, *, study_dir: Path, artifacts: Path) -> None:
    """A report cannot replace its predictions, generated inputs or sealed sources."""
    targets = [output.with_suffix(suffix).resolve() for suffix in (".json", ".md")]
    protected = {(study_dir / relative).resolve() for relative in generated_files()}
    protected.update((study_dir / relative).resolve()
                     for relative in ("README.md", "study.lock.json", "stochastic/study.lock.json"))
    runs = [directory.resolve() for directory in artifacts.glob("DRAFT-*/*/*")
            if directory.is_dir()]
    if any(target in protected or any(target.is_relative_to(run) for run in runs)
           for target in targets):
        raise ValueError("report output must preserve study inputs and sealed run directories")


def write_outputs(output: Path, *, json_text: str, markdown: str) -> None:
    """Check both targets before creating either; identical reports are a no-op."""
    targets = {output.with_suffix(".json"): json_text.encode("utf-8"),
               output.with_suffix(".md"): markdown.encode("utf-8")}
    for path, data in targets.items():
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"output differs from existing {path.name}; choose a fresh prefix")
    output.parent.mkdir(parents=True, exist_ok=True)
    for path, data in targets.items():
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--study-dir", type=Path, default=STUDY_DIR)
    parser.add_argument("--output", type=Path, required=True, help="output prefix (.json and .md)")
    args = parser.parse_args()
    try:
        validate_output(args.output, study_dir=args.study_dir, artifacts=args.artifacts)
        report = analyze(args.artifacts, study_dir=args.study_dir)
        canonical_json(report)  # Assert the authoritative record contains no floats.
        write_outputs(args.output, json_text=json.dumps(report, sort_keys=True, indent=2) + "\n",
                      markdown=render_markdown(report))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Study 002 report: {report['episode_count']} verified sealed episodes; "
          "analytical expectations separate from measured outcomes")


if __name__ == "__main__":
    main()
