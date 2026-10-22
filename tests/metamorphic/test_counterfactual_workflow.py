"""Counterfactuals must replay and reject unbound checkpoint state before writes."""

import json
import shutil

import pytest
from typer.testing import CliRunner

from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
from collaborative_hill.agents.scripted.nipd_policies import AllDPolicy
from collaborative_hill.cli import app
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.hashing import content_hash
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths
from collaborative_hill.experiments.study import run_study

from ._helpers import (
    default_ec_evidence,
    ec_spec,
    find_run_dirs,
    nipd_spec,
    plain_skin,
    write_study,
)

pytestmark = pytest.mark.metamorphic


def _snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.fixture(params=[('nipd', False), ('nipd', True), ('ec', False), ('ec', True)])
def counterfactual(tmp_path, request):
    kind, paired = request.param
    spec = (nipd_spec((('a1', 'random'), ('a2', 'tft_pairwise'), ('a3', 'allc')), rounds=6)
            if kind == 'nipd' else ec_spec(default_ec_evidence(), rounds=6))
    study = tmp_path / 'study'
    write_study(study, study_id='counterfactual', seed=17, checkpoint_every=2,
                conditions=[('cell', spec, plain_skin())])
    if paired:
        path = study / 'study.json'
        data = json.loads(path.read_text())
        data['seed_protocol'] = 'paired-policy-v2'
        data['conditions'][0]['scenario_block'] = 'shared'
        path.write_text(json.dumps(data))
    run_study(study, tmp_path / 'runs')
    parent, = find_run_dirs(tmp_path / 'runs')
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    policy = AllDPolicy('pairwise') if kind == 'nipd' else build_ec_policy('ec_freerider', {})
    return parent, fork, policy


def _branch(counterfactual, child, **kwargs):
    parent, fork, policy = counterfactual
    return branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
                      child_run_id=kwargs.pop('child_run_id', child.name),
                      policy_overrides=kwargs.pop('policy_overrides', {'a3': policy}), **kwargs)


def test_counterfactual_replays_without_parent_or_checkpoints(tmp_path, counterfactual):
    parent, fork, _ = counterfactual
    before = _snapshot(parent)
    child = tmp_path / 'child'
    result, _ = _branch(counterfactual, child)
    assert result.status == 'completed'
    assert _snapshot(parent) == before
    assert child.joinpath('events.jsonl').read_bytes().splitlines()[:fork + 1] == (
        parent.joinpath('events.jsonl').read_bytes().splitlines()[:fork + 1]
    )
    shutil.rmtree(parent)
    shutil.rmtree(child / 'checkpoints')
    before = _snapshot(child)
    replay = replay_run(child)
    assert replay.chains_match, replay.detail
    assert replay.original_events == replay.replayed_events == result.event_count
    assert _snapshot(child) == before


def test_nested_branch_replays_each_ancestral_segment(tmp_path, counterfactual):
    child = tmp_path / 'child'
    _branch(counterfactual, child)
    fork = FileCheckpointStore(RunPaths(child).checkpoints).list_seqs()[0]
    grandchild = tmp_path / 'grandchild'
    branch_run(parent_dir=child, fork_seq=fork, child_dir=grandchild,
               child_run_id='grandchild', policy_overrides={'a3': counterfactual[2]})
    events, _, _ = load_run(grandchild)
    assert len({event.run_id for event in events}) == 3
    assert replay_run(grandchild).chains_match


@pytest.mark.parametrize('field', ['seq', 'logical_time', 'last_event_hash', 'state'])
def test_checkpoint_must_match_sealed_boundary(tmp_path, counterfactual, field):
    parent, fork, _ = counterfactual
    checkpoint = parent / 'checkpoints' / f'ckpt-{fork:06d}.json'
    data = json.loads(checkpoint.read_text())
    if field == 'state':
        data['state']['round'] += 1
        data['state_hash'] = content_hash(data['state'])
        data['logical_time'] = data['state']['round']
    elif field == 'last_event_hash':
        data[field] = '0' * 64
    else:
        data[field] += 1
    checkpoint.write_text(json.dumps(data))
    child = tmp_path / 'rejected'
    before = _snapshot(parent)
    with pytest.raises(ValueError, match='checkpoint'):
        _branch(counterfactual, child)
    assert not child.exists()
    assert _snapshot(parent) == before


def test_new_branch_identity_must_not_reuse_parent(tmp_path, counterfactual):
    parent, _, _ = counterfactual
    child = tmp_path / 'rejected'
    parent_id = json.loads((parent / 'manifest.json').read_text())['run_id']
    with pytest.raises(ValueError, match='run.id|identity'):
        _branch(counterfactual, child, child_run_id=parent_id)
    assert not child.exists()


def test_inherited_override_is_not_silently_reset(tmp_path, counterfactual):
    child = tmp_path / 'child'
    _branch(counterfactual, child)
    fork = FileCheckpointStore(RunPaths(child).checkpoints).list_seqs()[0]
    grandchild = tmp_path / 'grandchild'
    with pytest.raises(ValueError, match='a3.*explicit|explicit.*a3'):
        branch_run(parent_dir=child, fork_seq=fork, child_dir=grandchild,
                   child_run_id='grandchild', policy_overrides={})
    assert not grandchild.exists()


def test_branch_manifest_names_the_effective_policies(tmp_path, counterfactual):
    child = tmp_path / 'child'
    _branch(counterfactual, child)
    manifest = json.loads((child / 'manifest.json').read_text())
    assert manifest['policies']['a3'] == counterfactual[2].policy_id


@pytest.mark.parametrize('field', ['event_count', 'final_event_hash', 'status'])
def test_replay_and_branch_reject_manifest_seal_drift(tmp_path, counterfactual, field):
    parent, _, _ = counterfactual
    path = parent / 'manifest.json'
    data = json.loads(path.read_text())
    data[field] = {'event_count': 1, 'final_event_hash': '0' * 64, 'status': 'failed'}[field]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='manifest|seal'):
        replay_run(parent)
    child = tmp_path / 'rejected'
    with pytest.raises(ValueError, match='manifest|seal'):
        _branch(counterfactual, child)
    assert not child.exists()


def test_replay_cli_reports_invalid_inputs_as_usage_error(tmp_path):
    result = CliRunner().invoke(app, ['replay', str(tmp_path / 'missing')])
    assert result.exit_code == 2
    assert 'error:' in result.stderr
    assert 'Traceback' not in result.stderr


def test_final_checkpoint_branch_replays(tmp_path, counterfactual):
    parent, _, policy = counterfactual
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[-1]
    child = tmp_path / 'terminal-child'
    branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
               child_run_id='terminal-child', policy_overrides={'a3': policy})
    assert replay_run(child).chains_match


def test_replay_preserves_occupied_output(tmp_path, counterfactual):
    parent, _, _ = counterfactual
    output = tmp_path / 'saved' / 'replay'
    output.mkdir(parents=True)
    (output / 'keep.txt').write_text('preserved')
    before = _snapshot(tmp_path / 'saved')
    with pytest.raises(FileExistsError):
        replay_run(parent, keep_dir=tmp_path / 'saved')
    assert _snapshot(tmp_path / 'saved') == before


def test_branch_does_not_inherit_parent_usage_measurements(tmp_path, counterfactual):
    parent, _, _ = counterfactual
    path = parent / 'manifest.json'
    data = json.loads(path.read_text())
    data.update(input_tokens=123, output_tokens=456, cost_usd='0.07')
    path.write_text(json.dumps(data))
    child = tmp_path / 'child'
    _branch(counterfactual, child)
    manifest = json.loads((child / 'manifest.json').read_text())
    for field in ('input_tokens', 'output_tokens', 'cost_usd'):
        assert manifest[field] is None


@pytest.mark.parametrize('record', [None, {}, []])
def test_malformed_checkpoint_is_a_clean_error(tmp_path, counterfactual, record):
    parent, fork, _ = counterfactual
    path = parent / 'checkpoints' / f'ckpt-{fork:06d}.json'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='checkpoint'):
        _branch(counterfactual, tmp_path / 'rejected')
    assert not (tmp_path / 'rejected').exists()


def test_malformed_branch_schema_is_a_clean_error(tmp_path, counterfactual):
    child = tmp_path / 'child'
    _branch(counterfactual, child)
    path = child / 'branch.json'
    branch = json.loads(path.read_text())
    branch['schema_version'] = 'not-a-version'
    path.write_text(json.dumps(branch))
    with pytest.raises(ValueError, match='branch.*schema'):
        replay_run(child)


def test_branch_cli_reports_missing_parent_as_usage_error(tmp_path):
    result = CliRunner().invoke(app, [
        'branch', str(tmp_path / 'missing'), '--at-event', '1',
        '--override', 'a3=alld', '--out', str(tmp_path / 'child'),
    ])
    assert result.exit_code == 2
    assert 'error:' in result.stderr
    assert not (tmp_path / 'child').exists()
