"""Exports keep a fresh leaf in the validated directory, including namespace races."""

import os
import struct
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

import pytest

from collaborative_hill.reporting import export
from collaborative_hill.reporting.export import write_new_text


def _directory_alias(alias, target):
    if sys.platform == "win32":
        # Junctions need no symlink privilege, so Windows CI exercises the alias
        # checks instead of skipping them on machines without Developer Mode.
        subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(target)],
                       check=True, capture_output=True)
    else:
        alias.symlink_to(target, target_is_directory=True)


def _windows_set_junction_in_place(path, target):
    """Use attribute-only access: sharing locks do not exclude this mutation."""
    import ctypes
    from ctypes import wintypes

    api = export._WindowsDirectories()
    handle = api.open(str(path), 0x100, 7, None, 3, 0x02200000, None)  # FILE_WRITE_ATTRIBUTES
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    substitute = ("\\??\\" + str(target)).encode("utf-16-le")
    display = str(target).encode("utf-16-le")
    names = substitute + b"\0\0" + display + b"\0\0"
    data = struct.pack("<IHHHHHH", 0xA0000003, 8 + len(names), 0,
                       0, len(substitute), len(substitute) + 2, len(display)) + names
    ioctl = ctypes.WinDLL("kernel32", use_last_error=True).DeviceIoControl
    ioctl.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                      wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
                      wintypes.LPVOID]
    ioctl.restype = wintypes.BOOL
    returned = wintypes.DWORD()
    buffer = ctypes.create_string_buffer(data)
    try:
        if not ioctl(handle, 0x900A4, buffer, len(data), None, 0, ctypes.byref(returned), None):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        api.close(handle)


def test_export_creates_nested_parents_and_fixed_utf8_bytes(tmp_path):
    out = tmp_path / "missing" / "nested" / "report.html"
    write_new_text(out, [], lambda: "caf\u00e9\nline two\n")
    assert out.read_bytes() == b"caf\xc3\xa9\nline two\n"


def test_existing_leaf_is_rejected_before_rendering(tmp_path):
    out = tmp_path / "report.html"
    out.write_bytes(b"existing")
    with pytest.raises(FileExistsError, match="already exists"):
        write_new_text(out, [], lambda: pytest.fail("must not render an existing destination"))
    assert out.read_bytes() == b"existing"


def test_export_preserves_hardlinked_evidence(tmp_path):
    run = tmp_path / "evidence"
    run.mkdir()
    source = run / "events.jsonl"
    source.write_bytes(b"sealed source\n")
    alias = tmp_path / "report.html"
    alias.hardlink_to(source)
    with pytest.raises(FileExistsError):
        write_new_text(alias, [run], lambda: "report")
    assert alias.read_bytes() == source.read_bytes() == b"sealed source\n"


def test_export_rejects_evidence_directory_alias_before_creating_parents(tmp_path):
    run = tmp_path / "evidence"
    run.mkdir()
    alias = tmp_path / "alias"
    _directory_alias(alias, run)
    with pytest.raises(ValueError, match="outside every run"):
        write_new_text(alias / "nested" / "new.html", [run], lambda: "report")
    assert list(run.iterdir()) == []


def test_export_accepts_existing_parent_alias_outside_evidence(tmp_path):
    parent = tmp_path / "reports"
    parent.mkdir()
    alias = tmp_path / "alias"
    _directory_alias(alias, parent)
    write_new_text(alias / "nested" / "new.html", [], lambda: "report")
    assert (parent / "nested" / "new.html").read_text(encoding="utf-8") == "report"


@pytest.mark.parametrize("target_exists", [False, True])
def test_export_never_resolves_a_leaf_symlink(tmp_path, target_exists):
    target = tmp_path / "source.txt"
    if target_exists:
        target.write_bytes(b"source bytes")
    out = tmp_path / "report.html"
    try:
        out.symlink_to(target)
    except OSError:
        pytest.skip("file symlinks require privileges on this platform")
    with pytest.raises(FileExistsError):
        write_new_text(out, [], lambda: "report")
    assert out.is_symlink()
    assert target.exists() is target_exists
    if target_exists:
        assert target.read_bytes() == b"source bytes"


def test_render_failure_creates_no_leaf_and_releases_directories(tmp_path):
    out = tmp_path / "parent" / "nested" / "report.html"

    def fail_render():
        raise ValueError("render failed")

    with pytest.raises(ValueError, match="render failed"):
        write_new_text(out, [], fail_render)
    assert not out.exists()
    # Windows would reject this rename if any ancestor handles leaked.
    out.parent.parent.rename(tmp_path / "released")
    assert (tmp_path / "released" / "nested").is_dir()


def test_competing_leaf_creation_preserves_winner_and_releases_directories(tmp_path):
    out = tmp_path / "parent" / "report.html"

    def render_and_create():
        out.write_bytes(b"other writer")
        return "report"

    with pytest.raises(FileExistsError):
        write_new_text(out, [], render_and_create)
    assert out.read_bytes() == b"other writer"
    out.parent.rename(tmp_path / "released")
    assert (tmp_path / "released" / "report.html").read_bytes() == b"other writer"


@pytest.mark.parametrize("replacement", ["alias", "evidence_directory"])
def test_ancestor_replacement_before_pin_is_rejected(tmp_path, monkeypatch, replacement):
    run = tmp_path / "evidence"
    run.mkdir()
    (run / "events.jsonl").write_bytes(b"sealed source\n")
    parent = tmp_path / "reports"
    parent.mkdir()
    backend = "_write_windows" if sys.platform == "win32" else "_write_posix"
    original = getattr(export, backend)

    def swap_before_pin(*args, **kwargs):
        parent.rename(tmp_path / "displaced")
        if replacement == "alias":
            _directory_alias(parent, run)
        else:
            run.rename(parent)
        return original(*args, **kwargs)

    monkeypatch.setattr(export, backend, swap_before_pin)
    with pytest.raises((OSError, ValueError)):
        write_new_text(parent / "new.html", [run],
                       lambda: pytest.fail("must not render into a substituted directory"))
    evidence = run if replacement == "alias" else parent
    assert {p.name: p.read_bytes() for p in evidence.iterdir()} == {
        "events.jsonl": b"sealed source\n",
    }


@pytest.mark.skipif(os.name != "posix", reason="POSIX feature guard")
def test_unavailable_directory_descriptors_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "supports_dir_fd", set())
    out = tmp_path / "missing" / "report.html"
    with pytest.raises(OSError, match="requires no-follow"):
        write_new_text(out, [], lambda: pytest.fail("must not render without a guard"))
    assert not out.parent.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 directory sharing guard")
@pytest.mark.parametrize("which", ["ancestor", "evidence"])
@pytest.mark.parametrize("access", [0x40000000, 0x10000])  # GENERIC_WRITE, DELETE
def test_windows_callback_cannot_open_pinned_directory_for_mutation(tmp_path, which, access):
    import ctypes

    out = tmp_path / "parent" / "nested" / "report.html"
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    protected = evidence if which == "evidence" else out.parent.parent
    api = export._WindowsDirectories()

    def mutation_handle():
        return api.open(str(protected), access, 7, None, 3, 0x02200000, None)

    def render_and_try_mutation():
        handle = mutation_handle()
        if handle != ctypes.c_void_p(-1).value:
            api.close(handle)
            pytest.fail("pinned directories must deny write and delete sharing")
        assert ctypes.get_last_error() == 32  # ERROR_SHARING_VIOLATION
        return "report"

    write_new_text(out, [evidence], render_and_try_mutation)
    assert out.read_text(encoding="utf-8") == "report"
    handle = mutation_handle()
    assert handle != ctypes.c_void_p(-1).value
    api.close(handle)


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 in-place reparse race")
def test_windows_attribute_only_reparse_during_callback_cannot_redirect_export(tmp_path):
    run = tmp_path / "evidence"
    run.mkdir()
    (run / "events.jsonl").write_bytes(b"sealed source\n")
    parent = tmp_path / "reports"
    parent.mkdir()
    attempted = []

    def render_and_reparse():
        _windows_set_junction_in_place(parent, run)
        attempted.append(True)
        return "report"

    # A no-reparse relative open may reject the changed directory. It must
    # never follow it into evidence, even if it retains the original object.
    with suppress(OSError):
        write_new_text(parent / "new.html", [run], render_and_reparse)
    assert attempted == [True]
    assert {p.name: p.read_bytes() for p in run.iterdir()} == {"events.jsonl": b"sealed source\n"}


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 nested-parent reparse race")
def test_windows_reparse_before_nested_parent_creation_cannot_redirect(tmp_path, monkeypatch):
    run = tmp_path / "evidence"
    run.mkdir()
    parent = tmp_path / "reports"
    parent.mkdir()
    original = export._WindowsDirectories.child
    attempted = []

    def reparse_then_create(self, name, handle, *, directory):
        if name == "nested":
            _windows_set_junction_in_place(parent, run)
            attempted.append(True)
        return original(self, name, handle, directory=directory)

    monkeypatch.setattr(export._WindowsDirectories, "child", reparse_then_create)
    with suppress(OSError):
        write_new_text(parent / "nested" / "new.html", [run], lambda: "report")
    assert attempted == [True]
    assert list(run.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 file-name aliases")
@pytest.mark.parametrize("name", ["NUL.html", "report.html:stream", "report.html.", "report.html "])
def test_windows_device_and_stream_names_are_rejected(tmp_path, monkeypatch, name):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="ordinary file names"):
        write_new_text(Path(name), [], lambda: "report")
    assert list(tmp_path.iterdir()) == []
