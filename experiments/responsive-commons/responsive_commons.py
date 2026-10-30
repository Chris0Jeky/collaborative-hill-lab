"""Execute and audit the predeclared, deterministic responsive EC enumeration."""

import argparse
import itertools
import json
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.agents.replay import ReplayPolicy, proposals_from_events  # noqa: E402
from collaborative_hill.engine.events import Event, EventType  # noqa: E402
from collaborative_hill.engine.hashing import content_hash, frac_str, sha256_hex  # noqa: E402
from collaborative_hill.engine.replay import load_run, replay_run  # noqa: E402
from collaborative_hill.engine.runner import RunConfig, run_episode  # noqa: E402
from collaborative_hill.engine.seeds import PAIRED_SEED_PROTOCOL, study_seed_roots  # noqa: E402
from collaborative_hill.engine.store import RunPaths  # noqa: E402
from collaborative_hill.experiments.manifests import (  # noqa: E402
    RunManifest,
    environment_provenance,
    git_provenance,
    lock_hash,
    write_manifest,
)
from collaborative_hill.experiments.scenario import (  # noqa: E402
    NarrativeSkin,
    ResolvedScenario,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import (  # noqa: E402
    StudySpec,
    build_policies,
    load_study,
    run_study,
    study_hash,
)

AGENTS = ("a1", "a2", "a3")
PROFILES = tuple("".join(p) for p in itertools.product("CF", repeat=3))
RULES = {
    "control": ("0", 5),
    "half-5": ("1/2", 5),
    "all-5": ("1", 5),
    "half-9": ("1/2", 9),
    "all-9": ("1", 9),
}
CORPORA = ("accurate", "misleading")
TOPOLOGIES = ("private", "shared_ledger")
ACCOUNTABILITIES = ("aggregate", "attributable")
ROUNDS = 12
SEED = 20261029
STUDY_ID = "responsive-commons-v1"
HERE = Path(__file__).resolve().parent
SKIN = NarrativeSkin(skin_id="responsive-commons-plain", title="Synthetic evidence review")


def cells() -> list[dict[str, str]]:
    return [dict(zip(("corpus", "topology", "accountability", "rule", "profile"),
                     values, strict=True))
            for values in itertools.product(CORPORA, TOPOLOGIES, ACCOUNTABILITIES,
                                            RULES, PROFILES)]


def cell_id(cell: dict[str, str]) -> str:
    return "-".join(cell[key] for key in
                    ("corpus", "topology", "accountability", "rule", "profile"))


def scenario(cell: dict[str, str]) -> ScenarioSpec:
    """No outcome-dependent inputs: this is the full DESIGN.md Cartesian product."""
    if cell not in cells():
        raise ValueError("cell is outside the declared design")
    threshold, warmup = RULES[cell["rule"]]
    accurate = cell["corpus"] == "accurate"
    evidence = [{
        "evidence_id": f"e{i}", "source_id": f"source{i}", "slot_id": f"s{i}",
        "proposition_id": f"s{i}-{'true' if accurate else 'false'}",
        "stance": "supports", "freshness": "fresh", "truth_aligned": accurate,
        "initial_holders": [agent],
    } for i, agent in enumerate(AGENTS, 1)]
    return ScenarioSpec.model_validate({
        "scenario_id": cell_id(cell),
        "world": {
            "kind": "evidence_commons",
            "slots": {f"s{i}": [f"s{i}-true", f"s{i}-false"] for i in range(1, 4)},
            "true_propositions": {f"s{i}": f"s{i}-true" for i in range(1, 4)},
            "params": {
                "rounds": ROUNDS, "inspect_budget": 3, "verify_budget": 3,
                "cost_inspect": 1, "cost_share": 1, "cost_propose": 1,
                "cost_verify": 2, "cost_challenge": 1,
                "benefit_correct_slot": 12, "penalty_wrong_slot": 12,
                "credit_propose_accepted_correct": 3, "credit_propose_accepted_wrong": -3,
                "credit_verify_accepted_correct": 2, "credit_verify_accepted_wrong": -2,
            },
        },
        "information": {"evidence": evidence},
        "interaction": {"structure": "commons"},
        "institution": {"accountability": cell["accountability"],
                        "evidence_topology": cell["topology"]},
        "cognition": {"agents": [{
            "agent_id": agent,
            "policy": {"name": "ec_conditional_contributor", "params": {
                "peer_threshold": threshold, "warmup_rounds": warmup,
                "share_evidence": True,
            }} if strategy == "C" else {"name": "ec_freerider"},
        } for agent, strategy in zip(AGENTS, cell["profile"], strict=True)]},
    })


def design() -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    conditions = [{
        "condition_id": cell_id(cell), "scenario": f"scenarios/{cell_id(cell)}.json",
        "skin": "skin.json",
        "scenario_block": "-".join(cell[key] for key in ("corpus", "rule", "profile")),
    } for cell in cells()]
    spec = StudySpec.model_validate({
        "study_id": STUDY_ID, "seed": SEED, "seed_protocol": PAIRED_SEED_PROTOCOL,
        "replicates": 1, "checkpoint_every": 0, "invalid_action_policy": "fail",
        "conditions": conditions,
    })
    return spec, {cell_id(cell): compile_scenario(scenario(cell), SKIN) for cell in cells()}


def write_inputs(destination: Path) -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    spec, resolved = design()
    destination.mkdir()
    (destination / "scenarios").mkdir()
    (destination / "study.json").write_text(spec.model_dump_json(indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
    (destination / "skin.json").write_text(SKIN.model_dump_json(indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    for cid, item in resolved.items():
        (destination / "scenarios" / f"{cid}.json").write_text(
            item.spec.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    return spec, resolved


def run_path(root: Path, study_digest: str, cid: str) -> Path:
    return root / "runs" / ("DRAFT-" + study_digest[:12]) / cid / (cid + "-r000")


def action_schedule(events: list[Event]) -> list[dict[str, Any]]:
    return [{"round": e.logical_time, "agent": e.payload["agent_id"],
             "action": e.payload["action"]}
            for e in events if e.event_type == EventType.ACTION_ACCEPTED]


def episode_record(path: Path, expected: ResolvedScenario, *,
                   expected_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    events, resolved, manifest = load_run(path)
    if resolved.scenario_hash != expected.scenario_hash:
        raise ValueError(f"unexpected scenario identity: {path}")
    if expected_manifest is not None:
        for key, value in expected_manifest.items():
            if manifest.get(key) != value:
                raise ValueError(f"unexpected manifest {key}: {path}")
    if events[-1].event_type != EventType.RUN_COMPLETED or manifest["status"] != "completed":
        raise ValueError(f"experiment requires a completed episode: {path}")
    actions = action_schedule(events)
    if len(actions) != ROUNDS * len(AGENTS):
        raise ValueError(f"incomplete action schedule: {path}")
    if any(e.event_type == EventType.ACTION_REJECTED for e in events):
        raise ValueError(f"rejected action in declared deterministic experiment: {path}")
    summary = events[-1].payload
    counts = Counter(row["action"]["type"] for row in actions)
    contributions = sum(v for k, v in counts.items() if k not in {"withhold", "abstain"})
    return {
        "scenario_hash": resolved.scenario_hash, "mechanism_hash": resolved.mechanism_hash,
        "terminal_hash": events[-1].event_hash, "event_count": len(events),
        "action_hash": content_hash(actions), "action_counts": dict(sorted(counts.items())),
        "contribution_fraction": frac_str(Fraction(contributions, len(actions))),
        "correct_slots": sum(x.get("correct") is True for x in summary["briefing"]),
        "wrong_slots": sum(x.get("correct") is False for x in summary["briefing"]),
        "collective_quality": summary["collective_quality"],
        "briefing": summary["briefing"], "effort": summary["effort"],
        "utility": summary["utility"], "individual_credit": summary["individual_credit"],
        "total_utility": frac_str(sum(map(Fraction, summary["utility"].values()), Fraction())),
    }


def fixed_action_run(source: Path, target: ResolvedScenario, destination: Path) -> None:
    events, _, original_manifest = load_run(source)
    proposals = proposals_from_events(events)
    policies = {agent: ReplayPolicy(agent, "recorded-actions@1", proposals[agent])
                for agent in AGENTS}
    run_id = target.spec.scenario_id + "-fixed-actions"
    config = RunConfig(study_id=STUDY_ID + "-c3", run_id=run_id,
                       seed_root=(SEED, "fixed-actions", target.spec.scenario_id))
    with RunPaths(destination).reserve() as paths:
        (destination / "scenario.resolved.json").write_text(
            target.model_dump_json(indent=2), encoding="utf-8", newline="\n")
        result = run_episode(mechanism=target.build_mechanism(), policies=policies,
                             config=config, paths=paths,
                             start_meta={"scenario_hash": target.scenario_hash,
                                         "mechanism_hash": target.mechanism_hash,
                                         "narrative_hash": target.narrative_hash})
        env = environment_provenance()
        manifest = RunManifest(
            study_id=config.study_id, condition_id=target.spec.scenario_id,
            run_id=run_id, replicate=0, scenario_hash=target.scenario_hash,
            mechanism_hash=target.mechanism_hash, narrative_hash=target.narrative_hash,
            evidence_corpus_hash=target.evidence_corpus_hash,
            institution=target.spec.institution.model_dump(mode="json"),
            code_commit=original_manifest["code_commit"],
            worktree_dirty=original_manifest["worktree_dirty"],
            python_version=env["python_version"], platform=env["platform"],
            dependency_lock_sha256=original_manifest["dependency_lock_sha256"],
            policies={a: p.policy_id for a, p in policies.items()},
            seed_root=list(config.seed_root), status=result.status,
            failure_reason=result.failure_reason, event_count=result.event_count,
            final_event_hash=result.final_event_hash,
        )
        write_manifest(manifest, paths.manifest)


def certificate(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Exact C1/C2 diagnostics for only the declared active/F strategy pair."""
    if set(records) != set(PROFILES):
        raise ValueError("finite-strategy certificate requires all eight profiles")
    deviations = []
    for profile in PROFILES:
        for index, agent in enumerate(AGENTS):
            if profile[index] != "C":
                continue
            target = profile[:index] + "F" + profile[index + 1:]
            gain = Fraction(records[target]["utility"][agent]) - Fraction(
                records[profile]["utility"][agent])
            deviations.append({"from": profile, "to": target, "agent": agent,
                               "gain": frac_str(gain)})
    collective_delta = Fraction(records["CCC"]["total_utility"]) - Fraction(
        records["FFF"]["total_utility"])
    c1 = any(Fraction(d["gain"]) > 0 for d in deviations)
    c2 = collective_delta > 0
    return {"c1": c1, "c2": c2, "finite_strategy_dilemma": c1 and c2,
            "ccc_minus_fff_total_utility": frac_str(collective_delta),
            "active_to_freerider_deviations": deviations}


def task_integrity(source: dict[str, Any], replayed: dict[str, Any]) -> dict[str, bool]:
    fields = ("action_hash", "briefing", "effort", "collective_quality", "total_utility")
    return {field: source[field] == replayed[field] for field in fields}


def collect(root: Path) -> dict[str, Any]:
    expected_spec, expected = design()
    actual_spec, actual = load_study(root / "inputs")
    digest = study_hash(expected_spec, expected)
    if actual_spec != expected_spec or study_hash(actual_spec, actual) != digest:
        raise ValueError("stored inputs differ from the predeclared design")
    records = {}
    for cell in cells():
        cid = cell_id(cell)
        block = "-".join(cell[key] for key in ("corpus", "rule", "profile"))
        seed, policy_seed = study_seed_roots(
            SEED, cid, 0, protocol=PAIRED_SEED_PROTOCOL, scenario_block=block)
        records[cid] = {"cell": cell, **episode_record(
            run_path(root, digest, cid), expected[cid], expected_manifest={
                "study_id": STUDY_ID, "study_hash": digest, "study_frozen": False,
                "condition_id": cid, "run_id": cid + "-r000", "replicate": 0,
                "seed_protocol": PAIRED_SEED_PROTOCOL, "scenario_block": block,
                "seed_root": list(seed),
                "policy_seed_root": list(policy_seed) if policy_seed else None,
                "policies": {a: p.policy_id for a, p in build_policies(expected[cid]).items()},
                "invalid_action_policy": "fail", "checkpoint_every": 0, "parent_run": None,
            })}
    contrasts = []
    integrity = []
    for cell in cells():
        if cell["accountability"] != "aggregate":
            continue
        target_cell = {**cell, "accountability": "attributable"}
        source, target = records[cell_id(cell)], records[cell_id(target_cell)]
        contrast = {k: cell[k] for k in ("corpus", "topology", "rule", "profile")}
        contrasts.append({
            **contrast, "actions_equal": source["action_hash"] == target["action_hash"],
            "quality_delta": target["collective_quality"] - source["collective_quality"],
            "contribution_delta": frac_str(Fraction(target["contribution_fraction"])
                                            - Fraction(source["contribution_fraction"])),
            "total_utility_delta": frac_str(Fraction(target["total_utility"])
                                             - Fraction(source["total_utility"])),
        })
        fixed = episode_record(root / "fixed-actions" / cell_id(target_cell),
                               expected[cell_id(target_cell)], expected_manifest={
                                   "study_id": STUDY_ID + "-c3", "study_hash": None,
                                   "study_frozen": False, "replicate": 0,
                                   "condition_id": cell_id(target_cell),
                                   "run_id": cell_id(target_cell) + "-fixed-actions",
                                   "policies": dict.fromkeys(AGENTS, "recorded-actions@1"),
                                   "seed_protocol": "legacy-independent-v1",
                                   "seed_root": [SEED, "fixed-actions", cell_id(target_cell)],
                                   "policy_seed_root": None, "scenario_block": None,
                                   "invalid_action_policy": "fail", "checkpoint_every": 0,
                                   "parent_run": None,
                               })
        checks = task_integrity(source, fixed)
        if not all(checks.values()):
            raise ValueError(f"same-action accountability integrity failed: {contrast}: {checks}")
        integrity.append({**contrast, "source_terminal_hash": source["terminal_hash"],
                          "replay_terminal_hash": fixed["terminal_hash"], "checks": checks})
    certificates = []
    for corpus, topology, accountability, rule in itertools.product(
            CORPORA, TOPOLOGIES, ACCOUNTABILITIES, RULES):
        group = {"corpus": corpus, "topology": topology,
                 "accountability": accountability, "rule": rule}
        profiles = {p: records[cell_id({**group, "profile": p})] for p in PROFILES}
        certificates.append({**group, **certificate(profiles)})
    return {
        "schema": "responsive-commons-results-v1", "status": "exploratory-unfrozen",
        "study_hash": digest, "seed_protocol": PAIRED_SEED_PROTOCOL,
        "behavioral_episodes": len(records), "fixed_action_episodes": len(integrity),
        "rounds_per_episode": ROUNDS,
        "design_sha256": sha256_hex((HERE / "DESIGN.md").read_bytes()),
        "contrast_direction": "attributable minus aggregate",
        "inference": "deterministic enumeration; no sample-based uncertainty intervals",
        "episodes": records, "accountability_contrasts": contrasts,
        "finite_strategy_certificates": certificates,
        "same_action_integrity": integrity,
    }


def render_report(result: dict[str, Any]) -> str:
    contrasts = result["accountability_contrasts"]
    positives = sum(c["quality_delta"] > 0 for c in contrasts)
    negatives = sum(c["quality_delta"] < 0 for c in contrasts)
    zeros = sum(c["quality_delta"] == 0 for c in contrasts)
    changed = sum(not c["actions_equal"] for c in contrasts)
    certificates = result["finite_strategy_certificates"]
    certified = sum(c["finite_strategy_dilemma"] for c in certificates)
    lines = [
        "# Responsive Evidence Commons — deterministic sensitivity results", "",
        "This is an unfrozen scripted-policy experiment, not a live-model or human result.",
        "The design and conditional predictions precede execution in [DESIGN.md](DESIGN.md).",
        "The checked-in [RESULTS.json](RESULTS.json) retains every profile, seal commitment,",
        "contrast and unilateral-deviation value; no cell is selected by its outcome.", "",
        "The execution's file commitments and local source identity are recorded separately",
        "in [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json). Hash-chain validation checks",
        "retained ledger consistency; the source record documents the execution version.", "",
        f"**{result['behavioral_episodes']} behavioral episodes and "
        f"{result['fixed_action_episodes']} controlled action replays**, each {ROUNDS} rounds.",
        f"Across {len(contrasts)} attributable-minus-aggregate contrasts, quality increases in "
        f"{positives}, decreases in {negatives}, and is unchanged in {zeros}.",
        f"Actions differ in {changed} contrasts. These counts describe this finite grid;",
        "they are not population frequency estimates or statistical significance tests.", "",
        "## All-active profile: the full policy sensitivity", "",
        "`C` means the active rule of that cell, not necessarily unconditional cooperation.",
        "Quality is the engine's signed accepted-slot value. Contribution is the fraction",
        "of all agent-round actions spent on inspection, sharing, proposing or verification.",
        "All differences below are attributable minus aggregate.", "",
        "| Corpus | Topology | Rule | Quality delta | Contribution delta | Total utility delta |",
        "|---|---|---|---:|---:|---:|",
    ]
    for c in contrasts:
        if c["profile"] == "CCC":
            lines.append(f"| {c['corpus']} | {c['topology']} | {c['rule']} | "
                         f"{c['quality_delta']} | {c['contribution_delta']} | "
                         f"{c['total_utility_delta']} |")
    lines += ["", "## Incentives and task integrity are separate findings", "",
              f"{certified} of {len(certificates)} finite-strategy cells satisfy both C1 "
              "(some strictly profitable active-to-free-rider deviation) and C2 "
              "(CCC total utility strictly exceeds FFF). This does not assert dominance, "
              "an equilibrium, or a social dilemma over untested strategies.", "",
              "| Corpus | Topology | Accountability | Rule | C1 | C2 | CCC−FFF total utility |",
              "|---|---|---|---|---|---|---:|"]
    for c in certificates:
        lines.append(f"| {c['corpus']} | {c['topology']} | {c['accountability']} | "
                     f"{c['rule']} | {c['c1']} | {c['c2']} | "
                     f"{c['ccc_minus_fff_total_utility']} |")
    lines += ["", "Every controlled same-action replay preserves the typed action schedule,",
              "briefing, effort, collective quality and total utility. Individual credit",
              "can redistribute. Adaptive policies may choose different actions when their",
              "observations change; that behavioral difference is compatible with task integrity.",
              "", "## Interpretation and limits", "",
              "The rule responds to visible contribution, not to true evidence quality or",
              "utility weights. Fresh false support can pass the provenance check. Attribution",
              "can therefore facilitate harmful as well as useful activity. Anonymous",
              "observations still certify distinct actors within a single verified claim;",
              "a warmup can remove the identity bottleneck. This finite, synthetic design",
              "does not select final Study 001 weights or establish that any institution",
              "will improve cooperation in a broader population.", "",
              "The paired seed protocol is explicitly declared, but these policies are",
              "deterministic. One execution per design point supplies exact outcomes of",
              "those algorithms, not independent samples for inferential confidence intervals.",
              "", "## Reproduce", "", "```bash",
              "python experiments/responsive-commons/responsive_commons.py "
              "--out artifacts/responsive-new",
              "python experiments/responsive-commons/responsive_commons.py --check", "```", "",
              "The first command requires a fresh output directory and retains inputs,",
              "sealed ledgers, manifests and the readout there. The second regenerates",
              "all 480 episodes in a temporary directory and checks byte-identical JSON",
              "and Markdown against the committed readout. It makes no provider calls.", "",
              f"Study hash: `{result['study_hash']}`. The study remains unfrozen.", ""]
    return "\n".join(lines)


def source_provenance() -> dict[str, Any]:
    commit, dirty = git_provenance(REPO)
    paths = sorted([*REPO.glob("src/**/*.py"), Path(__file__).resolve(), HERE / "DESIGN.md",
                    REPO / "requirements-lock.txt", REPO / "pyproject.toml"])
    return {"schema": "responsive-commons-execution-source-v1", "local_commit": commit,
            "worktree_dirty": dirty, "dependency_lock_sha256": lock_hash(REPO),
            "files_sha256": {p.relative_to(REPO).as_posix(): sha256_hex(p.read_bytes())
                             for p in paths}}


def execute(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    provenance = source_provenance()
    spec, resolved = write_inputs(root / "inputs")
    digest = study_hash(spec, resolved)
    results = run_study(root / "inputs", root / "runs")
    if any(result.status != "completed" for result in results):
        raise ValueError("behavioral execution failed; sealed failures retained in output")
    for cell in cells():
        if cell["accountability"] == "aggregate":
            target = {**cell, "accountability": "attributable"}
            fixed_action_run(run_path(root, digest, cell_id(cell)), resolved[cell_id(target)],
                             root / "fixed-actions" / cell_id(target))
    result = collect(root)
    # Separate replay check for both adaptive and fixed-action record formats.
    for path in (run_path(root, digest, cell_id(cells()[0])),
                 root / "fixed-actions" / cell_id({**cells()[0],
                                                   "accountability": "attributable"})):
        if not replay_run(path).chains_match:
            raise ValueError(f"recorded-ledger replay mismatch: {path}")
    (root / "RESULTS.json").write_text(encode(result), encoding="utf-8", newline="\n")
    (root / "RESULTS.md").write_text(render_report(result), encoding="utf-8", newline="\n")
    (root / "SOURCE_PROVENANCE.json").write_text(encode(provenance), encoding="utf-8", newline="\n")
    return result


def encode(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", type=Path)
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="chl-responsive-") as temp:
            destination = Path(temp) / "experiment"
            execute(destination)
            for filename in ("RESULTS.json", "RESULTS.md"):
                if (destination / filename).read_bytes() != (HERE / filename).read_bytes():
                    raise SystemExit(f"{filename} differs from the committed readout")
        print("Verified 320 behavioral episodes, 160 same-action controls and exact readout.")
    else:
        execute(args.out)
        print(f"Wrote sealed experiment and readout to {args.out}")


if __name__ == "__main__":
    main()
