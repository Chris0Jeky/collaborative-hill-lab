"""Execute/audit the predeclared 2^4 skeptical-rule component factorial."""

import argparse
import itertools
import json
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(REPO / "src"), str(HERE), str(HERE.parent / "quality-safeguards"),
               str(HERE.parent / "responsive-commons")]

import ablation_readout as readout  # noqa: E402
import quality_safeguards as qs  # type: ignore[import-not-found]  # noqa: E402
from ablation_readout import (  # noqa: E402
    CONTEXTS,
    FACTOR_KEYS,
    TRUTHS,
    VARIANTS,
    cell_id,
    cells,
    factorial_contrasts,
    render_report,
)

from collaborative_hill.agents.replay import ReplayPolicy, proposals_from_events  # noqa: E402
from collaborative_hill.agents.scripted.ec_policies import build_ec_policy  # noqa: E402
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
ROUNDS = 14
SEED = 20261102
STUDY_ID = "ec-rule-ablation-v1"
SKIN = NarrativeSkin(skin_id="ec-ablation-plain", title="Synthetic evidence review")
COMMON = {"min_sources": 2, "peer_threshold": "1", "warmup_rounds": 9, "share_evidence": True}
PROFILES = {context: ("UUA" if context == "defender-private" else
                      "UFA" if context == "unread-private" else "AAA") for context in CONTEXTS}


def scenario(item: dict[str, str], *, accountability: str = "attributable") -> ScenarioSpec:
    if item not in cells() or accountability not in ("aggregate", "attributable"):
        raise ValueError("cell is outside the declared ablation design")
    context = item["context"]
    structure = ("conflicted" if context.startswith("conflicted") or context == "defender-private"
                 else "echo" if context == "echo-private" else "corroborated")
    topology = "shared_ledger" if context == "conflicted-ledger" else "private"
    # The earlier generator supplies the exact original world/evidence/cost inputs.
    raw = qs.scenario(qs.cell(item["truth"], structure, topology, accountability,
                              "skeptical", "CCC")).model_dump(mode="json")
    raw["scenario_id"] = cell_id(item)
    params = {**COMMON, **{key: bit == "1" for key, bit in
                          zip(FACTOR_KEYS, item["variant"], strict=True)}}
    active = {"name": "ec_ablation_contributor", "params": params}
    assignments = {"A": active, "U": {"name": "ec_contributor", "params": {"share_evidence": True}},
                   "F": {"name": "ec_freerider"}}
    raw["cognition"]["agents"] = [
        {"agent_id": agent, "policy": assignments[strategy]}
        for agent, strategy in zip(AGENTS, PROFILES[context], strict=True)]
    if context == "unread-private":
        raw["world"]["slots"].pop("s2")
        raw["world"]["true_propositions"].pop("s2")
        raw["world"]["params"]["inspect_budget"] = 2
        evidence = raw["information"]["evidence"][:3]
        for entry in evidence:
            entry["initial_holders"] = ["a1" if entry["evidence_id"] == "e1c" else "a3"]
        raw["information"]["evidence"] = evidence
    return ScenarioSpec.model_validate(raw)


def design() -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    study = StudySpec.model_validate({
        "study_id": STUDY_ID, "seed": SEED, "seed_protocol": PAIRED_SEED_PROTOCOL,
        "replicates": 1, "checkpoint_every": 0, "invalid_action_policy": "fail",
        "conditions": [{"condition_id": cell_id(item),
                        "scenario": f"scenarios/{cell_id(item)}.json", "skin": "skin.json",
                        "scenario_block": item["context"]} for item in cells()],
    })
    return study, {cell_id(item): compile_scenario(scenario(item), SKIN) for item in cells()}


def write_inputs(destination: Path) -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    study, resolved = design()
    (destination / "scenarios").mkdir(parents=True)
    (destination / "study.json").write_text(study.model_dump_json(indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
    (destination / "skin.json").write_text(SKIN.model_dump_json(indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    for cid, value in resolved.items():
        (destination / "scenarios" / f"{cid}.json").write_text(
            value.spec.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    return study, resolved


def run_path(root: Path, digest: str, cid: str) -> Path:
    return root / "runs" / ("DRAFT-" + digest[:12]) / cid / (cid + "-r000")


def behavior_manifest(study: StudySpec, digest: str, item: dict[str, str]) -> dict[str, Any]:
    cid = cell_id(item)
    seed, policy_seed = study_seed_roots(SEED, cid, 0, protocol=PAIRED_SEED_PROTOCOL,
                                         scenario_block=item["context"])
    assert policy_seed is not None  # The paired protocol always supplies this root.
    policies = build_policies(compile_scenario(scenario(item), SKIN))
    return {"study_id": study.study_id, "study_hash": digest, "study_frozen": False,
            "condition_id": cid, "run_id": cid + "-r000", "replicate": 0,
            "seed_protocol": PAIRED_SEED_PROTOCOL, "seed_root": list(seed),
            "policy_seed_root": list(policy_seed), "scenario_block": item["context"],
            "checkpoint_every": 0, "invalid_action_policy": "fail",
            "policies": {agent: policy.policy_id for agent, policy in policies.items()}}


def fixed_manifest(item: dict[str, str], target: ResolvedScenario) -> dict[str, Any]:
    cid = cell_id(item)
    return {"study_id": STUDY_ID + "-same-action", "condition_id": cid,
            "run_id": cid + "-fixed", "replicate": 0, "study_hash": None, "study_frozen": False,
            "scenario_hash": target.scenario_hash, "mechanism_hash": target.mechanism_hash,
            "narrative_hash": target.narrative_hash,
            "evidence_corpus_hash": target.evidence_corpus_hash,
            "institution": target.spec.institution.model_dump(mode="json"),
            "seed_root": [SEED, "fixed-actions", cid], "seed_protocol": "legacy-independent-v1",
            "policy_seed_root": None, "scenario_block": None, "checkpoint_every": 0,
            "invalid_action_policy": "fail",
            "policies": dict.fromkeys(AGENTS, "recorded-actions@1")}


def fixed_action_run(source: Path, target: ResolvedScenario, destination: Path) -> None:
    events, _, original = load_run(source)
    proposals = proposals_from_events(events)
    policies = {a: ReplayPolicy(a, "recorded-actions@1", proposals[a]) for a in AGENTS}
    config = RunConfig(study_id=STUDY_ID + "-same-action",
                       run_id=target.spec.scenario_id + "-fixed",
                       seed_root=(SEED, "fixed-actions", target.spec.scenario_id))
    with RunPaths(destination).reserve() as paths:
        (destination / "scenario.resolved.json").write_text(
            target.model_dump_json(indent=2), encoding="utf-8", newline="\n")
        result = run_episode(mechanism=target.build_mechanism(), policies=policies,
                             config=config, paths=paths, start_meta={
                                 "scenario_hash": target.scenario_hash,
                                 "mechanism_hash": target.mechanism_hash,
                                 "narrative_hash": target.narrative_hash})
        environment = environment_provenance()
        write_manifest(RunManifest(
            study_id=config.study_id, condition_id=target.spec.scenario_id,
            run_id=config.run_id, replicate=0, scenario_hash=target.scenario_hash,
            mechanism_hash=target.mechanism_hash, narrative_hash=target.narrative_hash,
            evidence_corpus_hash=target.evidence_corpus_hash,
            institution=target.spec.institution.model_dump(mode="json"),
            policies={a: p.policy_id for a, p in policies.items()},
            seed_root=list(config.seed_root),
            code_commit=original["code_commit"], worktree_dirty=original["worktree_dirty"],
            dependency_lock_sha256=original["dependency_lock_sha256"],
            python_version=environment["python_version"], platform=environment["platform"],
            status=result.status, failure_reason=result.failure_reason,
            event_count=result.event_count, final_event_hash=result.final_event_hash),
            paths.manifest)


def endpoint_bridge(item: dict[str, str], observations: list[dict[str, Any]],
                    actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    if item["variant"] not in ("0000", "1111"):
        return None
    name = "ec_skeptical_contributor" if item["variant"] == "1111" else "ec_conditional_contributor"
    params = COMMON if item["variant"] == "1111" else {
        key: value for key, value in COMMON.items() if key != "min_sources"}
    original = build_ec_policy(name, params)
    active = {agent for agent, strategy in zip(AGENTS, PROFILES[item["context"]], strict=True)
              if strategy == "A"}
    mismatches = []
    for observation, action in zip(observations, actions, strict=True):
        if observation["agent"] in active:
            expected = original.propose(observation["observation"], None).action.model_dump(
                mode="json")
            if expected != action["action"]:
                mismatches.append({"round": action["round"], "agent": action["agent"],
                                   "expected": expected, "actual": action["action"]})
    return {"legacy_policy": original.policy_id, "checked_actions": ROUNDS * len(active),
            "actions_equal": not mismatches, "mismatches": mismatches}


def _observations(events: list[Event]) -> list[dict[str, Any]]:
    return [{"round": event.logical_time, "agent": event.payload["agent_id"],
             "observation": event.payload["observation"]}
            for event in events if event.event_type == EventType.OBSERVATION_ISSUED]


def episode_record(path: Path, expected: ResolvedScenario, expected_manifest: dict[str, Any],
                   item: dict[str, str], *, fixed: bool = False) -> dict[str, Any]:
    events, resolved, manifest = load_run(path)
    if resolved.scenario_hash != expected.scenario_hash:
        raise ValueError(f"unexpected scenario identity: {path}")
    for key, value in expected_manifest.items():
        if manifest.get(key) != value:
            raise ValueError(f"unexpected manifest {key}: {path}")
    if events[-1].event_type != EventType.RUN_COMPLETED or manifest["status"] != "completed":
        raise ValueError(f"experiment requires a completed episode: {path}")
    actions = qs.rc.action_schedule(events)
    observations = _observations(events)
    coordinates = list(itertools.product(range(ROUNDS), AGENTS))
    for rows in (actions, observations):
        if [(row["round"], row["agent"]) for row in rows] != coordinates:
            raise ValueError(f"incomplete or reordered episode transcript: {path}")
    if any(e.event_type == EventType.ACTION_REJECTED for e in events):
        raise ValueError(f"rejected action in declared experiment: {path}")
    if not replay_run(path).chains_match:
        raise ValueError(f"recorded-ledger replay mismatch: {path}")
    summary = events[-1].payload
    counts = Counter(row["action"]["type"] for row in actions)
    contribution = sum(count for key, count in counts.items() if key not in ("withhold", "abstain"))
    return {
        "cell": item, "scenario_hash": resolved.scenario_hash,
        "mechanism_hash": resolved.mechanism_hash, "terminal_hash": events[-1].event_hash,
        "event_count": len(events), "replay_verified": True, "actions": actions,
        "action_hash": content_hash(actions), "observation_hash": content_hash(observations),
        "action_counts": dict(sorted(counts.items())),
        "contribution_fraction": frac_str(Fraction(contribution, len(actions))),
        "accepted_slots": sum(entry["claim_id"] is not None for entry in summary["briefing"]),
        "collective_quality": summary["collective_quality"], "briefing": summary["briefing"],
        "effort": summary["effort"], "total_effort": sum(summary["effort"].values()),
        "utility": summary["utility"], "individual_credit": summary["individual_credit"],
        "total_credit": frac_str(sum(map(Fraction, summary["individual_credit"].values()),
                                     Fraction())),
        "total_utility": frac_str(sum(map(Fraction, summary["utility"].values()), Fraction())),
        "endpoint_bridge": None if fixed else endpoint_bridge(item, observations, actions),
    }


def collect(root: Path) -> dict[str, Any]:
    study, resolved = load_study(root / "inputs")
    declared, expected = design()
    digest = study_hash(study, resolved)
    if digest != study_hash(declared, expected):
        raise ValueError("saved inputs differ from declared ablation design")
    records, fixed_records, integrity = {}, {}, []
    for item in cells():
        cid = cell_id(item)
        record = episode_record(run_path(root, digest, cid), expected[cid],
                                behavior_manifest(declared, digest, item), item)
        records[cid] = record
        if item["truth"] == "accurate":
            target = compile_scenario(scenario(item, accountability="aggregate"), SKIN)
            fixed = episode_record(root / "fixed-actions" / cid, target,
                                   fixed_manifest(item, target), item, fixed=True)
            fixed_records[cid] = fixed
            fields = ("actions", "briefing", "effort", "collective_quality", "total_utility")
            integrity.append({"cell_id": cid,
                              "preserved": all(record[k] == fixed[k] for k in fields),
                              "checks": {key: record[key] == fixed[key] for key in fields}})
    truth_controls = []
    for context, variant in itertools.product(CONTEXTS, VARIANTS):
        good_id, bad_id = (cell_id({"context": context, "variant": variant, "truth": truth})
                           for truth in TRUTHS)
        good, bad = records[good_id], records[bad_id]
        truth_controls.append({
            "accurate_cell": good_id, "misleading_cell": bad_id,
            "actions_equal": good["actions"] == bad["actions"],
            "observations_equal": good["observation_hash"] == bad["observation_hash"],
            "effort_equal": good["effort"] == bad["effort"],
            "contribution_equal": good["contribution_fraction"] == bad["contribution_fraction"],
            "quality_opposite": good["collective_quality"] == -bad["collective_quality"],
            "credit_opposite": all(Fraction(good["individual_credit"][agent])
                                   == -Fraction(bad["individual_credit"][agent])
                                   for agent in AGENTS),
        })
    contrasts = factorial_contrasts(records)
    result = {"schema": "ec-rule-ablation-results-v1", "status": "exploratory-unfrozen",
              "study_hash": digest, "seed_protocol": PAIRED_SEED_PROTOCOL,
              "design_sha256": sha256_hex((HERE / "DESIGN.md").read_bytes()),
              "behavioral_episodes": len(records), "fixed_action_episodes": len(fixed_records),
              "verified_replays": len(records) + len(fixed_records), "rounds_per_episode": ROUNDS,
              "inference": "finite conditional contrasts; no sample-based uncertainty",
              "episodes": records, "fixed_action_records": fixed_records,
              "truth_controls": truth_controls, "same_action_integrity": integrity,
              "single_factor_contrasts": [r for r in contrasts if len(r["factors"]) == 1],
              "interactions": [r for r in contrasts if len(r["factors"]) > 1]}
    result["predictions"] = readout.predictions(result)
    return result


def execute(destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    study, resolved = write_inputs(destination / "inputs")
    digest = study_hash(study, resolved)
    runs = run_study(destination / "inputs", destination / "runs")
    if any(run.status != "completed" for run in runs):
        raise ValueError("behavioral execution failed; sealed failures retained")
    for item in cells():
        if item["truth"] == "accurate":
            cid = cell_id(item)
            target = compile_scenario(scenario(item, accountability="aggregate"), SKIN)
            fixed_action_run(run_path(destination, digest, cid), target,
                             destination / "fixed-actions" / cid)
    result = collect(destination)
    for filename, text in (("RESULTS.json", encode(result)), ("RESULTS.md", render_report(result))):
        (destination / filename).write_text(text, encoding="utf-8", newline="\n")
    return result


def source_provenance() -> dict[str, Any]:
    commit, dirty = git_provenance(REPO)
    if commit is None or dirty is not False:
        raise SystemExit("recording an execution requires a clean committed worktree")
    environment = environment_provenance()
    paths = sorted([*REPO.glob("src/**/*.py"), *HERE.glob("*.py"), HERE / "DESIGN.md",
                    REPO / "docs/adr/0016-ec-rule-component-ablation.md",
                    HERE.parent / "quality-safeguards/quality_safeguards.py",
                    HERE.parent / "responsive-commons/responsive_commons.py",
                    REPO / "requirements-lock.txt", REPO / "pyproject.toml"])
    return {"schema": "ec-rule-ablation-source-v1", "local_commit": commit, "worktree_dirty": dirty,
            "python_version": environment["python_version"], "platform": environment["platform"],
            "dependency_lock_sha256": lock_hash(REPO),
            "files_sha256": {p.relative_to(REPO).as_posix(): sha256_hex(p.read_bytes())
                             for p in paths}}


def encode(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", type=Path)
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="chl-ec-ablation-") as temp:
            destination = Path(temp) / "experiment"
            result = execute(destination)
            for filename in ("RESULTS.json", "RESULTS.md"):
                if (destination / filename).read_bytes() != (HERE / filename).read_bytes():
                    raise SystemExit(f"{filename} differs from committed ablation readout")
        print(f"Verified {result['behavioral_episodes']} behavioral episodes, "
              f"{result['fixed_action_episodes']} controls and "
              f"{result['verified_replays']} replays.")
    else:
        provenance = source_provenance()
        execute(args.out)
        (args.out / "SOURCE_PROVENANCE.json").write_text(encode(provenance),
                                                        encoding="utf-8", newline="\n")
        print(f"Wrote sealed ablation experiment and readout to {args.out}")


if __name__ == "__main__":
    main()
