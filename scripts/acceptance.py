"""Acceptance scenarios A-K, executed end-to-end. Exit 0 iff all pass.

Each scenario is self-contained (fresh tmp artifacts where it runs anything).
K exercises the clean-start path: fresh artifacts root, validate + run both
studies (1 replicate) + reports. The full test suites cover these properties
in more depth; this script is the single executable demonstration.
"""

import json
import shutil
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.domain.actions import (  # noqa: E402
    CooperateAction,
    DefectAction,
    PairwiseVoteAction,
)
from collaborative_hill.domain.world.nipd import (  # noqa: E402
    NIPDMechanism,
    NIPDParams,
)
from collaborative_hill.engine.branching import branch_run  # noqa: E402
from collaborative_hill.engine.replay import replay_run  # noqa: E402
from collaborative_hill.engine.runner import RunConfig, run_episode  # noqa: E402
from collaborative_hill.engine.seeds import rng_for  # noqa: E402
from collaborative_hill.engine.store import FileEventStore, RunPaths  # noqa: E402
from collaborative_hill.experiments.scenario import (  # noqa: E402
    NarrativeSkin,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import (  # noqa: E402
    build_policies,
    run_study,
    validate_study,
)
from collaborative_hill.reporting import run_report, study_report  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def record(scenario: str, ok: bool, detail: str) -> None:
    RESULTS.append((scenario, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'} [{scenario}] {detail}")


# hand-derived N=3 oracle (independent of the engine)
PAIRWISE_ORACLE = {
    ("C", "C", "C"): (6, 6, 6), ("C", "C", "D"): (3, 3, 10),
    ("C", "D", "C"): (3, 10, 3), ("D", "C", "C"): (10, 3, 3),
    ("C", "D", "D"): (0, 6, 6), ("D", "C", "D"): (6, 0, 6),
    ("D", "D", "C"): (6, 6, 0), ("D", "D", "D"): (2, 2, 2),
}
NEIGHBOURHOOD_ORACLE = {
    ("C", "C", "C"): (3, 3, 3),
    ("C", "C", "D"): (Fraction(3, 2), Fraction(3, 2), 5),
    ("C", "D", "C"): (Fraction(3, 2), 5, Fraction(3, 2)),
    ("D", "C", "C"): (5, Fraction(3, 2), Fraction(3, 2)),
    ("C", "D", "D"): (0, 3, 3), ("D", "C", "D"): (3, 0, 3),
    ("D", "D", "C"): (3, 3, 0), ("D", "D", "D"): (1, 1, 1),
}


def nipd_scenario(mode: str, policies: list[dict], rounds: int = 20) -> ScenarioSpec:
    return ScenarioSpec.model_validate({
        "scenario_id": f"acc-{mode}",
        "world": {"kind": "nipd", "mode": mode, "rounds": rounds},
        "interaction": {"structure": mode},
        "cognition": {"agents": [
            {"agent_id": f"a{i+1}", "policy": p} for i, p in enumerate(policies)
        ]},
    })


def scenario_a() -> None:
    agents = ["a1", "a2", "a3"]
    ok, checked = True, 0
    for mode, oracle in (("pairwise", PAIRWISE_ORACLE), ("neighbourhood", NEIGHBOURHOOD_ORACLE)):
        mech = NIPDMechanism(agent_ids=agents, mode=mode, params=NIPDParams(), rounds=1)
        for profile, expected in oracle.items():
            state = mech.initial_state()
            actions = {}
            for agent, move in zip(agents, profile, strict=True):
                if mode == "pairwise":
                    actions[agent] = PairwiseVoteAction(
                        moves={o: move for o in agents if o != agent})
                else:
                    actions[agent] = CooperateAction() if move == "C" else DefectAction()
            new_state, _ = mech.resolve(state, actions, rng_for(0))
            got = tuple(Fraction(new_state["scores"][a]) for a in agents)
            if got != tuple(Fraction(e) for e in expected):
                ok = False
            checked += 1
    record("A analytical mechanism", ok, f"{checked}/16 profiles match hand-derived oracle")


def scenario_bc(tmp: Path) -> None:
    results = run_study(REPO / "studies/000-legacy-reproduction", tmp / "b",
                        only_condition="pw-2tft-alld", replicates_override=2)
    ok_b = all(r.status == "completed" for r in results)
    study_dirs = list((tmp / "b").iterdir())
    run_dir = sorted((study_dirs[0] / "pw-2tft-alld").iterdir())[0]
    report_path = run_report(run_dir)
    study_report(study_dirs[0])
    record("B scripted legacy study", ok_b and report_path.exists(),
           f"{len(results)} runs completed, report generated")
    # C: replay the sealed run AND run the same sealed spec twice
    rep = replay_run(run_dir)
    r2 = run_study(REPO / "studies/000-legacy-reproduction", tmp / "c",
                   only_condition="pw-2tft-alld", replicates_override=2)
    twice_equal = [a.final_event_hash for a in results] == [b.final_event_hash for b in r2]
    record("C replay", rep.chains_match and twice_equal,
           f"ledger replay match={rep.chains_match}; independent rerun chains equal={twice_equal}")


def scenario_d(tmp: Path) -> None:
    skin = NarrativeSkin(skin_id="plain")
    base = nipd_scenario("pairwise", [{"name": "tft_pairwise"}, {"name": "tft_pairwise"},
                                      {"name": "alld"}])
    renamed = ScenarioSpec.model_validate(json.loads(
        base.model_dump_json().replace("a1", "z9").replace("a2", "z1").replace("a3", "z5")))
    outs = []
    for tag, spec in (("base", base), ("perm", renamed)):
        resolved = compile_scenario(spec, skin)
        paths = RunPaths(tmp / f"d-{tag}").create()
        res = run_episode(mechanism=resolved.build_mechanism(),
                          policies=build_policies(resolved),
                          config=RunConfig(study_id="acc", run_id=tag, seed_root=(5, "d", 0)),
                          paths=paths)
        outs.append(sorted(Fraction(v) for v in res.summary["scores"].values()))
    record("D agent permutation", outs[0] == outs[1],
           f"score multisets equal: {[str(x) for x in outs[0]]}")


def scenario_e() -> None:
    spec = ScenarioSpec.model_validate_json(
        (REPO / "studies/001-evidence-commons/scenarios/attr-ledger.json").read_text())
    skin_a = NarrativeSkin.model_validate_json(
        (REPO / "studies/001-evidence-commons/skins/official-briefing.json").read_text())
    skin_b = NarrativeSkin.model_validate_json(
        (REPO / "studies/001-evidence-commons/skins/newsroom-desk.json").read_text())
    ra, rb = compile_scenario(spec, skin_a), compile_scenario(spec, skin_b)
    record("E narrative isolation",
           ra.mechanism_hash == rb.mechanism_hash and ra.narrative_hash != rb.narrative_hash,
           f"mechanism {ra.mechanism_hash[:10]} identical; narratives differ")


def scenario_f(tmp: Path) -> None:
    run_study(REPO / "studies/000-legacy-reproduction", tmp / "f",
              only_condition="nb-2ptft-alld-incself", replicates_override=1)
    study_dir = next((tmp / "f").iterdir())
    parent = sorted((study_dir / "nb-2ptft-alld-incself").iterdir())[0]
    from collaborative_hill.engine.store import FileCheckpointStore

    seqs = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()
    fork = seqs[0]
    from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy

    child = tmp / "f-child"
    result, manifest = branch_run(
        parent_dir=parent, fork_seq=fork, child_dir=child, child_run_id="f-branch",
        policy_overrides={"a3": build_nipd_policy("allc", "neighbourhood", {})},
    )
    parent_lines = RunPaths(parent).events.read_text(encoding="utf-8").splitlines()
    child_lines = RunPaths(child).events.read_text(encoding="utf-8").splitlines()
    prefix_ok = parent_lines[: fork + 1] == child_lines[: fork + 1]
    events = FileEventStore(RunPaths(child).events).load_all(verify=True)
    binding_ok = events[fork + 1].parent_hash == manifest.parent_event_hash_at_fork
    record("F branch", prefix_ok and binding_ok and result.status == "completed",
           f"fork@{fork}: byte-identical prefix={prefix_ok}, parent-hash binding={binding_ok}")


def scenario_g(tmp: Path) -> None:
    run_study(REPO / "studies/001-evidence-commons", tmp / "g",
              only_condition="agg-priv", replicates_override=1)
    study_dir = next((tmp / "g").iterdir())
    run_dir = sorted((study_dir / "agg-priv").iterdir())[0]
    events = FileEventStore(RunPaths(run_dir).events).load_all()
    boundary_ok, truth_ok = True, True
    raw = RunPaths(run_dir).events.read_text(encoding="utf-8")
    for needle in ("truth_aligned", "true_propositions"):
        if needle in raw:
            truth_ok = False
    for ev in events:
        if ev.event_type.value != "ObservationIssued":
            continue
        obs = ev.payload["observation"]
        visible = {e["evidence_id"] for e in obs["evidence"]}
        # e02 initially held only by a2 (private topology): a1 must not see it round 0
        if obs["round"] == 0 and obs["self_id"] == "a1" and "e02" in visible:
            boundary_ok = False
    record("G information boundary", boundary_ok and truth_ok,
           f"private evidence invisible cross-agent={boundary_ok}; no truth fields={truth_ok}")


def scenario_h(tmp: Path) -> None:
    run_study(REPO / "studies/001-evidence-commons", tmp / "h",
              only_condition="attr-ledger", replicates_override=1)
    study_dir = next((tmp / "h").iterdir())
    run_dir = sorted((study_dir / "attr-ledger").iterdir())[0]
    events = FileEventStore(RunPaths(run_dir).events).load_all()
    completed = [e for e in events if e.event_type.value == "RunCompleted"]
    ok = bool(completed)
    detail_parts = []
    for entry in completed[0].payload.get("briefing", []):
        if entry.get("claim_id") is None:
            continue
        if entry.get("provenance_ok") is None:
            ok = False
        detail_parts.append(f"{entry['slot_id']}:prov_ok={entry.get('provenance_ok')}")
    record("H provenance", ok, "accepted claims carry explicit provenance flags: "
           + ", ".join(detail_parts))


def scenario_i(tmp: Path) -> None:
    # An llm_fake agent inspects the injection fixture e08; its rendered prompt
    # contains the malicious text, and the world remains rule-bound throughout.
    spec_data = json.loads(
        (REPO / "studies/001-evidence-commons/scenarios/attr-ledger.json").read_text())
    script = json.dumps([
        json.dumps({"action": {"type": "inspect_evidence", "evidence_id": "e08"},
                    "justification": "reading the forwarded message"}),
    ] + [json.dumps({"action": {"type": "abstain"}, "justification": "done"})] * 11)
    spec_data["cognition"]["agents"][0]["policy"] = {
        "name": "llm_fake", "params": {"script": script}}
    spec_data["scenario_id"] = "acc-injection"
    spec = ScenarioSpec.model_validate(spec_data)
    skin = NarrativeSkin.model_validate_json(
        (REPO / "studies/001-evidence-commons/skins/official-briefing.json").read_text())
    resolved = compile_scenario(spec, skin)
    paths = RunPaths(tmp / "i").create()
    policies = build_policies(resolved)
    res = run_episode(mechanism=resolved.build_mechanism(), policies=policies,
                      config=RunConfig(study_id="acc", run_id="i", seed_root=(9, "i", 0),
                                       invalid_action_policy="abstain"),
                      paths=paths)
    llm_policy = policies["a1"]
    rendered = list(llm_policy.transcript)
    # the injection text lives in the SKIN; the transcript stores prompt hashes,
    # so re-render the post-inspection observation to confirm delivery as data:
    from collaborative_hill.agents.llm.rendering import render_prompt

    mech = resolved.build_mechanism()
    state = mech.initial_state()
    state["inspected"]["a1"] = ["e08"]
    prompt = render_prompt(mech.observe(state, "a1"), resolved.skin)
    injection_reached_model = "Ignore all previous instructions" in prompt
    chain_ok = bool(FileEventStore(paths.events).load_all(verify=True))
    record("I prompt-injection fixture",
           res.status == "completed" and injection_reached_model and chain_ok,
           f"malicious text rendered as data={injection_reached_model}; "
           f"run completed rule-bound={res.status == 'completed'}; {len(rendered)} LLM calls")


def scenario_j(tmp: Path) -> None:
    spec_data = json.loads(
        (REPO / "studies/001-evidence-commons/scenarios/attr-ledger.json").read_text())
    script = json.dumps(["THIS IS NOT JSON AT ALL"] * 4)
    spec_data["cognition"]["agents"][0]["policy"] = {
        "name": "llm_fake", "params": {"script": script, "max_retries": 1}}
    spec_data["scenario_id"] = "acc-invalid"
    spec = ScenarioSpec.model_validate(spec_data)
    skin = NarrativeSkin(skin_id="plain-acc")
    resolved = compile_scenario(spec, skin)
    # abstain policy: run continues with recorded abstention
    paths = RunPaths(tmp / "j1").create()
    res = run_episode(mechanism=resolved.build_mechanism(),
                      policies=build_policies(resolved),
                      config=RunConfig(study_id="acc", run_id="j1", seed_root=(9, "j", 0),
                                       invalid_action_policy="abstain"),
                      paths=paths)
    events = FileEventStore(paths.events).load_all()
    proposals = [e for e in events if e.event_type.value == "ActionProposed"
                 and e.payload["agent_id"] == "a1"]
    abstained = (proposals and proposals[0].payload["proposal"]["action"]["type"] == "abstain"
                 and "invalid_llm_output" in proposals[0].payload["proposal"]["action"]["reason"])
    # provider exhaustion (script runs out) later seals RunFailed — typed failure either way
    record("J invalid model action",
           bool(abstained) and res.status in ("completed", "failed"),
           f"garbage output -> typed safe abstention={bool(abstained)}; "
           f"final status={res.status} ({res.failure_reason or 'no failure'})")


def scenario_k(tmp: Path) -> None:
    fresh = tmp / "k-artifacts"
    v0 = validate_study(REPO / "studies/000-legacy-reproduction")
    v1 = validate_study(REPO / "studies/001-evidence-commons")
    r0 = run_study(REPO / "studies/000-legacy-reproduction", fresh, replicates_override=1)
    r1 = run_study(REPO / "studies/001-evidence-commons", fresh, replicates_override=1)
    ok = (all(r.status == "completed" for r in r0 + r1)
          and v0["conditions"] and v1["conditions"])
    reports = 0
    for study_dir in fresh.iterdir():
        study_report(study_dir)
        reports += 1
    record("K clean start", bool(ok) and reports == 2,
           f"validate+run from fresh root: {len(r0)}+{len(r1)} runs, {reports} study reports")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="chl-acceptance-"))
    try:
        scenario_a()
        scenario_bc(tmp)
        scenario_d(tmp)
        scenario_e()
        scenario_f(tmp)
        scenario_g(tmp)
        scenario_h(tmp)
        scenario_i(tmp)
        scenario_j(tmp)
        scenario_k(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failures = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failures)}/{len(RESULTS)} acceptance scenarios pass")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
