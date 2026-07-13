"""Metamorphic: a sealed run replays to an identical hash chain.

Run two conditions through the full study pipeline into a temp artifacts tree:
a scripted Evidence Commons run and a pairwise NIPD run driven by a *stochastic*
policy (random). Then replay each sealed run directory. Replay re-issues the
recorded typed actions, so even the stochastic condition must reproduce the
original chain hash-for-hash (ADR-0001: determinism is given the recorded
actions). chains_match must be True for every run.
"""

import pytest

from collaborative_hill.engine.replay import replay_run
from collaborative_hill.experiments.study import run_study

from ._helpers import default_ec_evidence, ec_spec, find_run_dirs, nipd_spec, plain_skin

pytestmark = pytest.mark.metamorphic


def test_scripted_and_stochastic_runs_replay_exactly(tmp_path):
    from ._helpers import write_study

    study_dir = tmp_path / "study"
    artifacts = tmp_path / "artifacts"

    ec = ec_spec(default_ec_evidence(), scenario_id="ec", rounds=8)
    # Stochastic pairwise NIPD: the random policy draws from the kernel rng
    # streams, so this exercises "replay reproduces a stochastic run".
    nipd = nipd_spec(
        (("a1", "random"), ("a2", "random"), ("a3", "random")),
        scenario_id="nipd",
        mode="pairwise",
        rounds=5,
    )

    write_study(
        study_dir,
        study_id="replay-study",
        seed=4242,
        checkpoint_every=0,
        conditions=[("ec", ec, plain_skin()), ("nipd", nipd, plain_skin())],
    )

    results = run_study(study_dir, artifacts)
    assert len(results) == 2
    assert all(r.status == "completed" for r in results)

    run_dirs = find_run_dirs(artifacts)
    assert len(run_dirs) == 2

    for run_dir in run_dirs:
        report = replay_run(run_dir)
        assert report.chains_match, (
            f"{run_dir.name}: diverged at seq {report.first_divergence_seq}: {report.detail}"
        )
        assert report.original_events == report.replayed_events
        assert report.first_divergence_seq is None
