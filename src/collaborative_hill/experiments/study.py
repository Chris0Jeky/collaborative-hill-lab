"""Study lifecycle: draft -> validated -> frozen -> running -> sealed -> analysed.

A study directory contains:

    study.json          StudySpec (conditions reference scenario + skin files)
    scenarios/*.json    ScenarioSpec files
    skins/*.json        NarrativeSkin files
    study.lock.json     written by `chl study freeze` (HUMAN-CONFIRMED step;
                        never automatic — ADR-0006)

Freezing computes the study content hash over the resolved condition scenario
hashes plus the design parameters. Changing anything after freeze changes the
hash — that is a new study version, not an edit.

Runs land in artifacts/<study_hash-or-DRAFT>/<condition>/<run_id>/ with a full
RunManifest, the frozen resolved scenario, the event ledger, and checkpoints.
Missing seed_protocol means legacy-independent-v1: condition-specific policy
and mechanism streams. Explicit paired-policy-v2 shares policy streams only
within the declared (scenario_block, replicate); world streams remain
condition-specific. See ADR-0008 for compatibility and inference limits.
"""

import json
import os
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from collaborative_hill.agents.llm import (
    FakeProvider,
    LLMPolicy,
    OpenAICompatibleProvider,
    RequestBudget,
    build_openai_compatible_policy,
    llm_manifest_fields,
)
from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
from collaborative_hill.agents.scripted.graph_nipd_policies import build_graph_nipd_policy
from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.agents.scripted.params import coerce_policy_params
from collaborative_hill.engine.hashing import content_hash
from collaborative_hill.engine.runner import RunConfig, RunResult, run_episode
from collaborative_hill.engine.seeds import (
    LEGACY_SEED_PROTOCOL,
    PAIRED_SEED_PROTOCOL,
    SeedProtocol,
    study_seed_roots,
    validate_scenario_block,
)
from collaborative_hill.engine.store import RunPaths
from collaborative_hill.experiments.manifests import (
    RunManifest,
    environment_provenance,
    git_provenance,
    lock_hash,
    utc_now_iso,
    write_manifest,
)
from collaborative_hill.experiments.scenario import (
    GraphNIPDWorld,
    NarrativeSkin,
    NIPDWorld,
    ResolvedScenario,
    ScenarioSpec,
    compile_scenario,
)

InvalidActionPolicy = Literal["fail", "abstain"]

SCRIPTED_NIPD = {"allc", "alld", "random", "tft_pairwise", "tft_linked", "ptft",
                 "tft_threshold"}
SCRIPTED_EC = {"ec_contributor", "ec_freerider", "ec_verifier", "ec_misinformer",
               "ec_conditional_contributor", "ec_skeptical_contributor"}


class ConditionSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    condition_id: str
    scenario: str  # path relative to the study directory
    skin: str
    scenario_block: str | None = None

    @field_validator("condition_id")
    @classmethod
    def portable_output_component(cls, value: str) -> str:
        # A condition is both a seed identity and a directory component. Reject
        # ambiguous names instead of normalising them and changing their identity.
        if (not value or value in {".", ".."} or value != value.strip()
                or value.endswith(".") or PureWindowsPath(value).is_reserved()
                or any(ord(char) < 32 or char in '<>:"/\\|?*' for char in value)):
            raise ValueError("condition_id must be a portable, non-empty path component")
        return value

    @field_validator("scenario_block")
    @classmethod
    def valid_scenario_block(cls, block: str | None) -> str | None:
        validate_scenario_block(block)
        return block


class StudySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    study_id: str
    title: str = ""
    seed: int
    seed_protocol: SeedProtocol = LEGACY_SEED_PROTOCOL
    replicates: int = Field(default=1, ge=1, strict=True)
    checkpoint_every: int = Field(default=0, ge=0, strict=True)
    invalid_action_policy: InvalidActionPolicy = "fail"
    conditions: tuple[ConditionSpec, ...] = Field(min_length=1)

    @field_validator("conditions")
    @classmethod
    def unique_condition_ids(
        cls, conditions: tuple[ConditionSpec, ...]
    ) -> tuple[ConditionSpec, ...]:
        ids = [condition.condition_id.casefold() for condition in conditions]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "condition IDs must be unique, including on case-insensitive filesystems"
            )
        return conditions

    @model_validator(mode="after")
    def explicit_pairing_blocks(self) -> Self:
        for condition in self.conditions:
            if self.seed_protocol == PAIRED_SEED_PROTOCOL and condition.scenario_block is None:
                raise ValueError("paired-policy-v2 requires scenario_block for every condition")
            if self.seed_protocol == LEGACY_SEED_PROTOCOL and condition.scenario_block is not None:
                raise ValueError("scenario_block requires seed_protocol=paired-policy-v2")
        return self


def load_study(study_dir: Path) -> tuple[StudySpec, dict[str, ResolvedScenario]]:
    study_dir = Path(study_dir)
    spec = StudySpec.model_validate_json(
        (study_dir / "study.json").read_text(encoding="utf-8")
    )
    resolved: dict[str, ResolvedScenario] = {}
    for cond in spec.conditions:
        scenario = ScenarioSpec.model_validate_json(
            (study_dir / cond.scenario).read_text(encoding="utf-8")
        )
        skin = NarrativeSkin.model_validate_json(
            (study_dir / cond.skin).read_text(encoding="utf-8")
        )
        resolved[cond.condition_id] = compile_scenario(scenario, skin)
    return spec, resolved


def study_hash(spec: StudySpec, resolved: dict[str, ResolvedScenario]) -> str:
    payload: dict[str, Any] = {
        "domain": "chl.study.v1",
        "study_id": spec.study_id,
        "seed": spec.seed,
        "replicates": spec.replicates,
        "checkpoint_every": spec.checkpoint_every,
        "invalid_action_policy": spec.invalid_action_policy,
        "conditions": {
            c.condition_id: resolved[c.condition_id].scenario_hash for c in spec.conditions
        },
    }
    if spec.seed_protocol == PAIRED_SEED_PROTOCOL:
        payload.update({
            "domain": "chl.study.v2",
            "seed_protocol": spec.seed_protocol,
            "scenario_blocks": {c.condition_id: c.scenario_block for c in spec.conditions},
        })
    # Omitted/explicit legacy protocol retains the EXACT original hash payload.
    return content_hash(payload)


def validate_study(study_dir: Path) -> dict[str, Any]:
    spec, resolved = load_study(study_dir)
    return {
        "study_id": spec.study_id,
        "study_hash": study_hash(spec, resolved),
        "seed_protocol": spec.seed_protocol,
        "scenario_blocks": {c.condition_id: c.scenario_block for c in spec.conditions},
        "conditions": {
            cid: {
                "scenario_hash": r.scenario_hash,
                "mechanism_hash": r.mechanism_hash,
                "narrative_hash": r.narrative_hash,
                "evidence_corpus_hash": r.evidence_corpus_hash,
            }
            for cid, r in sorted(resolved.items())
        },
        "replicates": spec.replicates,
        "frozen": frozen_hash(study_dir) is not None,
    }


def freeze_study(study_dir: Path) -> str:
    """Write study.lock.json. Invoked only by an explicit human-run command."""
    spec, resolved = load_study(study_dir)
    h = study_hash(spec, resolved)
    lock = {
        "study_id": spec.study_id,
        "study_hash": h,
        "scenario_hashes": {cid: r.scenario_hash for cid, r in sorted(resolved.items())},
        "frozen_at": utc_now_iso(),
    }
    lock_path = Path(study_dir) / "study.lock.json"
    fd, temporary = tempfile.mkstemp(prefix=".study-lock-", suffix=".tmp", dir=study_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(lock, stream, indent=2, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # Publish the complete, flushed lock without replacing a competing freeze.
            os.link(temporary, lock_path)
        except FileExistsError:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
            if any(existing.get(key) != lock[key]
                   for key in ("study_id", "study_hash", "scenario_hashes")):
                raise ValueError(
                    "a frozen study is immutable; create a new version instead"
                ) from None
        except OSError as exc:
            raise ValueError(
                f"cannot atomically publish study.lock.json: {exc}; "
                "exclusive hard-link publication is required; study lock is unchanged"
            ) from exc
    finally:
        Path(temporary).unlink()
    return h


def frozen_hash(study_dir: Path) -> str | None:
    lock_path = Path(study_dir) / "study.lock.json"
    if not lock_path.exists():
        return None
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    return str(data["study_hash"])


def build_policies(resolved: ResolvedScenario, *, allow_provider_requests: bool = False,
                   overrides: dict[str, Any] | None = None,
                   budget: RequestBudget | None = None) -> dict[str, Any]:
    """Construct policies; network-backed policies require explicit execution opt-in.

    ``budget`` (operational, never hashed) is shared by every network policy built here.

    Explicit overrides are used before construction, so replacing a network
    policy with a scripted counterfactual does not read credentials or call it.
    """
    spec = resolved.spec
    mode = spec.world.mode if isinstance(spec.world, NIPDWorld | GraphNIPDWorld) else None
    policies: dict[str, Any] = {}
    replacements = overrides or {}
    unknown = set(replacements) - {agent.agent_id for agent in spec.cognition.agents}
    if unknown:
        raise ValueError(f"override for unknown agent {sorted(unknown)[0]}")
    for agent in spec.cognition.agents:
        if agent.agent_id in replacements:
            replacement = replacements[agent.agent_id]
            if (not allow_provider_requests and isinstance(replacement, LLMPolicy)
                    and isinstance(replacement.provider, OpenAICompatibleProvider)):
                raise ValueError("network-backed overrides require allow_provider_requests=True")
            policies[agent.agent_id] = replacement
            continue
        name = agent.policy.name
        params = dict(agent.policy.params)
        if name in SCRIPTED_NIPD:
            if mode is None:
                raise ValueError(f"{name} is an NIPD policy but world is not NIPD")
            parsed = coerce_policy_params(name, params)
            builder = (build_graph_nipd_policy if isinstance(spec.world, GraphNIPDWorld)
                       else build_nipd_policy)
            policies[agent.agent_id] = builder(name, mode, parsed)
        elif name in SCRIPTED_EC:
            policies[agent.agent_id] = build_ec_policy(name, coerce_policy_params(name, params))
        elif name == "llm_fake":
            script = json.loads(str(params.get("script", "[]")))
            policies[agent.agent_id] = LLMPolicy(
                agent_id=agent.agent_id,
                provider=FakeProvider(
                    script,
                    model_id=str(params.get("model_id", "fake-provider/fake-model-1")),
                    fail_at=int(params["fail_at"]) if "fail_at" in params else None,
                ),
                skin=resolved.skin,
                max_retries=_require_non_negative_retries(params),
            )
        elif name == "llm_openai_compatible":
            if not allow_provider_requests:
                raise ValueError(
                    "network-backed policies require allow_provider_requests=True "
                    "or --allow-provider-requests; validation and replay remain offline"
                )
            policies[agent.agent_id] = build_openai_compatible_policy(
                agent.agent_id, resolved.skin, params, budget=budget)
        else:
            raise ValueError(f"unknown policy {name} for agent {agent.agent_id}")
    return policies


def _require_non_negative_retries(params: dict[str, Any]) -> int:
    max_retries = int(params.get("max_retries", 1))
    if max_retries < 0:
        raise ValueError(f"max_retries must be >= 0, got {max_retries}")
    return max_retries


def _require_provider_opt_in(resolved: dict[str, ResolvedScenario],
                             only_condition: str | None, allowed: bool) -> None:
    if not allowed and any(
        agent.policy.name == "llm_openai_compatible"
        for cid, scenario in resolved.items()
        if only_condition is None or cid == only_condition
        for agent in scenario.spec.cognition.agents
    ):
        raise ValueError(
            "network-backed policies require allow_provider_requests=True "
            "or --allow-provider-requests; no run output was created"
        )
    if allowed:
        # Constructors make no requests. Check every selected credential/config
        # before any episode can spend tokens or create an output directory.
        for cid, scenario in resolved.items():
            if only_condition is None or cid == only_condition:
                for agent in scenario.spec.cognition.agents:
                    if agent.policy.name == "llm_openai_compatible":
                        build_openai_compatible_policy(
                            agent.agent_id, scenario.skin, agent.policy.params)


def select_replicates(spec: StudySpec, only_condition: str | None,
                      replicates_override: int | None) -> int:
    """Validate a run/plan selection and return the replicate count."""
    replicates = replicates_override if replicates_override is not None else spec.replicates
    if type(replicates) is not int:
        raise ValueError(f"replicates must be an integer >= 1, got {replicates!r}")
    if replicates < 1:
        raise ValueError(f"replicates must be >= 1, got {replicates}")
    if only_condition is not None and all(
        c.condition_id != only_condition for c in spec.conditions
    ):
        known = ", ".join(sorted(c.condition_id for c in spec.conditions))
        raise ValueError(f"unknown condition {only_condition!r}; known conditions: {known}")
    return replicates


def _write_llm_transcript(policies: dict[str, Any], run_dir: Path, *,
                          offsets: dict[str, int] | None = None) -> None:
    starts = offsets or {}
    transcript = [line for a, p in policies.items() if isinstance(p, LLMPolicy)
                  for line in p.transcript[starts.get(a, 0):]]
    if transcript:
        with (run_dir / "llm_transcript.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
            for line in transcript:
                stream.write(json.dumps(line, sort_keys=True) + "\n")


def _planned_run_dirs(
    artifacts_root: Path,
    study_prefix: str,
    spec: StudySpec,
    only_condition: str | None,
    replicates: int,
) -> list[Path]:
    """Every run directory a ``run_study`` call is about to write."""
    run_dirs: list[Path] = []
    for cond in spec.conditions:
        if only_condition is not None and cond.condition_id != only_condition:
            continue
        for r in range(replicates):
            run_id = f"{cond.condition_id}-r{r:03d}"
            run_dirs.append(Path(artifacts_root) / study_prefix / cond.condition_id / run_id)
    return run_dirs


def _refuse_if_runs_exist(run_dirs: list[Path]) -> None:
    """Preflight all output directories, including partial runs, before starting."""
    for run_dir in run_dirs:
        if run_dir.exists() and any(run_dir.iterdir()):
            raise FileExistsError(
                f"refusing to re-run into occupied run directory: {run_dir} — "
                "one run directory holds exactly one episode; pass a fresh "
                "--artifacts directory or run `make clean-generated`"
            )


def _require_output_within_root(run_dir: Path, artifacts_root: Path) -> Path:
    """Respect an explicitly chosen root symlink, but not escaping descendants.

    This checks the current filesystem layout; it is not protection against a
    different process replacing directories concurrently after the check.
    """
    destination = run_dir.resolve()
    if not destination.is_relative_to(artifacts_root.resolve()):
        raise ValueError(f"run output resolves outside the selected artifacts root: {run_dir}")
    for component in (run_dir, *run_dir.parents):
        if (component.exists() or component.is_symlink()) and not component.is_dir():
            raise FileExistsError(f"run output path is not a directory: {component}")
    return destination


def run_study(
    study_dir: Path,
    artifacts_root: Path,
    *,
    only_condition: str | None = None,
    replicates_override: int | None = None,
    allow_provider_requests: bool = False,
    request_budget: RequestBudget | None = None,
) -> list[RunResult]:
    """Execute all (condition x replicate) runs. Study need not be frozen for
    smoke runs; the manifest records frozen status so sealed science is
    distinguishable from exploration.

    ``request_budget`` is shared by the whole call: its episode counter resets at
    each episode, its run counter never does. After a run-level stop every later
    network episode is still sealed ``RunFailed`` with zero requests and the same
    stable reason; scripted episodes are unaffected. It is not hashed (ADR-0015)."""
    study_dir = Path(study_dir)
    spec, resolved = load_study(study_dir)
    h = study_hash(spec, resolved)
    locked = frozen_hash(study_dir)
    if locked is not None and locked != h:
        raise ValueError(
            f"study content changed after freeze: lock={locked[:12]} current={h[:12]} — "
            "a frozen study is immutable; create a new version instead"
        )
    replicates = select_replicates(spec, only_condition, replicates_override)
    _require_provider_opt_in(resolved, only_condition, allow_provider_requests)
    repo_root = _find_repo_root(study_dir)
    commit, dirty = git_provenance(repo_root)
    env = environment_provenance()
    dep_hash = lock_hash(repo_root)

    planned_dirs = _planned_run_dirs(
        Path(artifacts_root), locked or "DRAFT-" + h[:12],
        spec, only_condition, replicates,
    )
    destinations: set[Path] = set()
    for run_dir in planned_dirs:
        destination = _require_output_within_root(run_dir, Path(artifacts_root))
        if destination in destinations:
            raise ValueError("planned run output directories overlap after resolving symlinks")
        destinations.add(destination)
    if any(parent in destinations for path in destinations for parent in path.parents):
        raise ValueError("planned run output directories overlap after resolving symlinks")
    _refuse_if_runs_exist(planned_dirs)
    results: list[RunResult] = []
    for cond in spec.conditions:
        if only_condition is not None and cond.condition_id != only_condition:
            continue
        scenario = resolved[cond.condition_id]
        for r in range(replicates):
            run_id = f"{cond.condition_id}-r{r:03d}"
            seed_root, policy_seed_root = study_seed_roots(
                spec.seed, cond.condition_id, r,
                protocol=spec.seed_protocol, scenario_block=cond.scenario_block,
            )
            run_dir = (Path(artifacts_root) / (locked or "DRAFT-" + h[:12])
                       / cond.condition_id / run_id)
            _require_output_within_root(run_dir, Path(artifacts_root))
            with RunPaths(run_dir).reserve() as paths:
                (run_dir / "scenario.resolved.json").write_text(
                    scenario.model_dump_json(indent=2), encoding="utf-8", newline="\n"
                )
                budget_args: dict[str, Any] = {}
                if request_budget is not None:
                    request_budget.begin("episode")
                    budget_args = {"budget": request_budget}
                policies = build_policies(
                    scenario, allow_provider_requests=allow_provider_requests, **budget_args)
                manifest = RunManifest(
                    study_id=spec.study_id,
                    study_hash=h,
                    study_frozen=locked is not None,
                    condition_id=cond.condition_id,
                    run_id=run_id,
                    replicate=r,
                    scenario_hash=scenario.scenario_hash,
                    mechanism_hash=scenario.mechanism_hash,
                    narrative_hash=scenario.narrative_hash,
                    evidence_corpus_hash=scenario.evidence_corpus_hash,
                    institution=scenario.spec.institution.model_dump(mode="json"),
                    code_commit=commit,
                    worktree_dirty=dirty,
                    python_version=env["python_version"],
                    platform=env["platform"],
                    dependency_lock_sha256=dep_hash,
                    policies={a: p.policy_id for a, p in sorted(policies.items())},
                    **llm_manifest_fields(policies, budget=request_budget),
                    seed_root=list(seed_root),
                    seed_protocol=spec.seed_protocol,
                    policy_seed_root=list(policy_seed_root) if policy_seed_root else None,
                    scenario_block=cond.scenario_block,
                    checkpoint_every=spec.checkpoint_every,
                    invalid_action_policy=spec.invalid_action_policy,
                    scorer_versions=_scorer_versions(),
                    started_at=utc_now_iso(),
                )
                write_manifest(manifest, paths.manifest)

            config = RunConfig(
                study_id=spec.study_id,
                run_id=run_id,
                seed_root=seed_root,
                seed_protocol=spec.seed_protocol,
                policy_seed_root=policy_seed_root,
                scenario_block=cond.scenario_block,
                checkpoint_every=spec.checkpoint_every,
                invalid_action_policy=spec.invalid_action_policy,
            )
            result = run_episode(
                mechanism=scenario.build_mechanism(),
                policies=policies,
                config=config,
                paths=paths,
                start_meta={
                    "scenario_hash": scenario.scenario_hash,
                    "mechanism_hash": scenario.mechanism_hash,
                    "narrative_hash": scenario.narrative_hash,
                },
            )
            _write_llm_transcript(policies, run_dir)

            manifest = manifest.model_copy(update={
                **llm_manifest_fields(policies, budget=request_budget),
                "ended_at": utc_now_iso(),
                "status": result.status,
                "failure_reason": result.failure_reason,
                "event_count": result.event_count,
                "final_event_hash": result.final_event_hash,
            })
            write_manifest(manifest, paths.manifest)
            results.append(result)
    return results


def _scorer_versions() -> dict[str, str]:
    from collaborative_hill.metrics import METRIC_VERSIONS

    return dict(METRIC_VERSIONS)


def _find_repo_root(start: Path) -> Path:
    """Root of the CODE repository (provenance target), not the study's location.

    Derived from the installed package path (src layout), so manifests record
    the commit of the code that ran — even when a study/artifacts directory
    lives in a temp dir or inside some unrelated git repository. Falls back to
    walking up from ``start`` only if the package location has no .git (e.g. a
    non-editable install), and finally to ``start`` itself.
    """
    import collaborative_hill

    package_root = Path(collaborative_hill.__file__).resolve().parents[2]
    if (package_root / ".git").exists():
        return package_root
    p = Path(start).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / ".git").exists():
            return candidate
    return p
