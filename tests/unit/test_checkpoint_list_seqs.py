"""list_seqs ignores stray checkpoint names."""

import json

from collaborative_hill.engine.store import FileCheckpointStore


def _save(store: FileCheckpointStore, seq: int) -> None:
    store.save(seq=seq, logical_time=seq, last_event_hash="0" * 64, state={"round": seq})


def test_list_seqs_ignores_stray_names(tmp_path):
    store = FileCheckpointStore(tmp_path / "checkpoints")
    _save(store, 10)
    (store.directory / "ckpt-manual.json").write_text(json.dumps({"note": "manual"}), encoding="utf-8")
    (store.directory / "ckpt-backup.json").write_text(json.dumps({"note": "backup"}), encoding="utf-8")
    assert store.list_seqs() == [10]


def test_list_seqs_empty_and_missing(tmp_path):
    missing = FileCheckpointStore(tmp_path / "does-not-exist" / "checkpoints")
    assert missing.list_seqs() == []

    empty_dir = tmp_path / "empty-checkpoints"
    empty_dir.mkdir()
    assert FileCheckpointStore(empty_dir).list_seqs() == []


def test_list_seqs_sorted(tmp_path):
    store = FileCheckpointStore(tmp_path / "checkpoints")
    _save(store, 10)
    _save(store, 2)
    assert store.list_seqs() == [2, 10]
