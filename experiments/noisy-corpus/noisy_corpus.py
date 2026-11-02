"""Exact declared noisy-corpus enumeration, without an enabled audit channel.

See DESIGN.md. Behavioral outcomes are sealed once for every finite corpus and
then weighted under explicit probability models; rates are not extra replicates.
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
sys.path[:0] = [str(REPO / "src"), str(HERE)]

import closed_form  # noqa: E402
from audit_contract import (  # noqa: E402
    AuditConfig,
    AuditFinding,
    exact_probability,
    has_hidden_fields,
    project_audit,
)

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
TRUTHS = ("p", "q")
REPORTS = tuple("".join(reports) for reports in itertools.product(TRUTHS, repeat=3))
RULES = ("conditional", "skeptical")
LABELS = ("distinct", "collapsed")
MODELS = ("independent", "correlated")
RATES = ("0", "1/10", "1/4", "1/2", "3/4", "1")
ROUNDS = 8
SEED = 20261102
STUDY_ID = "noisy-corpus-v1"
SKIN = NarrativeSkin(skin_id="noisy-corpus-plain", title="Synthetic evidence review")


def cells() -> list[dict[str, str]]:
    return [dict(zip(("truth", "reports", "rule", "labels"), values, strict=True))
            for values in itertools.product(TRUTHS, REPORTS, RULES, LABELS)]


def cell_id(cell: dict[str, str]) -> str:
    world = TRUTHS.index(cell["truth"]) * len(REPORTS) + REPORTS.index(cell["reports"])
    return f"w{world:02}-{cell['rule'][0]}-{cell['labels'][0]}"


def block(cell: dict[str, str]) -> str:
    return f"{cell['reports']}-{cell['rule']}-{cell['labels']}"


def scenario(cell: dict[str, str], accountability: str = "aggregate") -> ScenarioSpec:
    if cell not in cells() or accountability not in {"aggregate", "attributable"}:
        raise ValueError("cell is outside the declared design")
    params: dict[str, Any] = {"peer_threshold": "0", "warmup_rounds": 0, "share_evidence": True}
    if cell["rule"] == "skeptical":
        params["min_sources"] = 2
    policy = {"name": f"ec_{cell['rule']}_contributor", "params": params}
    return ScenarioSpec.model_validate({
        "scenario_id": cell_id(cell),
        "world": {"kind": "evidence_commons", "slots": {"s1": ["p", "q"]},
                  "true_propositions": {"s1": cell["truth"]},
                  "params": {"rounds": ROUNDS, "inspect_budget": 3, "verify_budget": 2,
                             "cost_inspect": 1, "cost_share": 1, "cost_propose": 1,
                             "cost_verify": 2, "cost_challenge": 1,
                             "benefit_correct_slot": 12, "penalty_wrong_slot": 12,
                             "credit_propose_accepted_correct": 3,
                             "credit_propose_accepted_wrong": -3,
                             "credit_verify_accepted_correct": 2,
                             "credit_verify_accepted_wrong": -2}},
        "information": {"evidence": [
            {"evidence_id": f"e{index}",
             "source_id": f"src-{index}" if cell["labels"] == "distinct" else "src-1",
             "version": 1, "slot_id": "s1", "proposition_id": report,
             "stance": "supports", "freshness": "fresh", "truth_aligned": report == cell["truth"],
             "initial_holders": [agent]}
            for index, (agent, report) in enumerate(zip(AGENTS, cell["reports"], strict=True), 1)]},
        "interaction": {"structure": "commons"},
        "institution": {"accountability": accountability, "evidence_topology": "shared_ledger"},
        "cognition": {"agents": [{"agent_id": agent, "policy": policy} for agent in AGENTS]},
    })


def design() -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    spec = StudySpec.model_validate({
        "study_id": STUDY_ID, "seed": SEED, "seed_protocol": PAIRED_SEED_PROTOCOL,
        "replicates": 1, "checkpoint_every": 0, "invalid_action_policy": "fail",
        "conditions": [{"condition_id": cell_id(cell),
                        "scenario": f"scenarios/{cell_id(cell)}.json", "skin": "skin.json",
                        "scenario_block": block(cell)} for cell in cells()],
    })
    return spec, {cell_id(cell): compile_scenario(scenario(cell), SKIN) for cell in cells()}


def encode(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_json(path: Path, value: Any) -> None:
    path.write_text(encode(value), encoding="utf-8", newline="\n")


def write_inputs(destination: Path) -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    spec, resolved = design()
    (destination / "scenarios").mkdir(parents=True, exist_ok=False)
    write_json(destination / "study.json", spec.model_dump(mode="json"))
    write_json(destination / "skin.json", SKIN.model_dump(mode="json"))
    for cid, item in resolved.items():
        write_json(destination / "scenarios" / f"{cid}.json", item.spec.model_dump(mode="json"))
    return spec, resolved


def run_path(root: Path, digest: str, cid: str) -> Path:
    return root / "runs" / ("DRAFT-" + digest[:12]) / cid / (cid + "-r000")


def action_schedule(events: list[Event]) -> list[dict[str, Any]]:
    return [{"round": event.logical_time, "agent": event.payload["agent_id"],
             "action": event.payload["action"]}
            for event in events if event.event_type == EventType.ACTION_ACCEPTED]


def episode_record(path: Path, expected: ResolvedScenario,
                   expected_manifest: dict[str, Any]) -> dict[str, Any]:
    events, actual, manifest = load_run(path)
    if actual != expected:
        raise ValueError(f"stored scenario differs from the declared input: {path}")
    for key, value in expected_manifest.items():
        if manifest.get(key) != value:
            raise ValueError(f"unexpected manifest {key}: {path}")
    if manifest["status"] != "completed" or events[-1].event_type != EventType.RUN_COMPLETED:
        raise ValueError(f"experiment requires a completed episode: {path}")
    if any(event.event_type == EventType.ACTION_REJECTED for event in events):
        raise ValueError(f"rejected action in declared episode: {path}")
    if any(has_hidden_fields(event.payload) for event in events):
        raise ValueError(f"hidden truth field in ledger: {path}")
    actions = action_schedule(events)
    observations = [event.payload for event in events
                    if event.event_type == EventType.OBSERVATION_ISSUED]
    if len(actions) != ROUNDS * len(AGENTS) or len(observations) != len(actions):
        raise ValueError(f"incomplete episode: {path}")
    summary = events[-1].payload
    counts = Counter(row["action"]["type"] for row in actions)
    contributions = sum(count for action, count in counts.items()
                        if action not in {"withhold", "abstain"})
    return {
        "scenario_hash": actual.scenario_hash, "mechanism_hash": actual.mechanism_hash,
        "terminal_hash": events[-1].event_hash, "event_count": len(events),
        "action_schedule": actions, "action_hash": content_hash(actions),
        "observation_hash": content_hash(observations),
        "action_counts": dict(sorted(counts.items())),
        "contribution_fraction": frac_str(Fraction(contributions, len(actions))),
        "correct_slots": sum(row.get("correct") is True for row in summary["briefing"]),
        "wrong_slots": sum(row.get("correct") is False for row in summary["briefing"]),
        "collective_quality": summary["collective_quality"], "briefing": summary["briefing"],
        "effort": summary["effort"], "total_effort": sum(summary["effort"].values()),
        "utility": summary["utility"], "individual_credit": summary["individual_credit"],
        "total_credit": frac_str(sum(map(Fraction, summary["individual_credit"].values()),
                                     Fraction())),
        "total_utility": frac_str(sum(map(Fraction, summary["utility"].values()), Fraction())),
        "ledger_has_no_hidden_fields": True,
    }


def fixed_action_run(source: Path, target: ResolvedScenario, destination: Path) -> None:
    events, _, original = load_run(source)
    proposals = proposals_from_events(events)
    policies = {agent: ReplayPolicy(agent, "recorded-actions@1", proposals[agent])
                for agent in AGENTS}
    config = RunConfig(study_id=STUDY_ID + "-c3", run_id=target.spec.scenario_id + "-fixed",
                       seed_root=(SEED, "fixed-actions", target.spec.scenario_id))
    with RunPaths(destination).reserve() as paths:
        write_json(destination / "scenario.resolved.json", target.model_dump(mode="json"))
        result = run_episode(mechanism=target.build_mechanism(), policies=policies, config=config,
                             paths=paths, start_meta={"scenario_hash": target.scenario_hash,
                                                     "mechanism_hash": target.mechanism_hash,
                                                     "narrative_hash": target.narrative_hash})
        environment = environment_provenance()
        write_manifest(RunManifest(
            study_id=config.study_id, condition_id=target.spec.scenario_id, run_id=config.run_id,
            replicate=0, scenario_hash=target.scenario_hash, mechanism_hash=target.mechanism_hash,
            narrative_hash=target.narrative_hash, evidence_corpus_hash=target.evidence_corpus_hash,
            institution=target.spec.institution.model_dump(mode="json"),
            code_commit=original["code_commit"], worktree_dirty=original["worktree_dirty"],
            python_version=environment["python_version"], platform=environment["platform"],
            dependency_lock_sha256=original["dependency_lock_sha256"],
            policies={agent: policy.policy_id for agent, policy in policies.items()},
            seed_root=list(config.seed_root), status=result.status,
            failure_reason=result.failure_reason, event_count=result.event_count,
            final_event_hash=result.final_event_hash,
        ), paths.manifest)


def world_probability(truth: str, reports: str, model: str, error_rate: str) -> Fraction:
    """Joint P(truth,reports) in the declared synthetic population of worlds."""
    if truth not in TRUTHS or reports not in REPORTS or model not in MODELS:
        raise ValueError("unknown world or corpus model")
    error = exact_probability(error_rate)
    if model == "correlated":
        if reports == truth * 3:
            return (1 - error) / 2
        if len(set(reports)) == 1:
            return error / 2
        return Fraction(0)
    result = Fraction(1, 2)
    for report in reports:
        result *= error if report != truth else 1 - error
    return result


def probability_audit(model: str, error_rate: str) -> dict[str, Any]:
    masses = [{"truth": truth, "reports": reports,
               "mass": frac_str(world_probability(truth, reports, model, error_rate))}
              for truth, reports in itertools.product(TRUTHS, REPORTS)]
    truth_mass = {truth: sum((Fraction(row["mass"]) for row in masses if row["truth"] == truth),
                            Fraction()) for truth in TRUTHS}
    source_error = [sum((Fraction(row["mass"]) for row in masses
                        if row["reports"][index] != row["truth"]), Fraction())
                    for index in range(3)]
    total = sum((Fraction(row["mass"]) for row in masses), Fraction())
    return {"model": model, "error_rate": error_rate, "world_masses": masses,
            "total_mass": frac_str(total),
            "truth_mass": {key: frac_str(value) for key, value in truth_mass.items()},
            "source_error_rates": [frac_str(value) for value in source_error],
            "checks": {"normalized": total == 1,
                       "balanced_synthetic_truth": set(truth_mass.values()) == {Fraction(1, 2)},
                       "declared_source_marginals": all(value == Fraction(error_rate)
                                                        for value in source_error)}}


def weighted_metrics(records: dict[str, dict[str, Any]], model: str, error_rate: str,
                     rule: str, labels: str, truth_condition: str = "mixture") -> dict[str, Any]:
    if truth_condition not in (*TRUTHS, "mixture"):
        raise ValueError("unknown truth condition")
    weighted = []
    for cell in cells():
        if cell["rule"] != rule or cell["labels"] != labels:
            continue
        if truth_condition != "mixture" and cell["truth"] != truth_condition:
            continue
        mass = world_probability(cell["truth"], cell["reports"], model, error_rate)
        if truth_condition != "mixture":
            mass *= 2  # conditioning on an explicitly declared mass of 1/2
        weighted.append((mass, records[cell_id(cell)]))
    if sum((mass for mass, _ in weighted), Fraction()) != 1:
        raise ValueError("weighted cell masses do not sum to one")

    def mean(field: str) -> Fraction:
        return sum((mass * Fraction(record[field]) for mass, record in weighted), Fraction())

    correct, wrong = mean("correct_slots"), mean("wrong_slots")
    accepted = correct + wrong
    metrics = {
        "correct_probability": frac_str(correct), "wrong_probability": frac_str(wrong),
        "accepted_probability": frac_str(accepted),
        "abstention_probability": frac_str(1 - accepted),
        "selective_accuracy": frac_str(correct / accepted) if accepted else None,
        "expected_quality": frac_str(mean("collective_quality")),
        "expected_effort": frac_str(mean("total_effort")),
        "expected_contribution": frac_str(mean("contribution_fraction")),
        "expected_total_credit": frac_str(mean("total_credit")),
        "expected_total_utility": frac_str(mean("total_utility")),
    }
    expected = closed_form.expected_metrics(model, rule, labels, Fraction(error_rate))
    return {"model": model, "error_rate": error_rate, "rule": rule, "labels": labels,
            "truth_condition": truth_condition, **metrics, "closed_form": expected,
            "oracle_matches": metrics == expected}


def validate_audit_fixture() -> dict[str, Any]:
    fixture = json.loads((HERE / "AUDIT_FIXTURE.json").read_text(encoding="utf-8"))
    config = AuditConfig.model_validate_json(json.dumps(fixture["config"]))
    findings = tuple(AuditFinding.model_validate_json(json.dumps(finding))
                     for finding in fixture["findings"])
    projections = {rnd: project_audit(config, findings, int(rnd)).model_dump(mode="json")
                   for rnd in fixture["expected_public_verdicts_by_round"]}
    for rnd, expected in fixture["expected_public_verdicts_by_round"].items():
        if [finding["verdict"] for finding in projections[rnd]["reports"]] != expected:
            raise ValueError("audit projection differs from the declared timing fixture")
    return {"contract_version": config.contract_version, "contract_hash": config.contract_hash(),
            "status": "validated-standalone-projection-only; engine-channel-not-implemented",
            "fixture_sha256": sha256_hex((HERE / "AUDIT_FIXTURE.json").read_bytes()),
            "projections": projections}


def _expected_manifest(cell: dict[str, str], resolved: ResolvedScenario,
                       digest: str) -> dict[str, Any]:
    cid = cell_id(cell)
    seed, policy_seed = study_seed_roots(SEED, cid, 0, protocol=PAIRED_SEED_PROTOCOL,
                                        scenario_block=block(cell))
    return {"study_id": STUDY_ID, "study_hash": digest, "study_frozen": False,
            "condition_id": cid, "run_id": cid + "-r000", "replicate": 0,
            "seed_protocol": PAIRED_SEED_PROTOCOL, "scenario_block": block(cell),
            "seed_root": list(seed), "policy_seed_root": list(policy_seed) if policy_seed else None,
            "policies": {agent: policy.policy_id
                         for agent, policy in build_policies(resolved).items()},
            "invalid_action_policy": "fail", "checkpoint_every": 0, "parent_run": None}


def collect(root: Path) -> dict[str, Any]:
    expected_spec, expected = design()
    actual_spec, actual = load_study(root / "inputs")
    digest = study_hash(expected_spec, expected)
    if actual_spec != expected_spec or actual != expected:
        raise ValueError("stored inputs differ from the predeclared design")
    records, integrity, replays = {}, [], []
    for cell in cells():
        cid = cell_id(cell)
        path = run_path(root, digest, cid)
        manifest = _expected_manifest(cell, expected[cid], digest)
        record = episode_record(path, expected[cid], manifest)
        expected_metrics = closed_form.episode_metrics(**cell, accountability="aggregate")
        oracle_schedule = closed_form.action_schedule(cell["reports"], cell["rule"], cell["labels"])
        record["oracle_schedule_matches"] = record["action_schedule"] == oracle_schedule
        record["oracle_metrics_match"] = all(record[key] == value
                                            for key, value in expected_metrics.items())
        records[cid] = {"cell": cell, **record}
        target = compile_scenario(scenario(cell, "attributable"), SKIN)
        fixed_path = root / "fixed-actions" / cid
        fixed = episode_record(fixed_path, target, {
            "study_id": STUDY_ID + "-c3", "study_hash": None, "study_frozen": False,
            "replicate": 0, "condition_id": cid, "run_id": cid + "-fixed",
            "policies": dict.fromkeys(AGENTS, "recorded-actions@1"),
            "seed_root": [SEED, "fixed-actions", cid], "policy_seed_root": None,
            "seed_protocol": "legacy-independent-v1", "scenario_block": None,
            "invalid_action_policy": "fail", "checkpoint_every": 0, "parent_run": None,
        })
        invariant_fields = ("action_hash", "briefing", "effort", "collective_quality",
                            "total_credit", "total_utility")
        checks = {field: fixed[field] == record[field] for field in invariant_fields}
        literals = closed_form.episode_metrics(**cell, accountability="attributable")
        checks["attributable_literal_rewards"] = all(fixed[key] == value
                                                     for key, value in literals.items())
        integrity.append({"cell_id": cid, "source_terminal_hash": record["terminal_hash"],
                          "replay_terminal_hash": fixed["terminal_hash"], "checks": checks})
        for kind, replay_path in (("behavioral", path), ("fixed-actions", fixed_path)):
            replay = replay_run(replay_path)
            replays.append({"cell_id": cid, "kind": kind, "chains_match": replay.chains_match})
    truth_controls = []
    for cell in cells():
        if cell["truth"] != "p":
            continue
        source = records[cell_id(cell)]
        flipped = records[cell_id({**cell, "truth": "q"})]
        quality_sum = source["collective_quality"] + flipped["collective_quality"]
        checks = {"observations_equal": source["observation_hash"] == flipped["observation_hash"],
                  "actions_equal": source["action_hash"] == flipped["action_hash"],
                  "opposite_quality": quality_sum == 0,
                  "equal_effort": source["effort"] == flipped["effort"]}
        truth_controls.append({"reports": cell["reports"], "rule": cell["rule"],
                               "labels": cell["labels"], "checks": checks})
    expectations = [weighted_metrics(records, model, rate, rule, labels, truth)
                    for model, rate, rule, labels, truth in itertools.product(
                        MODELS, RATES, RULES, LABELS, ("mixture", *TRUTHS))]
    result: dict[str, Any] = {
        "schema": "noisy-corpus-results-v1", "status": "exploratory-unfrozen",
        "inference": "exact expectations under declared synthetic models; no empirical prevalence",
        "study_hash": digest, "seed_protocol": PAIRED_SEED_PROTOCOL,
        "design_sha256": sha256_hex((HERE / "DESIGN.md").read_bytes()),
        "rounds_per_episode": ROUNDS, "behavioral_episodes": len(records),
        "fixed_action_episodes": len(integrity), "episodes": records,
        "probability_audits": [probability_audit(model, rate)
                               for model, rate in itertools.product(MODELS, RATES)],
        "expectations": expectations, "truth_controls": truth_controls,
        "same_action_integrity": integrity, "full_ledger_replays": replays,
        "audit_contract_foundation": validate_audit_fixture(),
    }
    result["predictions"] = predictions(result)
    return result


def predictions(result: dict[str, Any]) -> list[dict[str, Any]]:
    records = result["episodes"].values()
    rows = [row for row in result["expectations"] if row["truth_condition"] == "mixture"]

    def row(model: str, rate: str, rule: str) -> dict[str, Any]:
        return next(item for item in rows if (item["model"], item["error_rate"], item["rule"],
                                             item["labels"]) == (model, rate, rule, "distinct"))

    deltas = {rate: Fraction(row("independent", rate, "skeptical")["expected_quality"])
              - Fraction(row("independent", rate, "conditional")["expected_quality"])
              for rate in RATES}
    correlated = all(row("correlated", rate, "skeptical")[key]
                     == row("correlated", rate, "conditional")[key]
                     for rate in RATES
                     for key in row("correlated", rate, "conditional")["closed_form"])
    checks = (
        all(all(control["checks"].values()) for control in result["truth_controls"])
        and all(record["ledger_has_no_hidden_fields"] for record in records),
        all(record["oracle_schedule_matches"] and record["oracle_metrics_match"]
            for record in records),
        all(all(audit["checks"].values()) for audit in result["probability_audits"]),
        all(item["oracle_matches"] for item in result["expectations"]),
        all(deltas[rate] < 0 for rate in ("1/10", "1/4")) and deltas["3/4"] > 0
        and all(deltas[rate] == 0 for rate in ("0", "1/2", "1")),
        correlated,
        all(item["accepted_probability"] == "0" and item["selective_accuracy"] is None
            for item in rows if (item["rule"], item["labels"]) == ("skeptical", "collapsed")),
        all(all(item["checks"].values()) for item in result["same_action_integrity"])
        and all(item["chains_match"] for item in result["full_ledger_replays"]),
    )
    return [{"prediction": f"P{index}", "held": held} for index, held in enumerate(checks, 1)]


def render_report(result: dict[str, Any]) -> str:
    held = [item["prediction"] for item in result["predictions"] if item["held"]]
    failed = [item["prediction"] for item in result["predictions"] if not item["held"]]
    lines = [
        "# Noisy corpus — exact synthetic expectations", "",
        "This is an unfrozen offline scripted-policy experiment. Its complete local",
        "[design](DESIGN.md) and "
        "[ADR-0017](../../docs/adr/0017-noisy-corpus-and-audit-contract.md)",
        "precede execution. The source commit and file digests are in",
        "[SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json); every finite outcome, schedule,",
        "terminal hash and exact weighting is retained in [RESULTS.json](RESULTS.json).", "",
        f"**{result['behavioral_episodes']} behavioral episodes, "
        f"{result['fixed_action_episodes']} action-fixed accounting controls, "
        f"{len(result['full_ledger_replays'])} full ledger replays; {ROUNDS} rounds per episode.**",
        "The six error rates and two error-dependence models reweight those same outcomes.",
        "These are declared models, not estimates, extra replicates or empirical prevalence.",
        "The truth mixture assigns p and q probability 1/2 each by construction.", "",
        f"Declared predictions held: {', '.join(held) or 'none'}. "
        f"Not held: {', '.join(failed) or 'none'}.",
        "", "## Exact outcomes by rate", "",
        "C and W are probabilities of a correct or wrong accepted slot. Abstention is the",
        "probability of no accepted slot. Selective accuracy conditions on acceptance; an",
        "em dash means undefined because acceptance has probability zero. All values are exact.",
        "Effort, contribution and total utility are expectations at the declared placeholders.",
        "Behavioral expectations use aggregate accountability; attributable runs replay the same",
        "actions.",
        "", "| Error model | Labels | e | Rule | C | W | Abstention | Selective accuracy | "
        "Quality | Effort | Contribution | Total utility |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["expectations"]:
        if row["truth_condition"] != "mixture":
            continue
        lines.append(f"| {row['model']} | {row['labels']} | {row['error_rate']} | {row['rule']} | "
                     f"{row['correct_probability']} | {row['wrong_probability']} | "
                     f"{row['abstention_probability']} | {row['selective_accuracy'] or '—'} | "
                     f"{row['expected_quality']} | {row['expected_effort']} | "
                     f"{row['expected_contribution']} | {row['expected_total_utility']} |")
    lines += [
        "", "## Conditional expectations and negative controls", "",
        "RESULTS.json also retains separate p-true and q-true expectation rows. Each is checked",
        "against the closed-form oracle; their equality is a property of this symmetric synthetic",
        "design. It does not estimate real truth prevalence.", "",
        f"All {len(result['truth_controls'])} matched truth-flip pairs are checked for identical",
        "observations and typed actions, opposite signed quality and equal effort. Whole ledgers",
        "are checked for hidden truth-field keys. Correctness in the final unobserved seal is",
        "permitted; neither baseline policy receives truth during the episode.", "",
        "The independent error model has C=(1-e)^3 and W=e^3 for the distinct-label skeptic.",
        "The conditional control follows the first report: C=1-e and W=e. Thus the declared",
        "skeptical-minus-conditional quality difference is -12 e(1-e)(1-2e). Screening lowers",
        "signed quality at e=1/10 and e=1/4 despite improving selective accuracy; it discards",
        "many correct claims along with wrong ones. At e=3/4 its positive contrast means",
        "less negative quality. Effort savings and utility changes remain separate outcomes.", "",
        "With fully correlated errors, three distinct labels always agree, even when wrong.",
        "Both rules then have the same C=1-e and W=e. The marginal error rate alone does not",
        "identify the value of corroboration. Collapsing labels always silences the skeptic,",
        "including when the generator produces independent reports or perfect evidence.", "",
        "## Audit observation contract foundation", "",
        "The separately versioned `ec-audit-observation@1` contract has strict validated inputs,",
        "a deterministic public projection, fixed target/publication timing, exact declared",
        "accuracy and explicit unavailable reports. The checked fixture is in RESULTS.json.",
        "**No audit-enabled engine, audit policy, truth-feedback episode or learned behavior is",
        "implemented here.** The supplied fixture findings do not establish their accuracy.",
        "Accuracy 1 would be a perfect synthetic trusted-oracle assumption, not deployed truth.",
        "ADR-0017 lists the remaining compiler/version/hash, generator, engine/event, policy,",
        "replay/branch/leak/C3, and pre-execution experimental-design gates.", "",
        "## Scope", "",
        "This one-slot, all-active, full-reading design identifies exact outcomes only under",
        "its imposed corpus distributions and placeholders. It supplies no general benefit,",
        "optimal institution, equilibrium, social-dilemma, human or LLM claim. No weights or",
        "models were selected and no study was frozen. Existing study and experiment evidence",
        "was left unchanged. Distinct source labels are not evidence of real independence.", "",
        "## Reproduce", "", "```bash",
        "python experiments/noisy-corpus/noisy_corpus.py --out artifacts/noisy-corpus-new",
        "python experiments/noisy-corpus/noisy_corpus.py --check", "```", "",
        "`--out` requires a clean committed worktree and a fresh directory. `--check`",
        "recreates all 128 sealed runs, verifies every full replay, and byte-compares the JSON",
        "and Markdown readouts in a temporary directory. Both remain offline.", "",
        f"Study hash: `{result['study_hash']}`. The study remains unfrozen.", "",
    ]
    return "\n".join(lines)


def source_provenance() -> dict[str, Any]:
    commit, dirty = git_provenance(REPO)
    if commit is None or dirty is not False:
        raise SystemExit("recording an execution requires a clean committed worktree")
    paths = sorted([*REPO.glob("src/**/*.py"), *HERE.glob("*.py"), HERE / "DESIGN.md",
                    HERE / "AUDIT_FIXTURE.json", REPO / "requirements-lock.txt",
                    REPO / "pyproject.toml",
                    REPO / "docs/adr/0017-noisy-corpus-and-audit-contract.md"])
    return {"schema": "noisy-corpus-execution-source-v1", "local_commit": commit,
            "worktree_dirty": dirty, **environment_provenance(),
            "dependency_lock_sha256": lock_hash(REPO),
            "files_sha256": {path.relative_to(REPO).as_posix(): sha256_hex(path.read_bytes())
                             for path in paths}}


def execute(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    spec, resolved = write_inputs(root / "inputs")
    digest = study_hash(spec, resolved)
    results = run_study(root / "inputs", root / "runs")
    if any(result.status != "completed" for result in results):
        raise ValueError("execution failed; sealed failures retained in output")
    for cell in cells():
        cid = cell_id(cell)
        target = compile_scenario(scenario(cell, "attributable"), SKIN)
        fixed_action_run(run_path(root, digest, cid), target, root / "fixed-actions" / cid)
    result = collect(root)
    write_json(root / "RESULTS.json", result)
    (root / "RESULTS.md").write_text(render_report(result), encoding="utf-8", newline="\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path)
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="chl-noisy-") as temporary:
            destination = Path(temporary) / "experiment"
            result = execute(destination)
            for filename in ("RESULTS.json", "RESULTS.md"):
                if (destination / filename).read_bytes() != (HERE / filename).read_bytes():
                    raise SystemExit(f"{filename} differs from the committed readout")
        print(f"Verified {result['behavioral_episodes']} behavioral episodes, "
              f"{result['fixed_action_episodes']} fixed-action controls and "
              f"{len(result['full_ledger_replays'])} full replays; exact readout reproduced.")
    else:
        provenance = source_provenance()
        result = execute(args.out)
        write_json(args.out / "SOURCE_PROVENANCE.json", provenance)
        missed = [item["prediction"] for item in result["predictions"] if not item["held"]]
        print(f"Wrote sealed experiment to {args.out}; predictions not held: {missed}")


if __name__ == "__main__":
    main()
