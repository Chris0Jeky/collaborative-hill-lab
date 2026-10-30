"""chl — the Collaborative Hill Lab command line.

    chl scenario validate <scenario.json> --skin <skin.json>
    chl study validate <study-dir>
    chl study audit-seeds <study-dir> [--replicate N] [--round N]
    chl study freeze <study-dir>          (explicit human step)
    chl study plan <study-dir> [--condition ID] [--replicates N]   (offline request maxima)
    chl run <study-dir> [--artifacts DIR] [--condition ID] [--replicates N]
    chl replay <run-dir>
    chl branch <run-dir> --at-event N --override agent=policy[:param=value...] --out DIR
    chl compare <left-run> <right-run> [--verify-replay]
    chl report <run-or-study-artifacts-dir>
    chl analyze <study-artifacts-dir> [--out FILE]
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


@study_app.command("audit-seeds")
def study_audit_seeds(
    study_dir: Path,
    replicate: int = typer.Option(0, "--replicate", min=0, help="Zero-based study replicate"),
    round_index: int = typer.Option(0, "--round", min=0, help="Zero-based scheduled round"),
) -> None:
    """Print kernel stream identities as JSON, without running or changing the study."""
    from collaborative_hill.experiments.seed_audit import audit_study_seeds

    try:
        audit = audit_study_seeds(study_dir, replicate=replicate, round_index=round_index)
    except (ValueError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(audit, indent=2, sort_keys=True))


@study_app.command("plan")
def study_plan(
    study_dir: Path,
    condition: str | None = typer.Option(None, "--condition"),
    replicates: int | None = typer.Option(None, "--replicates"),
    max_episode_request_attempts: int | None = typer.Option(None, min=0),
    max_run_request_attempts: int | None = typer.Option(None, min=0),
) -> None:
    """Print worst-case request counts as JSON. Offline: no credentials, no requests."""
    from collaborative_hill.experiments.request_plan import plan_study

    try:
        plan = plan_study(study_dir, only_condition=condition, replicates_override=replicates,
                          max_episode_attempts=max_episode_request_attempts,
                          max_run_attempts=max_run_request_attempts)
    except (ValueError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(plan, indent=2, sort_keys=True))


@study_app.command("freeze")
def study_freeze(study_dir: Path,
                 yes: bool = typer.Option(False, "--yes",
                                          help="Confirm freezing (human decision)")) -> None:
    """Freeze a study (content hash + lock file). Requires explicit --yes."""
    from collaborative_hill.experiments.study import freeze_study

    if not yes:
        typer.echo("Freezing is a human-confirmed step. Re-run with --yes to confirm.")
        raise typer.Exit(code=1)
    try:
        h = freeze_study(study_dir)
    except ValueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"frozen: {h}")


@app.command("run")
def run(
    study_dir: Path,
    artifacts: Path = typer.Option(DEFAULT_ARTIFACTS, "--artifacts"),
    condition: str | None = typer.Option(None, "--condition"),
    replicates: int | None = typer.Option(None, "--replicates"),
    allow_provider_requests: bool = typer.Option(
        False, "--allow-provider-requests", help="Explicitly enable configured model requests"),
    max_episode_request_attempts: int | None = typer.Option(
        None, min=0, help="Admit at most N HTTP attempts per episode (default: no limit)"),
    max_run_request_attempts: int | None = typer.Option(
        None, min=0, help="Admit at most N HTTP attempts in this whole invocation"),
    deadline_seconds: int | None = typer.Option(
        None, min=0, help="Stop admitting requests after N seconds; checked between requests"),
) -> None:
    """Run a study's conditions x replicates."""
    from collaborative_hill.agents.llm import RequestBudget
    from collaborative_hill.experiments.study import run_study

    budget = None
    if (max_episode_request_attempts, max_run_request_attempts, deadline_seconds) != (None,) * 3:
        budget = RequestBudget(max_episode_attempts=max_episode_request_attempts,
                               max_run_attempts=max_run_request_attempts,
                               deadline_seconds=deadline_seconds)
    try:
        results = run_study(study_dir, artifacts, only_condition=condition,
                            replicates_override=replicates,
                            allow_provider_requests=allow_provider_requests,
                            request_budget=budget)
    except (ValueError, FileExistsError) as exc:
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

    try:
        report = replay_run(run_dir)
    except (ValueError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(report.model_dump_json(indent=2))
    if not report.chains_match:
        raise typer.Exit(code=2)


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


@app.command("branch")
def branch(
    run_dir: Path,
    at_event: int = typer.Option(..., "--at-event", help="checkpoint seq to fork at"),
    override: list[str] = typer.Option(..., "--override",
                                       help="agent=policy[:key=value,...] (repeatable)"),
    out: Path = typer.Option(..., "--out", help="child run directory"),
    run_id: str | None = typer.Option(None, "--run-id"),
    allow_provider_requests: bool = typer.Option(
        False, "--allow-provider-requests", help="Enable model requests in the continuation"),
) -> None:
    """Fork a sealed run at a checkpoint with overridden agent policies."""
    from collaborative_hill.agents.scripted.params import (
        EC_POLICY_PARAMS,
        NIPD_POLICY_PARAMS,
        coerce_policy_params,
    )
    from collaborative_hill.engine.branching import branch_run
    from collaborative_hill.engine.replay import load_run
    from collaborative_hill.experiments.scenario import GraphNIPDWorld, NIPDWorld

    try:
        _, resolved, manifest = load_run(run_dir)
    except (ValueError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    overrides = {}
    for item in override:
        agent, name, params = _parse_override_item(item)
        if isinstance(resolved.spec.world, NIPDWorld | GraphNIPDWorld):
            from collaborative_hill.agents.scripted.graph_nipd_policies import (
                build_graph_nipd_policy,
            )
            from collaborative_hill.agents.scripted.nipd_policies import build_nipd_policy

            if name not in NIPD_POLICY_PARAMS:
                raise typer.BadParameter(
                    f"unknown NIPD policy {name!r} in --override {item!r}"
                )
            try:
                parsed = coerce_policy_params(name, params)
                builder = (
                    build_graph_nipd_policy
                    if isinstance(resolved.spec.world, GraphNIPDWorld) else build_nipd_policy
                )
                overrides[agent] = builder(name, resolved.spec.world.mode, parsed)
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc
        else:
            from collaborative_hill.agents.scripted.ec_policies import build_ec_policy

            if name not in EC_POLICY_PARAMS:
                raise typer.BadParameter(
                    f"unknown EC policy {name!r} in --override {item!r}"
                )
            try:
                overrides[agent] = build_ec_policy(
                    name, coerce_policy_params(name, params)
                )
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc
    child_run_id = run_id or f"{manifest['run_id']}-branch{at_event}"
    try:
        result, branch_manifest = branch_run(
            parent_dir=run_dir, fork_seq=at_event, child_dir=out,
            child_run_id=child_run_id, policy_overrides=overrides,
            allow_provider_requests=allow_provider_requests,
        )
    except (ValueError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(branch_manifest.model_dump_json(indent=2))
    typer.echo(f"{result.run_id}: {result.status} ({result.event_count} events)")


@app.command("compare")
def compare(
    left: Path,
    right: Path,
    verify_replay: bool = typer.Option(False, "--verify-replay",
                                       help="Re-execute both ledgers before comparing"),
) -> None:
    """Print a read-only, descriptive JSON comparison of two compatible runs."""
    from collaborative_hill.reporting.comparison import compare_runs

    try:
        result = compare_runs(left, right, verify_replay=verify_replay)
    except (ValueError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result, indent=2, sort_keys=True))


@app.command("report")
def report(target: Path) -> None:
    """Generate report.md for a run directory or a study artifacts directory."""
    from collaborative_hill.reporting import run_report, study_report

    if (Path(target) / "events.jsonl").exists():
        out = run_report(target)
    else:
        out = study_report(target)
    typer.echo(str(out))


@app.command("analyze")
def analyze(
    study_dir: Path,
    out: Path | None = typer.Option(None, "--out", help="New canonical JSON file"),
) -> None:
    """Draft SAP analysis of sealed artifacts/<study-prefix> (no episode re-execution)."""
    from collaborative_hill.engine.hashing import canonical_json
    from collaborative_hill.reporting.analysis import analyze_study

    try:
        result = canonical_json(analyze_study(study_dir)) + "\n"
        if out is None:
            typer.echo(result, nl=False)
        else:
            target, source = out.resolve(), study_dir.resolve()
            if target.is_relative_to(source) and target.parent != source:
                raise ValueError("analysis output must be outside run directories")
            # Never overwrite a sealed source, existing analysis, or unrelated file.
            with out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(result)
    except (ValueError, OSError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


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
