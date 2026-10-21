"""Episode runner: the deterministic lifecycle every run follows.

Per round (all deterministic given policies' recorded outputs; ADR-0001):

  1. observe      - one ObservationIssued per agent (sorted order); the FULL
                    observation is in the payload, so hidden-truth leak tests
                    can scan sealed ledgers directly.
  2. propose      - each policy gets its own derived rng stream
                    (*policy_seed_root, "agent", id, "round", t); legacy runs
                    use the condition-specific seed_root instead (ADR-0008).
                    It returns a typed ActionProposal -> ActionProposed event.
  3. validate     - mechanism legality check. Invalid actions become
                    ActionRejected plus the configured fallback: "fail" aborts
                    the run (RunFailed), "abstain" substitutes an explicit
                    AbstainAction (never a silent repair; ADR-0007).
  4. resolve      - mechanism applies all accepted actions simultaneously with
                    its own derived stream; emits domain events.
  5. checkpoint   - at the configured cadence: sealed state snapshot +
                    CheckpointCreated event (branch points; ADR-0002).
  6. seal         - RunCompleted with the mechanism's summary + final state
                    hash (or RunFailed with the reason).

Wall-clock time and other environment facts go only into unhashed event meta.
"""

from copy import deepcopy
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from collaborative_hill.domain.actions import AbstainAction, ActionProposal
from collaborative_hill.engine.events import (
    ENGINE_ACTOR,
    Event,
    EventType,
    make_event,
)
from collaborative_hill.engine.hashing import GENESIS_HASH, content_hash
from collaborative_hill.engine.interfaces import MechanismEngine
from collaborative_hill.engine.seeds import (
    LEGACY_SEED_PROTOCOL,
    PAIRED_SEED_PROTOCOL,
    SeedPath,
    SeedProtocol,
    rng_for,
    validate_seed_metadata,
)
from collaborative_hill.engine.store import FileCheckpointStore, FileEventStore, RunPaths

InvalidActionPolicy = Literal["fail", "abstain"]

# Reserved even when omitted from legacy payloads: supplemental metadata cannot
# add a different account of the seed protocol or other engine-owned facts.
_RUN_STARTED_RESERVED_KEYS = frozenset({
    "agents", "policies", "seed_root", "invalid_action_policy",
    "seed_protocol", "policy_seed_root", "scenario_block",
})


class RunConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    study_id: str
    run_id: str
    seed_root: SeedPath
    seed_protocol: SeedProtocol = LEGACY_SEED_PROTOCOL
    policy_seed_root: SeedPath | None = None
    scenario_block: str | None = None
    checkpoint_every: int = 0  # rounds; 0 = final checkpoint only
    invalid_action_policy: InvalidActionPolicy = "fail"

    @model_validator(mode="after")
    def consistent_seed_metadata(self) -> Self:
        validate_seed_metadata(self.seed_protocol, self.policy_seed_root, self.scenario_block)
        return self


class _Emitter:
    """Sequences, links, and persists events for one run."""

    def __init__(self, store: FileEventStore, study_id: str, run_id: str) -> None:
        self.store = store
        self.study_id = study_id
        self.run_id = run_id
        self.seq = store.count
        self.last_hash = store.last_hash or GENESIS_HASH

    def emit(self, *, logical_time: int, actor: str, event_type: EventType,
             payload: dict[str, Any], meta: dict[str, Any] | None = None) -> Event:
        event = make_event(
            study_id=self.study_id,
            run_id=self.run_id,
            seq=self.seq,
            logical_time=logical_time,
            actor=actor,
            event_type=event_type,
            payload=payload,
            parent_hash=self.last_hash,
            meta=meta,
        )
        self.store.append(event)
        self.seq += 1
        self.last_hash = event.event_hash
        return event


def seal_summary(mechanism: Any, state: dict[str, Any]) -> dict[str, Any]:
    """Mechanism-specific sealed summary (final rewards / scores)."""
    if hasattr(mechanism, "final_rewards"):
        result: dict[str, Any] = mechanism.final_rewards(state)
        return result
    return {"scores": dict(sorted(state["scores"].items()))}


class RunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    status: str  # "completed" | "failed"
    failure_reason: str | None = None
    rounds_played: int
    event_count: int
    final_event_hash: str
    summary: dict[str, Any]


def run_episode(
    *,
    mechanism: MechanismEngine,
    policies: dict[str, Any],
    config: RunConfig,
    paths: RunPaths,
    start_state: dict[str, Any] | None = None,
    start_meta: dict[str, Any] | None = None,
) -> RunResult:
    """Execute one episode (or continue a branched one from ``start_state``).

    ``start_meta`` supplies supplemental hashed RunStarted fields. Engine-owned
    keys are rejected before callbacks or artifact access, including continuations.
    """
    # Validate the same snapshot we emit; callbacks must not be able to inject
    # reserved keys by changing the caller's dictionary after this check.
    start_metadata = dict(start_meta) if start_meta is not None else {}
    reserved = _RUN_STARTED_RESERVED_KEYS.intersection(start_metadata)
    if reserved:
        raise ValueError(
            f"start_meta contains reserved RunStarted keys: {', '.join(sorted(reserved))}"
        )
    if start_state is None:
        # Detach nested values before callbacks can change them. Continuations
        # emit no RunStarted and retain their existing ignored-value behavior.
        start_metadata = deepcopy(start_metadata)

    agent_ids = mechanism.agent_ids()
    if set(policies) != set(agent_ids):
        raise ValueError("policies must cover exactly the mechanism's agents")

    store = FileEventStore(paths.events)
    ckpts = FileCheckpointStore(paths.checkpoints)
    emitter = _Emitter(store, config.study_id, config.run_id)

    state = start_state if start_state is not None else mechanism.initial_state()
    if start_state is None:
        # Do not retrofit new fields into legacy hashed payloads: old sealed
        # ledgers must replay byte-for-byte. New manifests label legacy runs.
        seed_meta = {}
        if config.seed_protocol == PAIRED_SEED_PROTOCOL:
            assert config.policy_seed_root is not None  # validated by RunConfig
            seed_meta = {
                "seed_protocol": config.seed_protocol,
                "policy_seed_root": [str(c) for c in config.policy_seed_root],
                "scenario_block": config.scenario_block,
            }
        emitter.emit(
            logical_time=0,
            actor=ENGINE_ACTOR,
            event_type=EventType.RUN_STARTED,
            payload={
                "agents": sorted(agent_ids),
                "policies": {a: getattr(policies[a], "policy_id", "?") for a in sorted(policies)},
                "seed_root": [str(c) for c in config.seed_root],
                **seed_meta,
                "invalid_action_policy": config.invalid_action_policy,
                **start_metadata,
            },
        )

    failure: str | None = None
    while not mechanism.is_terminal(state):
        t = int(state["round"])

        observations: dict[str, dict[str, Any]] = {}
        for agent in sorted(agent_ids):
            obs = mechanism.observe(state, agent)
            observations[agent] = obs
            emitter.emit(
                logical_time=t, actor=ENGINE_ACTOR,
                event_type=EventType.OBSERVATION_ISSUED,
                payload={"agent_id": agent, "observation": obs},
            )

        accepted: dict[str, Any] = {}
        for agent in sorted(agent_ids):
            policy_root = config.policy_seed_root or config.seed_root
            rng = rng_for(*policy_root, "agent", agent, "round", t)
            try:
                proposal: ActionProposal = policies[agent].propose(observations[agent], rng)
            except Exception as exc:  # provider outages etc. seal the run as failed
                failure = f"policy error for {agent}: {type(exc).__name__}: {exc}"
                break
            emitter.emit(
                logical_time=t, actor=agent,
                event_type=EventType.ACTION_PROPOSED,
                payload={
                    "agent_id": agent,
                    "proposal": proposal.model_dump(mode="json"),
                },
            )
            error = mechanism.validate_action(state, agent, proposal.action)
            if error is None:
                accepted[agent] = proposal.action
                emitter.emit(
                    logical_time=t, actor=ENGINE_ACTOR,
                    event_type=EventType.ACTION_ACCEPTED,
                    payload={"agent_id": agent,
                             "action": proposal.action.model_dump(mode="json")},
                )
                continue
            emitter.emit(
                logical_time=t, actor=ENGINE_ACTOR,
                event_type=EventType.ACTION_REJECTED,
                payload={"agent_id": agent, "reason": error,
                         "proposal": proposal.model_dump(mode="json")},
            )
            if config.invalid_action_policy == "abstain":
                fallback = AbstainAction(reason="invalid_action_fallback")
                fb_error = mechanism.validate_action(state, agent, fallback)
                if fb_error is None:
                    accepted[agent] = fallback
                    emitter.emit(
                        logical_time=t, actor=ENGINE_ACTOR,
                        event_type=EventType.ACTION_ACCEPTED,
                        payload={"agent_id": agent,
                                 "action": fallback.model_dump(mode="json"),
                                 "fallback": True},
                    )
                    continue
                failure = (f"invalid action by {agent} and abstain fallback illegal "
                           f"in this mechanism: {fb_error}")
            else:
                failure = f"invalid action by {agent}: {error}"
            break

        if failure is not None:
            break

        mech_rng = rng_for(*config.seed_root, "mechanism", "round", t)
        state, domain_events = mechanism.resolve(state, accepted, mech_rng)
        for de in domain_events:
            emitter.emit(
                logical_time=t,
                actor=str(de.get("actor", ENGINE_ACTOR)),
                event_type=EventType(de["event_type"]),
                payload=de["payload"],
            )

        new_round = int(state["round"])
        at_cadence = config.checkpoint_every > 0 and new_round % config.checkpoint_every == 0
        if at_cadence and not mechanism.is_terminal(state):
            ckpts.save(seq=emitter.seq - 1, logical_time=new_round,
                       last_event_hash=emitter.last_hash, state=state)
            emitter.emit(
                logical_time=new_round, actor=ENGINE_ACTOR,
                event_type=EventType.CHECKPOINT_CREATED,
                payload={"at_seq": emitter.seq - 1, "round": new_round,
                         "state_hash": content_hash(state)},
            )

    if failure is not None:
        final = emitter.emit(
            logical_time=int(state["round"]), actor=ENGINE_ACTOR,
            event_type=EventType.RUN_FAILED,
            payload={"reason": failure, "final_state_hash": content_hash(state)},
        )
        return RunResult(
            run_id=config.run_id, status="failed", failure_reason=failure,
            rounds_played=int(state["round"]), event_count=store.count,
            final_event_hash=final.event_hash, summary={},
        )

    summary = seal_summary(mechanism, state)
    ckpts.save(seq=emitter.seq - 1, logical_time=int(state["round"]),
               last_event_hash=emitter.last_hash, state=state)
    final = emitter.emit(
        logical_time=int(state["round"]), actor=ENGINE_ACTOR,
        event_type=EventType.RUN_COMPLETED,
        payload={**summary, "final_state_hash": content_hash(state)},
    )
    return RunResult(
        run_id=config.run_id, status="completed", failure_reason=None,
        rounds_played=int(state["round"]), event_count=store.count,
        final_event_hash=final.event_hash, summary=summary,
    )
