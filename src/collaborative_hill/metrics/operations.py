"""Operational metrics (v1): run health, never scientific outcomes.

Token/cost figures are read from the manifest and stay None when unmeasured —
these metrics never invent them.
"""

from typing import Any

from collaborative_hill.engine.events import Event, EventType


def operational_metrics(events: list[Event],
                        manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    counts: dict[str, int] = {}
    rejected = 0
    fallbacks = 0
    for ev in events:
        counts[ev.event_type.value] = counts.get(ev.event_type.value, 0) + 1
        if ev.event_type == EventType.ACTION_REJECTED:
            rejected += 1
        if ev.event_type == EventType.ACTION_ACCEPTED and ev.payload.get("fallback"):
            fallbacks += 1

    proposed = counts.get(EventType.ACTION_PROPOSED.value, 0)
    return {
        "version": "1",
        "events_total": len(events),
        "event_counts": dict(sorted(counts.items())),
        "actions_proposed": proposed,
        "actions_rejected": rejected,
        "invalid_action_rate": (rejected / proposed) if proposed else 0.0,
        "fallback_abstentions": fallbacks,
        "run_failed": counts.get(EventType.RUN_FAILED.value, 0) > 0,
        "input_tokens": (manifest or {}).get("input_tokens"),
        "output_tokens": (manifest or {}).get("output_tokens"),
        "cost_usd": (manifest or {}).get("cost_usd"),
    }
