"""Reservation cleanup must retain manifests and resources it cannot prove it owns."""

import os
from pathlib import Path

import pytest

from collaborative_hill.engine.store import RunPaths


@pytest.mark.parametrize("existing_root", [False, True])
def test_reservation_setup_failure_only_removes_owned_directory(
    tmp_path, monkeypatch, existing_root,
):
    paths = RunPaths(tmp_path / "run")
    if existing_root:
        paths.root.mkdir()
    mkdir = Path.mkdir

    def fail_metrics(path, *args, **kwargs):
        if path == paths.metrics:
            raise OSError("synthetic mkdir failure")
        return mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_metrics)
    with pytest.raises(OSError, match="synthetic mkdir failure"), paths.reserve():
        pytest.fail("setup should fail")
    assert paths.root.exists() == existing_root
    if existing_root:
        assert list(paths.root.iterdir()) == []

    monkeypatch.setattr(Path, "mkdir", mkdir)
    with paths.reserve():
        assert paths.events.exists()


@pytest.mark.parametrize("preserve", ["manifest", "replacement", "symlink"])
def test_failed_reservation_preserves_manifest_or_new_owner(tmp_path, preserve):
    paths = RunPaths(tmp_path / "run")
    before = {}
    with pytest.raises(ValueError, match="synthetic failure"), paths.reserve():
        if preserve == "manifest":
            paths.manifest.write_bytes(b'{"status":"running"}')
        elif preserve == "symlink":
            original = tmp_path / "original-ledger"
            paths.events.replace(original)
            try:
                paths.events.symlink_to(original)
            except OSError as exc:
                pytest.skip(f"symlinks unavailable: {exc}")
        else:
            replacement = tmp_path / "replacement"
            replacement.write_bytes(b"competing reservation")
            replacement.replace(paths.events)
        (paths.root / "scenario.resolved.json").write_bytes(b"preserve scenario")
        before = {p: p.read_bytes() for p in paths.root.rglob("*") if p.is_file()}
        raise ValueError("synthetic failure")
    assert paths.root.exists()
    assert {p: p.read_bytes() for p in paths.root.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("replace_ledger", [False, True])
def test_unidentifiable_reservation_preserves_artifacts(tmp_path, monkeypatch, replace_ledger):
    paths = RunPaths(tmp_path / "run")
    fstat = os.fstat
    stat = Path.stat

    def without_inode(record):
        fields = list(record)
        fields[1] = 0
        return os.stat_result(fields)

    def stat_without_inode(path, *args, **kwargs):
        result = stat(path, *args, **kwargs)
        return without_inode(result) if path == paths.events else result

    monkeypatch.setattr(os, "fstat", lambda fd: without_inode(fstat(fd)))
    monkeypatch.setattr(Path, "stat", stat_without_inode)
    before = {}
    with pytest.raises(ValueError, match="synthetic failure"), paths.reserve():
        if replace_ledger:
            replacement = tmp_path / "replacement"
            replacement.write_bytes(b"competing reservation")
            replacement.replace(paths.events)
        (paths.checkpoints / "ckpt-000001.json").write_bytes(b"retain checkpoint")
        (paths.root / "scenario.resolved.json").write_bytes(b"retain scenario")
        before = {p: p.read_bytes() for p in paths.root.rglob("*") if p.is_file()}
        raise ValueError("synthetic failure")

    assert paths.root.exists()
    assert {p: p.read_bytes() for p in paths.root.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("existing_root", [False, True])
def test_transient_identity_failure_releases_reservation(tmp_path, monkeypatch, existing_root):
    paths = RunPaths(tmp_path / "run")
    if existing_root:
        paths.root.mkdir()
    fstat = os.fstat
    failure = OSError("synthetic fstat failure")
    failed = False

    def fail_once(fd):
        nonlocal failed
        if not failed:
            failed = True
            raise failure
        return fstat(fd)

    monkeypatch.setattr(os, "fstat", fail_once)
    with pytest.raises(OSError) as caught, paths.reserve():
        pytest.fail("identity lookup should fail before yielding")

    assert caught.value is failure
    assert paths.root.exists() == existing_root
    if existing_root:
        assert list(paths.root.iterdir()) == []
    with paths.reserve():
        assert paths.events.exists()


@pytest.mark.parametrize("replace_ledger", [False, True])
def test_identity_failure_never_claims_a_replacement(tmp_path, monkeypatch, replace_ledger):
    paths = RunPaths(tmp_path / "run")
    fstat = os.fstat
    failure = OSError("synthetic fstat failure")
    failed = False

    def fail_identity(fd):
        nonlocal failed
        if failed and replace_ledger:
            return fstat(fd)
        if replace_ledger:
            replacement = tmp_path / "replacement"
            replacement.write_bytes(b"competing reservation")
            try:
                replacement.replace(paths.events)
            except PermissionError:
                pytest.skip("filesystem refuses replacing an open ledger")
        failed = True
        raise failure

    monkeypatch.setattr(os, "fstat", fail_identity)
    with pytest.raises(OSError) as caught, paths.reserve():
        pytest.fail("identity lookup should fail before yielding")

    assert caught.value is failure
    assert paths.events.read_bytes() == (b"competing reservation" if replace_ledger else b"")
    assert list(paths.root.iterdir()) == [paths.events]


@pytest.mark.parametrize("directory_name", ["checkpoints", "metrics"])
def test_cleanup_refuses_symlink_without_masking_failure(tmp_path, directory_name):
    paths = RunPaths(tmp_path / "run")
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "retain.json"
    sentinel.write_bytes(b"external data")
    linked = paths.root / directory_name
    failure = ValueError("synthetic failure")

    with pytest.raises(ValueError) as caught, paths.reserve():
        linked.rmdir()
        try:
            linked.symlink_to(external, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")
        raise failure

    assert caught.value is failure
    assert sentinel.read_bytes() == b"external data"
    assert linked.is_symlink()
    assert paths.events.exists()
