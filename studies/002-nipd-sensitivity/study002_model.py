"""Canonical Study 002 design and exact pre-execution analytical predictions.

This module never runs a policy or mechanism to obtain an expectation. The
derivations are in README.md, committed before execution; tests use hand-derived
literals. Production policy/engine semantics remain unchanged.
"""

from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from collaborative_hill.engine.hashing import frac_str
from collaborative_hill.engine.seeds import LEGACY_SEED_PROTOCOL
from collaborative_hill.experiments.scenario import NarrativeSkin, ScenarioSpec
from collaborative_hill.experiments.study import ConditionSpec, StudySpec

SEED = 20261029
ROUNDS = 50
WINDOW = 10
BOOTSTRAP_SAMPLES = 2000
STOCHASTIC_REPLICATES = 32
THRESHOLDS = ("0", "49/100", "1/2", "51/100", "3/4", "76/100", "1")
DENOMINATORS: tuple[Literal["include_self", "exclude_self"], ...] = (
    "include_self", "exclude_self",
)
STUDY_DIR = Path(__file__).resolve().parent


class Condition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    condition_id: str
    n_agents: int
    reciprocators: int
    policy: Literal["tft_threshold", "ptft", "tft_pairwise", "tft_linked", "alld"]
    threshold: str | None = None
    denominator: Literal["include_self", "exclude_self"] | None = None

    @property
    def deterministic(self) -> bool:
        return self.policy != "ptft" or self.reciprocators == self.n_agents

    @property
    def mode(self) -> str:
        return "pairwise" if self.policy in {"tft_pairwise", "tft_linked"} else "neighbourhood"


def conditions() -> list[Condition]:
    result: list[Condition] = []
    for n, m in ((3, 2), (5, 4), (5, 3)):
        values = THRESHOLDS if m == n - 1 else ("49/100", "1/2", "51/100")
        result.extend(Condition(
            condition_id=f"nb-n{n}-m{m}-q{q.replace('/', '-')}",
            n_agents=n, reciprocators=m, policy="tft_threshold", threshold=q,
        ) for q in values)
    for n in (3, 5):
        result.extend([
            Condition(condition_id=f"nb-n{n}-all-q1", n_agents=n,
                      reciprocators=n, policy="tft_threshold", threshold="1"),
            Condition(condition_id=f"nb-n{n}-alld", n_agents=n,
                      reciprocators=0, policy="alld"),
            Condition(condition_id=f"pw-n{n}-m{n-1}-tft", n_agents=n,
                      reciprocators=n-1, policy="tft_pairwise"),
            Condition(condition_id=f"pw-n{n}-m{n-1}-linked", n_agents=n,
                      reciprocators=n-1, policy="tft_linked"),
        ])
        for denominator in DENOMINATORS:
            suffix = denominator.removesuffix("_self")
            result.append(Condition(
                condition_id=f"nb-n{n}-all-ptft-{suffix}", n_agents=n,
                reciprocators=n, policy="ptft", denominator=denominator,
            ))
    for n, m in ((3, 2), (5, 4), (5, 3)):
        for denominator in DENOMINATORS:
            suffix = denominator.removesuffix("_self")
            result.append(Condition(
                condition_id=f"nb-n{n}-m{m}-ptft-{suffix}", n_agents=n,
                reciprocators=m, policy="ptft", denominator=denominator,
            ))
    return result


def skin() -> NarrativeSkin:
    return NarrativeSkin(
        skin_id="plain-nipd-002", title="N-person Prisoner's Dilemma sensitivity",
        preamble="A repeated N-person social dilemma. Mechanism-transparent skin.",
    )


def scenario(condition: Condition) -> ScenarioSpec:
    params: dict[str, str | int] = {"epsilon": "0"}
    if condition.threshold is not None:
        q = Fraction(condition.threshold)
        params.update(threshold_num=q.numerator, threshold_den=q.denominator)
    if condition.denominator is not None:
        params["denominator"] = condition.denominator
    agents = []
    for i in range(condition.n_agents):
        policy = ({"name": condition.policy, "params": params}
                  if i < condition.reciprocators else {"name": "alld"})
        agents.append({"agent_id": f"a{i+1}", "policy": policy})
    return ScenarioSpec.model_validate({
        "scenario_id": f"002-{condition.condition_id}",
        "description": f"Study 002 unfrozen sensitivity draft: {condition.condition_id}",
        "world": {"kind": "nipd", "mode": condition.mode, "rounds": ROUNDS},
        "interaction": {"structure": condition.mode},
        "cognition": {"agents": agents},
    })


def study_specs() -> dict[str, StudySpec]:
    result = {}
    for component in ("deterministic", "stochastic"):
        deterministic = component == "deterministic"
        prefix = "" if deterministic else "../"
        result[component] = StudySpec(
            study_id=f"002-nipd-sensitivity-{component}",
            title=f"N-IPD sensitivity: {component} component (UNFROZEN DRAFT)",
            seed=SEED, seed_protocol=LEGACY_SEED_PROTOCOL,
            replicates=1 if deterministic else STOCHASTIC_REPLICATES,
            checkpoint_every=10, invalid_action_policy="fail",
            conditions=tuple(ConditionSpec(
                condition_id=c.condition_id,
                scenario=f"{prefix}scenarios/{c.condition_id}.json",
                skin=f"{prefix}skins/plain.json",
            ) for c in conditions() if c.deterministic == deterministic),
        )
    return result


def generated_files() -> dict[Path, bytes]:
    specs = study_specs()
    models = {
        Path("study.json"): specs["deterministic"],
        Path("stochastic/study.json"): specs["stochastic"],
        Path("skins/plain.json"): skin(),
        **{Path(f"scenarios/{c.condition_id}.json"): scenario(c) for c in conditions()},
    }
    return {path: (model.model_dump_json(indent=2) + "\n").encode("utf-8")
            for path, model in models.items()}


def generate(output: Path, *, check: bool = False) -> None:
    """Preflight all inputs before writes; never replace divergent/frozen inputs."""
    expected = generated_files()
    if not check and any((output / name).exists()
                         for name in ("study.lock.json", "stochastic/study.lock.json")):
        raise ValueError("refusing to overwrite a frozen component; use a new output directory")
    for relative, data in expected.items():
        path = output / relative
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"generated input differs: {relative}; use a new output directory")
        if check and not path.exists():
            raise ValueError(f"generated input missing: {relative}")
    if check:
        return
    for relative, data in expected.items():
        path = output / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)


def _deterministic_path(condition: Condition, rounds: int) -> tuple[
    list[Fraction], dict[str, str],
]:
    n, m = condition.n_agents, condition.reciprocators
    first, later = Fraction(m, n), Fraction(m, n)
    if m == 0:
        reciprocal_score, defector_score = Fraction(), Fraction(rounds)
    elif m == n:
        reciprocal_score, defector_score = Fraction(3 * rounds), Fraction()
    elif condition.mode == "neighbourhood":
        assert condition.threshold is not None
        persists = Fraction(condition.threshold) <= Fraction(m - 1, n - 1)
        reciprocal_initial = Fraction(3 * (m - 1), n - 1)
        defector_initial = 1 + Fraction(4 * m, n - 1)
        reciprocal_score = (rounds * reciprocal_initial if persists
                            else reciprocal_initial + rounds - 1)
        defector_score = (rounds * defector_initial if persists
                         else defector_initial + rounds - 1)
        later = first if persists else Fraction()
    else:
        targeted = condition.policy == "tft_pairwise"
        later = Fraction(m * (m - 1), n * (n - 1)) if targeted else Fraction()
        reciprocal_score = Fraction(3 * (m - 1) + (rounds - 1) * (
            3 * (m - 1) + n - m if targeted else n - 1
        ))
        defector_score = Fraction(5 * m + (n - m - 1) + (rounds - 1) * (n - 1))
    scores = {f"a{i+1}": frac_str(reciprocal_score if i < m else defector_score)
              for i in range(n)}
    return [first] + [later] * (rounds - 1), scores


def predict(condition: Condition, *, rounds: int = ROUNDS,
            window: int = WINDOW) -> dict[str, Any]:
    """Closed-form expectation or deterministic trajectory, never a run result."""
    if not 1 <= window <= rounds:
        raise ValueError("window must satisfy 1 <= window <= rounds")
    n, m = condition.n_agents, condition.reciprocators
    decay = None
    scores = None
    if condition.deterministic:
        curve, scores = _deterministic_path(condition, rounds)
    else:
        decay = (Fraction(m, n) if condition.denominator == "include_self"
                 else Fraction(m - 1, n - 1))
        curve = [Fraction(m, n) * decay ** t for t in range(rounds)]
    return {
        "kind": "exact_trajectory" if condition.deterministic else "expectation",
        "critical_quorum": (frac_str(Fraction(m - 1, n - 1))
                            if condition.policy == "tft_threshold" else None),
        "decay_factor": frac_str(decay) if decay is not None else None,
        "cooperation_by_round": [frac_str(v) for v in curve],
        "mean_cooperation": frac_str(sum(curve, Fraction()) / rounds),
        "final_window_cooperation": frac_str(sum(curve[-window:], Fraction()) / window),
        "scores": scores,
    }
