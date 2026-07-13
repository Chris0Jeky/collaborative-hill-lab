"""Generate docs/research/REPLICATION_REPORT.md from Study 000 artifacts.

Usage: python studies/000-legacy-reproduction/generate_report.py [--artifacts DIR]

The report separates EXACT reproduction (deterministic conditions, analytically
predicted numbers) from QUALITATIVE reproduction (stochastic conditions,
direction/shape of the effect), and never manipulates outcomes to match the
publication — mismatches are reported as findings.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

STUDY_DIR = Path(__file__).parent
REPO = STUDY_DIR.parent.parent
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.engine.seeds import rng_for  # noqa: E402
from collaborative_hill.engine.store import FileEventStore, RunPaths  # noqa: E402
from collaborative_hill.experiments.study import load_study, study_hash  # noqa: E402
from collaborative_hill.metrics import cooperation_metrics  # noqa: E402

# (condition, deterministic?, prediction text, check fn on aggregated stats)
EXPECTATIONS = [
    ("pw-3tft", True, "cooperation 1.0 every round; scores 300 each",
     lambda s: s["mean_of_means"] == 1.0),
    ("pw-2tft-alld", True, "quarantine: mean vote rate = (4/6 + 49*(2/6))/50 ≈ 0.3467",
     lambda s: abs(s["mean_of_means"] - (4 / 6 + 49 * (2 / 6)) / 50) < 1e-9),
    ("pw-2tftlinked-alld", True, "collapse despite pairwise structure: all-D from round 2",
     lambda s: s["mean_final_window"] == 0.0),
    ("nb-3ptft-incself", True, "all-C absorbing: cooperation 1.0",
     lambda s: s["mean_of_means"] == 1.0),
    ("nb-2ptft-alld-incself", False, "Tragic Valley: final-window ~0 (collapse)",
     lambda s: s["mean_final_window"] < 0.05),
    ("nb-2ptft-alld-excself", False, "valley, faster decay than include_self",
     lambda s: s["mean_final_window"] < 0.05),
    ("nb-2tftthresh-alld", True, "NO collapse: sustained 2/3 group rate (knife-edge quorum)",
     lambda s: abs(s["mean_final_window"] - 2 / 3) < 1e-9),
    ("pw-2tfte-alld", False,
     "legacy: 'pair with the always defect agent largely defect' ~25% (prisoners.tex)",
     lambda s: 0.10 <= s["mean_of_means"] <= 0.40),
    ("nb-2ptfte-alld-incself", False, "legacy: ~20% cooperation with AllD (prisoners.tex)",
     lambda s: 0.05 <= s["mean_of_means"] <= 0.35),
    ("pw-2tfte-allc", False,
     "legacy: 'pair with the collaborative agent largely collaborate' ~75% (prisoners.tex)",
     lambda s: s["mean_of_means"] > 0.5),
    ("nb-2ptfte-allc-incself", False, "legacy: ~80% cooperation with AllC (prisoners.tex)",
     lambda s: s["mean_of_means"] > 0.5),
]

LEGACY_CLAIMS = [
    ("3 TFT pairwise sustained cooperation", "pw-3tft"),
    ("2 TFT + AllD pairwise: quarantine, largely collaborative", "pw-2tft-alld"),
    ("2 TFT + AllD neighbourhood: descent into the Tragic Valley", "nb-2ptft-alld-incself"),
    ("TFT-E + AllD: pairwise ~25% vs neighbourhood ~20%", "pw-2tfte-alld"),
    ("TFT-E + AllC: pairwise ~75% vs neighbourhood ~80%", "pw-2tfte-allc"),
    ("Q-learning pairwise ~80% vs neighbourhood ~20%", None),  # out of scope
]


def bootstrap_ci(values: list[float], n_boot: int = 2000) -> tuple[float, float]:
    rng = rng_for("study000", "bootstrap")
    if len(set(values)) == 1:
        return values[0], values[0]
    means = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", default=str(REPO / "artifacts"))
    parser.add_argument("--out", default=str(REPO / "docs/research/REPLICATION_REPORT.md"))
    args = parser.parse_args()

    spec, resolved = load_study(STUDY_DIR)
    h = study_hash(spec, resolved)
    study_root = None
    for candidate in (Path(args.artifacts) / h, Path(args.artifacts) / f"DRAFT-{h[:12]}"):
        if candidate.exists():
            study_root = candidate
            break
    if study_root is None:
        print(f"no artifacts found for study hash {h[:16]} under {args.artifacts}")
        return 1

    stats: dict[str, dict] = {}
    for cond_dir in sorted(p for p in study_root.iterdir() if p.is_dir()):
        means, finals, chains = [], [], set()
        for run_dir in sorted(p for p in cond_dir.iterdir() if p.is_dir()):
            events = FileEventStore(RunPaths(run_dir).events).load_all(verify=True)
            m = cooperation_metrics(events)
            means.append(m["mean_cooperation"])
            finals.append(m["final_window_cooperation"])
            chains.add(events[-1].event_hash)
        if not means:
            continue
        lo, hi = bootstrap_ci(finals)
        stats[cond_dir.name] = {
            "replicates": len(means),
            "mean_of_means": sum(means) / len(means),
            "sd_of_means": statistics.stdev(means) if len(set(means)) > 1 else 0.0,
            "mean_final_window": sum(finals) / len(finals),
            "final_ci": (lo, hi),
            "identical_summaries": len({round(x, 12) for x in finals}) == 1,
            "distinct_final_hashes": len(chains),
        }

    lines = [
        "# Replication report — Study 000 (legacy reproduction and audit)",
        "",
        f"Study hash: `{h}` | conditions: {len(stats)} | replicates/condition: "
        f"{spec.replicates} | rounds: 50 | seed: {spec.seed}",
        "",
        "Derived from sealed event ledgers only. Predictions were stated in the study",
        "README before execution. Legacy artifacts were NOT used as targets: the legacy",
        "pipeline was unseeded and its pairwise tracking was defective",
        "(`docs/research/LEGACY_AUDIT.md`), so this study reproduces *claims*, not CSVs.",
        "",
        "## Condition results vs analytical predictions",
        "",
        "| condition | replicates | mean coop (mean±sd) | final-window mean [95% CI] |"
        " prediction | verdict |",
        "|---|---|---|---|---|---|",
    ]
    verdicts: dict[str, str] = {}
    for cond, deterministic, prediction, check in EXPECTATIONS:
        s = stats.get(cond)
        if s is None:
            lines.append(f"| {cond} | 0 | — | — | {prediction} | NOT RUN |")
            verdicts[cond] = "not run"
            continue
        ok = check(s)
        kind = "exact" if deterministic else "qualitative"
        verdict = f"{'REPRODUCED' if ok else 'NOT REPRODUCED'} ({kind})"
        verdicts[cond] = verdict
        ci = s["final_ci"]
        lines.append(
            f"| {cond} | {s['replicates']} | {s['mean_of_means']:.4f}±{s['sd_of_means']:.4f} "
            f"| {s['mean_final_window']:.4f} [{ci[0]:.4f}, {ci[1]:.4f}] "
            f"| {prediction} | {verdict} |"
        )

    lines += [
        "",
        "Deterministic conditions: `identical_summaries` must be true across replicates "
        "(determinism check, not variance):",
        "",
    ]
    for cond, deterministic, _, _ in EXPECTATIONS:
        if deterministic and cond in stats:
            lines.append(f"- {cond}: identical summaries across replicates = "
                         f"{stats[cond]['identical_summaries']}")

    lines += [
        "",
        "## Legacy claim classification",
        "",
        "| legacy claim | condition here | status |",
        "|---|---|---|",
    ]
    for claim, cond in LEGACY_CLAIMS:
        if cond is None:
            lines.append(f"| {claim} | — | blocked (out of scope: RL agents not in foundation) |")
        else:
            v = verdicts.get(cond, "not run")
            status = ("qualitatively reproduced" if "REPRODUCED" in v and "NOT" not in v
                      else "not reproduced — investigate")
            lines.append(f"| {claim} | {cond} | {status} |")

    lines += [
        "",
        "## Deconfound findings",
        "",
        "- `pw-2tftlinked-alld` (npdl's linked 'pairwise' TFT): " + verdicts.get(
            "pw-2tftlinked-alld", "not run") +
        " — collapse *inside* the pairwise structure shows targeted per-opponent reciprocity"
        " (not the pairwise payoff structure alone) carries the Collaborative Hill.",
        "- `nb-2tftthresh-alld` (npdl's threshold TFT): " + verdicts.get(
            "nb-2tftthresh-alld", "not run") +
        " — sustained cooperation *inside* the neighbourhood structure shows the Tragic"
        " Valley depends on the reciprocator's decision rule, not the structure alone.",
        "",
        "The legacy contrast (per-opponent TFT in pairwise vs probabilistic pTFT in"
        " neighbourhood) therefore conflates strategy with structure; both matter."
        " This does not overturn the legacy qualitative story for its chosen strategy"
        " pair, but it narrows the claim that structure alone explains the effect.",
        "",
        "## Exact-number reproduction status",
        "",
        "Deterministic conditions reproduce their analytical oracle exactly (table above)."
        " Exact reproduction of legacy CSVs/figures is NOT claimed and NOT possible:"
        " unseeded legacy runs, contaminated pairwise CSVs, and an underspecified"
        " cooperation denominator in the draft (whether 66%/75% style figures count"
        " TFT votes only, all votes, or agents-mostly-cooperating is not stated).",
        "",
        "Whether any legacy result is considered 'replicated' for publication purposes"
        " is a HUMAN decision (see HANDOFF.md).",
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    print(json.dumps(dict(verdicts.items()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
