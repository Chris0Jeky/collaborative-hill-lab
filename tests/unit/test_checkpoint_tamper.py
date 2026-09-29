"""Checkpoint tamper-evidence: load rejects a state edited after sealing."""

import json

import pytest

from collaborative_hill.engine.events import ChainError
from collaborative_hill.engine.store import FileCheckpointStore


def test_load_rejects_tampered_state(tmp_path):
    store = FileCheckpointStore(tmp_path / "checkpoints")
    path = store.save(seq=0, logical_time=0, last_event_hash="0" * 64, state={"round": 0})

    record = json.loads(path.read_text(encoding="utf-8"))
    record["state"]["round"] += 1
    path.write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        encoding="utf-8",
    )

    with pytest.raises(ChainError, match="state hash mismatch"):
        store.load(0)
