"""chl — the Collaborative Hill Lab command line.

    chl scenario validate <scenario.json> --skin <skin.json>
    chl study validate <study-dir>
    chl study freeze <study-dir>          (explicit human step)
    chl run <study-dir> [--artifacts DIR] [--condition ID] [--replicates N]
    chl replay <run-dir>
    chl branch <run-dir> --at-event N --override agent=policy[:param=value...] --out DIR
    chl report <run-or-study-artifacts-dir>
    chl doctor
"""

import json
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, no_args_is_help=True)
scenario_app = typer.Typer(no_args_is_help=True)
study_app = typer.Typer(no_args_is_help=True)
app.add_typer(scenario_app, name="scenario")
app.add_typer(study_app, name="study")

DEFAULT_ARTIFACTS = Path("artifacts")


@scenario_app.command("validate")
def scenario_validate(
    scenario_path: Path,
    skin: Path = typer.Option(..., "--skin", help="NarrativeSkin json"),
) -> None:
    """Compile a scenario+skin and print its content hashes."""
    from collaborative_hill.experiments.scenario import (
        NarrativeSkin,
        ScenarioSpec,
        compile_scenario,
    )

    spec = ScenarioSpec.model_validate_json(scenario_path.read_text(encoding="utf-8"))
    skin_model = NarrativeSkin.model_validate_json(skin.read_text(encoding="utf-8"))
    resolved = compile_scenario(spec, skin_model)
    typer.echo(json.dumps({
        "scenario_id": spec.scenario_id,
        "scenario_hash": resolved.scenario_hash,
        "mechanism_hash": resolved.mechanism_hash,
        "narrative_hash": resolved.narrative_hash,
        "evidence_corpus_hash": resolved.evidence_corpus_hash,
    }, indent=2))


@study_app.command("validate")
def study_validate(study_dir: Path) -> None:
    from collaborative_hill.experiments.study import validate_study

    typer.echo(json.dumps(validate_study(study_dir), indent=2))


@study_app.command("freeze")
def study_freeze(study_dir: Path,
                 yes: bool = typer.Option(False, "--yes",
                                          help="Confirm freezing (human decision)")) -> None:
    """Freeze a study (content hash + lock file). Requires explicit --yes."""
    from collaborative_hill.experiments.study import freeze_study

    if not yes:
        typer.echo("Freezing is a human-confirmed step. Re-run with --yes to confirm.")
        raise typer.Exit(code=1)
    h = freeze_study(study_dir)
    typer.echo(f"frozen: {h}")


@app.command("run")
def run(
    study_dir: Path,
    artifacts: Path = typer.Option(DEFAULT_ARTIFACTS, "--artifacts"),
    condition: str | None = typer.Option(None, "--condition"),
    replicates: int | None = typer.Option(None, "--replicates"),
) -> None:
    """Run a study's conditions x replicates."""
    from collaborative_hill.experiments.study import run_study

    try:
        results = run_study(study_dir, artifacts, only_condition=condition,
                            replicates_override=replicates)
    except ValueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if not results:
        typer.echo("error: no runs executed", err=True)
        raise typer.Exit(code=2)
    for r in results:
        line = f"{r.run_id}: {r.status} ({r.event_count} events, {r.rounds_played} rounds)"
        if r.failure_reason:
            line += f" — {r.failure_reason}"
        typer.echo(line)
    if any(r.status != "completed" for r in results):
        raise typer.Exit(code=2)


@app.command("replay")
def replay(run_dir: Path) -> None:
    """Re-execute a sealed run and verify the event hash chain matches."""
    from collaborative_hill.engine.replay import replay_run

    report = replay_run(run_dir)
    typer.echo(report.model_dump_json(indent=2))
    if not report.chains_match:
        raise typer.Exit(code=2)


_ALLOWED_EC_OVERRIDE_PARAMS: dict[str, set[str]] = {
    "ec_contributor": {"share_evidence"},
    "ec_freerider": set(),
    "ec_verifier": set(),
    "ec_misinformer": set(),
}

_ALLOWED_NIPD_OVERRIDE_PARAMS: dict[str, set[str]] = {
    "allc": set(),
    "alld": set(),
    "random": set(),
    "tft_pairwise": {"epsilon"},
    "tft_linked": {"epsilon"},
    "ptft": {"denominator", "epsilon"},
    "tft_threshold": {"threshold_num", "threshold_den", "epsilon"},
}


def _parse_override_item(item: str) -> tuple[str, str, dict[str, str]]:
    agent, sep, policy_expr = item.partition("=")
    if not sep or not agent or not policy_expr:
        raise typer.BadParameter(
            f"invalid --override {item!r}: expected agent=policy[:key=value,...]"
        )
    name, _, param_str = policy_expr.partition(":")
    if not name:
        raise typer.BadParameter(
            f"invalid --override {item!r}: expected agent=policy[:key=value,...]"
        )
    params: dict[str, str] = {}
    if param_str:
        for kv in param_str.split(","):
            k, ksep, v = kv.partition("=")
            if not ksep or not k or v == "":
                raise typer.BadParameter(
                    f"invalid param segment {kv!r} in --override {item!r}: "
                    "expected key=value"
                )
            params[k] = v
    return agent, name, params


def _reject_unknown_params(policy: str, params: dict[str, str],
                           allowed: set[str], item: str) -> None:
    unknown = sorted(set(params) - allowed)
    if unknown:
        raise typer.BadParameter(
            f"unknown param(s) {unknown} for policy {policy!r} "
            f"in --override {item!r}"
        )


@app.command("branch")
def branch(
    run_dir: Path,
    at_event: int = typer.Option(..., "--at-event", help="checkpoint seq to fork at"),
    override: list[str] = typer.Option(..., "--override",
                                       help="agent=policy[:key=value,...] (repeatable)"),
    out: Path = typer.Option(..., "--out", help="child run directory"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Fork a sealed run at a checkpoint with overridden agent policies."""
    from collaborative_hill.agents.scripted.params import coerce_policy_params
    from collaborative_hill.engine.branching import branch_run
    from collaborative_hill.engine.replay import load_run
    from collaborative_hill.experiments.scenario import NIPDWorld

    _, resolved, manifest = load_run(run_dir)
    overrides = {}
    for item in override:
        agent, name, params = _parse_override_item(item)
        if isinstance(resolved.spec.world, NIPDWorld):
            from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy

            allowed = _ALLOWED_NIPD_OVERRIDE_PARAMS.get(name)
            if allowed is None:
                raise typer.BadParameter(
                    f"unknown NIPD policy {name!r} in --override {item!r}"
                )
            _reject_unknown_params(name, params, allowed, item)
            try:
                parsed = coerce_policy_params(name, params)
                overrides[agent] = build_nipd_policy(
                    name, resolved.spec.world.mode, parsed
                )
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc
        else:
            from collaborative_hill.agents.scripted.ec_policies import build_ec_policy

            allowed = _ALLOWED_EC_OVERRIDE_PARAMS.get(name)
            if allowed is None:
                raise typer.BadParameter(
                    f"unknown EC policy {name!r} in --override {item!r}"
                )
            _reject_unknown_params(name, params, allowed, item)
            try:
                overrides[agent] = build_ec_policy(
                    name, coerce_policy_params(name, params)
                )
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc
    child_run_id = run_id or f"{manifest['run_id']}-branch{at_event}"
    result, branch_manifest = branch_run(
        parent_dir=run_dir, fork_seq=at_event, child_dir=out,
        child_run_id=child_run_id, policy_overrides=overrides,
    )
    typer.echo(branch_manifest.model_dump_json(indent=2))
    typer.echo(f"{result.run_id}: {result.status} ({result.event_count} events)")


@app.command("report")
def report(target: Path) -> None:
    """Generate report.md for a run directory or a study artifacts directory."""
    from collaborative_hill.reporting import run_report, study_report

    if (Path(target) / "events.jsonl").exists():
        out = run_report(target)
    else:
        out = study_report(target)
    typer.echo(str(out))


@app.command("doctor")
def doctor() -> None:
    """Check the environment: imports, determinism primitives, optional extras."""
    import platform
    import sys

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    check("python", sys.version_info >= (3, 12), sys.version.split()[0])
    try:
        import pydantic

        check("pydantic", True, pydantic.__version__)
    except ImportError:
        check("pydantic", False, "missing")
    from collaborative_hill.engine.hashing import content_hash
    from collaborative_hill.engine.seeds import derive_seed

    digest = content_hash({"a": 1})
    check("canonical-hash", len(digest) == 64, digest[:12])
    check("seed-derivation", derive_seed(42, "c", 0) == derive_seed(42, "c", 0), "stable")
    for extra in ("duckdb", "pyarrow", "matplotlib", "hypothesis", "pytest"):
        try:
            __import__(extra)
            check(extra, True, "ok")
        except ImportError:
            check(extra, False, "not installed (optional for core)")
    check("platform", True, platform.platform())

    width = max(len(n) for n, _, _ in checks)
    failures = 0
    for name, ok, detail in checks:
        status = "OK " if ok else "FAIL"
        if not ok:
            failures += 1
        typer.echo(f"{status} {name.ljust(width)} {detail}")
    if failures:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
