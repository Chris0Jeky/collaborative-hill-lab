"""Metamorphic: the ORDER of evidence in the information plane is not signal.

Permuting the evidence tuple is a pure reordering of the corpus. The mechanism
keys everything by id and sorts on read, so the scientific outcome — final
briefing, per-agent utilities, and collective_quality — must be identical.

The evidence_corpus_hash, however, is content-addressed over the *ordered* list
(order is part of the serialized artifact), so it legitimately differs. We
assert that difference too: the invariance is a property of the run, not of the
hash, and conflating the two would hide a real bug.
"""

import pytest

from ._helpers import compile_ec, default_ec_evidence, execute

pytestmark = pytest.mark.metamorphic


def test_permuting_evidence_order_preserves_outcome(tmp_path):
    base_ev = default_ec_evidence()
    # A non-trivial permutation of the four items.
    perm_ev = (base_ev[3], base_ev[1], base_ev[0], base_ev[2])
    assert perm_ev != base_ev

    base = compile_ec(base_ev, scenario_id="order-base")
    perm = compile_ec(perm_ev, scenario_id="order-perm")

    # Corpus hash is order-sensitive by construction — this MUST differ.
    assert base.evidence_corpus_hash != perm.evidence_corpus_hash

    base_res, _, _ = execute(base, tmp_path / "base", seed_root=("order", 0))
    perm_res, _, _ = execute(perm, tmp_path / "perm", seed_root=("order", 0))

    assert base_res.status == perm_res.status == "completed"

    # The outcome is invariant to corpus ordering.
    assert base_res.summary["briefing"] == perm_res.summary["briefing"]
    assert base_res.summary["utility"] == perm_res.summary["utility"]
    assert base_res.summary["collective_quality"] == perm_res.summary["collective_quality"]
    assert base_res.summary["individual_credit"] == perm_res.summary["individual_credit"]
    assert base_res.summary["effort"] == perm_res.summary["effort"]

    # Guard against a vacuous pass: the run must actually accept claims.
    assert any(entry["claim_id"] for entry in base_res.summary["briefing"])
