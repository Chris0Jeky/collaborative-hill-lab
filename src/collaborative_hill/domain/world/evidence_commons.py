"""Evidence Commons v0 — a social dilemma over shared truth.

Agents jointly assemble a briefing: for each briefing *slot* they may propose,
verify, and challenge *claims* (proposition ids from a finite, environment-
defined space) citing *evidence items*. Contribution actions cost effort;
the briefing's final quality pays out equally to everyone — so free-riding
(Withhold) is individually tempting while collective quality needs work.
The mechanism certificate (studies/001) proves the dilemma by enumeration
for the configured parameters.

Deterministic rules, all adjudicated by typed code (never a model):

- INSPECT: spend inspect budget; learn an item's structured facts.
- SHARE (private topology): spend effort; item becomes visible to all.
- PROPOSE: spend effort; create a claim (slot, proposition, citations).
- VERIFY: spend verify budget; the ENGINE checks provenance — outcome
  "supported" iff >=1 cited item is accessible to the verifier, fresh, and
  supports the proposition. Verification checks provenance, NOT truth:
  well-cited misinformation passes; that is the epistemics under study.
- CHALLENGE: spend effort; valid iff >=1 cited item is accessible to the
  challenger, fresh, and contradicts the claim's proposition.
- WITHHOLD/ABSTAIN: no cost, no effect (Withhold = deliberate free-riding,
  Abstain = safe no-op/fallback; identical mechanics, distinct events).

Acceptance (at seal, per slot): candidates with net_support >= 1 where
net_support = supported-verifications - valid-challenges; winner = highest
net_support, ties -> earliest claim. Self-verification does not count.

Scoring (integer credit units): each agent's utility =
    individual_credit + collective_quality/N - effort_spent
where collective_quality = sum over slots of +B_correct (accepted claim's
proposition true) / -B_wrong (false), and individual credit accrues to
proposers/verifiers of accepted claims (attributable accountability) or is
pooled and split equally (aggregate accountability). The institution changes
attribution and visibility only — never legal actions or the task.

ApproveClaim is a documented v1 extension point: the action type exists in
the union but is not legal in v0 (acceptance is the deterministic net-support
rule above).
"""

import copy
import random
from fractions import Fraction
from typing import Any

from pydantic import BaseModel, ConfigDict

from collaborative_hill.domain.actions import (
    AbstainAction,
    Action,
    ChallengeClaimAction,
    InspectEvidenceAction,
    ProposeClaimAction,
    ShareEvidenceAction,
    VerifyClaimAction,
    WithholdAction,
)
from collaborative_hill.domain.evidence import EvidenceSpec
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.hashing import frac_str


class ECParams(BaseModel):
    """Integer credit-unit parameters. Defaults provably yield a social dilemma
    at N=3 (see the mechanism certificate); final weights are HUMAN-OWNED."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rounds: int = 12
    inspect_budget: int = 6
    verify_budget: int = 3
    cost_inspect: int = 1
    cost_share: int = 1
    cost_propose: int = 1
    cost_verify: int = 2
    cost_challenge: int = 1
    benefit_correct_slot: int = 12
    penalty_wrong_slot: int = 12
    credit_propose_accepted_correct: int = 3
    credit_propose_accepted_wrong: int = -3
    credit_verify_accepted_correct: int = 2
    credit_verify_accepted_wrong: int = -2


class ECWorldSpec(BaseModel):
    """World + information plane content for one Evidence Commons episode."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_ids: tuple[str, ...]
    slots: dict[str, tuple[str, ...]]  # slot_id -> candidate proposition ids
    true_propositions: dict[str, str]  # slot_id -> the true proposition (HIDDEN)
    evidence: tuple[EvidenceSpec, ...]
    params: ECParams = ECParams()

    def validate_consistency(self) -> None:
        for slot, true_prop in self.true_propositions.items():
            if slot not in self.slots:
                raise ValueError(f"truth for unknown slot {slot}")
            if true_prop not in self.slots[slot]:
                raise ValueError(f"true proposition {true_prop} not a candidate of {slot}")
        if set(self.true_propositions) != set(self.slots):
            raise ValueError("every slot needs exactly one true proposition")
        seen = set()
        for item in self.evidence:
            if item.evidence_id in seen:
                raise ValueError(f"duplicate evidence id {item.evidence_id}")
            seen.add(item.evidence_id)
            if item.slot_id not in self.slots:
                raise ValueError(f"evidence {item.evidence_id} references unknown slot")
            if item.proposition_id not in self.slots[item.slot_id]:
                raise ValueError(f"evidence {item.evidence_id} references unknown proposition")
            supports_truth = (
                item.proposition_id == self.true_propositions[item.slot_id]
            ) == (item.stance == "supports")
            if item.truth_aligned != supports_truth:
                raise ValueError(
                    f"evidence {item.evidence_id}: truth_aligned flag inconsistent with world truth"
                )
            for holder in item.initial_holders:
                if holder not in self.agent_ids:
                    raise ValueError(f"evidence {item.evidence_id}: unknown holder {holder}")


class EvidenceCommonsMechanism:
    """Deterministic Evidence Commons engine. See module docstring for rules."""

    def __init__(self, *, spec: ECWorldSpec, institution: InstitutionConfig) -> None:
        spec.validate_consistency()
        self.spec = spec
        self.institution = institution
        self.params = spec.params
        self._by_id = {e.evidence_id: e for e in spec.evidence}

    def agent_ids(self) -> list[str]:
        return list(self.spec.agent_ids)

    def initial_state(self) -> dict[str, Any]:
        visible: dict[str, list[str]] = {}
        for item in self.spec.evidence:
            if self.institution.evidence_topology == "shared_ledger":
                # ledger publishes existence+source metadata to all from round 0
                visible[item.evidence_id] = sorted(self.spec.agent_ids)
            else:
                visible[item.evidence_id] = sorted(item.initial_holders)
        return {
            "round": 0,
            "budgets": {
                a: {"inspect": self.params.inspect_budget, "verify": self.params.verify_budget}
                for a in self.spec.agent_ids
            },
            "effort": dict.fromkeys(self.spec.agent_ids, 0),
            "credits": dict.fromkeys(self.spec.agent_ids, 0),
            "visible_to": visible,
            "inspected": {a: [] for a in self.spec.agent_ids},
            "claims": {},
            "claim_order": [],
            "next_claim_seq": 1,
        }

    def is_terminal(self, state: dict[str, Any]) -> bool:
        return int(state["round"]) >= self.params.rounds

    # -- helpers ---------------------------------------------------------------

    def _accessible(self, state: dict[str, Any], agent_id: str, evidence_id: str) -> bool:
        return agent_id in state["visible_to"].get(evidence_id, [])

    def _claim_net_support(self, claim: dict[str, Any]) -> int:
        supported = sum(1 for v in claim["verifications"] if v["outcome"] == "supported")
        valid_challenges = sum(1 for c in claim["challenges"] if c["valid"])
        return supported - valid_challenges

    # -- observation -----------------------------------------------------------

    def observe(self, state: dict[str, Any], agent_id: str) -> dict[str, Any]:
        """Agent view. NEVER includes true_propositions, truth_aligned, or other
        agents' budgets/effort/credit. Attribution follows the institution."""
        attributable = self.institution.accountability == "attributable"
        visible_ids = sorted(
            eid for eid in state["visible_to"] if self._accessible(state, agent_id, eid)
        )
        inspected = list(state["inspected"][agent_id])
        evidence_view = []
        for eid in visible_ids:
            item = self._by_id[eid]
            entry: dict[str, Any] = {
                "evidence_id": eid,
                "source_id": item.source_id,
                "slot_id": item.slot_id,
                # institutional bookkeeping, not truth: is this item public?
                "public": len(state["visible_to"][eid]) == len(self.spec.agent_ids),
            }
            if eid in inspected:
                entry["facts"] = item.observable_facts()
            evidence_view.append(entry)

        claims_view = []
        for cid in state["claim_order"]:
            claim = state["claims"][cid]
            entry = {
                "claim_id": cid,
                "slot_id": claim["slot_id"],
                "proposition_id": claim["proposition_id"],
                "evidence_ids": list(claim["cited"]),
                "net_support": self._claim_net_support(claim),
                "n_verifications": len(claim["verifications"]),
                "n_challenges": len(claim["challenges"]),
            }
            if attributable:
                entry["proposer"] = claim["proposer"]
                entry["verifiers"] = sorted(v["agent"] for v in claim["verifications"])
                entry["challengers"] = sorted(c["agent"] for c in claim["challenges"])
            # self-knowledge is exempt from anonymization: an agent always knows
            # what it itself did, under any accountability institution.
            entry["proposed_by_me"] = claim["proposer"] == agent_id
            entry["verified_by_me"] = any(v["agent"] == agent_id for v in claim["verifications"])
            entry["challenged_by_me"] = any(c["agent"] == agent_id for c in claim["challenges"])
            claims_view.append(entry)

        return {
            "mechanism": "evidence_commons",
            "round": state["round"],
            "n_agents": len(self.spec.agent_ids),
            "self_id": agent_id,
            "accountability": self.institution.accountability,
            "evidence_topology": self.institution.evidence_topology,
            "slots": {s: list(props) for s, props in sorted(self.spec.slots.items())},
            "my_budgets": dict(state["budgets"][agent_id]),
            "my_effort_spent": state["effort"][agent_id],
            "my_credit": state["credits"][agent_id] if attributable else None,
            "evidence": evidence_view,
            "claims": claims_view,
        }

    # -- legality ----------------------------------------------------------------

    def validate_action(self, state: dict[str, Any], agent_id: str,
                        action: Action) -> str | None:
        if isinstance(action, WithholdAction | AbstainAction):
            return None
        if isinstance(action, InspectEvidenceAction):
            if state["budgets"][agent_id]["inspect"] <= 0:
                return "inspect budget exhausted"
            if not self._accessible(state, agent_id, action.evidence_id):
                return f"evidence {action.evidence_id} not visible to {agent_id}"
            return None
        if isinstance(action, ShareEvidenceAction):
            if self.institution.evidence_topology == "shared_ledger":
                return "sharing is a no-op under shared_ledger topology; not a legal action"
            if not self._accessible(state, agent_id, action.evidence_id):
                return f"cannot share evidence {action.evidence_id} you do not hold"
            return None
        if isinstance(action, ProposeClaimAction):
            if action.slot_id not in self.spec.slots:
                return f"unknown slot {action.slot_id}"
            if action.proposition_id not in self.spec.slots[action.slot_id]:
                return f"proposition {action.proposition_id} not a candidate for {action.slot_id}"
            for eid in action.evidence_ids:
                if eid not in self._by_id:
                    return f"cited evidence {eid} does not exist"
                if not self._accessible(state, agent_id, eid):
                    return f"cited evidence {eid} not visible to proposer"
            return None
        if isinstance(action, VerifyClaimAction):
            if state["budgets"][agent_id]["verify"] <= 0:
                return "verify budget exhausted"
            claim = state["claims"].get(action.claim_id)
            if claim is None:
                return f"unknown claim {action.claim_id}"
            if claim["proposer"] == agent_id:
                return "self-verification is not allowed"
            return None
        if isinstance(action, ChallengeClaimAction):
            if action.claim_id not in state["claims"]:
                return f"unknown claim {action.claim_id}"
            for eid in action.evidence_ids:
                if eid not in self._by_id:
                    return f"cited evidence {eid} does not exist"
                if not self._accessible(state, agent_id, eid):
                    return f"cited counter-evidence {eid} not visible to challenger"
            return None
        return f"action {action.type} is not part of Evidence Commons v0"

    # -- resolution ----------------------------------------------------------------

    def resolve(
        self,
        state: dict[str, Any],
        actions: dict[str, Action],
        rng: random.Random,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        del rng  # v0 world dynamics are deterministic; randomness lives in policies
        rnd = int(state["round"])
        new = copy.deepcopy(state)
        events: list[dict[str, Any]] = []
        attributable = self.institution.accountability == "attributable"

        def actor_label(agent: str) -> str:
            return agent if attributable else "anonymous"

        # Simultaneous submission, deterministic application order: sorted by
        # agent id (documented; claims created this round get ids in that order).
        for agent in sorted(actions):
            action = actions[agent]
            if isinstance(action, WithholdAction | AbstainAction):
                # no cost, no effect; the runner's ActionAccepted event records it
                continue
            if isinstance(action, InspectEvidenceAction):
                new["budgets"][agent]["inspect"] -= 1
                new["effort"][agent] += self.params.cost_inspect
                if action.evidence_id not in new["inspected"][agent]:
                    new["inspected"][agent].append(action.evidence_id)
                events.append({
                    "event_type": EventType.EVIDENCE_INSPECTED.value, "actor": agent,
                    "payload": {"round": rnd, "agent_id": agent,
                                "evidence_id": action.evidence_id},
                })
            elif isinstance(action, ShareEvidenceAction):
                new["effort"][agent] += self.params.cost_share
                new["visible_to"][action.evidence_id] = sorted(self.spec.agent_ids)
                events.append({
                    "event_type": EventType.EVIDENCE_SHARED.value,
                    "actor": actor_label(agent),
                    "payload": {"round": rnd, "agent_id": agent,
                                "evidence_id": action.evidence_id,
                                "attributed": attributable},
                })
            elif isinstance(action, ProposeClaimAction):
                cid = f"c{new['next_claim_seq']}"
                new["next_claim_seq"] += 1
                new["effort"][agent] += self.params.cost_propose
                new["claims"][cid] = {
                    "claim_id": cid,
                    "slot_id": action.slot_id,
                    "proposition_id": action.proposition_id,
                    "proposer": agent,
                    "cited": sorted(action.evidence_ids),
                    "verifications": [],
                    "challenges": [],
                    "round": rnd,
                }
                new["claim_order"].append(cid)
                events.append({
                    "event_type": EventType.CLAIM_PROPOSED.value,
                    "actor": actor_label(agent),
                    "payload": {"round": rnd, "agent_id": agent, "claim_id": cid,
                                "slot_id": action.slot_id,
                                "proposition_id": action.proposition_id,
                                "evidence_ids": sorted(action.evidence_ids),
                                "attributed": attributable},
                })
            elif isinstance(action, VerifyClaimAction):
                new["budgets"][agent]["verify"] -= 1
                new["effort"][agent] += self.params.cost_verify
                claim = new["claims"][action.claim_id]
                outcome = self._adjudicate_verification(new, agent, claim)
                claim["verifications"].append({"agent": agent, "outcome": outcome})
                events.append({
                    "event_type": EventType.CLAIM_VERIFIED.value,
                    "actor": actor_label(agent),
                    "payload": {"round": rnd, "agent_id": agent,
                                "claim_id": action.claim_id, "outcome": outcome,
                                "attributed": attributable},
                })
            elif isinstance(action, ChallengeClaimAction):
                new["effort"][agent] += self.params.cost_challenge
                claim = new["claims"][action.claim_id]
                valid = self._adjudicate_challenge(new, agent, claim, list(action.evidence_ids))
                claim["challenges"].append(
                    {"agent": agent, "valid": valid, "cited": sorted(action.evidence_ids)}
                )
                events.append({
                    "event_type": EventType.CLAIM_CHALLENGED.value,
                    "actor": actor_label(agent),
                    "payload": {"round": rnd, "agent_id": agent,
                                "claim_id": action.claim_id, "valid": valid,
                                "evidence_ids": sorted(action.evidence_ids),
                                "attributed": attributable},
                })
            else:  # pragma: no cover - validate_action gates this
                raise AssertionError(f"unvalidated action reached resolve: {action.type}")

        new["round"] = rnd + 1
        events.append({
            "event_type": EventType.WORLD_TRANSITIONED.value, "actor": "engine",
            "payload": {"round": rnd, "n_claims": len(new["claim_order"])},
        })
        return new, events

    def _adjudicate_verification(self, state: dict[str, Any], verifier: str,
                                 claim: dict[str, Any]) -> str:
        """Provenance check by typed code. 'supported' iff >=1 cited item is
        accessible to the verifier, fresh, and supports the claim's proposition."""
        for eid in claim["cited"]:
            item = self._by_id.get(eid)
            if item is None or not self._accessible(state, verifier, eid):
                continue
            if (item.freshness == "fresh" and item.stance == "supports"
                    and item.proposition_id == claim["proposition_id"]
                    and item.slot_id == claim["slot_id"]):
                return "supported"
        return "not_supported"

    def _adjudicate_challenge(self, state: dict[str, Any], challenger: str,
                              claim: dict[str, Any], cited: list[str]) -> bool:
        """Valid iff >=1 cited item is accessible to the challenger, fresh, and
        contradicts the claim's proposition (same slot)."""
        for eid in cited:
            item = self._by_id.get(eid)
            if item is None or not self._accessible(state, challenger, eid):
                continue
            if (item.freshness == "fresh" and item.stance == "contradicts"
                    and item.proposition_id == claim["proposition_id"]
                    and item.slot_id == claim["slot_id"]):
                return True
        return False

    # -- sealing --------------------------------------------------------------------

    def final_briefing(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Deterministic acceptance: per slot, highest net_support >= 1 wins;
        ties break to the earliest claim. Includes truth + provenance audit
        fields — this output feeds scoring and the sealed RunCompleted event."""
        briefing: list[dict[str, Any]] = []
        for slot in sorted(self.spec.slots):
            candidates = [
                c for c in state["claims"].values()
                if c["slot_id"] == slot and self._claim_net_support(c) >= 1
            ]
            if not candidates:
                briefing.append({"slot_id": slot, "claim_id": None})
                continue
            candidates.sort(
                key=lambda c: (-self._claim_net_support(c),
                               state["claim_order"].index(c["claim_id"]))
            )
            winner = candidates[0]
            provenance_ok = any(
                self._by_id[eid].freshness == "fresh"
                and self._by_id[eid].stance == "supports"
                and self._by_id[eid].proposition_id == winner["proposition_id"]
                for eid in winner["cited"]
                if eid in self._by_id
            )
            briefing.append({
                "slot_id": slot,
                "claim_id": winner["claim_id"],
                "proposition_id": winner["proposition_id"],
                "proposer": winner["proposer"],
                "correct": winner["proposition_id"] == self.spec.true_propositions[slot],
                "provenance_ok": provenance_ok,
                "net_support": self._claim_net_support(winner),
            })
        return briefing

    def final_rewards(self, state: dict[str, Any]) -> dict[str, Any]:
        """Utility per agent = individual_credit + collective_quality/N - effort.

        Under aggregate accountability the earned individual credits are pooled
        and split equally — same total value, no attribution."""
        briefing = self.final_briefing(state)
        n = len(self.spec.agent_ids)
        quality = 0
        credits = dict.fromkeys(self.spec.agent_ids, 0)
        for entry in briefing:
            if entry["claim_id"] is None:
                continue
            claim = state["claims"][entry["claim_id"]]
            if entry["correct"]:
                quality += self.params.benefit_correct_slot
                credits[claim["proposer"]] += self.params.credit_propose_accepted_correct
                for v in claim["verifications"]:
                    if v["outcome"] == "supported":
                        credits[v["agent"]] += self.params.credit_verify_accepted_correct
            else:
                quality -= self.params.penalty_wrong_slot
                credits[claim["proposer"]] += self.params.credit_propose_accepted_wrong
                for v in claim["verifications"]:
                    if v["outcome"] == "supported":
                        credits[v["agent"]] += self.params.credit_verify_accepted_wrong

        if self.institution.accountability == "aggregate":
            pool = sum(credits.values())
            individual = {a: Fraction(pool, n) for a in self.spec.agent_ids}
        else:
            individual = {a: Fraction(credits[a]) for a in self.spec.agent_ids}

        utilities = {}
        for a in self.spec.agent_ids:
            utilities[a] = individual[a] + Fraction(quality, n) - state["effort"][a]
        return {
            "briefing": briefing,
            "collective_quality": quality,
            "individual_credit": {a: frac_str(individual[a]) for a in sorted(individual)},
            "effort": {a: state["effort"][a] for a in sorted(self.spec.agent_ids)},
            "utility": {a: frac_str(utilities[a]) for a in sorted(utilities)},
        }
