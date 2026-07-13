"""Shared builders for the metamorphic suite.

These construct real ScenarioSpec / NarrativeSkin objects and drive full runs
through the *public* API only (compile_scenario, build_policies, run_episode,
run_study, branch_run, replay_run). Nothing here depends on internal state
shapes, so the metamorphic relations are asserted against observable outputs
(summaries, event payloads, metrics), never against the code under test.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from collaborative_hill.domain.evidence import EvidenceSpec
from collaborative_hill.domain.institutions import InstitutionConfig
from collaborative_hill.domain.world.evidence_commons import ECParams
from collaborative_hill.domain.world.nipd import NIPDParams
from collaborative_hill.engine.runner import RunConfig, RunResult, run_episode
from collaborative_hill.engine.store import FileEventStore, RunPaths
from collaborative_hill.experiments.scenario import (
    AgentSpec,
    CognitionPlane,
    ECWorld,
    InformationPlane,
    InteractionPlane,
    NarrativeSkin,
    NIPDWorld,
    PolicySpec,
    ResolvedScenario,
    ScenarioSpec,
    compile_scenario,
)
from collaborative_hill.experiments.study import (
    ConditionSpec,
    StudySpec,
    build_policies,
)

# --- Evidence Commons content --------------------------------------------------

EC_SLOTS: dict[str, tuple[str, ...]] = {"s1": ("p1a", "p1b"), "s2": ("p2a", "p2b")}
EC_TRUE: dict[str, str] = {"s1": "p1a", "s2": "p2a"}

# Default cognition: a real collaborative dynamic (contributor + verifier +
# misinformer) so the metamorphic invariants are exercised on a non-trivial run.
DEFAULT_EC_AGENTS: tuple[tuple[str, str], ...] = (
    ("a1", "ec_contributor"),
    ("a2", "ec_verifier"),
    ("a3", "ec_misinformer"),
)


def ec_item(
    evidence_id: str,
    source_id: str,
    slot_id: str,
    proposition_id: str,
    stance: str,
    *,
    freshness: str = "fresh",
    holders: tuple[str, ...] = (),
) -> EvidenceSpec:
    """Build an EvidenceSpec, deriving ``truth_aligned`` from world truth so the
    mechanism's consistency validator always accepts it."""
    truth_aligned = (proposition_id == EC_TRUE[slot_id]) == (stance == "supports")
    return EvidenceSpec(
        evidence_id=evidence_id,
        source_id=source_id,
        slot_id=slot_id,
        proposition_id=proposition_id,
        stance=stance,  # type: ignore[arg-type]
        freshness=freshness,  # type: ignore[arg-type]
        truth_aligned=truth_aligned,
        initial_holders=holders,
    )


def default_ec_evidence() -> tuple[EvidenceSpec, ...]:
    """A four-item corpus that yields two correct accepted claims and one
    rejected misinformer claim (verified by the smoke run)."""
    return (
        ec_item("e1", "src_x", "s1", "p1a", "supports", holders=("a1",)),
        ec_item("e2", "src_y", "s1", "p1b", "supports", holders=("a3",)),
        ec_item("e3", "src_z", "s2", "p2a", "supports", holders=("a2",)),
        ec_item("e4", "src_w", "s2", "p2a", "supports", holders=("a1",)),
    )


def ec_spec(
    evidence: tuple[EvidenceSpec, ...],
    *,
    scenario_id: str = "ec",
    rounds: int = 10,
    institution: InstitutionConfig | None = None,
    agents: tuple[tuple[str, str], ...] = DEFAULT_EC_AGENTS,
) -> ScenarioSpec:
    return ScenarioSpec(
        scenario_id=scenario_id,
        world=ECWorld(slots=EC_SLOTS, true_propositions=EC_TRUE, params=ECParams(rounds=rounds)),
        information=InformationPlane(evidence=evidence),
        interaction=InteractionPlane(structure="commons"),
        institution=institution or InstitutionConfig(),
        cognition=CognitionPlane(
            agents=tuple(
                AgentSpec(agent_id=a, policy=PolicySpec(name=p)) for a, p in agents
            )
        ),
    )


def nipd_spec(
    agents: tuple[tuple[str, str], ...],
    *,
    scenario_id: str = "nipd",
    mode: str = "pairwise",
    rounds: int = 5,
) -> ScenarioSpec:
    return ScenarioSpec(
        scenario_id=scenario_id,
        world=NIPDWorld(mode=mode, params=NIPDParams(), rounds=rounds),  # type: ignore[arg-type]
        interaction=InteractionPlane(structure=mode),  # type: ignore[arg-type]
        cognition=CognitionPlane(
            agents=tuple(
                AgentSpec(agent_id=a, policy=PolicySpec(name=p)) for a, p in agents
            )
        ),
    )


def plain_skin(skin_id: str = "plain") -> NarrativeSkin:
    return NarrativeSkin(skin_id=skin_id)


def rich_ec_skin() -> NarrativeSkin:
    """A fully-populated, valid skin for the default EC corpus — every reference
    resolves to a real id, so it differs from the plain skin only in prose."""
    return NarrativeSkin(
        skin_id="newsroom",
        version=3,
        title="The Newsroom Standoff",
        preamble="Three editors race to file an accurate wire brief before deadline.",
        agent_names={"a1": "Ada", "a2": "Bram", "a3": "Cyra"},
        action_wording={"propose_claim": "file", "verify_claim": "fact-check"},
        slot_titles={"s1": "Headline", "s2": "Byline"},
        proposition_texts={
            "p1a": "The dam held.", "p1b": "The dam failed.",
            "p2a": "No casualties reported.", "p2b": "Dozens missing.",
        },
        source_names={"src_x": "Wire A", "src_y": "Wire B", "src_z": "Wire C", "src_w": "Wire D"},
        evidence_content={
            "e1": "Structural engineers confirm the dam is intact.",
            "e2": "An anonymous post claims a breach.",
            "e3": "Local hospital reports no admissions.",
            "e4": "Emergency services log a quiet night.",
        },
    )


# --- run helpers ---------------------------------------------------------------


def execute(
    resolved: ResolvedScenario,
    run_dir: Path,
    *,
    seed_root: tuple[str | int, ...] = ("m", 0),
    study_id: str = "s",
    run_id: str = "r",
    checkpoint_every: int = 0,
    start_meta: dict[str, Any] | None = None,
) -> tuple[RunResult, list[Any], RunPaths]:
    """Compile-free single run via the public engine entry point."""
    paths = RunPaths(Path(run_dir)).create()
    policies = build_policies(resolved)
    config = RunConfig(
        study_id=study_id,
        run_id=run_id,
        seed_root=tuple(seed_root),
        checkpoint_every=checkpoint_every,
    )
    result = run_episode(
        mechanism=resolved.build_mechanism(),
        policies=policies,
        config=config,
        paths=paths,
        start_meta=start_meta,
    )
    events = FileEventStore(paths.events).load_all(verify=True)
    return result, events, paths


def compile_ec(evidence: tuple[EvidenceSpec, ...], skin: NarrativeSkin | None = None,
               **kwargs: Any) -> ResolvedScenario:
    return compile_scenario(ec_spec(evidence, **kwargs), skin or plain_skin())


def compile_nipd(agents: tuple[tuple[str, str], ...], **kwargs: Any) -> ResolvedScenario:
    return compile_scenario(nipd_spec(agents, **kwargs), plain_skin())


def write_study(
    study_dir: Path,
    *,
    study_id: str,
    seed: int,
    checkpoint_every: int,
    conditions: list[tuple[str, ScenarioSpec, NarrativeSkin]],
) -> Path:
    """Materialise a study directory (study.json + scenarios/ + skins/) on disk
    so it can be driven through run_study exactly as the CLI would."""
    study_dir = Path(study_dir)
    (study_dir / "scenarios").mkdir(parents=True, exist_ok=True)
    (study_dir / "skins").mkdir(parents=True, exist_ok=True)
    conds: list[ConditionSpec] = []
    for cid, spec, skin in conditions:
        (study_dir / "scenarios" / f"{cid}.json").write_text(
            spec.model_dump_json(indent=2), encoding="utf-8"
        )
        (study_dir / "skins" / f"{cid}.json").write_text(
            skin.model_dump_json(indent=2), encoding="utf-8"
        )
        conds.append(
            ConditionSpec(condition_id=cid, scenario=f"scenarios/{cid}.json",
                          skin=f"skins/{cid}.json")
        )
    study = StudySpec(
        study_id=study_id,
        seed=seed,
        replicates=1,
        checkpoint_every=checkpoint_every,
        conditions=tuple(conds),
    )
    (study_dir / "study.json").write_text(study.model_dump_json(indent=2), encoding="utf-8")
    return study_dir


def find_run_dirs(artifacts_root: Path) -> list[Path]:
    """Every materialised run directory under an artifacts root (has events.jsonl)."""
    return sorted(p.parent for p in Path(artifacts_root).rglob("events.jsonl"))
