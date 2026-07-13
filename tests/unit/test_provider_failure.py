"""A provider outage seals the run as RunFailed with a typed reason naming the
agent — and the ledger chain still verifies end to end."""

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.store import FileEventStore
from collaborative_hill.experiments.scenario import NarrativeSkin

from _fixtures import AGENTS, ec_hand_example, run_episode_tmp

SKIN = NarrativeSkin(skin_id="plain")
GOOD = '{"action":{"type":"abstain"}}'


def _llm(agent_id, *, fail_at=None):
    return LLMPolicy(agent_id, FakeProvider([GOOD] * 20, fail_at=fail_at), SKIN)


def test_provider_outage_seals_runfailed_naming_agent(tmp_path):
    mech = ec_hand_example(InstitutionConfig(), rounds=3)
    # a1 is first to act (sorted); fail its provider on the very first call.
    policies = {a: _llm(a, fail_at=(0 if a == "a1" else None)) for a in AGENTS}
    result, _events, paths = run_episode_tmp(
        mech, policies, tmp_path, invalid_action_policy="fail", run_id="prov_fail")

    assert result.status == "failed"
    assert result.failure_reason is not None
    assert "a1" in result.failure_reason
    assert "ProviderError" in result.failure_reason

    events = FileEventStore(paths.events).load_all(verify=True)  # chain must verify
    assert events[-1].event_type == EventType.RUN_FAILED
    assert "a1" in events[-1].payload["reason"]
