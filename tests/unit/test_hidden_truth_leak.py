"""Hidden-truth leak audit: the WHICH-proposition-is-true bit and its bookkeeping
fields must never reach observations or the sealed ledger.

The environment-only fields are ``true_propositions`` (world plane) and
``truth_aligned`` (per-evidence audit flag). We scan a full run's ledger text
for those FIELD NAMES, and check that every inspected evidence entry exposes
exactly the keys of EvidenceSpec.observable_facts() — nothing more.
"""

import json

from collaborative_hill.domain.evidence import EvidenceSpec
from collaborative_hill.engine.events import EventType

from _fixtures import ec_provenance_run

# Environment-only field names that must never leak into agent-facing artifacts.
TRUTH_FIELD_NAMES = ("truth_aligned", "true_propositions")

# The exact key set an agent may learn about an evidence item on inspection.
OBSERVABLE_FACT_KEYS = set(
    EvidenceSpec(evidence_id="x", source_id="s", slot_id="s1", proposition_id="p1a",
                 stance="supports", truth_aligned=True).observable_facts().keys()
)


def test_events_jsonl_text_never_contains_truth_field_names(tmp_path):
    _result, _events, paths = ec_provenance_run(tmp_path)
    text = paths.events.read_text(encoding="utf-8")
    for name in TRUTH_FIELD_NAMES:
        assert name not in text, f"leaked truth field name {name!r} into the ledger"


def test_observations_never_carry_truth_fields(tmp_path):
    _result, events, _paths = ec_provenance_run(tmp_path)
    obs_events = [e for e in events if e.event_type == EventType.OBSERVATION_ISSUED]
    assert obs_events, "expected observations in the ledger"
    for ev in obs_events:
        obs = ev.payload["observation"]
        serialized = json.dumps(obs, sort_keys=True)
        for name in TRUTH_FIELD_NAMES:
            assert name not in serialized


def test_inspected_facts_expose_only_observable_fact_keys(tmp_path):
    _result, events, _paths = ec_provenance_run(tmp_path)
    seen_any_facts = False
    for ev in events:
        if ev.event_type != EventType.OBSERVATION_ISSUED:
            continue
        for entry in ev.payload["observation"].get("evidence", []):
            if "facts" in entry:
                seen_any_facts = True
                assert set(entry["facts"].keys()) == OBSERVABLE_FACT_KEYS
                # explicitly: no environment-only fields
                assert "truth_aligned" not in entry["facts"]
                assert "adversarial" not in entry["facts"]
                assert "initial_holders" not in entry["facts"]
    assert seen_any_facts, "run should have produced at least one inspected item"


def test_observable_facts_key_set_is_exactly_the_documented_projection():
    # Guard against silent widening of the projection.
    assert OBSERVABLE_FACT_KEYS == {
        "evidence_id", "source_id", "version", "slot_id",
        "proposition_id", "stance", "freshness",
    }
