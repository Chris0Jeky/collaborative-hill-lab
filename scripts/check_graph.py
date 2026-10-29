"""Regenerate graph controls without rewriting the original execution provenance."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from collaborative_hill.engine.hashing import canonical_json, content_hash

REPO = Path(__file__).resolve().parents[1]
EXPERIMENT = REPO / "experiments/graph-topology"
SCRIPT = EXPERIMENT / "graph_experiment.py"
SOURCE_DOMAIN = "chl.graph-topology.source-files.v1"
MAPPING_DOMAIN = "chl.graph-topology.published-source-mapping.v1"
GENERATOR_KEY = "experiments/graph-topology/graph_experiment.py"
RETAINED_FILES = ("RESULTS.json", "RESULTS.md", "EXECUTION_SOURCE.json")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"invalid retained graph {label}")
    return value


def _hex_digest(value: Any, digits: int = 64) -> bool:
    return (isinstance(value, str) and len(value) == digits
            and all(character in "0123456789abcdef" for character in value))


def _same(actual: Any, expected: Any, label: str) -> None:
    # Python equality treats True as 1. Evidence identity must also preserve types.
    if canonical_json(actual) != canonical_json(expected):
        raise ValueError(f"inconsistent retained graph {label}")


def _verify_episode_inventory(original: dict[str, Any], mapping: dict[str, Any]) -> None:
    cells = _object(original.get("cells"), "cells")
    if not cells or type(original.get("rounds")) is not int or original["rounds"] <= 0:
        raise ValueError("invalid retained graph episode inventory")
    totals = {"completed_episodes": len(cells), "full_analytical_curves_matched": 0,
              "ledger_events": 0, "rounds": 0, "sealed_replays_verified": 0}
    for value in cells.values():
        cell = _object(value, "episode")
        _same(cell.get("manifest_worktree_dirty"), False, "original episode cleanliness")
        _same(cell.get("replay_verified"), True, "original episode replay")
        observed, analytical = cell.get("observed_curve"), cell.get("analytical_curve")
        if not isinstance(observed, list) or not isinstance(analytical, list):
            raise ValueError("invalid retained graph episode curves")
        _same(len(observed), original["rounds"], "episode round count")
        _same(len(analytical), original["rounds"], "analytical round count")
        matched = canonical_json(observed) == canonical_json(analytical)
        _same(cell.get("analytical_curve_match"), matched, "analytical match annotation")
        if type(cell.get("event_count")) is not int or cell["event_count"] <= 0:
            raise ValueError("invalid retained graph episode event count")
        totals["full_analytical_curves_matched"] += int(matched)
        totals["ledger_events"] += cell["event_count"]
        totals["rounds"] += len(observed)
        totals["sealed_replays_verified"] += 1
    _same(original.get("episode_count"), len(cells), "report episode count")
    _same(original.get("matching_analytical_curves"), totals["full_analytical_curves_matched"],
          "report analytical match count")
    verification = _object(mapping.get("verification"), "verification record")
    for key, expected in totals.items():
        _same(verification.get(key), expected, key)
    _same(verification.get("all_manifest_worktree_dirty_false"), True,
          "original episode cleanliness summary")


def verify_retained_records(directory: Path) -> dict[str, Any]:
    """Verify historical records against each other, never against today's code.

    These are retained-evidence consistency checks, not independent authenticity
    or a new verification of the historical remote commit or runtime environment.
    """
    try:
        blobs = {name: (directory / name).read_bytes()
                 for name in (*RETAINED_FILES, "SOURCE_PROVENANCE.json")}
        records = {name: _object(json.loads(data), name) for name, data in blobs.items()
                   if name.endswith(".json")}
        canonical_json(records)
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError("missing or unreadable retained graph evidence") from exc
    original = records["RESULTS.json"]
    source = records["EXECUTION_SOURCE.json"]
    mapping = records["SOURCE_PROVENANCE.json"]
    for record, domain in ((source, SOURCE_DOMAIN), (mapping, MAPPING_DOMAIN)):
        _same(record.get("schema_version"), 1, "schema version")
        _same(record.get("domain"), domain, "source domain")

    files = _object(source.get("files"), "source files")
    if (not files or any(not name or not _hex_digest(digest) for name, digest in files.items())
            or GENERATOR_KEY not in files or "requirements-lock.txt" not in files):
        raise ValueError("invalid retained graph source file commitments")
    _same(source.get("files_sha256"), content_hash({"domain": SOURCE_DOMAIN, "files": files}),
          "source self-commitment")
    if (not _hex_digest(source.get("local_source_commit"), 40)
            or not _hex_digest(source.get("clean_local_source_tree"), 40)):
        raise ValueError("invalid retained graph source commit/tree")
    _same(source.get("worktree_dirty_before_run"), False, "original source cleanliness")
    _same(original.get("execution_source"), source, "embedded execution source")
    _same(original.get("report_source_sha256"), files[GENERATOR_KEY], "report generator source")
    if not _hex_digest(original.get("study_hash")):
        raise ValueError("invalid retained graph study hash")

    retained = _object(mapping.get("original_retained_files"), "retained-file mapping")
    if set(retained) != set(RETAINED_FILES):
        raise ValueError("incomplete retained graph file mapping")
    for name in RETAINED_FILES:
        commitment = _object(retained[name], f"commitment for {name}")
        _same(commitment.get("bytes"), len(blobs[name]), f"byte length for {name}")
        _same(commitment.get("sha256"), hashlib.sha256(blobs[name]).hexdigest(),
              f"byte commitment for {name}")
    for key, expected in {
        "execution_source_files": len(files),
        "execution_source_files_sha256": source["files_sha256"],
        "local_execution_source_commit": source["local_source_commit"],
        "local_execution_source_tree": source["clean_local_source_tree"],
        "study_hash": original["study_hash"],
        "report_generator_source_sha256": files[GENERATOR_KEY],
        "worktree_dirty_before_execution": False,
    }.items():
        _same(mapping.get(key), expected, key)
    published = _object(mapping.get("published_source"), "published source")
    _same(published.get("tree"), source["clean_local_source_tree"], "published source tree")
    if (not _hex_digest(published.get("commit"), 40)
            or not isinstance(published.get("repository"), str)):
        raise ValueError("invalid retained graph published source identity")
    _same(published.get("commit_url"),
          f"https://github.com/{published['repository']}/commit/{published['commit']}",
          "published source URL")
    runtime = _object(mapping.get("runtime"), "runtime record")
    _same(runtime.get("requirements_lock_sha256"), files["requirements-lock.txt"],
          "runtime dependency commitment")

    _verify_episode_inventory(original, mapping)
    return original


def mechanical_view(report: dict[str, Any]) -> dict[str, Any]:
    """Keep every design, trajectory, score, identity and terminal commitment.

    A new execution legitimately has different source provenance/dirty flags.
    Removing exactly those annotations does not replace the historical record.
    """
    view = {key: value for key, value in report.items()
            if key not in {"execution_source", "report_source_sha256", "cells"}}
    view["cells"] = {
        cid: {key: value for key, value in cell.items() if key != "manifest_worktree_dirty"}
        for cid, cell in report["cells"].items()
    }
    return view


def verify_readout(original: dict[str, Any], regenerated: dict[str, Any]) -> None:
    if canonical_json(mechanical_view(original)) != canonical_json(mechanical_view(regenerated)):
        raise ValueError("graph outcomes or recorded identities differ from the original controls")


def main() -> None:
    original = verify_retained_records(EXPERIMENT)
    module_spec = importlib.util.spec_from_file_location("chl_graph_verification", SCRIPT)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("cannot load the graph report generator")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    expected_markdown: str = module.render_markdown(original)
    if (EXPERIMENT / "RESULTS.md").read_bytes() != expected_markdown.encode("utf-8"):
        raise ValueError("graph Markdown differs from its retained JSON readout")
    with tempfile.TemporaryDirectory(prefix="chl-graph-check-") as temporary:
        artifacts = Path(temporary) / "execution"
        subprocess.run([sys.executable, str(SCRIPT), "--run", "--artifacts", str(artifacts)],
                       cwd=REPO, check=True)
        regenerated = json.loads((artifacts / "RESULTS.json").read_text(encoding="utf-8"))
        verify_readout(original, regenerated)
    print(
        "Verified all 18 graph trajectories, scores, identities and replayed terminal commitments; "
        "historical execution provenance retained."
    )


if __name__ == "__main__":
    main()
