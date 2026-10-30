"""Execute and audit the predeclared quality-safeguards enumeration (see DESIGN.md).

Shares PR #81's finite-strategy certificate and helpers by import; the responsive
experiment's bytes and evidence are not altered.
"""

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
sys.path[:0] = [str(REPO / "src"), str(HERE.parent / "responsive-commons")]

import responsive_commons as rc  # type: ignore[import-not-found]  # noqa: E402

from collaborative_hill.agents.replay import ReplayPolicy, proposals_from_events  # noqa: E402
from collaborative_hill.engine.events import EventType  # noqa: E402
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
SLOTS = ("s1", "s2")
HOLDERS = {"a": "a1", "b": "a2", "c": "a3"}
CONTRIBUTOR: dict[str, Any] = {"name": "ec_contributor", "params": {"share_evidence": True}}
QUORUM = {"peer_threshold": "1", "warmup_rounds": 9, "share_evidence": True}
RULES: dict[str, dict[str, Any]] = {
    "unconditional": CONTRIBUTOR,
    "conditional": {"name": "ec_conditional_contributor", "params": QUORUM},
    "skeptical": {"name": "ec_skeptical_contributor", "params": {"min_sources": 2, **QUORUM}},
}
TRUTHS = ("accurate", "misleading")
CORE_STRUCTURES = ("corroborated", "conflicted")
TOPOLOGIES = ("private", "shared_ledger")
ACCOUNTABILITIES = ("aggregate", "attributable")
PROFILES = tuple("".join(p) for p in itertools.product("CF", repeat=3))
ROUNDS = 14
SEED = 20261029
STUDY_ID = "quality-safeguards-v1"
SKIN = NarrativeSkin(skin_id="quality-safeguards-plain", title="Synthetic evidence review")
# Identifiers are path components; short forms keep Windows paths within limits.
SHORT = {"corroborated": "corrob", "conflicted": "conflict", "echo": "echo", "private": "priv",
         "shared_ledger": "ledger", "aggregate": "agg", "attributable": "attr",
         "unconditional": "U", "conditional": "Q", "skeptical": "S"}
FIELDS = ("truth", "structure", "topology", "accountability", "rule", "profile")


def cell(*values: str) -> dict[str, str]:
    return dict(zip(FIELDS, values, strict=True))


def cells() -> list[dict[str, str]]:
    grid = list(itertools.product(TRUTHS, CORE_STRUCTURES, TOPOLOGIES, ACCOUNTABILITIES))
    core = [cell(*base, rule, profile)
            for base, rule, profile in itertools.product(grid, RULES, PROFILES)]
    echo = [cell(truth, "echo", topology, accountability, rule, "CCC")
            for truth, topology, accountability, rule in itertools.product(
                TRUTHS, TOPOLOGIES, ACCOUNTABILITIES, RULES)]
    defender = [cell(*base, rule, "UUC")
                for base, rule in itertools.product(grid, ("conditional", "skeptical"))]
    return core + echo + defender


def cell_id(item: dict[str, str]) -> str:
    return "-".join(SHORT.get(item[key], item[key]) for key in FIELDS)


def block(item: dict[str, str]) -> str:
    return "-".join(SHORT.get(item[key], item[key]) for key in ("structure", "rule", "profile"))


def evidence_item(item: dict[str, str], slot: str, letter: str) -> dict[str, Any]:
    proposition = f"{slot}-p"
    stance = "contradicts" if item["structure"] == "conflicted" and letter == "c" else "supports"
    proposition_true = item["truth"] == "accurate"
    return {
        "evidence_id": f"e{slot[1]}{letter}",
        "source_id": "src-a" if item["structure"] == "echo" else f"src-{letter}",
        "slot_id": slot, "proposition_id": proposition, "stance": stance, "freshness": "fresh",
        "truth_aligned": proposition_true == (stance == "supports"),
        "initial_holders": [HOLDERS[letter]],
    }


def agent_policy(item: dict[str, str], index: int) -> dict[str, Any]:
    strategy = item["profile"][index]
    if strategy == "F":
        return {"name": "ec_freerider"}
    return CONTRIBUTOR if strategy == "U" else RULES[item["rule"]]


def scenario(item: dict[str, str]) -> ScenarioSpec:
    """No outcome-dependent inputs: exactly DESIGN.md's declared cells."""
    if item not in cells():
        raise ValueError("cell is outside the declared design")
    true_suffix = "p" if item["truth"] == "accurate" else "q"
    return ScenarioSpec.model_validate({
        "scenario_id": cell_id(item),
        "world": {
            "kind": "evidence_commons",
            "slots": {s: [f"{s}-p", f"{s}-q"] for s in SLOTS},
            "true_propositions": {s: f"{s}-{true_suffix}" for s in SLOTS},
            "params": {
                "rounds": ROUNDS, "inspect_budget": 6, "verify_budget": 3,
                "cost_inspect": 1, "cost_share": 1, "cost_propose": 1,
                "cost_verify": 2, "cost_challenge": 1,
                "benefit_correct_slot": 12, "penalty_wrong_slot": 12,
                "credit_propose_accepted_correct": 3, "credit_propose_accepted_wrong": -3,
                "credit_verify_accepted_correct": 2, "credit_verify_accepted_wrong": -2,
            },
        },
        "information": {"evidence": [evidence_item(item, slot, letter)
                                     for slot in SLOTS for letter in HOLDERS]},
        "interaction": {"structure": "commons"},
        "institution": {"accountability": item["accountability"],
                        "evidence_topology": item["topology"]},
        "cognition": {"agents": [{"agent_id": agent, "policy": agent_policy(item, index)}
                                 for index, agent in enumerate(AGENTS)]},
    })


def design() -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    conditions = [{"condition_id": cell_id(item), "scenario": f"scenarios/{cell_id(item)}.json",
                   "skin": "skin.json", "scenario_block": block(item)} for item in cells()]
    spec = StudySpec.model_validate({
        "study_id": STUDY_ID, "seed": SEED, "seed_protocol": PAIRED_SEED_PROTOCOL,
        "replicates": 1, "checkpoint_every": 0, "invalid_action_policy": "fail",
        "conditions": conditions,
    })
    return spec, {cell_id(item): compile_scenario(scenario(item), SKIN) for item in cells()}


def write_inputs(destination: Path) -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    spec, resolved = design()
    (destination / "scenarios").mkdir(parents=True)
    (destination / "study.json").write_text(spec.model_dump_json(indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
    (destination / "skin.json").write_text(SKIN.model_dump_json(indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    for cid, item in resolved.items():
        (destination / "scenarios" / f"{cid}.json").write_text(
            item.spec.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    return spec, resolved


def episode_record(path: Path, expected: ResolvedScenario,
                   expected_manifest: dict[str, Any]) -> dict[str, Any]:
    events, resolved, manifest = load_run(path)
    if resolved.scenario_hash != expected.scenario_hash:
        raise ValueError(f"unexpected scenario identity: {path}")
    for key, value in expected_manifest.items():
        if manifest.get(key) != value:
            raise ValueError(f"unexpected manifest {key}: {path}")
    if events[-1].event_type != EventType.RUN_COMPLETED or manifest["status"] != "completed":
        raise ValueError(f"experiment requires a completed episode: {path}")
    actions = rc.action_schedule(events)
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
        "total_effort": sum(summary["effort"].values()),
        "utility": summary["utility"], "individual_credit": summary["individual_credit"],
        "total_utility": frac_str(sum(map(Fraction, summary["utility"].values()), Fraction())),
    }


def fixed_action_run(source: Path, target: ResolvedScenario, destination: Path) -> None:
    events, _, original = load_run(source)
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
        write_manifest(RunManifest(
            study_id=config.study_id, condition_id=target.spec.scenario_id,
            run_id=run_id, replicate=0, scenario_hash=target.scenario_hash,
            mechanism_hash=target.mechanism_hash, narrative_hash=target.narrative_hash,
            evidence_corpus_hash=target.evidence_corpus_hash,
            institution=target.spec.institution.model_dump(mode="json"),
            code_commit=original["code_commit"], worktree_dirty=original["worktree_dirty"],
            python_version=env["python_version"], platform=env["platform"],
            dependency_lock_sha256=original["dependency_lock_sha256"],
            policies={a: p.policy_id for a, p in policies.items()},
            seed_root=list(config.seed_root), status=result.status,
            failure_reason=result.failure_reason, event_count=result.event_count,
            final_event_hash=result.final_event_hash,
        ), paths.manifest)


def delta(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    return {
        "actions_equal": target["action_hash"] == source["action_hash"],
        "quality_delta": target["collective_quality"] - source["collective_quality"],
        "contribution_delta": frac_str(Fraction(target["contribution_fraction"])
                                       - Fraction(source["contribution_fraction"])),
        "effort_delta": target["total_effort"] - source["total_effort"],
        "total_utility_delta": frac_str(Fraction(target["total_utility"])
                                        - Fraction(source["total_utility"])),
    }


def contrasts(records: dict[str, dict[str, Any]], field: str, target: str,
              source: str) -> list[dict[str, Any]]:
    """Every declared pair differing only in `field`, with all else held fixed."""
    rows = []
    for item in cells():
        pair = {**item, field: target}
        if item[field] == source and cell_id(pair) in records:
            shared = {k: v for k, v in item.items() if k != field}
            rows.append({**shared, **delta(records[cell_id(pair)], records[cell_id(item)])})
    return rows


def alignment(records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Unweighted quality over each pairing of structure with truth; no prevalence."""
    def total(pairing: tuple[tuple[str, str], ...], rest: tuple[str, ...]) -> int:
        topology, accountability, rule, profile = rest
        return sum(int(records[cell_id(cell(truth, structure, topology, accountability, rule,
                                            profile))]["collective_quality"])
                   for truth, structure in pairing)

    return [{
        "topology": rest[0], "accountability": rest[1], "rule": rest[2], "profile": rest[3],
        "aligned": total((("accurate", "corroborated"), ("misleading", "conflicted")), rest),
        "inverted": total((("accurate", "conflicted"), ("misleading", "corroborated")), rest),
    } for rest in itertools.product(TOPOLOGIES, ACCOUNTABILITIES, RULES, PROFILES)]


def predictions(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Mechanical scoring of DESIGN.md's P1-P10. Failures are reported, never raised."""
    records = result["episodes"]

    def rec(*values: str) -> dict[str, Any]:
        return dict(records[cell_id(cell(*values))])

    def q(*values: str) -> int:
        return int(rec(*values)["collective_quality"])

    signs = {"accurate": 1, "misleading": -1}
    grid = list(itertools.product(TOPOLOGIES, ACCOUNTABILITIES))
    truth_grid = [(t, *rest) for t in TRUTHS for rest in grid]
    attribution = result["attribution_contrasts"]
    certificates = result["finite_strategy_certificates"]

    p1 = all(row["actions_equal"] for row in result["truth_controls"]) and all(
        row["quality_sum"] == 0 for row in result["truth_controls"])
    p2 = all(
        rec(t, "corroborated", o, a, "skeptical", "CCC")["action_hash"]
        == rec(t, "corroborated", o, a, "conditional", "CCC")["action_hash"]
        for t, o, a in truth_grid
    ) and q("misleading", "corroborated", "private", "attributable", "skeptical", "CCC") == -24 \
        and all(q("misleading", "corroborated", "shared_ledger", a, "skeptical", "CCC") == -24
                for a in ACCOUNTABILITIES)
    p3 = all(q(t, "conflicted", o, a, "skeptical", "CCC") == 0
             and q(t, "conflicted", o, a, "conditional", "CCC") == 24 * signs[t]
             for t, o, a in truth_grid)
    p4 = all(q(t, "echo", o, a, "skeptical", "CCC") == 0
             and q(t, "echo", o, a, "unconditional", "CCC") == 24 * signs[t]
             for t, o, a in truth_grid)
    p5 = all(q("misleading", "conflicted", "private", a, "skeptical", "CCF") == -12
             and q("misleading", "conflicted", "shared_ledger", a, "skeptical", "CCF") == 0
             for a in ACCOUNTABILITIES)
    p6 = all(
        q(t, "conflicted", "private", "attributable", "skeptical", "UUC") == 0
        and q(t, "conflicted", "private", "aggregate", "skeptical", "UUC") == 12 * signs[t]
        and q(t, "conflicted", "private", "attributable", "conditional", "UUC") == 24 * signs[t]
        and all(q(t, "conflicted", "shared_ledger", a, "skeptical", "UUC") == 0
                for a in ACCOUNTABILITIES)
        for t in TRUTHS)

    def attribution_expected(row: dict[str, Any]) -> int:
        driven = (row["structure"], row["topology"]) == ("corroborated", "private")
        if driven and row["rule"] in ("conditional", "skeptical"):
            return 24 * signs[row["truth"]]
        return 0

    p7 = all(row["quality_delta"] == attribution_expected(row) for row in attribution
             if row["profile"] == "CCC" and row["structure"] in CORE_STRUCTURES) and all(
        row["actions_equal"] for row in attribution if row["rule"] == "unconditional"
        and row["profile"] in PROFILES)
    expected = {"skeptical": (24, -24), "conditional": (0, 0), "unconditional": (0, 0)}
    p8 = all((row["aligned"], row["inverted"]) == expected[row["rule"]]
             for row in result["observable_alignment"]
             if (row["profile"], row["topology"], row["accountability"])
             == ("CCC", "private", "attributable"))
    p9 = all(c["c1"] and not c["c2"] for c in certificates)
    p10 = all(all(row["checks"].values()) for row in result["same_action_integrity"])
    scores = (p1, p2, p3, p4, p5, p6, p7, p8, p9, p10)
    return [{"prediction": f"P{index}", "held": bool(score)}
            for index, score in enumerate(scores, 1)]


def collect(root: Path) -> dict[str, Any]:
    expected_spec, expected = design()
    actual_spec, actual = load_study(root / "inputs")
    digest = study_hash(expected_spec, expected)
    if actual_spec != expected_spec or study_hash(actual_spec, actual) != digest:
        raise ValueError("stored inputs differ from the predeclared design")
    records: dict[str, dict[str, Any]] = {}
    for item in cells():
        cid = cell_id(item)
        seed, policy_seed = study_seed_roots(
            SEED, cid, 0, protocol=PAIRED_SEED_PROTOCOL, scenario_block=block(item))
        records[cid] = {"cell": item, **episode_record(
            rc.run_path(root, digest, cid), expected[cid], {
                "study_id": STUDY_ID, "study_hash": digest, "study_frozen": False,
                "condition_id": cid, "run_id": cid + "-r000", "replicate": 0,
                "seed_protocol": PAIRED_SEED_PROTOCOL, "scenario_block": block(item),
                "seed_root": list(seed),
                "policy_seed_root": list(policy_seed) if policy_seed else None,
                "policies": {a: p.policy_id for a, p in build_policies(expected[cid]).items()},
                "invalid_action_policy": "fail", "checkpoint_every": 0, "parent_run": None,
            })}
    integrity = []
    for item in cells():
        if item["accountability"] != "aggregate":
            continue
        target = cell_id({**item, "accountability": "attributable"})
        fixed = episode_record(root / "fixed-actions" / target, expected[target], {
            "study_id": STUDY_ID + "-c3", "study_hash": None, "study_frozen": False,
            "replicate": 0, "condition_id": target, "run_id": target + "-fixed-actions",
            "policies": dict.fromkeys(AGENTS, "recorded-actions@1"),
            "seed_root": [SEED, "fixed-actions", target], "policy_seed_root": None,
            "scenario_block": None, "invalid_action_policy": "fail", "checkpoint_every": 0,
            "parent_run": None,
        })
        source = records[cell_id(item)]
        checks = rc.task_integrity(source, fixed)
        if not all(checks.values()):
            raise ValueError(f"same-action integrity failed: {item}: {checks}")
        shared = {k: v for k, v in item.items() if k != "accountability"}
        integrity.append({**shared, "source_terminal_hash": source["terminal_hash"],
                          "replay_terminal_hash": fixed["terminal_hash"], "checks": checks})
    certificates = []
    for truth, structure, topology, accountability, rule in itertools.product(
            TRUTHS, CORE_STRUCTURES, TOPOLOGIES, ACCOUNTABILITIES, RULES):
        group = cell(truth, structure, topology, accountability, rule, "")
        del group["profile"]
        profiles = {p: records[cell_id({**group, "profile": p})] for p in PROFILES}
        certificates.append({**group, **rc.certificate(profiles)})
    truth_controls = [
        {**row, "quality_sum": records[cell_id(cell("misleading", row["structure"], row["topology"],
                                                    row["accountability"], row["rule"],
                                                    row["profile"]))]["collective_quality"]
         + records[cell_id(cell("accurate", row["structure"], row["topology"],
                                row["accountability"], row["rule"],
                                row["profile"]))]["collective_quality"]}
        for row in contrasts(records, "truth", "misleading", "accurate")]
    result: dict[str, Any] = {
        "schema": "quality-safeguards-results-v1", "status": "exploratory-unfrozen",
        "study_hash": digest, "seed_protocol": PAIRED_SEED_PROTOCOL,
        "behavioral_episodes": len(records), "fixed_action_episodes": len(integrity),
        "rounds_per_episode": ROUNDS,
        "design_sha256": sha256_hex((HERE / "DESIGN.md").read_bytes()),
        "inference": "deterministic enumeration; no sample-based uncertainty intervals",
        "episodes": records, "truth_controls": truth_controls,
        "screen_contrasts": contrasts(records, "rule", "skeptical", "conditional"),
        "structure_contrasts": [
            row for row in contrasts(records, "structure", "conflicted", "corroborated")
            if row["profile"] != "UUC"],
        "attribution_contrasts": contrasts(records, "accountability", "attributable", "aggregate"),
        "observable_alignment": alignment(records),
        "finite_strategy_certificates": certificates,
        "same_action_integrity": integrity,
    }
    result["predictions"] = predictions(result)
    return result


def sign_counts(rows: list[dict[str, Any]]) -> tuple[int, int, int]:
    deltas = [row["quality_delta"] for row in rows]
    return (sum(d > 0 for d in deltas), sum(d < 0 for d in deltas), sum(d == 0 for d in deltas))


def episode_rows(result: dict[str, Any], profile: str, structures: tuple[str, ...]) -> list[str]:
    lines = ["| Truth | Structure | Topology | Accountability | Rule | Correct/wrong | Quality | "
             "Contribution | Effort | Utility a1/a2/a3 | Total utility |",
             "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for record in result["episodes"].values():
        item = record["cell"]
        if item["profile"] == profile and item["structure"] in structures:
            utility = "/".join(record["utility"][agent] for agent in AGENTS)
            lines.append(
                f"| {item['truth']} | {item['structure']} | {item['topology']} | "
                f"{item['accountability']} | {item['rule']} | "
                f"{record['correct_slots']}/{record['wrong_slots']} | "
                f"{record['collective_quality']} | {record['contribution_fraction']} | "
                f"{record['total_effort']} | {utility} | {record['total_utility']} |")
    return lines


def render_report(result: dict[str, Any]) -> str:
    held = [p["prediction"] for p in result["predictions"] if p["held"]]
    missed = [p["prediction"] for p in result["predictions"] if not p["held"]]
    screen = result["screen_contrasts"]
    certificates = result["finite_strategy_certificates"]
    certified = sum(c["finite_strategy_dilemma"] for c in certificates)
    lines = [
        "# Quality safeguards — deterministic sensitivity results", "",
        "This is an unfrozen scripted-policy experiment, not a live-model or human result.",
        "The design and predictions precede execution in [DESIGN.md](DESIGN.md). The checked-in",
        "[RESULTS.json](RESULTS.json) retains every cell, terminal hash, contrast and unilateral",
        "deviation. Execution identity is in [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json).",
        "Post-execution reading is separate, in [FINDINGS.md](FINDINGS.md).", "",
        f"**{result['behavioral_episodes']} behavioral episodes and "
        f"{result['fixed_action_episodes']} controlled action replays**, each {ROUNDS} rounds.",
        "Counts describe this finite grid. They are not frequencies or significance tests.", "",
        "## Declared predictions", "",
        f"Held: {', '.join(held) or 'none'}. Not held: {', '.join(missed) or 'none'}.", "",
        "## Truth negative control", "",
        f"Across {len(result['truth_controls'])} accurate/misleading pairs, "
        f"{sum(r['actions_equal'] for r in result['truth_controls'])} have identical action "
        f"schedules and {sum(r['quality_sum'] == 0 for r in result['truth_controls'])} have "
        "exactly opposite quality. Corpora in a pair differ only in hidden truth.", "",
        "## All-active profile", "",
        "Quality is signed accepted-slot value. Contribution is the fraction of agent-rounds",
        "not withheld. Effort and total utility sum over agents.", "",
        *episode_rows(result, "CCC", (*CORE_STRUCTURES, "echo")), "",
        "## Screen effect: skeptical minus conditional", "", "Same quorum, same cell otherwise.",
        "", "| Truth | Structure | Pairs | Quality up | Quality down | Quality unchanged | "
        "Actions equal |", "|---|---|---:|---:|---:|---:|---:|",
    ]
    for truth, structure in itertools.product(TRUTHS, (*CORE_STRUCTURES, "echo")):
        rows = [r for r in screen if (r["truth"], r["structure"]) == (truth, structure)]
        up, down, same = sign_counts(rows)
        lines.append(f"| {truth} | {structure} | {len(rows)} | {up} | {down} | {same} | "
                     f"{sum(r['actions_equal'] for r in rows)} |")
    lines += [
        "", "## Conflicted minus corroborated", "", "Core cells, access and budgets identical.",
        "", "| Truth | Rule | Pairs | Quality up | Quality down | Quality unchanged |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for truth, rule in itertools.product(TRUTHS, RULES):
        rows = [r for r in result["structure_contrasts"]
                if (r["truth"], r["rule"]) == (truth, rule)]
        up, down, same = sign_counts(rows)
        lines.append(f"| {truth} | {rule} | {len(rows)} | {up} | {down} | {same} |")
    lines += [
        "", "## Observable alignment", "",
        "Aligned sums accurate-corroborated and misleading-conflicted quality; inverted sums",
        "accurate-conflicted and misleading-corroborated. These are unweighted sums over the",
        "`CCC` cells, not expectations: nothing here says which pairing occurs.", "",
        "| Topology | Accountability | Rule | Aligned | Inverted |", "|---|---|---|---:|---:|",
    ]
    for row in result["observable_alignment"]:
        if row["profile"] == "CCC":
            lines.append(f"| {row['topology']} | {row['accountability']} | {row['rule']} | "
                         f"{row['aligned']} | {row['inverted']} |")
    lines += [
        "", "## Hidden contradiction: conflicted, `CCF`", "",
        "`a3` free-rides and holds the only contradicting items.", "",
        *episode_rows(result, "CCF", ("conflicted",)), "",
        "## Defender probe: `UUC`", "",
        "`a1` and `a2` are unconditional; `a3` holds `*c` and runs the rule.", "",
        *episode_rows(result, "UUC", CORE_STRUCTURES), "",
        "## Attribution: attributable minus aggregate", "",
        "| Structure | Rule | Pairs | Quality up | Quality down | Quality unchanged | "
        "Actions differ |", "|---|---|---:|---:|---:|---:|---:|",
    ]
    for structure, rule in itertools.product((*CORE_STRUCTURES, "echo"), RULES):
        rows = [r for r in result["attribution_contrasts"]
                if (r["structure"], r["rule"]) == (structure, rule)]
        up, down, same = sign_counts(rows)
        lines.append(f"| {structure} | {rule} | {len(rows)} | {up} | {down} | {same} | "
                     f"{sum(not r['actions_equal'] for r in rows)} |")
    lines += [
        "", "## Incentives over the tested strategy pair", "",
        f"{certified} of {len(certificates)} core groups satisfy both C1 (some strictly "
        "profitable active-to-free-rider deviation) and C2 (`CCC` total utility strictly "
        "exceeds `FFF`). This applies only to the two designated strategies and these "
        "placeholder settings.", "",
        "| Truth | Structure | Topology | Accountability | Rule | C1 | C2 | CCC−FFF |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for c in certificates:
        lines.append(f"| {c['truth']} | {c['structure']} | {c['topology']} | "
                     f"{c['accountability']} | {c['rule']} | {c['c1']} | {c['c2']} | "
                     f"{c['ccc_minus_fff_total_utility']} |")
    lines += [
        "", "## C3 same-action integrity", "",
        f"All {len(result['same_action_integrity'])} replays of an aggregate action schedule "
        "under attributable preserve the schedule, briefing, effort, quality and total utility.",
        "Individual credit can redistribute.", "",
        "## Reproduce", "", "```bash",
        "python experiments/quality-safeguards/quality_safeguards.py --out artifacts/quality-new",
        "python experiments/quality-safeguards/quality_safeguards.py --check", "```", "",
        "`--out` needs a clean worktree and a fresh directory, and retains inputs, sealed",
        "ledgers, manifests and the readout there. `--check` regenerates everything in a",
        "temporary directory and byte-compares the readout. Neither calls a provider.", "",
        f"Study hash: `{result['study_hash']}`. The study remains unfrozen.", "",
    ]
    return "\n".join(lines)


def source_provenance() -> dict[str, Any]:
    commit, dirty = git_provenance(REPO)
    if commit is None or dirty is not False:
        raise SystemExit("recording an execution requires a clean committed worktree")
    environment = environment_provenance()
    paths = sorted([*REPO.glob("src/**/*.py"), Path(__file__).resolve(), HERE / "DESIGN.md",
                    HERE.parent / "responsive-commons/responsive_commons.py",
                    REPO / "requirements-lock.txt", REPO / "pyproject.toml"])
    return {"schema": "quality-safeguards-execution-source-v1", "local_commit": commit,
            "worktree_dirty": dirty, "python_version": environment["python_version"],
            "platform": environment["platform"], "dependency_lock_sha256": lock_hash(REPO),
            "files_sha256": {p.relative_to(REPO).as_posix(): sha256_hex(p.read_bytes())
                             for p in paths}}


def execute(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    spec, resolved = write_inputs(root / "inputs")
    digest = study_hash(spec, resolved)
    results = run_study(root / "inputs", root / "runs")
    if any(result.status != "completed" for result in results):
        raise ValueError("behavioral execution failed; sealed failures retained in output")
    aggregate = [item for item in cells() if item["accountability"] == "aggregate"]
    for item in aggregate:
        target = cell_id({**item, "accountability": "attributable"})
        fixed_action_run(rc.run_path(root, digest, cell_id(item)), resolved[target],
                         root / "fixed-actions" / target)
    result = collect(root)
    first = aggregate[0]
    for path in (rc.run_path(root, digest, cell_id(first)),
                 root / "fixed-actions" / cell_id({**first, "accountability": "attributable"})):
        if not replay_run(path).chains_match:
            raise ValueError(f"recorded-ledger replay mismatch: {path}")
    (root / "RESULTS.json").write_text(encode(result), encoding="utf-8", newline="\n")
    (root / "RESULTS.md").write_text(render_report(result), encoding="utf-8", newline="\n")
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
        with tempfile.TemporaryDirectory(prefix="chl-quality-") as temp:
            destination = Path(temp) / "experiment"
            result = execute(destination)
            for filename in ("RESULTS.json", "RESULTS.md"):
                if (destination / filename).read_bytes() != (HERE / filename).read_bytes():
                    raise SystemExit(f"{filename} differs from the committed readout")
        print(f"Verified {result['behavioral_episodes']} behavioral episodes, "
              f"{result['fixed_action_episodes']} same-action controls and exact readout.")
    else:
        provenance = source_provenance()
        execute(args.out)
        (args.out / "SOURCE_PROVENANCE.json").write_text(
            encode(provenance), encoding="utf-8", newline="\n")
        print(f"Wrote sealed experiment and readout to {args.out}")


if __name__ == "__main__":
    main()
