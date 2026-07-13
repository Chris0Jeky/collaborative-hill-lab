"""Regression fixture for THE historical defect.

The legacy npd_simulator cooperation extractor keyed round records off an
"agents" list or a "cooperation_rate" field. The legacy *pairwise* engine
emitted PAIR-INDEXED records (agent1_id/action1/agent2_id/action2, no "agents"
list, no "cooperation_rate"), so the extractor silently read cooperation as 0.0
for every round — erasing all reciprocity from pairwise studies.

We reproduce the exact bug on records derived from a REAL pairwise run of our
engine, and prove our schema-safe cooperation_metrics reads the same ledger
correctly.
"""

from collaborative_hill.engine.events import EventType
from collaborative_hill.metrics.cooperation import cooperation_metrics

from _fixtures import nipd_pairwise_2tft_alld_run


def _legacy_cooperation_by_round(round_records):
    """Faithful reimplementation of the legacy extractor (~12 lines).

    cooperation = mean(1 - action) over `agents` if present, else the record's
    `cooperation_rate`, defaulting to 0. Actions: 0 = cooperate, 1 = defect.
    """
    rates = []
    for rec in round_records:
        agents = rec.get("agents")
        if agents:
            rates.append(sum(1 - a["action"] for a in agents) / len(agents))
        else:
            rates.append(rec.get("cooperation_rate", 0))
    return rates


def _pair_indexed_records(events):
    """Shape our pairwise transitions like the legacy pairwise engine's output:
    per-round records carrying agent1_id/action1/agent2_id/action2 pairs and
    NEITHER an 'agents' list NOR a 'cooperation_rate' field."""
    records = []
    for ev in events:
        if ev.event_type != EventType.WORLD_TRANSITIONED:
            continue
        if ev.payload.get("mode") != "pairwise":
            continue
        pairs = [
            {"agent1_id": p["a"], "action1": 0 if p["move_ab"] == "C" else 1,
             "agent2_id": p["b"], "action2": 0 if p["move_ba"] == "C" else 1}
            for p in ev.payload["pair_results"]
        ]
        records.append({"round": ev.payload["round"], "pairs": pairs})
    return records


def test_legacy_extractor_reports_zero_while_ours_sees_cooperation(tmp_path):
    _result, events, _paths = nipd_pairwise_2tft_alld_run(tmp_path, rounds=5)

    legacy_records = _pair_indexed_records(events)
    assert len(legacy_records) == 5
    # every legacy per-round record lacks the keys the extractor expects
    for rec in legacy_records:
        assert "agents" not in rec
        assert "cooperation_rate" not in rec

    legacy_rates = _legacy_cooperation_by_round(legacy_records)
    # THE BUG: pairwise reciprocity is erased to a flat zero.
    assert legacy_rates == [0, 0, 0, 0, 0]

    # OUR metric reads the same ledger correctly: two TFTs vs one AllD cooperate
    # heavily in round 1 and sustain nontrivial cooperation thereafter.
    ours = cooperation_metrics(events)
    assert ours["cooperation_rate_by_round"][0] > 0.6
    assert ours["mean_cooperation"] > 0.3
    # and the two metrics genuinely disagree — the point of the regression.
    assert ours["cooperation_rate_by_round"][0] != legacy_rates[0]
