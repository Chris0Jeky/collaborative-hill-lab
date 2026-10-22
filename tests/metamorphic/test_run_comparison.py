"""Comparisons are descriptive, validated, deterministic, and read-only."""

import json

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.scripted.nipd_policies import AllDPolicy
from collaborative_hill.cli import app
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths
from collaborative_hill.experiments import study as study_module

from ._helpers import find_run_dirs, nipd_spec, plain_skin, write_study
from .test_counterfactual_workflow import _branch, _snapshot, counterfactual

__all__ = ["counterfactual"]

pytestmark = pytest.mark.metamorphic


def _compare(left, right, *options):
    return CliRunner().invoke(app, ['compare', str(left), str(right), *options])


def test_comparison_is_stable_read_only_and_ignores_cached_metrics(tmp_path, counterfactual):
    parent, fork, _ = counterfactual
    child = tmp_path / 'child'
    _branch(counterfactual, child)
    (parent / 'metrics' / 'metrics.json').write_text('{"forged": "ignore this cache"}')
    before = _snapshot(tmp_path)
    result = _compare(parent, child, '--verify-replay')
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data['schema_version'] == 1
    assert data['scope'] == 'descriptive_run_comparison'
    assert data['direction'] == 'right_minus_left'
    assert data['common_prefix_events'] == fork + 1
    assert data['replay_verified'] is True
    assert all(r['chains_match'] for r in data['replay_reports'].values())
    assert set(data['replay_reports']) == {'left', 'right'}
    assert data['same_kernel_streams'] is True
    assert data['right']['policy_ids']['a3'] == counterfactual[2].policy_id
    assert data['first_action_difference']['round'] >= 2
    assert 'forged' not in data['left']['metrics']
    assert data['right']['metrics']['operations']['cost_usd'] is None
    assert 'not statistical evidence' in ' '.join(data['notes'])
    assert _compare(parent, child, '--verify-replay').stdout == result.stdout
    assert _snapshot(tmp_path) == before


def test_self_comparison_has_no_action_or_utility_change(counterfactual):
    parent, _, _ = counterfactual
    result = _compare(parent, parent)
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data['replay_verified'] is False
    assert data['first_action_difference'] is None
    assert set(data['utility_delta'].values()) == {'0'}
    assert data['common_prefix_events'] == data['left']['event_count']


def test_nipd_comparison_has_hand_derived_exact_utility_deltas(tmp_path):
    directory = tmp_path / 'study'
    spec = nipd_spec((('a1', 'allc'), ('a2', 'allc'), ('a3', 'allc')), rounds=6)
    write_study(directory, study_id='oracle', seed=17, checkpoint_every=2,
                conditions=[('cell', spec, plain_skin())])
    study_module.run_study(directory, tmp_path / 'runs')
    parent, = find_run_dirs(tmp_path / 'runs')
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    child = tmp_path / 'child'
    branch_run(parent_dir=parent, fork_seq=fork, child_dir=child, child_run_id='child',
               policy_overrides={'a3': AllDPolicy('pairwise')})
    result = _compare(parent, child)
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    # R=3 per opponent; T=5, S=0. Two all-cooperate rounds precede four defecting rounds.
    assert data['left']['utilities_exact'] == {'a1': '36', 'a2': '36', 'a3': '36'}
    assert data['right']['utilities_exact'] == {'a1': '24', 'a2': '24', 'a3': '52'}
    assert data['utility_delta'] == {'a1': '-12', 'a2': '-12', 'a3': '16'}
    assert data['first_action_difference']['round'] == 2
    assert data['first_action_difference']['agent_id'] == 'a3'


def test_failed_run_has_no_outcome_comparison(tmp_path, counterfactual, monkeypatch):
    parent, _, _ = counterfactual
    original = study_module.build_policies

    def failing(resolved):
        policies = original(resolved)

        class BrokenPolicy:
            policy_id = policies['a3'].policy_id

            def propose(self, observation, rng):
                raise RuntimeError('synthetic provider outage')

        policies['a3'] = BrokenPolicy()
        return policies

    monkeypatch.setattr(study_module, 'build_policies', failing)
    study_module.run_study(tmp_path / 'study', tmp_path / 'failed')
    failed, = find_run_dirs(tmp_path / 'failed')
    result = _compare(parent, failed)
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data['right']['status'] == 'failed'
    assert set(data['right']['metrics']) == {'operations', 'metric_versions'}
    assert data['right']['utilities_exact'] is None
    assert data['utility_delta'] is None


def test_mismatched_mechanisms_are_refused_without_writes(tmp_path, counterfactual):
    parent, _, _ = counterfactual
    directory = tmp_path / 'other-study'
    write_study(directory, study_id='other', seed=19, checkpoint_every=2,
                conditions=[('other', nipd_spec((('a1', 'allc'), ('a2', 'allc')), rounds=3),
                             plain_skin())])
    study_module.run_study(directory, tmp_path / 'other-runs')
    other, = find_run_dirs(tmp_path / 'other-runs')
    before = _snapshot(tmp_path)
    result = _compare(parent, other)
    assert result.exit_code == 2
    assert 'mechanism' in result.stderr
    assert not result.stdout
    assert _snapshot(tmp_path) == before


def test_comparison_refuses_corrupt_inputs(tmp_path, counterfactual):
    parent, _, _ = counterfactual
    path = parent / 'events.jsonl'
    path.write_bytes(path.read_bytes() + b'\n')
    before = _snapshot(tmp_path)
    result = _compare(parent, parent)
    assert result.exit_code == 2
    assert 'error:' in result.stderr
    assert not result.stdout
    assert _snapshot(tmp_path) == before
