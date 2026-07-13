"""Cooperation metrics (v1) — defined for NIPD ledgers.

Definitions (pre-registered wording; the episode is the unit of analysis):

- cooperation_rate_by_round: cooperative votes / total votes cast that round
  (pairwise counts each per-opponent move as one vote; neighbourhood counts
  each agent's single vote).
- mean_cooperation: unweighted mean of the per-round rates over the episode.
- final_window_cooperation: mean over the last ``window`` rounds (default 10,
  capped at episode length) — the convergence estimate.
- per_agent_cooperation: each agent's cooperative votes / its total votes.
- first_full_defection_round: first round with zero cooperative votes, else None.
- collapsed: final_window_cooperation <= 0.1 (descriptive flag, not a test).
"""

from typing import Any

from collaborative_hill.engine.events import Event, EventType


def cooperation_metrics(events: list[Event], *, window: int = 10) -> dict[str, Any]:
    by_round: list[tuple[int, int, int]] = []  # (round, coop_votes, total_votes)
    per_agent_coop: dict[str, int] = {}
    per_agent_total: dict[str, int] = {}

    for ev in events:
        if ev.event_type != EventType.WORLD_TRANSITIONED:
            continue
        p = ev.payload
        if "cooperative_votes" not in p:
            continue
        by_round.append((p["round"], p["cooperative_votes"], p["total_votes"]))
        if p.get("mode") == "pairwise":
            for pair in p["pair_results"]:
                for agent, move in ((pair["a"], pair["move_ab"]), (pair["b"], pair["move_ba"])):
                    per_agent_total[agent] = per_agent_total.get(agent, 0) + 1
                    if move == "C":
                        per_agent_coop[agent] = per_agent_coop.get(agent, 0) + 1
        elif p.get("mode") == "neighbourhood":
            for agent, move in p["moves"].items():
                per_agent_total[agent] = per_agent_total.get(agent, 0) + 1
                if move == "C":
                    per_agent_coop[agent] = per_agent_coop.get(agent, 0) + 1

    if not by_round:
        return {"version": "1", "rounds": 0}

    by_round.sort()
    rates = [c / t for _, c, t in by_round]
    w = min(window, len(rates))
    final_window = sum(rates[-w:]) / w
    first_full_defection = next((rnd for rnd, c, _ in by_round if c == 0), None)
    return {
        "version": "1",
        "rounds": len(rates),
        "cooperation_rate_by_round": rates,
        "mean_cooperation": sum(rates) / len(rates),
        "final_window_cooperation": final_window,
        "final_window": w,
        "per_agent_cooperation": {
            a: per_agent_coop.get(a, 0) / per_agent_total[a]
            for a in sorted(per_agent_total)
        },
        "first_full_defection_round": first_full_defection,
        "collapsed": final_window <= 0.1,
    }
