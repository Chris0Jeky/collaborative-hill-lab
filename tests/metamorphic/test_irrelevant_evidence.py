"""Metamorphic: evidence nobody can see changes nothing observable.

Add one extra evidence item with ``initial_holders=()`` under the private
topology, so it is visible to no agent and (private topology, no sharing path to
it) can never be inspected, cited, or shared. The run must be indistinguishable
from the baseline on every observable channel: the final briefing, per-agent
utilities, and every WORLD_TRANSITIONED / REWARD_ASSIGNED payload.

(REWARD_ASSIGNED is emitted by NIPD, not Evidence Commons; the assertion simply
compares whichever of the two event families the ledger contains — for EC that
is the WORLD_TRANSITIONED stream.)
"""

import pytest

from collaborative_hill.engine.events import EventType

from ._helpers import compile_ec, default_ec_evidence, ec_item, execute

pytestmark = pytest.mark.metamorphic

_WORLD_OR_REWARD = {EventType.WORLD_TRANSITIONED, EventType.REWARD_ASSIGNED}


def _world_and_reward_payloads(events):
    return [e.payload for e in events if e.event_type in _WORLD_OR_REWARD]


def test_invisible_evidence_is_inert(tmp_path):
    base_ev = default_ec_evidence()
    # An extra item held by nobody: exists in the corpus, accessible to no one.
    ghost = ec_item("e_ghost", "src_ghost", "s1", "p1b", "supports", holders=())
    aug_ev = (*base_ev, ghost)

    base = compile_ec(base_ev, scenario_id="inert-base")
    aug = compile_ec(aug_ev, scenario_id="inert-aug")

    # The corpus genuinely changed (new item, new hash) ...
    assert base.evidence_corpus_hash != aug.evidence_corpus_hash

    base_res, base_events, _ = execute(base, tmp_path / "base", seed_root=("inert", 0))
    aug_res, aug_events, _ = execute(aug, tmp_path / "aug", seed_root=("inert", 0))

    assert base_res.status == aug_res.status == "completed"

    # ... yet the sealed outcome is byte-for-byte the same.
    assert base_res.summary["briefing"] == aug_res.summary["briefing"]
    assert base_res.summary["utility"] == aug_res.summary["utility"]
    assert base_res.summary["collective_quality"] == aug_res.summary["collective_quality"]

    # And every world-transition / reward payload matches, in order.
    base_payloads = _world_and_reward_payloads(base_events)
    aug_payloads = _world_and_reward_payloads(aug_events)
    assert base_payloads  # the EC run emits WORLD_TRANSITIONED every round
    assert base_payloads == aug_payloads
