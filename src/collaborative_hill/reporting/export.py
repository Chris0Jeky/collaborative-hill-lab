"""Create report files without following a changed destination ancestry.

Rendering runs while the destination directory is pinned. Both platforms create
children relative to directory handles without following reparse points/symlinks.
Windows also denies ancestor rename until writing finishes. There is no fallback
to a check-then-open pathname when those OS guarantees are unavailable.
"""

import os
import sys
from collections.abc import Callable, Iterable
from contextlib import ExitStack, suppress
from pathlib import Path

_OUTSIDE_EVIDENCE = "report output must be outside every run's evidence directory"


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _check_directory(info: os.stat_result, protected: set[tuple[int, int]]) -> None:
    if _identity(info) in protected:
        raise ValueError(_OUTSIDE_EVIDENCE)


def _check_fresh(out: Path, parent_fd: int | None = None) -> None:
    try:
        os.stat(out if parent_fd is None else out.name,
                dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise FileExistsError(f"report output already exists: {out}")


def _write_posix(out: Path, protected: set[tuple[int, int]],
                 render: Callable[[], str]) -> None:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    flags = getattr(os, "O_DIRECTORY", 0) | no_follow
    if (not getattr(os, "O_DIRECTORY", 0) or not no_follow
            or not {os.open, os.mkdir, os.stat} <= os.supports_dir_fd
            or os.stat not in os.supports_follow_symlinks):
        raise OSError("safe report export requires no-follow directory descriptors")
    with ExitStack() as stack:
        parent_fd = os.open(out.anchor, os.O_RDONLY | flags)
        stack.callback(os.close, parent_fd)
        _check_directory(os.fstat(parent_fd), protected)
        for name in out.parent.parts[1:]:
            try:
                child_fd = os.open(name, os.O_RDONLY | flags, dir_fd=parent_fd)
            except FileNotFoundError:
                # The no-follow open also validates a competing creator.
                with suppress(FileExistsError):
                    os.mkdir(name, dir_fd=parent_fd)
                child_fd = os.open(name, os.O_RDONLY | flags, dir_fd=parent_fd)
            stack.callback(os.close, child_fd)
            _check_directory(os.fstat(child_fd), protected)
            parent_fd = child_fd
        _check_fresh(out, parent_fd)
        page = render()
        fd = os.open(out.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
                     0o666, dir_fd=parent_fd)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(page)


if sys.platform == "win32":
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class _AttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    class _FileIdInfo(ctypes.Structure):
        _fields_ = [("volume", ctypes.c_ulonglong), ("identifier", ctypes.c_ubyte * 16)]

    class _UnicodeString(ctypes.Structure):
        _fields_ = [("length", wintypes.USHORT), ("capacity", wintypes.USHORT),
                    ("buffer", wintypes.LPWSTR)]

    class _ObjectAttributes(ctypes.Structure):
        _fields_ = [("length", wintypes.ULONG), ("root", wintypes.HANDLE),
                    ("name", ctypes.POINTER(_UnicodeString)), ("attributes", wintypes.ULONG),
                    ("security", wintypes.LPVOID), ("quality", wintypes.LPVOID)]

    class _IoStatusBlock(ctypes.Structure):
        _fields_ = [("status", wintypes.LPVOID), ("information", ctypes.c_size_t)]

    class _WindowsDirectories:
        """Native relative opens cover the gap left by Win32 sharing locks.

        FILE_WRITE_ATTRIBUTES bypasses sharing restrictions and can set a reparse
        point on an empty directory. RootDirectory + one-component names and
        OBJ_DONT_REPARSE therefore protect every create, including missing parents.
        See Microsoft's NtCreateFile and OBJECT_ATTRIBUTES documentation.
        """

        def __init__(self) -> None:
            api = ctypes.WinDLL("kernel32", use_last_error=True)
            self.open = api.CreateFileW
            self.open.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.HANDLE]
            self.open.restype = wintypes.HANDLE
            self.info = api.GetFileInformationByHandleEx
            self.info.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                                  wintypes.DWORD]
            self.info.restype = wintypes.BOOL
            self.close = api.CloseHandle
            self.close.argtypes = [wintypes.HANDLE]
            self.close.restype = wintypes.BOOL
            native = ctypes.WinDLL("ntdll", use_last_error=True)
            self.create = native.NtCreateFile
            self.create.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
                                    ctypes.POINTER(_ObjectAttributes),
                                    ctypes.POINTER(_IoStatusBlock), wintypes.LPVOID,
                                    wintypes.ULONG, wintypes.ULONG, wintypes.ULONG,
                                    wintypes.ULONG, wintypes.LPVOID, wintypes.ULONG]
            self.create.restype = wintypes.LONG
            self.error = native.RtlNtStatusToDosError
            self.error.argtypes = [wintypes.LONG]
            self.error.restype = wintypes.ULONG

        def pin(self, path: Path, stack: ExitStack) -> int:
            # Only the anchor and read-only evidence identity handles use paths.
            # All destination descendants are opened relative to the anchor.
            handle = self.open(str(path), 0, 0x1, None, 3, 0x02200000, None)
            if handle == ctypes.c_void_p(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            return self.directory(int(handle), stack)

        def directory(self, handle: int, stack: ExitStack) -> int:
            stack.callback(self.close, handle)
            info = _AttributeTagInfo()
            if not self.info(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            if info.attributes & 0x400 or not info.attributes & 0x10:
                raise OSError("safe report export requires ordinary directory ancestors")
            return handle

        def identity(self, handle: int) -> tuple[int, bytes]:
            info = _FileIdInfo()
            if not self.info(handle, 18, ctypes.byref(info), ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            return info.volume, bytes(info.identifier)

        def child(self, name: str, parent: int, *, directory: bool) -> int:
            buffer = ctypes.create_unicode_buffer(name)
            size = len(name.encode("utf-16-le"))
            if size > 65532:
                raise ValueError("report output component is too long")
            string = _UnicodeString(size, size + 2, ctypes.cast(buffer, wintypes.LPWSTR))
            # OBJ_CASE_INSENSITIVE | OBJ_DONT_REPARSE: no path-component reparse.
            attributes = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), parent,
                                           ctypes.pointer(string), 0x1040, None, None)
            status = _IoStatusBlock()
            handle = wintypes.HANDLE()
            # SYNCHRONIZE, FILE_READ_ATTRIBUTES for dirs / GENERIC_WRITE for files.
            access = 0x100000 | (0x80 if directory else 0x40000000)
            # FILE_OPEN_REPARSE_POINT | FILE_SYNCHRONOUS_IO_NONALERT, plus type.
            options = 0x200020 | (0x1 if directory else 0x40)
            # FILE_OPEN_IF for directories; FILE_CREATE exclusively creates a leaf.
            result = self.create(ctypes.byref(handle), access, ctypes.byref(attributes),
                                 ctypes.byref(status), None, 0x80, 0x1,
                                 3 if directory else 2, options, None, 0)
            if result < 0:
                raise ctypes.WinError(self.error(result))
            if handle.value is None:
                raise OSError("safe report export did not obtain a directory-relative handle")
            return handle.value

    def _write_windows(out: Path, evidence: tuple[Path, ...],
                       render: Callable[[], str]) -> None:
        api = _WindowsDirectories()
        with ExitStack() as stack:
            protected = {api.identity(api.pin(path, stack)) for path in evidence}
            parent = api.pin(Path(out.anchor), stack)
            if api.identity(parent) in protected:
                raise ValueError(_OUTSIDE_EVIDENCE)
            for name in out.parent.parts[1:]:
                parent = api.directory(api.child(name, parent, directory=True), stack)
                if api.identity(parent) in protected:
                    raise ValueError(_OUTSIDE_EVIDENCE)
            page = render()
            handle = api.child(out.name, parent, directory=False)
            try:
                fd = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY | os.O_NOINHERIT)
            except OSError:
                api.close(handle)
                raise
            # open_osfhandle transfers ownership; closing the stream closes HANDLE.
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(page)


def write_new_text(out: Path, evidence_dirs: Iterable[Path],
                   render: Callable[[], str]) -> None:
    """Render and exclusively create UTF-8 text outside the protected run directories.

    Existing parent aliases are canonicalized before directory handles are acquired.
    Missing parents are created through pinned ancestors. ``render`` may raise; in
    that case no report leaf is created and all handles are released. A competing
    leaf creator wins unchanged. On POSIX, an ancestor rename may move the pinned
    directory, but cannot redirect the write into the directory replacing it.
    """
    out = Path(out)
    if not out.name or out.name == "..":
        raise ValueError("report output must name a new file")
    if sys.platform == "win32":
        names = out.parts[1:] if out.anchor else out.parts
        if out.drive.startswith("\\\\.\\") or any(
                ":" in name or name.endswith((" ", ".")) or Path(name).is_reserved()
                for name in names if name not in {".", ".."}):
            raise ValueError("report output requires ordinary file names "
                             "without device/stream aliases")
    # Do not resolve the leaf: a dangling symlink is an existing leaf, not a fresh
    # filename at its target. Exclusive creation enforces this again at write time.
    target = out.parent.resolve() / out.name
    evidence = tuple(path.resolve(strict=True) for path in evidence_dirs)
    if any(target.is_relative_to(path) for path in evidence):
        raise ValueError(_OUTSIDE_EVIDENCE)
    _check_fresh(target)
    if sys.platform == "win32":
        _write_windows(target, evidence, render)
    elif os.name == "posix":
        protected = {_identity(path.stat()) for path in evidence}
        _write_posix(target, protected, render)
    else:
        raise OSError("safe report export is unavailable on this platform")
