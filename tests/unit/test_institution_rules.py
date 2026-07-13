"""Institution plane: aggregate anonymizes actors and pools credit; attributable
exposes identities and assigns credit individually. Same task, same totals."""

from _fixtures import ec_hand_example, run_episode_tmp

from collaborative_hill.domain.actions import (
    ActionProposal,
    ProposeClaimAction,
    VerifyClaimAction,
    WithholdAction,
)
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.engine.events import EventType

ATTR = InstitutionConfig(accountability="attributable")
AGG = InstitutionConfig(accountability="aggregate")


class _Scripted:
    """Minimal per-round scripted policy: fixed action sequence by round index."""

    def __init__(self, agent_id, by_round, policy_id="scripted@1"):
        self.agent_id = agent_id
        self._by_round = by_round
        self.policy_id = policy_id

    def propose(self, observation, rng):
        t = int(observation["round"])
        action = self._by_round.get(t, WithholdAction())
        return ActionProposal(action=action)


def _hand_policies():
    # a1 proposes c1 round0; a2 verifies c1 round1; a3 idle.
    return {
        "a1": _Scripted("a1", {0: ProposeClaimAction(
            slot_id="s1", proposition_id="p1a", evidence_ids=("e1",))}),
        "a2": _Scripted("a2", {1: VerifyClaimAction(claim_id="c1")}),
        "a3": _Scripted("a3", {}),
    }


def _run(institution, tmp_path):
    mech = ec_hand_example(institution, rounds=3)
    return run_episode_tmp(mech, _hand_policies(), tmp_path,
                           run_id=f"inst_{institution.accountability}")


def test_aggregate_claim_proposed_event_is_anonymous(tmp_path):
    _result, events, _paths = _run(AGG, tmp_path)
    proposed = [e for e in events if e.event_type == EventType.CLAIM_PROPOSED]
    assert len(proposed) == 1
    ev = proposed[0]
    assert ev.actor == "anonymous"
    assert ev.payload["attributed"] is False
    # payload still records agent_id for the sealed audit trail (not agent-visible)
    assert ev.payload["agent_id"] == "a1"


def test_attributable_claim_proposed_event_names_actor(tmp_path):
    _result, events, _paths = _run(ATTR, tmp_path)
    proposed = [e for e in events if e.event_type == EventType.CLAIM_PROPOSED]
    ev = proposed[0]
    assert ev.actor == "a1"
    assert ev.payload["attributed"] is True


def _claim_view(events, accountability):
    """Pull one agent's observed claims from the last observation carrying them."""
    latest = None
    for e in events:
        if e.event_type == EventType.OBSERVATION_ISSUED and e.payload["observation"]["claims"]:
            latest = e.payload["observation"]
    assert latest is not None
    assert latest["accountability"] == accountability
    return latest["claims"][0]


def test_aggregate_observation_hides_identities_keeps_self_knowledge(tmp_path):
    _result, events, _paths = _run(AGG, tmp_path)
    claim = _claim_view(events, "aggregate")
    # anonymized: no proposer/verifiers/challengers identity keys
    assert "proposer" not in claim
    assert "verifiers" not in claim
    assert "challengers" not in claim
    # self-knowledge is exempt: the acting agent still knows what it did
    assert "proposed_by_me" in claim
    assert "verified_by_me" in claim
    assert "challenged_by_me" in claim


def test_attributable_observation_reveals_identities(tmp_path):
    _result, events, _paths = _run(ATTR, tmp_path)
    claim = _claim_view(events, "attributable")
    assert claim["proposer"] == "a1"
    assert "verifiers" in claim
    assert "challengers" in claim
    assert "proposed_by_me" in claim


def test_credit_individual_vs_pooled_exact_numbers(tmp_path):
    # Same behaviour, two institutions -> same total credit, different distribution.
    _r_attr, ev_attr, _p = _run(ATTR, tmp_path / "attr")
    _r_agg, ev_agg, _p2 = _run(AGG, tmp_path / "agg")

    def summary(events):
        rc = next(e for e in events if e.event_type == EventType.RUN_COMPLETED)
        return rc.payload

    s_attr = summary(ev_attr)
    s_agg = summary(ev_agg)
    # attributable: credit accrues to the actor (a1 propose +3, a2 verify +2)
    assert s_attr["individual_credit"] == {"a1": "3", "a2": "2", "a3": "0"}
    # aggregate: pool 5 split three ways
    assert s_agg["individual_credit"] == {"a1": "5/3", "a2": "5/3", "a3": "5/3"}
    # collective quality identical (task unchanged by the institution)
    assert s_attr["collective_quality"] == s_agg["collective_quality"] == 12
