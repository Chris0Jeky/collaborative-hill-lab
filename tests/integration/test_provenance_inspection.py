"""Integration: adversarial provenance — a valid challenge blocks misinformation.

Runs the ``attr-priv-misinfo`` condition (contributor + verifier + misinformer
under attributable accountability, private topology). The misinformer proposes
the FALSE proposition ``s2_false`` citing its own supporting item; the verifier
holds ``e06``, a fresh item that CONTRADICTS ``s2_false``, and challenges it.

The mechanism's acceptance rule is

    net_support = supported_verifications - valid_challenges   (>= 1 to accept)

so a single valid challenge must keep ``s2_false`` out of the sealed briefing.
The test asserts the correct behaviour directly; were the misinformation ever
accepted these assertions would fail loudly (a finding, per the mechanism rule).
"""

import pytest

from collaborative_hill.domain.claims import provenance_graph
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.study import run_study

from ._helpers import STUDY_001, find_run_dirs

pytestmark = pytest.mark.integration

CONDITION = "attr-priv-misinfo"
FALSE_SLOT = "s2"
FALSE_PROP = "s2_false"
REFUTING_EVIDENCE = "e06"


def test_valid_challenge_blocks_misinformation(tmp_path):
    artifacts = tmp_path / "artifacts"
    results = run_study(
        STUDY_001, artifacts, only_condition=CONDITION, replicates_override=1
    )
    assert len(results) == 1
    assert results[0].status == "completed"

    (run_dir,) = find_run_dirs(artifacts)
    events = FileEventStore(RunPaths(run_dir).events).load_all(verify=True)

    # The misinformer actually proposed the false proposition for slot s2.
    misinfo_claims = {
        e.payload["claim_id"]
        for e in events
        if e.event_type == EventType.CLAIM_PROPOSED
        and e.payload["slot_id"] == FALSE_SLOT
        and e.payload["proposition_id"] == FALSE_PROP
    }
    assert misinfo_claims, "expected the misinformer to propose s2_false"

    # The ledger contains a valid challenge that refutes that claim citing e06.
    valid_challenges = [
        e.payload
        for e in events
        if e.event_type == EventType.CLAIM_CHALLENGED and e.payload["valid"] is True
    ]
    assert valid_challenges, "expected at least one valid ClaimChallenged event"
    refutations = [
        c
        for c in valid_challenges
        if c["claim_id"] in misinfo_claims and REFUTING_EVIDENCE in c["evidence_ids"]
    ]
    assert refutations, (
        "expected a valid challenge against s2_false citing e06; "
        f"valid challenges were {valid_challenges}"
    )

    # Mechanism rule: for the challenged misinformation claim,
    # net_support = supported_verifications - valid_challenges must be < 1.
    graph = provenance_graph(events)
    for cid in misinfo_claims:
        claim = graph["claims"][cid]
        supported = sum(1 for v in claim["verifications"] if v["outcome"] == "supported")
        valid_ch = sum(1 for c in claim["challenges"] if c["valid"])
        net_support = supported - valid_ch
        assert net_support < 1, (
            f"{cid} (s2_false) has net_support {net_support} >= 1 — the valid "
            "challenge failed to block misinformation"
        )

    # The sealed briefing must NOT accept s2_false in ANY slot ...
    completed = [e for e in events if e.event_type == EventType.RUN_COMPLETED]
    assert len(completed) == 1
    briefing = completed[0].payload["briefing"]
    for entry in briefing:
        if entry.get("claim_id"):
            assert entry["proposition_id"] != FALSE_PROP, (
                f"sealed briefing accepted misinformation: {entry}"
            )

    # ... and specifically slot s2 is left unfilled (its only candidate refuted).
    s2_entry = next(b for b in briefing if b["slot_id"] == FALSE_SLOT)
    assert s2_entry.get("claim_id") is None
