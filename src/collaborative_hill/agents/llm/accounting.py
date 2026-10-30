"""Measured usage and provider provenance, independent of scientific outcomes."""

from collections.abc import Mapping, Sequence
from typing import Any

from collaborative_hill.agents.llm.budget import RequestBudget
from collaborative_hill.agents.llm.providers import ProviderAttempt


def summarize_attempts(attempts: Sequence[ProviderAttempt]) -> dict[str, int | None]:
    """Unknown dimensions never become a total by silently dropping a request."""
    result: dict[str, int | None] = {"request_attempts": len(attempts)}
    for dimension in ("input", "output"):
        values = [getattr(attempt, f"{dimension}_tokens") for attempt in attempts]
        known = [value for value in values if value is not None]
        result[f"known_{dimension}_tokens"] = sum(known)
        result[f"{dimension}_measured_attempts"] = len(known)
        result[f"{dimension}_tokens"] = (
            sum(known) if values and len(known) == len(values) else None
        )
    return result


def llm_manifest_fields(policies: Mapping[str, Any], *,
                        since: Mapping[str, int] | None = None,
                        budget: RequestBudget | None = None) -> dict[str, Any]:
    """Manifest updates for an episode or an explicitly offset continuation.

    Snapshot each LLMPolicy.call_count before continuing reused policy objects.
    A ``budget`` adds its settings, charged attempts and stable stop reason.
    Transcript slicing uses its own length because legacy failures have no raw
    completion transcript. Costs remain unavailable; token counts are not prices.
    """
    from collaborative_hill.agents.llm.policy import LLMPolicy

    selected = {agent: policy for agent, policy in sorted(policies.items())
                if isinstance(policy, LLMPolicy)}
    offsets = since or {}
    if set(offsets) - set(selected):
        raise ValueError("usage offsets must refer to the current LLM policies")
    metadata = {agent: policy.audit_metadata(since=offsets.get(agent, 0))
                for agent, policy in selected.items()}
    usage = {agent: policy.usage_totals(since=offsets.get(agent, 0))
             for agent, policy in selected.items()}

    def total(key: str) -> int:
        return sum(int(item[key] or 0) for item in usage.values())

    fields: dict[str, Any] = {
        "providers": {agent: item["provider"] for agent, item in metadata.items()},
        "prompt_template_hashes": {agent: item["prompt_template_hash"]
                                   for agent, item in metadata.items()},
        "sampling": {agent: item["sampling"] for agent, item in metadata.items()
                     if item["sampling"]},
        "provider_metadata": {agent: item["provider_metadata"]
                              for agent, item in metadata.items() if item["provider_metadata"]},
        "reported_models": {agent: item["reported_models"] for agent, item in metadata.items()},
        "provider_usage": usage,
        "provider_usage_scope": ("continuation" if since is not None else "episode")
        if selected else None,
        "cost_usd": None,
    }
    if budget is not None:  # unbudgeted runs keep the manifest default of null
        fields["request_budget"] = budget.snapshot()
    requests = total("request_attempts")
    for dimension in ("input", "output"):
        fields[f"{dimension}_tokens"] = (
            total(f"known_{dimension}_tokens")
            if requests and total(f"{dimension}_measured_attempts") == requests else None
        )
    return fields
