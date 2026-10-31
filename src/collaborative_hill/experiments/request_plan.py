"""Offline worst-case request plan for a study selection (ADR-0015).

Reads only study files. No policy is built, no credential is read and nothing
touches the network. Counts are maxima for episodes that run to completion: an
LLM agent proposes once per round, each proposal may need ``max_retries`` extra
action-repair completions, and each completion may need ``rate_limit_retries``
extra HTTP 429 attempts. Real usage can be lower and is never inferred here.
"""

from pathlib import Path
from typing import Any

from collaborative_hill.agents.llm.configuration import validate_provider_params
from collaborative_hill.experiments.scenario import ECWorld, ResolvedScenario
from collaborative_hill.experiments.study import load_study, select_replicates

_NOTE = ("Maxima, not predictions or measurements. Token figures are the requested "
         "completion cap times attempts; input tokens and prices are not estimated.")


def _agent_plan(name: str, params: dict[str, Any], rounds: int) -> dict[str, Any] | None:
    if name == "llm_openai_compatible":
        config = validate_provider_params(params)  # offline; never reads api_key_env
        repair, retry_429 = config.max_retries, config.rate_limit_retries
        cap = config.sampling.get("max_completion_tokens", config.sampling.get("max_tokens"))
    elif name == "llm_fake":
        repair, retry_429, cap = int(params.get("max_retries", 1)), 0, None
    else:
        return None
    completions = rounds * (repair + 1)
    attempts = completions * (retry_429 + 1) if name == "llm_openai_compatible" else 0
    return {
        "network": name == "llm_openai_compatible",
        "max_logical_completions": completions,
        "max_action_repair_completions": rounds * repair,
        "max_rate_limit_retry_attempts": completions * retry_429 if attempts else 0,
        "max_http_request_attempts": attempts,
        "requested_output_token_ceiling": attempts * cap if cap is not None else None,
    }


def _episode(scenario: ResolvedScenario) -> dict[str, Any]:
    world = scenario.spec.world
    rounds = world.params.rounds if isinstance(world, ECWorld) else world.rounds
    agents = {a.agent_id: p for a in scenario.spec.cognition.agents
              if (p := _agent_plan(a.policy.name, dict(a.policy.params), rounds)) is not None}
    totals = {key: sum(item[key] for item in agents.values())
              for key in ("max_logical_completions", "max_action_repair_completions",
                          "max_rate_limit_retry_attempts", "max_http_request_attempts")}
    ceilings = [item["requested_output_token_ceiling"] for item in agents.values()
                if item["network"]]
    totals["requested_output_token_ceiling"] = sum(ceilings) if ceilings else None
    return {"rounds": rounds, "llm_agents": dict(sorted(agents.items())), **totals}


def plan_study(study_dir: Path, *, only_condition: str | None = None,
               replicates_override: int | None = None,
               max_episode_attempts: int | None = None,
               max_run_attempts: int | None = None) -> dict[str, Any]:
    spec, resolved = load_study(study_dir)
    replicates = select_replicates(spec, only_condition, replicates_override)
    conditions = {c.condition_id: _episode(resolved[c.condition_id]) for c in spec.conditions
                  if only_condition is None or c.condition_id == only_condition}
    worst_episode = max((c["max_http_request_attempts"] for c in conditions.values()), default=0)
    run_total = replicates * sum(c["max_http_request_attempts"] for c in conditions.values())
    ceilings = [c["requested_output_token_ceiling"] for c in conditions.values()
                if c["requested_output_token_ceiling"] is not None]
    return {
        "study_id": spec.study_id, "offline": True, "note": _NOTE, "replicates": replicates,
        "conditions": conditions,
        "selection": {
            "episodes": replicates * len(conditions),
            "max_http_request_attempts_per_episode": worst_episode,
            "max_http_request_attempts": run_total,
            "requested_output_token_ceiling":
                replicates * sum(ceilings) if ceilings else None,
        },
        "limits": {
            "episode": max_episode_attempts, "run": max_run_attempts,
            "worst_case_exceeds_episode_limit":
                None if max_episode_attempts is None else worst_episode > max_episode_attempts,
            "worst_case_exceeds_run_limit":
                None if max_run_attempts is None else run_total > max_run_attempts,
        },
    }
