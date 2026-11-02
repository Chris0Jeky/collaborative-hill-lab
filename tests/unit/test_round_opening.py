"""The real runner opens a round before observation, including replay adapters."""

from copy import deepcopy

import pytest

from collaborative_hill.agents.scripted.nipd_policies import RandomPolicy
from collaborative_hill.domain.world.nipd import NIPDMechanism, NIPDParams
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.replay import _RoundBoundary
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.seeds import rng_for
from collaborative_hill.engine.store import FileEventStore, RunPaths


class OpeningNIPD(NIPDMechanism):
    """Small mechanism extension exercising the kernel seam, without audit code."""

    def __init__(self, *, extra_consumer=False, rounds=3):
        super().__init__(agent_ids=["a", "b"], mode="neighbourhood",
                         params=NIPDParams(), rounds=rounds)
        self.extra_consumer = extra_consumer

    def prepare_round(self, state, rng_for_key):
        if self.extra_consumer:
            rng_for_key(("unrelated", state["round"])).randrange(100)
        signal = rng_for_key(("fixture", state["round"])).randrange(1_000_000)
        new_state = deepcopy(state)
        new_state["public_signal"] = signal
        return new_state, [{"event_type": "MessageSent", "payload": {"signal": signal}}]

    def observe(self, state, agent_id):
        observation = super().observe(state, agent_id)
        observation["public_signal"] = state.get("public_signal")
        return observation


def execute(mechanism, run_dir, *, policy_root=("policy", 1)):
    config = RunConfig(study_id="opening", run_id="run", seed_root=("world", 7),
                       seed_protocol="paired-policy-v2", policy_seed_root=policy_root,
                       scenario_block="block", checkpoint_every=1)
    with RunPaths(run_dir).reserve() as paths:
        result = run_episode(mechanism=mechanism,
                             policies={a: RandomPolicy("neighbourhood") for a in ("a", "b")},
                             config=config, paths=paths)
    return result, FileEventStore(paths.events).load_all(verify=True)


@pytest.mark.parametrize("wrapped", [False, True])
def test_opening_event_and_state_precede_every_observation(tmp_path, wrapped):
    engine = OpeningNIPD()
    mechanism = _RoundBoundary(engine, 2) if wrapped else engine
    result, events = execute(mechanism, tmp_path / "run")
    rounds = 2 if wrapped else 3
    assert result.status == "completed" and result.rounds_played == rounds
    for t in range(rounds):
        messages = [e for e in events if e.logical_time == t
                    and e.event_type == EventType.MESSAGE_SENT]
        observations = [e for e in events if e.logical_time == t
                        and e.event_type == EventType.OBSERVATION_ISSUED]
        assert len(messages) == 1, "round opening must run once before observations"
        assert len(observations) == 2
        assert messages[0].seq < min(e.seq for e in observations)
        expected_signal = rng_for("world", 7, "mechanism", "round-opening", "fixture", t
                                  ).randrange(1_000_000)
        assert messages[0].payload == {"signal": expected_signal}
        assert all(e.payload["observation"]["public_signal"] == expected_signal
                   for e in observations)
    assert not any(e.event_type == EventType.MESSAGE_SENT and e.logical_time == rounds
                   for e in events), "terminal replay boundaries must not open the child round"


def test_keyed_consumers_do_not_shift_each_other_or_policy_randomness(tmp_path):
    _, plain = execute(NIPDMechanism(agent_ids=["a", "b"], mode="neighbourhood",
                                    params=NIPDParams(), rounds=3), tmp_path / "plain")
    _, first = execute(OpeningNIPD(), tmp_path / "first")
    _, extra = execute(OpeningNIPD(extra_consumer=True), tmp_path / "extra")
    assert first == extra
    kind = EventType.ACTION_PROPOSED
    assert [e.payload for e in plain if e.event_type == kind] == [
        e.payload for e in first if e.event_type == kind
    ]
    _, other_policy_root = execute(OpeningNIPD(), tmp_path / "other", policy_root=("other", 19))
    signals = [e.payload for e in first if e.event_type == EventType.MESSAGE_SENT]
    assert len(signals) == 3
    assert signals == [e.payload for e in other_policy_root
                       if e.event_type == EventType.MESSAGE_SENT]


def test_terminal_initial_state_has_no_opening_events(tmp_path):
    result, events = execute(OpeningNIPD(rounds=0), tmp_path / "terminal")
    assert result.rounds_played == 0
    assert [e.event_type for e in events] == [EventType.RUN_STARTED, EventType.RUN_COMPLETED]
