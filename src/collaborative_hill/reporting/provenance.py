"""Validate optional ancestry fields before using them in a reporting projection."""

from typing import Any

from collaborative_hill.engine.events import ChainError, Event


def display_fork_seq(events: list[Event], manifest: dict[str, Any]) -> int | None:
    """Return a display boundary only for an already load_run-validated branch.

    The core loader permits unused extra fields on ordinary root manifests.
    Reporting must not promote an unbound root ``fork_seq`` into inherited
    history. This extra projection guard does not change the loader or legacy
    comparison JSON contract, and does not replace branch.json validation.
    """
    parent, fork = manifest.get("parent_run"), manifest.get("fork_seq")
    if parent is None:
        if fork is not None:
            raise ChainError("fork_seq requires a recorded parent_run for ancestry display")
        return None
    if not isinstance(parent, str) or not parent:
        raise ChainError("parent_run must be a nonempty string for ancestry display")
    if type(fork) is not int or not 0 <= fork < len(events) - 1:
        raise ChainError("invalid fork_seq for ancestry display")
    if (events[fork].run_id != parent
            or events[fork + 1].run_id != manifest.get("run_id")):
        raise ChainError("fork_seq does not identify the recorded parent/child boundary")
    return fork
