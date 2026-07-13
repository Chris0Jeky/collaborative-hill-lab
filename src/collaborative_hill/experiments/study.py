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
Paired seeds: replicate r of every condition shares the same seed path prefix
(study_seed, condition, r) — and policy streams are keyed by agent id, so
conditions differing only in institution reuse identical policy randomness.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from collaborative_hill.agents.llm import FakeProvider, LLMPolicy
from collaborative_hill.agents.scripted.ec_policies import build_ec_policy
from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy
from collaborative_hill.engine.hashing import content_hash
from collaborative_hill.engine.runner import RunConfig, RunResult, run_episode
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
    NarrativeSkin,
    NIPDWorld,
    ResolvedScenario,
    ScenarioSpec,
    compile_scenario,
)

SCRIPTED_NIPD = {"allc", "alld", "random", "tft_pairwise", "tft_linked", "ptft",
                 "tft_threshold"}
SCRIPTED_EC = {"ec_contributor", "ec_freerider", "ec_verifier", "ec_misinformer"}


class ConditionSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    condition_id: str
    scenario: str  # path relative to the study directory
    skin: str


class StudySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    study_id: str
    title: str = ""
    seed: int
    replicates: int = 1
    checkpoint_every: int = 0
    invalid_action_policy: str = "fail"
    conditions: tuple[ConditionSpec, ...]


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
    return content_hash({
        "domain": "chl.study.v1",
        "study_id": spec.study_id,
        "seed": spec.seed,
        "replicates": spec.replicates,
        "checkpoint_every": spec.checkpoint_every,
        "invalid_action_policy": spec.invalid_action_policy,
        "conditions": {
            c.condition_id: resolved[c.condition_id].scenario_hash for c in spec.conditions
        },
    })


def validate_study(study_dir: Path) -> dict[str, Any]:
    spec, resolved = load_study(study_dir)
    return {
        "study_id": spec.study_id,
        "study_hash": study_hash(spec, resolved),
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
    (Path(study_dir) / "study.lock.json").write_text(
        json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8"
    )
    return h


def frozen_hash(study_dir: Path) -> str | None:
    lock_path = Path(study_dir) / "study.lock.json"
    if not lock_path.exists():
        return None
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    return str(data["study_hash"])


def build_policies(resolved: ResolvedScenario) -> dict[str, Any]:
    """Construct one policy object per agent from the cognition plane."""
    spec = resolved.spec
    mode = spec.world.mode if isinstance(spec.world, NIPDWorld) else None
    policies: dict[str, Any] = {}
    for agent in spec.cognition.agents:
        name = agent.policy.name
        params = dict(agent.policy.params)
        if name in SCRIPTED_NIPD:
            if mode is None:
                raise ValueError(f"{name} is an NIPD policy but world is not NIPD")
            parsed = {
                k: (float(_fraction(v)) if k == "epsilon" else v) for k, v in params.items()
            }
            policies[agent.agent_id] = build_nipd_policy(name, mode, parsed)
        elif name in SCRIPTED_EC:
            policies[agent.agent_id] = build_ec_policy(name, params)
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
                max_retries=int(params.get("max_retries", 1)),
            )
        else:
            raise ValueError(f"unknown policy {name} for agent {agent.agent_id}")
    return policies


def _fraction(value: Any) -> Any:
    from fractions import Fraction

    return Fraction(str(value))


def run_study(
    study_dir: Path,
    artifacts_root: Path,
    *,
    only_condition: str | None = None,
    replicates_override: int | None = None,
) -> list[RunResult]:
    """Execute all (condition x replicate) runs. Study need not be frozen for
    smoke runs; the manifest records frozen status so sealed science is
    distinguishable from exploration."""
    study_dir = Path(study_dir)
    spec, resolved = load_study(study_dir)
    h = study_hash(spec, resolved)
    locked = frozen_hash(study_dir)
    if locked is not None and locked != h:
        raise ValueError(
            f"study content changed after freeze: lock={locked[:12]} current={h[:12]} — "
            "a frozen study is immutable; create a new version instead"
        )
    repo_root = _find_repo_root(study_dir)
    commit, dirty = git_provenance(repo_root)
    env = environment_provenance()
    dep_hash = lock_hash(repo_root)

    replicates = replicates_override if replicates_override is not None else spec.replicates
    results: list[RunResult] = []
    for cond in spec.conditions:
        if only_condition is not None and cond.condition_id != only_condition:
            continue
        scenario = resolved[cond.condition_id]
        for r in range(replicates):
            run_id = f"{cond.condition_id}-r{r:03d}"
            run_dir = (Path(artifacts_root) / (locked or "DRAFT-" + h[:12])
                       / cond.condition_id / run_id)
            paths = RunPaths(run_dir).create()
            (run_dir / "scenario.resolved.json").write_text(
                scenario.model_dump_json(indent=2), encoding="utf-8"
            )
            policies = build_policies(scenario)
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
                providers={a: p.provider.model_id for a, p in sorted(policies.items())
                           if isinstance(p, LLMPolicy)},
                prompt_template_hashes={a: p.prompt_template_hash
                                        for a, p in sorted(policies.items())
                                        if isinstance(p, LLMPolicy)},
                seed_root=[spec.seed, cond.condition_id, r],
                checkpoint_every=spec.checkpoint_every,
                invalid_action_policy=spec.invalid_action_policy,
                scorer_versions=_scorer_versions(),
                started_at=utc_now_iso(),
            )
            write_manifest(manifest, paths.manifest)

            config = RunConfig(
                study_id=spec.study_id,
                run_id=run_id,
                seed_root=(spec.seed, cond.condition_id, r),
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
            transcript = [
                line for p in policies.values() if isinstance(p, LLMPolicy)
                for line in p.transcript
            ]
            if transcript:
                with (run_dir / "llm_transcript.jsonl").open("w", encoding="utf-8") as f:
                    for line in transcript:
                        f.write(json.dumps(line, sort_keys=True) + "\n")

            manifest = manifest.model_copy(update={
                "ended_at": utc_now_iso(),
                "status": result.status,
                "failure_reason": result.failure_reason,
            })
            write_manifest(manifest, paths.manifest)
            results.append(result)
    return results


def _scorer_versions() -> dict[str, str]:
    from collaborative_hill.metrics import METRIC_VERSIONS

    return dict(METRIC_VERSIONS)


def _find_repo_root(start: Path) -> Path:
    p = Path(start).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / ".git").exists():
            return candidate
    return p
