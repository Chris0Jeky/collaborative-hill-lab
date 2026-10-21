"""Markdown + JSON (+ optional Parquet) reports derived from sealed ledgers.

Every figure/table is traceable: reports embed the study/scenario/mechanism
hashes, the run id, and the metric versions that produced each number.
Parquet output is attempted when pyarrow is installed and skipped (with a
note) otherwise — parquet is a convenience, JSON is the record.
"""

import json
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import ChainError, Event, EventType
from collaborative_hill.engine.seeds import LEGACY_SEED_PROTOCOL, validate_recorded_seed_metadata
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.metrics import (
    METRIC_VERSIONS,
    cooperation_metrics,
    distribution_metrics,
    epistemic_metrics,
    operational_metrics,
)


def compute_all_metrics(events: list[Event],
                        manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "metric_versions": dict(METRIC_VERSIONS),
        "operations": operational_metrics(events, manifest),
        "distribution": distribution_metrics(events),
    }
    coop = cooperation_metrics(events)
    if coop.get("rounds"):
        metrics["cooperation"] = coop
    epi = epistemic_metrics(events)
    if epi.get("slots"):
        metrics["epistemics"] = epi
    return metrics


def _load_sealed_run(run_dir: Path) -> tuple[list[Event], dict[str, Any]]:
    paths = RunPaths(Path(run_dir))
    events = FileEventStore(paths.events).load_all(verify=True)
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    terminal_types = {EventType.RUN_COMPLETED, EventType.RUN_FAILED}
    terminals = [i for i, event in enumerate(events) if event.event_type in terminal_types]
    if terminals != [len(events) - 1]:
        raise ChainError("reporting requires exactly one terminal seal at the end of the ledger")
    terminal = events[-1]
    expected = {"completed": EventType.RUN_COMPLETED, "failed": EventType.RUN_FAILED}
    if terminal.event_type != expected.get(manifest["status"]):
        raise ChainError("manifest status does not match the terminal seal")
    if (terminal.study_id, terminal.run_id) != (manifest["study_id"], manifest["run_id"]):
        raise ChainError("manifest study/run identity does not match the terminal seal")
    for field, actual in (("event_count", len(events)), ("final_event_hash", terminal.event_hash)):
        if manifest.get(field) is not None and manifest[field] != actual:
            raise ChainError(f"manifest {field} does not match the sealed ledger")
    try:
        validate_recorded_seed_metadata(manifest, events[0].payload)
    except ValueError as exc:
        raise ChainError(str(exc)) from exc
    return events, manifest


def write_run_metrics(run_dir: Path) -> dict[str, Any]:
    paths = RunPaths(Path(run_dir))
    events, manifest = _load_sealed_run(run_dir)
    metrics = compute_all_metrics(events, manifest)
    paths.metrics.mkdir(exist_ok=True)
    (paths.metrics / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8"
    )
    _try_parquet(events, paths.metrics / "events.parquet")
    return metrics


def _try_parquet(events: list[Event], path: Path) -> bool:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return False
    table = pa.table({
        "seq": [e.seq for e in events],
        "logical_time": [e.logical_time for e in events],
        "actor": [e.actor for e in events],
        "event_type": [e.event_type.value for e in events],
        "payload_json": [json.dumps(e.payload, sort_keys=True) for e in events],
        "event_hash": [e.event_hash for e in events],
    })
    pq.write_table(table, path)
    return True


def run_report(run_dir: Path) -> Path:
    run_dir = Path(run_dir)
    paths = RunPaths(run_dir)
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    metrics = write_run_metrics(run_dir)

    lines = [
        f"# Run report: {manifest['run_id']}",
        "",
        f"- study: `{manifest['study_id']}` (hash `{_short(manifest.get('study_hash'))}`,"
        f" frozen: {manifest.get('study_frozen')})",
        f"- condition: `{manifest['condition_id']}` | replicate {manifest['replicate']}",
        f"- scenario `{_short(manifest['scenario_hash'])}` | mechanism"
        f" `{_short(manifest['mechanism_hash'])}` | narrative"
        f" `{_short(manifest['narrative_hash'])}`",
        f"- code commit `{_short(manifest.get('code_commit'))}`"
        f" (dirty: {manifest.get('worktree_dirty')})",
        f"- policies: {manifest['policies']}",
        f"- seed root: {manifest['seed_root']} | status: **{manifest['status']}**",
        f"- kernel seed protocol: `{manifest.get('seed_protocol', LEGACY_SEED_PROTOCOL)}`"
        f" | scenario block: {manifest.get('scenario_block')}",
        f"- policy seed root: {manifest.get('policy_seed_root')}",
        f"- metric versions: {metrics['metric_versions']}",
        "",
    ]
    if "cooperation" in metrics:
        c = metrics["cooperation"]
        lines += [
            "## Cooperation",
            "",
            f"- mean cooperation: {c['mean_cooperation']:.3f}",
            f"- final-window ({c['final_window']} rounds): {c['final_window_cooperation']:.3f}",
            f"- per agent: { {a: round(v, 3) for a, v in c['per_agent_cooperation'].items()} }",
            f"- first full-defection round: {c['first_full_defection_round']}",
            f"- collapsed (<=0.1 in final window): {c['collapsed']}",
            "",
        ]
    if "epistemics" in metrics:
        e = metrics["epistemics"]
        lines += [
            "## Epistemics",
            "",
            f"- slots filled: {e['slots_filled']}/{e['slots']}"
            f" (correct: {e['accepted_correct']}, incorrect: {e['accepted_incorrect']},"
            f" provenance-broken: {e['accepted_provenance_broken']})",
            f"- actions: {e['action_counts']}",
            "",
            "| slot | claim | proposition | correct | provenance ok |",
            "|---|---|---|---|---|",
        ]
        for entry in e["briefing"]:
            if entry.get("claim_id"):
                lines.append(
                    f"| {entry['slot_id']} | {entry['claim_id']} | {entry['proposition_id']} "
                    f"| {entry['correct']} | {entry['provenance_ok']} |"
                )
            else:
                lines.append(f"| {entry['slot_id']} | (unfilled) | — | — | — |")
        lines.append("")
    d = metrics["distribution"]
    if d.get("utilities"):
        lines += [
            "## Distribution",
            "",
            f"- utilities: { {a: round(v, 3) for a, v in d['utilities'].items()} }",
            f"- payoff Gini: {d['payoff_gini']:.3f}",
        ]
        if d.get("free_rider_advantage") is not None:
            lines.append(f"- free-rider advantage: {d['free_rider_advantage']:.3f}")
        lines.append("")
    o = metrics["operations"]
    lines += [
        "## Operations",
        "",
        f"- events: {o['events_total']} | invalid-action rate: {o['invalid_action_rate']:.3f}"
        f" | fallback abstentions: {o['fallback_abstentions']}",
        f"- tokens in/out: {o['input_tokens']}/{o['output_tokens']}"
        f" | cost: {o['cost_usd']} (None = not measured; never fabricated)",
        "",
    ]
    paths.report.write_text("\n".join(lines), encoding="utf-8")
    return paths.report


def study_report(artifacts_study_dir: Path) -> Path:
    """Aggregate over every run under artifacts/<study_hash>/ into report.md."""
    root = Path(artifacts_study_dir)
    rows = []
    for manifest_path in sorted(root.glob("*/*/manifest.json")):
        run_dir = manifest_path.parent
        events, manifest = _load_sealed_run(run_dir)
        metrics_path = run_dir / "metrics" / "metrics.json"
        cached = (json.loads(metrics_path.read_text(encoding="utf-8"))
                  if metrics_path.exists() else None)
        # A cache from other metric code is stale: recompute in memory (reports stay read-only).
        metrics = (cached if cached and cached.get("metric_versions") == dict(METRIC_VERSIONS)
                   else compute_all_metrics(events, manifest))
        row: dict[str, Any] = {
            "condition": manifest["condition_id"],
            "run": manifest["run_id"],
            "replicate": manifest["replicate"],
            "status": manifest["status"],
            "seed_protocol": manifest.get("seed_protocol", LEGACY_SEED_PROTOCOL),
            "scenario_block": manifest.get("scenario_block"),
        }
        if manifest["status"] != "completed":
            rows.append(row)
            continue
        if "cooperation" in metrics:
            row["mean_coop"] = round(metrics["cooperation"]["mean_cooperation"], 4)
            row["final_coop"] = round(metrics["cooperation"]["final_window_cooperation"], 4)
        if "epistemics" in metrics:
            e = metrics["epistemics"]
            row["correct"] = e["accepted_correct"]
            row["incorrect"] = e["accepted_incorrect"]
        if metrics["distribution"].get("free_rider_advantage") is not None:
            row["free_rider_adv"] = round(metrics["distribution"]["free_rider_advantage"], 3)
        rows.append(row)

    lines = [f"# Study report: {root.name}", ""]
    if rows:
        keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "condition", k))
        lines.append("| " + " | ".join(keys) + " |")
        lines.append("|" + "---|" * len(keys))
        for r in rows:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
        lines.append("")
        lines.append(f"Runs: {len(rows)}. Derived from sealed ledgers; per-run detail in "
                     "each run directory's report.md.")
    else:
        lines.append("No runs found.")
    out = root / "report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _short(value: str | None) -> str:
    return value[:12] if value else "unknown"
