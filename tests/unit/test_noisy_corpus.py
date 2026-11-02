"""Independent exact masses, hand traces, and toy-model limits for issue #96."""

import importlib.util
import itertools
from fractions import Fraction
from pathlib import Path

import pytest

from collaborative_hill.engine.hashing import content_hash
from collaborative_hill.engine.seeds import rng_for
from collaborative_hill.experiments.scenario import compile_scenario
from collaborative_hill.experiments.study import build_policies

MODULE_PATH = Path(__file__).resolve().parents[2] / "experiments/noisy-corpus/noisy_corpus.py"
spec = importlib.util.spec_from_file_location("noisy_corpus_experiment", MODULE_PATH)
assert spec is not None and spec.loader is not None
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


def run_cell(cell, accountability="aggregate"):
    resolved = compile_scenario(experiment.scenario(cell, accountability), experiment.SKIN)
    mechanism = resolved.build_mechanism()
    policies = build_policies(resolved)
    state = mechanism.initial_state()
    schedule, observations = [], []
    for rnd in range(8):
        actions = {}
        for agent in ("a1", "a2", "a3"):
            observation = mechanism.observe(state, agent)
            observations.append(observation)
            action = policies[agent].propose(observation, rng_for(96, "policy", agent, rnd)).action
            assert mechanism.validate_action(state, agent, action) is None
            actions[agent] = action
            schedule.append({"round": rnd, "agent": agent,
                             "action": action.model_dump(mode="json")})
        state, _ = mechanism.resolve(state, actions, rng_for(96, "mechanism", rnd))
    assert mechanism.is_terminal(state)
    rewards = mechanism.final_rewards(state)
    nonwithhold = sum(row["action"]["type"] != "withhold" for row in schedule)
    return {**rewards, "action_schedule": schedule, "observations": observations,
            "action_hash": content_hash(schedule), "observation_hash": content_hash(observations),
            "correct_slots": sum(row.get("correct") is True for row in rewards["briefing"]),
            "wrong_slots": sum(row.get("correct") is False for row in rewards["briefing"]),
            "total_effort": sum(rewards["effort"].values()),
            "contribution_fraction": str(Fraction(nonwithhold, 24)),
            "total_credit": str(sum(map(Fraction, rewards["individual_credit"].values()))),
            "total_utility": str(sum(map(Fraction, rewards["utility"].values())))}


@pytest.fixture(scope="module")
def records():
    return {experiment.cell_id(cell): run_cell(cell) for cell in experiment.cells()}


def test_declared_grid_and_no_audit_channel():
    study, resolved = experiment.design()
    assert len(study.conditions) == len(resolved) == 64
    assert len({condition.scenario_block for condition in study.conditions}) == 32
    assert study.replicates == 1
    assert study.seed_protocol == "paired-policy-v2"
    for scenario in resolved.values():
        assert scenario.spec.institution.model_dump() == {
            "accountability": "aggregate", "evidence_topology": "shared_ledger"}
        assert "audit" not in scenario.build_mechanism().observe(
            scenario.build_mechanism().initial_state(), "a1")


@pytest.mark.parametrize("cell", experiment.cells(), ids=experiment.cell_id)
def test_full_typed_schedules_and_rewards_match_independent_hand_oracle(cell, records):
    record = records[experiment.cell_id(cell)]
    assert record["action_schedule"] == experiment.closed_form.action_schedule(
        cell["reports"], cell["rule"], cell["labels"])
    expected = experiment.closed_form.episode_metrics(**cell, accountability="aggregate")
    assert {key: record[key] for key in expected} == expected


def test_first_source_is_not_a_majority_vote_and_unanimous_false_claims_pass(records):
    # The first report p loses a two-to-one source vote but is still selected by Q.
    base = {"truth": "q", "reports": "pqq", "labels": "distinct"}
    conditional = records[experiment.cell_id({**base, "rule": "conditional"})]
    skeptical = records[experiment.cell_id({**base, "rule": "skeptical"})]
    assert conditional["collective_quality"] == -12
    assert conditional["utility"] == dict.fromkeys(("a1", "a2", "a3"), "-43/3")
    assert conditional["action_schedule"][9]["action"] == {
        "type": "propose_claim", "slot_id": "s1", "proposition_id": "p", "evidence_ids": ["e1"]}
    assert skeptical["collective_quality"] == 0
    assert skeptical["total_effort"] == 9
    unanimous_wrong = records[experiment.cell_id({**base, "reports": "ppp", "rule": "skeptical"})]
    assert unanimous_wrong["collective_quality"] == -12
    assert unanimous_wrong["total_utility"] == "-43"


def test_truth_flips_change_no_observation_or_action(records):
    for reports, rule, labels in itertools.product(experiment.REPORTS, experiment.RULES,
                                                 experiment.LABELS):
        base = {"reports": reports, "rule": rule, "labels": labels}
        first = records[experiment.cell_id({**base, "truth": "p"})]
        second = records[experiment.cell_id({**base, "truth": "q"})]
        assert first["observation_hash"] == second["observation_hash"]
        assert first["action_hash"] == second["action_hash"]
        assert first["collective_quality"] == -second["collective_quality"]
        assert not experiment.has_hidden_fields(first["observations"])


@pytest.mark.parametrize("truth,utilities", [
    ("p", {"a1": "-1", "a2": "-2", "a3": "-2"}),
    ("q", {"a1": "-15", "a2": "-14", "a3": "-14"}),
])
def test_literal_attributable_rewards_and_schedule(truth, utilities, records):
    cell = {"truth": truth, "reports": "ppp", "rule": "skeptical", "labels": "distinct"}
    attributable = run_cell(cell, "attributable")
    aggregate = records[experiment.cell_id(cell)]
    assert attributable["utility"] == utilities
    assert attributable["action_schedule"] == aggregate["action_schedule"]
    for field in ("briefing", "effort", "total_credit", "total_utility", "collective_quality"):
        assert attributable[field] == aggregate[field]


def test_hand_derived_labeled_world_masses_have_no_binomial_double_count():
    # Individual labeled worlds have these masses; binomial coefficients appear
    # only after aggregating the three distinct worlds with one or two errors.
    masses = [experiment.world_probability("p", reports, "independent", "1/4")
              for reports in ("ppp", "ppq", "pqp", "pqq", "qpp", "qpq", "qqp", "qqq")]
    assert masses == [Fraction(value, 128) for value in (27, 9, 9, 3, 9, 3, 3, 1)]
    assert sum(masses) == Fraction(1, 2)
    correlated = [experiment.world_probability("p", reports, "correlated", "1/4")
                  for reports in experiment.REPORTS]
    assert correlated == [Fraction(3, 8), 0, 0, 0, 0, 0, 0, Fraction(1, 8)]


@pytest.mark.parametrize("model,rate", list(itertools.product(experiment.MODELS, experiment.RATES)))
def test_exact_mass_normalization_truth_mixture_and_source_marginals(model, rate):
    audit = experiment.probability_audit(model, rate)
    assert audit["total_mass"] == "1"
    assert audit["truth_mass"] == {"p": "1/2", "q": "1/2"}
    assert audit["source_error_rates"] == [rate] * 3
    assert all(audit["checks"].values())
    for truth in ("p", "q"):
        for position in range(3):
            error_mass = sum(Fraction(row["mass"]) for row in audit["world_masses"]
                             if row["truth"] == truth and row["reports"][position] != truth)
            assert 2 * error_mass == Fraction(rate)


@pytest.mark.parametrize("rate,correct,wrong,accepted,accuracy,quality", [
    ("0", "1", "0", "1", "1", "12"),
    ("1/10", "729/1000", "1/1000", "73/100", "729/730", "1092/125"),
    ("1/4", "27/64", "1/64", "7/16", "27/28", "39/8"),
    ("1/2", "1/8", "1/8", "1/4", "1/2", "0"),
    ("3/4", "1/64", "27/64", "7/16", "1/28", "-39/8"),
    ("1", "0", "1", "1", "0", "-12"),
])
def test_weighted_sealed_fields_against_hand_derived_literals(
        rate, correct, wrong, accepted, accuracy, quality, records):
    row = experiment.weighted_metrics(records, "independent", rate, "skeptical", "distinct")
    assert [row[key] for key in ("correct_probability", "wrong_probability", "accepted_probability",
                                "selective_accuracy", "expected_quality")] == [
                                    correct, wrong, accepted, accuracy, quality]
    if rate == "1/4":
        assert row["expected_effort"] == "249/16"
        assert row["expected_contribution"] == "69/128"
        assert row["expected_total_credit"] == "91/32"
        assert row["expected_total_utility"] == "-251/32"


def test_every_weighted_row_matches_algebra_and_is_truth_symmetric(records):
    for model, rate, rule, labels in itertools.product(experiment.MODELS, experiment.RATES,
                                                     experiment.RULES, experiment.LABELS):
        rows = [experiment.weighted_metrics(records, model, rate, rule, labels, truth)
                for truth in ("mixture", "p", "q")]
        assert all(row["oracle_matches"] for row in rows)
        for key in rows[0]["closed_form"]:
            assert rows[0][key] == rows[1][key] == rows[2][key]


def test_correlated_errors_nullify_corroboration_and_collapsed_labels_abstain(records):
    for rate in experiment.RATES:
        conditional = experiment.weighted_metrics(records, "correlated", rate,
                                                  "conditional", "distinct")
        skeptical = experiment.weighted_metrics(records, "correlated", rate,
                                                "skeptical", "distinct")
        assert conditional["closed_form"] == skeptical["closed_form"]
        for model in experiment.MODELS:
            collapsed = experiment.weighted_metrics(records, model, rate, "skeptical", "collapsed")
            assert collapsed["accepted_probability"] == "0"
            assert collapsed["selective_accuracy"] is None
            assert collapsed["expected_quality"] == "0"
            assert collapsed["expected_effort"] == "9"


@pytest.mark.parametrize("value", [0, True, 0.1, "0.1", "2/4", "-1/2", "3/2", "1/0", "nan"])
def test_rates_reject_coercions_floats_and_noncanonical_values(value):
    with pytest.raises(ValueError):
        experiment.world_probability("p", "ppp", "independent", value)


def test_design_rejects_outside_cells_and_existing_output_is_preserved(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        experiment.scenario({"truth": "p", "reports": "ppp", "rule": "new", "labels": "distinct"})
    sentinel = tmp_path / "prior.txt"
    sentinel.write_bytes(b"original evidence\n")
    with pytest.raises(FileExistsError):
        experiment.execute(tmp_path)
    assert sentinel.read_bytes() == b"original evidence\n"
    assert list(tmp_path.iterdir()) == [sentinel]
