"""A terminal branch cannot pretend to contribute an inherited fork prefix."""

import pytest

from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.replay import replay_run
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths

from .test_counterfactual_workflow import _snapshot
from .test_counterfactual_workflow import counterfactual

__all__ = ["counterfactual"]

pytestmark = pytest.mark.metamorphic


def test_nested_terminal_fork_is_rejected_before_writes(tmp_path, counterfactual):
    parent, _, policy = counterfactual
    final = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[-1]
    child = tmp_path / 'terminal-child'
    branch_run(parent_dir=parent, fork_seq=final, child_dir=child,
               child_run_id='terminal-child', policy_overrides={'a3': policy})
    assert replay_run(child).chains_match
    inherited = FileCheckpointStore(RunPaths(child).checkpoints).list_seqs()[-1]
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match='inherited checkpoint'):
        branch_run(parent_dir=child, fork_seq=inherited, child_dir=tmp_path / 'grandchild',
                   child_run_id='grandchild', policy_overrides={'a3': policy})
    assert _snapshot(tmp_path) == before
    assert not (tmp_path / 'grandchild').exists()
