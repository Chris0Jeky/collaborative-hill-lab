"""The follow-up design, literal contrast arithmetic and fail-closed audit."""

import copy
import importlib.util
import itertools
import json
from pathlib import Path

import pytest
from _fixtures import step

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "experiments/ec-rule-ablation/ec_rule_ablation.py"
SPEC = importlib.util.spec_from_file_location("ec_rule_ablation", PATH)
assert SPEC and SPEC.loader
ab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ab)


def test_declared_factorial_counts_and_fixed_inputs():
    cells = ab.cells()
    assert len(cells) == 192
    assert len({ab.cell_id(c) for c in cells}) == 192
    for context, truth in itertools.product(ab.CONTEXTS, ab.TRUTHS):
        selected = [c for c in cells if c["context"] == context and c["truth"] == truth]
        assert {c["variant"] for c in selected} == {
            "".join(bits) for bits in itertools.product("01", repeat=4)}
        views = []
        for item in selected:
            raw = ab.scenario(item).model_dump(mode="json")
            raw.pop("scenario_id")
            raw.pop("cognition")
            views.append(raw)
        assert all(view == views[0] for view in views)


def test_truth_pair_changes_only_hidden_fields():
    for context, variant in itertools.product(ab.CONTEXTS, ("0000", "1111")):
        good = ab.scenario({"context": context, "truth": "accurate", "variant": variant})
        bad = ab.scenario({"context": context, "truth": "misleading", "variant": variant})
        left, right = good.model_dump(mode="json"), bad.model_dump(mode="json")
        for raw in (left, right):
            raw.pop("scenario_id")
            raw["world"].pop("true_propositions")
            for evidence in raw["information"]["evidence"]:
                evidence.pop("truth_aligned")
        assert left == right


def test_unknown_cells_and_variants_fail_before_execution():
    for override in ({"context": "typo"}, {"truth": "unknown"}, {"variant": "111"},
                     {"variant": "1112"}, {"unexpected": "field"}):
        with pytest.raises(ValueError, match="declared"):
            ab.scenario({"context": "echo-private", "truth": "accurate",
                         "variant": "0000", **override})


def test_interaction_arithmetic_has_literal_signed_terms_and_no_averaging():
    # Four-factor response 2S + 3H + 5SH + 7SHC; no R dependence.
    records = {}
    for item in ab.cells():
        s, h, c, _ = map(int, item["variant"])
        value = 2 * s + 3 * h + 5 * s * h + 7 * s * h * c
        records[ab.cell_id(item)] = {
            "cell": item, "action_hash": "constant", "collective_quality": value,
            "contribution_fraction": "1/2", "total_effort": 10,
            "total_credit": "0", "total_utility": "-1/3", "accepted_slots": 1,
        }
    contrasts = ab.factorial_contrasts(records)
    assert len(contrasts) == 780
    assert sum(len(row["factors"]) == 1 for row in contrasts) == 384
    assert sum(len(row["factors"]) > 1 for row in contrasts) == 396
    rows = {r["factors"] + r["background"]: r for r in contrasts
            if r["context"] == "echo-private" and r["truth"] == "accurate"}
    assert rows["SH--00"]["deltas"]["quality"] == "5"
    assert rows["SH--10"]["deltas"]["quality"] == "12"
    assert rows["SHC---0"]["deltas"]["quality"] == "7"
    assert rows["SHCR----"]["deltas"]["quality"] == "0"
    assert rows["SH--00"]["terms"] == [
        {"cell_id": "ep-a-0000", "coefficient": 1},
        {"cell_id": "ep-a-0100", "coefficient": -1},
        {"cell_id": "ep-a-1000", "coefficient": -1},
        {"cell_id": "ep-a-1100", "coefficient": 1},
    ]
    assert all(r["deltas"]["contribution"] == "0" for r in contrasts)
    assert all(r["deltas"]["quality"] == "0" for r in contrasts if "R" in r["factors"])


def test_hand_predictions_transcribe_the_preexecution_table():
    for variant in ("0000", "1111"):
        assert ab.readout.expected_outcome("corroborated-private", variant) == (2, 48, 14, "13/14")
    assert ab.readout.expected_outcome("conflicted-private", "1000") == (1, 26, 5, "4/7")
    assert ab.readout.expected_outcome("conflicted-private", "1010") == (0, 30, 0, "2/3")
    assert ab.readout.expected_outcome("conflicted-private", "0010") == (2, 40, 14, "11/14")
    assert ab.readout.expected_outcome("defender-private", "0110") == (1, 47, 7, "20/21")
    assert ab.readout.expected_outcome("unread-private", "1110") == (1, 10, 5, "3/14")
    assert ab.readout.expected_outcome("unread-private", "1111") == (0, 8, 0, "4/21")


@pytest.mark.parametrize("context,variant,quality,effort,tail", [
    ("conflicted-private", "1000", 12, {"a1": 10, "a2": 10, "a3": 6},
     ["withhold"] * 7),
    ("conflicted-private", "1010", 0, {"a1": 10, "a2": 10, "a3": 10},
     ["challenge_claim"] * 4 + ["withhold"] * 3),
    ("conflicted-private", "0010", 24, {"a1": 12, "a2": 12, "a3": 16},
     ["challenge_claim"] * 4 + ["verify_claim"] * 3),
    ("defender-private", "0110", 12, {"a1": 16, "a2": 16, "a3": 15},
     ["inspect_evidence", "propose_claim", *["challenge_claim"] * 4, "verify_claim"]),
])
def test_t2_t3_literal_challenge_and_quorum_traces(context, variant, quality, effort, tail):
    item = {"context": context, "truth": "accurate", "variant": variant}
    resolved = ab.compile_scenario(ab.scenario(item), ab.SKIN)
    mechanism, policies = resolved.build_mechanism(), ab.build_policies(resolved)
    state = mechanism.initial_state()
    schedule = []
    while not mechanism.is_terminal(state):
        actions = {a: policies[a].propose(mechanism.observe(state, a), None).action
                   for a in ab.AGENTS}
        assert all(mechanism.validate_action(state, a, action) is None
                   for a, action in actions.items())
        schedule.append(actions)
        state = step(mechanism, state, actions)[0]
    assert [row["a3"].type for row in schedule[7:]] == tail
    rewards = mechanism.final_rewards(state)
    assert rewards["collective_quality"] == quality
    assert rewards["effort"] == effort
    if context == "conflicted-private":
        assert schedule[9]["a1"].type == "withhold"
        assert schedule[9]["a2"].type == "withhold"
    if variant == "0010":
        assert schedule[12]["a1"].claim_id == "c4"
        assert schedule[12]["a2"].claim_id == "c3"


def test_changed_saved_inputs_fail_before_reading_any_runs(tmp_path):
    ab.write_inputs(tmp_path / "inputs")
    source = tmp_path / "inputs/scenarios/cp-a-0000.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    raw["world"]["params"]["cost_inspect"] = 2
    source.write_text(json.dumps(raw), encoding="utf-8", newline="\n")
    with pytest.raises(ValueError, match="saved inputs differ"):
        ab.collect(tmp_path)


@pytest.fixture(scope="module")
def one_run(tmp_path_factory):
    destination = tmp_path_factory.mktemp("ec-ablation") / "inputs"
    study, resolved = ab.write_inputs(destination)
    item = {"context": "unread-private", "truth": "accurate", "variant": "0000"}
    cid = ab.cell_id(item)
    runs = destination.parent / "runs"
    ab.run_study(destination, runs, only_condition=cid)
    digest = ab.study_hash(study, resolved)
    path = ab.run_path(destination.parent, digest, cid)
    return item, path, resolved[cid], ab.behavior_manifest(study, digest, item)


def test_record_binds_literal_schedule_rewards_and_replay(one_run):
    item, path, expected, manifest = one_run
    record = ab.episode_record(path, expected, manifest, item)
    assert record["collective_quality"] == 12
    assert record["total_effort"] == 10
    assert record["total_credit"] == "5"
    assert record["total_utility"] == "7"
    assert record["contribution_fraction"] == "3/14"
    assert record["action_counts"] == {
        "inspect_evidence": 4, "share_evidence": 3, "propose_claim": 1,
        "verify_claim": 1, "withhold": 33,
    }
    assert record["replay_verified"] is True
    assert record["endpoint_bridge"]["actions_equal"] is True
    assert record["actions"][14] == {
        "round": 4, "agent": "a3", "action": {"type": "verify_claim", "claim_id": "c1"}}


def test_audit_rejects_mislabeled_or_swapped_cells(one_run):
    item, path, expected, manifest = one_run
    for key, wrong in (("study_hash", "0" * 64), ("condition_id", "other"),
                       ("policies", {}), ("seed_root", [0]), ("scenario_block", "other")):
        changed = {**manifest, key: wrong}
        with pytest.raises(ValueError, match="unexpected manifest"):
            ab.episode_record(path, expected, changed, item)
    altered = ab.compile_scenario(ab.scenario({**item, "variant": "1111"}), ab.SKIN)
    with pytest.raises(ValueError, match="scenario identity"):
        ab.episode_record(path, altered, manifest, item)


def test_fixed_actions_preserve_task_under_aggregate(one_run, tmp_path):
    item, source, _, _ = one_run
    target = ab.compile_scenario(ab.scenario(item, accountability="aggregate"), ab.SKIN)
    path = tmp_path / "fixed"
    ab.fixed_action_run(source, target, path)
    record = ab.episode_record(path, target, ab.fixed_manifest(item, target), item, fixed=True)
    assert record["collective_quality"] == 12
    assert record["effort"] == {"a1": 4, "a2": 0, "a3": 6}
    assert record["total_utility"] == "7"
    assert record["individual_credit"] == dict.fromkeys(("a1", "a2", "a3"), "5/3")
    assert record["replay_verified"] is True


def test_prediction_misses_remain_visible_without_rewriting_expected_values():
    expected = (1, 10, 5, "3/14")
    record = {"cell": {"context": "unread-private", "variant": "0000", "truth": "accurate"},
              "accepted_slots": 1, "total_effort": 10, "total_credit": "5",
              "collective_quality": 12, "total_utility": "7", "contribution_fraction": "3/14"}
    assert ab.readout.outcome_prediction(record)["held"] is True
    changed = copy.deepcopy(record)
    changed["collective_quality"] = 0
    missed = ab.readout.outcome_prediction(changed)
    assert missed["held"] is False
    assert missed["expected"]["quality"] == 12
    assert missed["actual"]["quality"] == 0
    assert ab.readout.expected_outcome("unread-private", "0000") == expected
