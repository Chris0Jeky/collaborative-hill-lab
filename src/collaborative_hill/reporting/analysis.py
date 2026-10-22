"""Notebook-free Study 001 draft analysis, derived only from verified sealed runs.

Input is the artifacts study directory, containing condition/run directories.
The four original factorial conditions are selected explicitly; the misinformer
condition is exploratory and must never be pooled into attr-priv. No run, cache,
study input, or lock is modified. No episode is re-executed.
"""

import math
from fractions import Fraction
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.hashing import frac_str
from collaborative_hill.engine.replay import load_run
from collaborative_hill.engine.seeds import (
    LEGACY_SEED_PROTOCOL,
    PAIRED_SEED_PROTOCOL,
    derive_seed,
    study_seed_roots,
)
from collaborative_hill.experiments.scenario import ECWorld
from collaborative_hill.metrics import METRIC_VERSIONS
from collaborative_hill.reporting.analysis_stats import CELLS, contrasts, describe
from collaborative_hill.reporting.report import compute_all_metrics

DEFAULT_SEED = 20261022
DEFAULT_SAMPLES = 2000
SECONDARIES = (
    "contribution_rate", "verify_actions", "verify_supported", "free_rider_advantage",
    "payoff_gini", "effort_gini", "collective_quality", "false_claim_accepted",
)
AXES = {
    "agg-priv": ("aggregate", "private"),
    "agg-ledger": ("aggregate", "shared_ledger"),
    "attr-priv": ("attributable", "private"),
    "attr-ledger": ("attributable", "shared_ledger"),
}


def _episode(directory: Path) -> dict[str, Any]:
    events, resolved, manifest = load_run(directory)
    if manifest.get("parent_run"):
        raise ValueError("branch_not_independent_episode")
    if not isinstance(resolved.spec.world, ECWorld):
        raise ValueError("not_evidence_commons")
    condition = manifest["condition_id"]
    if condition not in CELLS:
        raise ValueError("outside_primary_2x2")
    institution = resolved.spec.institution
    if (institution.accountability, institution.evidence_topology) != AXES[condition]:
        raise ValueError("condition_axes_mismatch")
    replicate = manifest["replicate"]
    if type(replicate) is not int or replicate < 0:
        raise ValueError("invalid_replicate")
    roots = study_seed_roots(
        manifest["seed_root"][0], condition, replicate,
        protocol=manifest["seed_protocol"], scenario_block=manifest.get("scenario_block"),
    )
    if (list(roots[0]) != manifest["seed_root"]
            or (list(roots[1]) if roots[1] else None) != manifest.get("policy_seed_root")):
        raise ValueError("episode_seed_identity_mismatch")
    row = {key: manifest.get(key) for key in (
        "study_id", "study_hash", "condition_id", "run_id", "replicate", "seed_protocol",
        "scenario_block", "seed_root", "policy_seed_root", "providers", "prompt_template_hashes",
        "input_tokens", "output_tokens", "cost_usd", "policies", "scenario_hash",
    )}
    row.update(run_status=manifest["status"], final_event_hash=events[-1].event_hash)
    if manifest["status"] != "completed":
        return row
    metrics = compute_all_metrics(events, manifest)
    epi, operations = metrics["epistemics"], metrics["operations"]
    proposed = operations["actions_proposed"]
    contributions = sum(epi["action_counts"].values())
    parser_abstentions = sum(
        ev.event_type == EventType.ACTION_PROPOSED
        and ev.payload["proposal"]["action"].get("type") == "abstain"
        and ev.payload["proposal"]["action"].get("reason") == "invalid_llm_output"
        for ev in events
    )
    row.update({
        "briefing_quality": epi["accepted_correct"] - epi["accepted_incorrect"],
        "accepted_correct": epi["accepted_correct"],
        "accepted_incorrect": epi["accepted_incorrect"],
        "slots_filled": epi["slots_filled"],
        "n_agents": len(events[0].payload["agents"]),
        "contribution_rate": frac_str(Fraction(contributions, proposed)) if proposed else None,
        "verify_actions": epi["action_counts"]["verify"],
        "verify_supported": epi["verifications_supported"],
        "false_claim_accepted": int(epi["false_claim_accepted"]),
        "collective_quality": events[-1].payload["collective_quality"],
        "invalid_action_count": operations["actions_rejected"],
        "invalid_llm_output_abstentions": parser_abstentions,
        "fallback_abstentions": operations["fallback_abstentions"],
        # SAP invalid-output reporting includes parser failures and mechanism
        # rejections once each; fallback abstentions already follow a rejection.
        "invalid_action_rate": (frac_str(Fraction(
            operations["actions_rejected"] + parser_abstentions, proposed,
        ))
                                if proposed else "0"),
    })
    for key in ("free_rider_advantage", "payoff_gini", "effort_gini"):
        value = metrics["distribution"].get(key)
        # These existing metrics are derived floats; preserve their decimal value,
        # rather than pretending it is an exact mechanism Fraction.
        row[key] = str(value) if value is not None else None
    return row


def _collect(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = sorted({p.parent for name in ("manifest.json", "events.jsonl",
                                              "scenario.resolved.json")
                         for p in root.glob(f"*/*/{name}")})
    if not candidates:
        raise ValueError("no run artifacts found; pass artifacts/<study-hash-or-DRAFT-prefix>")
    rows, exclusions = [], []
    identities: set[tuple[str, int]] = set()
    studies: set[tuple[str, str | None, str]] = set()
    for directory in candidates:
        identity = {"run_path": directory.relative_to(root).as_posix(),
                    "condition_id": directory.parent.name}
        try:
            row = _episode(directory)
            studies.add((row["study_id"], row["study_hash"], row["seed_protocol"]))
            if row["condition_id"] != directory.parent.name:
                raise ValueError("condition_directory_mismatch")
            key = (row["condition_id"], row["replicate"])
            if key in identities:
                raise ValueError("duplicate_episode")
            identities.add(key)
        except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
            # Stable categories; no absolute host paths, timestamps, or raw
            # provider error messages enter the derived analysis artifact.
            detail = str(exc)
            known = {"branch_not_independent_episode", "not_evidence_commons",
                     "outside_primary_2x2", "condition_axes_mismatch", "invalid_replicate",
                     "episode_seed_identity_mismatch", "condition_directory_mismatch",
                     "duplicate_episode"}
            exclusions.append({**identity, "reason": (detail if detail in known
                                                      else "invalid_or_unsealed_artifact"),
                               "detail": type(exc).__name__})
            continue
        if row["run_status"] == "failed":
            exclusions.append({**identity, "reason": "run_failed", "detail": "RunFailed",
                               "study_hash": row["study_hash"], "replicate": row["replicate"]})
        else:
            rows.append(row)
    if len(studies) > 1:
        raise ValueError("analysis requires one study identity, hash and seed protocol")
    return rows, exclusions


def _blocks(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not rows or rows[0]["seed_protocol"] == LEGACY_SEED_PROTOCOL:
        return None, None
    if any(r["providers"] for r in rows):
        return None, "provider_randomness_not_verified_for_pairing"
    verified_policies = {"ec_contributor[share=True]@1", "ec_contributor[share=False]@1",
                         "ec_freerider@1", "ec_verifier@1", "ec_misinformer@1"}
    if any(p not in verified_policies for r in rows for p in r["policies"].values()):
        return None, "policy_randomness_coupling_not_verified"
    groups: dict[tuple[str, int], dict[str, Any]] = {}
    roots: dict[tuple[str, int], list[str | int]] = {}
    for row in rows:
        key = (row["scenario_block"], row["replicate"])
        groups.setdefault(key, {})[row["condition_id"]] = row
        if key in roots and roots[key] != row["policy_seed_root"]:
            return None, "policy_roots_disagree_within_block"
        roots[key] = row["policy_seed_root"]
    if any(set(group) != set(CELLS) for group in groups.values()):
        return None, "incomplete_paired_blocks"
    return [groups[key] for key in sorted(groups)], None


def _effects(rows: list[dict[str, Any]], outcome: str, seed: int,
             samples: int) -> dict[str, Any]:
    blocks, reason = _blocks(rows)
    cells = {c: [Fraction(r[outcome]) for r in rows
                 if r["condition_id"] == c and r[outcome] is not None] for c in CELLS}
    if any(r[outcome] is None for r in rows):
        reason = "missing_outcomes_no_imputation"
    return contrasts(
        cells, seed=seed, samples=samples, unavailable=reason,
        blocks=([{c: Fraction(b[c][outcome]) for c in CELLS} for b in blocks]
                if blocks and reason is None else None),
    )


def _attrition(rows: list[dict[str, Any]], exclusions: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {}
    for cell in CELLS:
        completed_rows = [r for r in rows if r["condition_id"] == cell]
        included = len(completed_rows)
        cell_exclusions = [e for e in exclusions if e["condition_id"] == cell]
        # Copies and counterfactual branches are not additional attempted episodes.
        excluded = [e for e in cell_exclusions if e["reason"] not in {
            "duplicate_episode", "branch_not_independent_episode",
        }]
        failed = sum(e["reason"] == "run_failed" for e in excluded)
        counts[cell] = {
            "included": included, "failed": failed, "other_excluded": len(excluded) - failed,
            "non_episode_artifacts": len(cell_exclusions) - len(excluded),
            "inclusion_rate": frac_str(Fraction(included, included + len(excluded)))
            if included + len(excluded) else None,
            "invalid_action_count": sum(r.get("invalid_action_count", 0) for r in completed_rows),
            "invalid_llm_output_abstentions": sum(
                r.get("invalid_llm_output_abstentions", 0) for r in completed_rows
            ),
            "fallback_abstentions": sum(r.get("fallback_abstentions", 0) for r in completed_rows),
            "mean_invalid_action_rate": frac_str(sum(
                (Fraction(r.get("invalid_action_rate", 0)) for r in completed_rows), Fraction(),
            ) / included) if included else None,
        }
    completed = sum(c["included"] for c in counts.values())
    failures = sum(c["failed"] for c in counts.values())
    test: dict[str, Any] = {"method": "Pearson chi-square, df=3", "statistic": None,
                            "p_value": None, "reason": "empty_margin",
                            "small_expected_counts": None}
    if completed and failures and all(c["included"] + c["failed"] for c in counts.values()):
        statistic, minimum = Fraction(), Fraction(completed + failures)
        for cell_counts in counts.values():
            for field, total in (("included", completed), ("failed", failures)):
                expected = Fraction((cell_counts["included"] + cell_counts["failed"]) * total,
                                    completed + failures)
                statistic += (cell_counts[field] - expected) ** 2 / expected
                minimum = min(minimum, expected)
        x = float(statistic) / 2
        survival = math.erfc(math.sqrt(x)) + 2 * math.sqrt(x / math.pi) * math.exp(-x)
        test.update(statistic=frac_str(statistic), p_value=format(survival, ".12g"),
                    reason=None, small_expected_counts=minimum < 5)
    return {"per_cell": counts, "differential_attrition": test}


def analyze_study(study_dir: Path, *, seed: int = DEFAULT_SEED,
                  samples: int = DEFAULT_SAMPLES) -> dict[str, Any]:
    """Read artifacts/<study-prefix>; output remains draft even for frozen inputs."""
    if samples < 2:
        raise ValueError("bootstrap samples must be >= 2")
    rows, exclusions = _collect(Path(study_dir))
    hashes = {r["study_hash"] for r in rows} | {
        e["study_hash"] for e in exclusions if "study_hash" in e
    }
    if len(hashes) > 1 or (hashes and None in hashes):
        raise ValueError("analysis requires one recorded study hash")
    if len({r["seed_protocol"] for r in rows}) > 1:
        raise ValueError("analysis cannot mix seed protocols")
    for cell in CELLS:
        if len({r["scenario_hash"] for r in rows if r["condition_id"] == cell}) > 1:
            raise ValueError("analysis cannot pool different scenarios within a condition")
    primary = _effects(rows, "briefing_quality", seed, samples)
    secondary = {}
    for outcome in SECONDARIES:
        by_cell = {}
        for cell in CELLS:
            selected = [r[outcome] for r in rows if r["condition_id"] == cell]
            summary = describe([Fraction(v) for v in selected if v is not None],
                               seed=seed, samples=samples, scope=f"{outcome}/{cell}")
            summary["n_missing"] = sum(v is None for v in selected)
            by_cell[cell] = summary
        effects = _effects(rows, outcome, seed, samples)
        for effect in effects.values():
            effect.pop("p_unadjusted")
            effect.pop("p_holm")
        secondary[outcome] = {"confirmatory": False, "per_cell": by_cell, "effects": effects}
    return {
        "schema_version": 1, "sap_status": "draft", "unit": "episode",
        "study_hash": next(iter(hashes)) if hashes else None,
        "metric_versions": dict(METRIC_VERSIONS),
        "seed_protocol": rows[0]["seed_protocol"] if rows else None,
        "bootstrap": {"seed": seed, "stream_domain": "chl.analyze.v1", "samples": samples,
                      "derived_seed_example": derive_seed(seed, "chl.analyze.v1", CELLS[0]),
                      "method": "percentile_type7", "confidence": "19/20",
                      "resampling_unit": ("scenario_block,replicate" if rows and
                                          rows[0]["seed_protocol"] == PAIRED_SEED_PROTOCOL
                                          else "episode_within_cell")},
        "open_choices": [
            "Bootstrap count 2000 and analysis seed 20261022 are draft defaults.",
            "Legacy independent runs: equal-cell-weight contrasts and within-cell resampling.",
            "P-values: two-sided centered bootstrap, +1 correction; Holm family E1/E2/E3.",
            "Percentiles: linear order-statistic interpolation (type 7).",
            "Invalid-rate cutoff and preregistered exclusions are undeclared; no cutoff inferred.",
            "Attrition: asymptotic Pearson chi-square; small expected counts flagged, not Fisher.",
            "Paired provider inference requires verified coupling; kernel seeds are insufficient.",
            "Confirmatory use remains gated on R2 pilot, preregistration and human SAP freeze.",
        ],
        "interpretation": "Draft mechanism comparison only; no prediction about humans.",
        "episodes": rows, "exclusions": exclusions,
        "primary": {"outcome": "briefing_quality", "family": primary, "alpha": "1/20",
                    "per_cell": {c: describe(
                        [Fraction(r["briefing_quality"]) for r in rows if r["condition_id"] == c],
                        seed=seed, samples=samples, scope=c,
                    ) for c in CELLS}},
        "secondary": secondary, "attrition": _attrition(rows, exclusions),
        "sensitivity": {
            "all_completed": primary,
            "excluding_high_invalid_rate": {
                "status": "not_run", "reason": "threshold_not_declared",
            },
            "predeclared_exclusions": {"status": "not_run", "reason": "rules_not_declared"},
        },
    }
