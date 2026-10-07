"""Replay every sealed run and verify chain equality (make replay-smoke)."""

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.engine.replay import replay_run  # noqa: E402


def main() -> int:
    artifacts = REPO / "artifacts"
    run_dirs = sorted(p.parent for p in artifacts.glob("*/*/*/events.jsonl"))
    if not run_dirs:
        print("no sealed runs under artifacts/ — run `make study-000` first")
        return 1
    # replay every run dir: two runs under the same study hash may differ
    # (e.g. a tampered events.jsonl), so per-study deduplication would hide failures
    failures = 0
    for run_dir in run_dirs:
        study = run_dir.parent.parent.name
        report = replay_run(run_dir)
        status = "OK " if report.chains_match else "FAIL"
        print(f"{status} {study[:16]}.../{run_dir.name}: "
              f"{report.replayed_events} events replayed")
        if not report.chains_match:
            failures += 1
            print(f"     divergence at seq {report.first_divergence_seq}: {report.detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
