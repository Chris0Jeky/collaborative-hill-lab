import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest  # noqa: E402

from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy  # noqa: E402
from collaborative_hill.engine.branching import branch_run  # noqa: E402
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths  # noqa: E402
from collaborative_hill.experiments.study import run_study  # noqa: E402

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]
CONDITION = "nb-2ptft-alld-incself"
GUARDED = ("events.jsonl", "manifest.json", "branch.json")


def _make_parent(tmp_path: Path) -> tuple[Path, int]:
    run_study(
        REPO_ROOT / "studies/000-legacy-reproduction",
        tmp_path / "art",
        only_condition=CONDITION,
        replicates_override=1,
    )
    (parent,) = sorted(p.parent for p in (tmp_path / "art").rglob("events.jsonl"))
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    return parent, fork


def _override():
    return {"a3": build_nipd_policy("allc", "neighbourhood", {})}


def test_branch_into_existing_run_is_refused(tmp_path: Path) -> None:
    parent, fork = _make_parent(tmp_path)
    child = tmp_path / "child"
    branch_run(
        parent_dir=parent,
        fork_seq=fork,
        child_dir=child,
        child_run_id="guard-child",
        policy_overrides=_override(),
    )
    before = {name: (child / name).read_bytes() for name in GUARDED}
    with pytest.raises(FileExistsError):
        branch_run(
            parent_dir=parent,
            fork_seq=fork,
            child_dir=child,
            child_run_id="guard-child-retry",
            policy_overrides=_override(),
        )
    for name, data in before.items():
        assert (child / name).read_bytes() == data


def test_branch_into_parent_dir_is_refused(tmp_path: Path) -> None:
    parent, fork = _make_parent(tmp_path)
    before = (parent / "events.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        branch_run(
            parent_dir=parent,
            fork_seq=fork,
            child_dir=parent,
            child_run_id="guard-parent",
            policy_overrides=_override(),
        )
    assert (parent / "events.jsonl").read_bytes() == before


def test_branch_into_empty_existing_dir_is_accepted(tmp_path: Path) -> None:
    parent, fork = _make_parent(tmp_path)
    child = tmp_path / "empty-child"
    child.mkdir()
    result, _ = branch_run(
        parent_dir=parent,
        fork_seq=fork,
        child_dir=child,
        child_run_id="guard-empty",
        policy_overrides=_override(),
    )
    assert result.status == "completed"
    assert (child / "events.jsonl").exists()
