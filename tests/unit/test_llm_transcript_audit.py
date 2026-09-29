"""Joint ledger-plus-transcript pin for exhausted LLM retries.

A FakeProvider script of two non-JSON strings with max_retries=1 must yield
an abstain with reason ``invalid_llm_output`` (the hashed-ledger side) while
keeping one transcript entry per attempt with the raw text preserved (the
unhashed audit sidecar). Dropping entries or silently repairing output must
fail this test.
"""

import random

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.experiments.scenario import NarrativeSkin

SKIN = NarrativeSkin(skin_id="plain")

OBSERVATION = {
    "round": 0,
    "mechanism": "evidence_commons",
    "self_id": "a1",
    "slots": {},
    "evidence": [],
    "claims": [],
    "my_budgets": {"inspect": 6, "verify": 3},
    "my_effort_spent": 0,
}


def test_exhausted_retries_abstains_and_logs_raw():
    script = ["not json one", "not json two"]
    provider = FakeProvider(list(script))
    policy = LLMPolicy("a1", provider, SKIN, max_retries=1)

    proposal = policy.propose(dict(OBSERVATION), random.Random(0))

    # Ledger side: abstain, never a silently repaired action.
    assert proposal.action.type == "abstain"
    assert proposal.action.reason == "invalid_llm_output"

    # Transcript side: one entry per attempt, raw text preserved.
    assert len(policy.transcript) == 2
    assert [entry["raw_text"] for entry in policy.transcript] == script
    assert all("invalid" in entry["outcome"] for entry in policy.transcript)
