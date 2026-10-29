"""Compiled observations, fresh policies and recorded actions reproduce chains.

Direct policy construction keeps this foundation test independent of the study
and CLI registration layer. Narrative-bearing start metadata is intentionally
omitted when comparing full chains across skins, as in the existing skin test.
"""

import pytest

from collaborative_hill.agents.replay import (
    ReplayPolicy,
    policy_ids_from_events,
    proposals_from_events,
)
from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.scenario import compile_scenario

from ._helpers import default_ec_evidence, ec_spec, plain_skin, rich_ec_skin

pytestmark = pytest.mark.metamorphic


class RebuiltPolicy:
    """A new policy instance for every observed decision, with the same config."""

    def __init__(self, specification):
        self.specification = specification
        self.policy_id = build_ec_policy(specification.name, dict(specification.params)).policy_id

    def propose(self, observation, rng):
        return build_ec_policy(self.specification.name, dict(self.specification.params)).propose(
            observation, rng,
        )


def execute(resolved, directory, policies):
    paths = RunPaths(directory).create()
    result = run_episode(
        mechanism=resolved.build_mechanism(), policies=policies,
        config=RunConfig(study_id="responsive", run_id="r", seed_root=("responsive", 0),
                         checkpoint_every=3),
        paths=paths,
    )
    assert result.status == "completed", result.failure_reason
    return result, FileEventStore(paths.events).load_all(verify=True)


@pytest.mark.parametrize("accountability", ["aggregate", "attributable"])
@pytest.mark.parametrize("topology", ["private", "shared_ledger"])
def test_skin_fresh_instance_and_recorded_action_replay_invariants(
    tmp_path, accountability, topology,
):
    spec = ec_spec(
        default_ec_evidence(),
        institution=InstitutionConfig(accountability=accountability, evidence_topology=topology),
        agents=(("a1", "ec_conditional_contributor"),
                ("a2", "ec_contributor"), ("a3", "ec_freerider")),
    )
    plain = compile_scenario(spec, plain_skin())
    rich = compile_scenario(spec, rich_ec_skin())
    assert plain.mechanism_hash == rich.mechanism_hash
    assert plain.narrative_hash != rich.narrative_hash
    original = {a.agent_id: build_ec_policy(a.policy.name, dict(a.policy.params))
                for a in spec.cognition.agents}
    original_result, original_events = execute(plain, tmp_path / "original", original)
    fresh = {a.agent_id: RebuiltPolicy(a.policy) for a in spec.cognition.agents}
    fresh_result, fresh_events = execute(rich, tmp_path / "fresh-rich", fresh)
    assert fresh_result.summary == original_result.summary
    assert [event.event_hash for event in fresh_events] == [
        event.event_hash for event in original_events
    ]
    proposals = proposals_from_events(original_events)
    assert any(proposal.action.type == "propose_claim"
               for proposal in proposals["a1"].values())
    identities = policy_ids_from_events(original_events)
    recorded = {agent: ReplayPolicy(agent, identities[agent], proposals[agent])
                for agent in identities}
    replay_result, replay_events = execute(plain, tmp_path / "replay", recorded)
    assert replay_result.summary == original_result.summary
    assert [event.event_hash for event in replay_events] == [
        event.event_hash for event in original_events
    ]
