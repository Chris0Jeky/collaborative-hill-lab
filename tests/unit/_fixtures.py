"""Shared builders for the unit suite.

Imported as a bare module (``import _fixtures``) — pytest's default prepend
import mode puts ``tests/unit`` on ``sys.path`` because the directory has no
``__init__.py``. Keeping it a plain helper module (no ``test_`` prefix) means
pytest never collects it as a test.

Nothing here derives expected values from the code under test: these are
construction helpers only. Oracle values live as literals in the test files.
"""

import random
from pathlib import Path
from typing import Any

from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.domain.actions import (
    CooperateAction,
    DefectAction,
    PairwiseVoteAction,
)
from collaborative_hill.domain.evidence import EvidenceSpec
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import (
    ECParams,
    ECWorldSpec,
    EvidenceCommonsMechanism,
)
from collaborative_hill.domain.world.nipd import NIPDMechanism, NIPDParams
from collaborative_hill.engine.runner import RunConfig, run_episode
from collaborative_hill.engine.store import FileEventStore, RunPaths

AGENTS = ("a1", "a2", "a3")


# -- NIPD -----------------------------------------------------------------------


def nipd(mode: str, *, rounds: int = 5, agents=AGENTS, params: NIPDParams | None = None
         ) -> NIPDMechanism:
    return NIPDMechanism(agent_ids=list(agents), mode=mode,
                         params=params or NIPDParams(), rounds=rounds)


def uniform_pairwise(letter: str, agents=AGENTS) -> dict[str, PairwiseVoteAction]:
    return {a: PairwiseVoteAction(moves={o: letter for o in agents if o != a})
            for a in agents}


def pairwise_actions(moves: dict[str, dict[str, str]]) -> dict[str, PairwiseVoteAction]:
    return {a: PairwiseVoteAction(moves=m) for a, m in moves.items()}


def neighbourhood_actions(letters: dict[str, str]):
    return {a: (CooperateAction() if L == "C" else DefectAction())
            for a, L in letters.items()}


def step(mech: Any, state: dict[str, Any], actions: dict[str, Any]):
    """Apply one resolve; rng is unused by both v0 worlds."""
    return mech.resolve(state, actions, random.Random(0))


# -- Evidence Commons -----------------------------------------------------------


def make_evidence(eid: str, slot: str, prop: str, stance: str, true_prop: str, *,
                  holders=(), source: str | None = None, freshness: str = "fresh"
                  ) -> EvidenceSpec:
    """Build an item with ``truth_aligned`` derived from world truth so
    ECWorldSpec.validate_consistency accepts it. The derivation is the world's
    own definition, independent of any mechanism method under test."""
    truth_aligned = (prop == true_prop) == (stance == "supports")
    return EvidenceSpec(
        evidence_id=eid, source_id=source or f"src_{eid}", slot_id=slot,
        proposition_id=prop, stance=stance, freshness=freshness,
        truth_aligned=truth_aligned, initial_holders=tuple(holders),
    )


def ec_hand_example(institution: InstitutionConfig, *, rounds: int = 12
                    ) -> EvidenceCommonsMechanism:
    """Single slot s1 (true=p1a), one fresh supporting item e1 held by a1 & a2."""
    e1 = make_evidence("e1", "s1", "p1a", "supports", "p1a", holders=("a1", "a2"))
    spec = ECWorldSpec(
        agent_ids=AGENTS, slots={"s1": ("p1a", "p1b")},
        true_propositions={"s1": "p1a"}, evidence=(e1,), params=ECParams(rounds=rounds),
    )
    return EvidenceCommonsMechanism(spec=spec, institution=institution)


def ec_provenance_world(rounds: int = 8) -> ECWorldSpec:
    """Two slots. e1 (a1) supports true p1a; e2 (a3) supports FALSE p2b; e3 (a2)
    contradicts p2b. Drives a real run with a proposal, a supported verification,
    and a valid challenge."""
    e1 = make_evidence("e1", "s1", "p1a", "supports", "p1a", holders=("a1",))
    e2 = make_evidence("e2", "s2", "p2b", "supports", "p2a", holders=("a3",))
    e3 = make_evidence("e3", "s2", "p2b", "contradicts", "p2a", holders=("a2",))
    return ECWorldSpec(
        agent_ids=AGENTS,
        slots={"s1": ("p1a", "p1b"), "s2": ("p2a", "p2b")},
        true_propositions={"s1": "p1a", "s2": "p2a"},
        evidence=(e1, e2, e3), params=ECParams(rounds=rounds),
    )


def ec_provenance_run(tmp_path, *, accountability: str = "attributable"):
    """Run the provenance world with contributor/verifier/misinformer policies."""
    spec = ec_provenance_world()
    mech = EvidenceCommonsMechanism(
        spec=spec, institution=InstitutionConfig(accountability=accountability))
    policies = {
        "a1": build_ec_policy("ec_contributor", {}),
        "a2": build_ec_policy("ec_verifier", {}),
        "a3": build_ec_policy("ec_misinformer", {}),
    }
    return run_episode_tmp(mech, policies, tmp_path, run_id="ec_prov")


# -- run harness ----------------------------------------------------------------


def run_episode_tmp(mechanism, policies, tmp_path, *, seed_root=("seed", "cond", 0),
                    invalid_action_policy: str = "fail", checkpoint_every: int = 0,
                    study_id: str = "study-t", run_id: str = "run-t"):
    """Run one episode in an isolated dir; return (result, verified_events, paths)."""
    paths = RunPaths(Path(tmp_path) / run_id).create()
    config = RunConfig(
        study_id=study_id, run_id=run_id, seed_root=tuple(seed_root),
        checkpoint_every=checkpoint_every, invalid_action_policy=invalid_action_policy,
    )
    result = run_episode(mechanism=mechanism, policies=policies, config=config, paths=paths)
    events = FileEventStore(paths.events).load_all(verify=True)
    return result, events, paths


def nipd_pairwise_2tft_alld_run(tmp_path, *, rounds: int = 5):
    """Two pairwise-TFT reciprocators plus one AllD — the legacy-defect fixture run."""
    mech = nipd("pairwise", rounds=rounds)
    policies = {
        "a1": build_nipd_policy("tft_pairwise", "pairwise", {}),
        "a2": build_nipd_policy("tft_pairwise", "pairwise", {}),
        "a3": build_nipd_policy("alld", "pairwise", {}),
    }
    return run_episode_tmp(mech, policies, tmp_path, run_id="pw_legacy")
