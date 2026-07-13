"""Run manifests: exact provenance for every run (ADR-0006).

Wall-clock fields, token counts, and cost are recorded when measured and are
NEVER fabricated: a manifest with tokens=None means "not measured", full stop.
"""

import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from collaborative_hill.engine.hashing import sha256_hex


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    study_id: str
    study_hash: str | None = None
    study_frozen: bool = False
    condition_id: str
    run_id: str
    replicate: int

    scenario_hash: str
    mechanism_hash: str
    narrative_hash: str
    evidence_corpus_hash: str
    institution: dict[str, Any]

    code_commit: str | None = None
    worktree_dirty: bool | None = None
    python_version: str = ""
    platform: str = ""
    dependency_lock_sha256: str | None = None

    policies: dict[str, str] = Field(default_factory=dict)
    providers: dict[str, str] = Field(default_factory=dict)
    prompt_template_hashes: dict[str, str] = Field(default_factory=dict)
    sampling: dict[str, dict[str, Any]] = Field(default_factory=dict)

    seed_root: list[str | int] = Field(default_factory=list)
    checkpoint_every: int = 0
    invalid_action_policy: str = "fail"
    scorer_versions: dict[str, str] = Field(default_factory=dict)

    # Never fabricated: None means unmeasured/unavailable.
    pricing_table_version: str | None = None
    pricing_table_date: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: str | None = None

    started_at: str | None = None
    ended_at: str | None = None
    parent_run: str | None = None
    parent_event_hash_at_fork: str | None = None
    fork_seq: int | None = None
    status: str = "running"
    failure_reason: str | None = None


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def git_provenance(repo_root: Path) -> tuple[str | None, bool | None]:
    """(commit, dirty) — fail-soft to (None, None) if git is unavailable."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True,
            text=True, check=True, timeout=10,
        ).stdout.strip()
        porcelain = subprocess.run(
            ["git", "status", "--porcelain"], cwd=repo_root, capture_output=True,
            text=True, check=True, timeout=10,
        ).stdout
        return commit, bool(porcelain.strip())
    except Exception:
        return None, None


def environment_provenance() -> dict[str, str]:
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
    }


def lock_hash(repo_root: Path) -> str | None:
    lock = repo_root / "requirements-lock.txt"
    if lock.exists():
        return sha256_hex(lock.read_bytes())
    return None


def write_manifest(manifest: RunManifest, path: Path) -> None:
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
