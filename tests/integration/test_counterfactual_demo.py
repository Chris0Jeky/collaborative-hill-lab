"""The offline tutorial runs real studies without changing their source inputs."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


def test_counterfactual_demo_is_end_to_end_and_refuses_existing_output(tmp_path):
    before = {str(p): p.read_bytes() for p in (ROOT / 'studies').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts}
    output = tmp_path / 'demo'
    command = [sys.executable, str(ROOT / 'scripts' / 'counterfactual_demo.py'),
               '--out', str(output)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            timeout=45, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((output / 'summary.json').read_text())
    assert summary['scope'] == 'offline_counterfactual_demonstration'
    assert set(summary['mechanisms']) == {'nipd', 'evidence_commons'}
    for entry in summary['mechanisms'].values():
        assert set(entry['replays']) == {'parent', 'child', 'grandchild'}
        assert all(report['chains_match'] for report in entry['replays'].values())
        assert entry['parent_to_child']['replay_verified'] is True
        assert entry['parent_to_child']['first_action_difference'] is not None
        assert entry['child_to_grandchild']['replay_verified'] is True
        assert entry['child_to_grandchild']['first_action_difference'] is None
        assert set(entry['child_to_grandchild']['utility_delta'].values()) == {'0'}
    assert (output / 'README.md').is_file()
    snapshot = {str(p): p.read_bytes() for p in output.rglob('*') if p.is_file()}
    repeat = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            timeout=45, check=False)
    assert repeat.returncode == 2
    assert 'exist' in repeat.stderr.lower()
    assert snapshot == {str(p): p.read_bytes() for p in output.rglob('*') if p.is_file()}
    assert all(Path(p).read_bytes() == data for p, data in before.items())
