"""Reservation cleanup must retain manifests and competing writers' artifacts."""

from pathlib import Path

import pytest

from collaborative_hill.engine.store import RunPaths


def test_reservation_setup_failure_removes_owned_directory(tmp_path, monkeypatch):
    paths = RunPaths(tmp_path / "run")
    mkdir = Path.mkdir

    def fail_metrics(path, *args, **kwargs):
        if path == paths.metrics:
            raise OSError("synthetic mkdir failure")
        return mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_metrics)
    with pytest.raises(OSError, match="synthetic mkdir failure"), paths.reserve():
        pytest.fail("setup should fail")
    assert not paths.root.exists()


@pytest.mark.parametrize("preserve", ["manifest", "replacement"])
def test_failed_reservation_preserves_manifest_or_new_owner(tmp_path, preserve):
    paths = RunPaths(tmp_path / "run")
    before = {}
    with pytest.raises(ValueError, match="synthetic failure"), paths.reserve():
        if preserve == "manifest":
            paths.manifest.write_bytes(b'{"status":"running"}')
        else:
            replacement = tmp_path / "replacement"
            replacement.write_bytes(b"competing reservation")
            replacement.replace(paths.events)
        (paths.root / "scenario.resolved.json").write_bytes(b"preserve scenario")
        before = {p: p.read_bytes() for p in paths.root.rglob("*") if p.is_file()}
        raise ValueError("synthetic failure")
    assert paths.root.exists()
    assert {p: p.read_bytes() for p in paths.root.rglob("*") if p.is_file()} == before
