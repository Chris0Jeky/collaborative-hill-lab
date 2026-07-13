"""Metamorphic: renaming + reordering agents relabels outcomes, nothing more.

Follow-up relation: run an NIPD scenario, then run the SAME scenario with every
agent renamed via a bijection and the cognition plane reordered. The aggregate
deterministic outcome must be equivalent up to that relabeling — the multiset of
final scores is unchanged, the per-round cooperation-rate series is byte-for-byte
identical, and every per-agent value maps through the bijection.

Why deterministic policies only (tft_pairwise / alld): agent ids feed the
runner's per-decision seed path (study_seed, condition, replicate, "agent", id,
"round", t). A stochastic policy would therefore draw a *different* rng stream
under a renamed id, breaking the relabeling equivalence for a reason that has
nothing to do with the mechanism. tft_pairwise and alld ignore their rng
entirely, so the run depends only on strategy interactions, which are genuinely
relabel-invariant.
"""

import pytest

from collaborative_hill.metrics.cooperation import cooperation_metrics

from ._helpers import compile_nipd, execute

pytestmark = pytest.mark.metamorphic

# A non-order-preserving bijection: sorted preimages (a1,a2,a3) map to images
# whose sort order is scrambled (z1,z5,z9) — so the test also proves the outcome
# is independent of id sort order, not just of the label alphabet.
BIJECTION = {"a1": "z9", "a2": "z1", "a3": "z5"}

# Two reciprocators and one unconditional defector: per-agent cooperation and
# per-agent scores genuinely differ across agents, so mapping through the
# bijection is a real constraint rather than a symmetry that holds vacuously.
BASE_POLICIES = {"a1": "tft_pairwise", "a2": "tft_pairwise", "a3": "alld"}


def test_agent_permutation_relabels_outcomes(tmp_path):
    base_agents = (("a1", "tft_pairwise"), ("a2", "tft_pairwise"), ("a3", "alld"))
    # Renamed AND reordered: images listed in a scrambled order, each carrying
    # its preimage's policy.
    perm_agents = (
        ("z5", BASE_POLICIES["a3"]),  # a3 -> z5 (alld)
        ("z9", BASE_POLICIES["a1"]),  # a1 -> z9 (tft)
        ("z1", BASE_POLICIES["a2"]),  # a2 -> z1 (tft)
    )

    base = compile_nipd(base_agents, scenario_id="perm-base", rounds=5)
    perm = compile_nipd(perm_agents, scenario_id="perm-image", rounds=5)

    # Same seed_root for both: legitimate here precisely because these policies
    # never consult their rng stream.
    base_res, base_events, _ = execute(base, tmp_path / "base", seed_root=("perm", 0))
    perm_res, perm_events, _ = execute(perm, tmp_path / "perm", seed_root=("perm", 0))

    assert base_res.status == "completed"
    assert perm_res.status == "completed"

    base_scores = base_res.summary["scores"]
    perm_scores = perm_res.summary["scores"]

    # Multiset of final scores is invariant.
    assert sorted(base_scores.values()) == sorted(perm_scores.values())
    # Per-agent final score maps through the bijection.
    for a, image in BIJECTION.items():
        assert base_scores[a] == perm_scores[image]

    base_coop = cooperation_metrics(base_events)
    perm_coop = cooperation_metrics(perm_events)

    # The per-round cooperation-rate series is identical (aggregate, id-free).
    assert base_coop["cooperation_rate_by_round"] == perm_coop["cooperation_rate_by_round"]
    assert base_coop["mean_cooperation"] == perm_coop["mean_cooperation"]

    # Per-agent cooperation maps through the bijection.
    base_pa = base_coop["per_agent_cooperation"]
    perm_pa = perm_coop["per_agent_cooperation"]
    assert set(perm_pa) == set(BIJECTION.values())
    for a, image in BIJECTION.items():
        assert base_pa[a] == perm_pa[image]

    # Sanity: the defector really is distinguishable from the reciprocators,
    # so the mapping constraint above is non-vacuous.
    assert base_pa["a3"] == 0.0
    assert base_pa["a1"] > 0.0
