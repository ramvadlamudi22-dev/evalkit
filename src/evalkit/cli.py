"""EvalKit command-line interface.

Phase 0 surface:
    evalkit --version          Print version and exit.
    evalkit --help             Show help and exit.

Phase 1 additions:
    evalkit init [DIR]         Scaffold a starter project.
    evalkit run SUITE          Execute a suite end-to-end.
    evalkit list runs          List recent runs.
    evalkit show RUN_ID        Render one run.

Phase 2 additions:
    evalkit baseline set RUN_ID [--name NAME]
    evalkit baseline get [--name NAME]
    evalkit compare RUN_A RUN_B [--threshold P]

The remaining subcommands (report, doctor) land in subsequent phases per
docs/architecture/21_PHASED_ROADMAP.md.
"""

from __future__ import annotations

import asyncio
import shutil
from importlib import resources
from pathlib import Path
from typing import Annotated

import typer

from evalkit import __version__
from evalkit.errors import EvalKitError, UsageError
from evalkit.loaders import load_dataset, load_suite
from evalkit.logging import configure_logging
from evalkit.runner import run_suite
from evalkit.storage import db_path_from_env, engine_for, ensure_schema, session_factory_for
from evalkit.storage.repo import Repo

app = typer.Typer(
    name="evalkit",
    help="A pytest-shaped LLM evaluation toolkit.",
    no_args_is_help=True,
    add_completion=False,
)
list_app = typer.Typer(name="list", help="List EvalKit resources.", no_args_is_help=True)
app.add_typer(list_app, name="list")
baseline_app = typer.Typer(
    name="baseline", help="Manage named baseline runs.", no_args_is_help=True
)
app.add_typer(baseline_app, name="baseline")


DEFAULT_BASELINE = "default"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"evalkit {__version__}")
        raise typer.Exit(code=0)


@app.callback()
def root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the EvalKit version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """EvalKit - declarative LLM evaluation suites with reproducible runs."""


# ----- init ---------------------------------------------------------------


@app.command("init")
def cmd_init(
    directory: Annotated[
        Path,
        typer.Argument(
            help="Target directory; created if missing.",
            file_okay=False,
            resolve_path=True,
        ),
    ] = Path("."),
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files.")] = False,
) -> None:
    """Scaffold a starter project (suite.yaml + dataset + mock fixture)."""
    directory.mkdir(parents=True, exist_ok=True)
    template_root = resources.files("evalkit._resources.init_template")
    written: list[Path] = []
    for entry in template_root.iterdir():
        # The init_template is a Python sub-package so importlib can find it,
        # so we skip the package machinery (`__init__.py`, `__pycache__`).
        if entry.name == "__init__.py" or entry.name == "__pycache__":
            continue
        target = directory / entry.name
        if entry.is_dir():
            target.mkdir(exist_ok=True)
            for child in entry.iterdir():
                if child.name == "__init__.py" or child.name == "__pycache__":
                    continue
                child_target = target / child.name
                _copy_resource(child, child_target, force=force, written=written)
        else:
            _copy_resource(entry, target, force=force, written=written)
    typer.echo(f"Scaffolded EvalKit project in {directory}")
    for p in written:
        typer.echo(f"  + {p.relative_to(directory)}")


def _copy_resource(src: object, dst: Path, *, force: bool, written: list[Path]) -> None:
    if dst.exists() and not force:
        raise UsageError(f"refusing to overwrite {dst} (use --force)")
    # `src` is an `importlib.resources.abc.Traversable`; mypy doesn't know that
    # all the methods we call exist. Cast through `object` to silence noise.
    data = src.read_bytes()  # type: ignore[attr-defined]
    dst.write_bytes(data)
    written.append(dst)


# ----- run ---------------------------------------------------------------


@app.command("run")
def cmd_run(
    suite_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the suite YAML file.",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Override the SQLite DB path."),
    ] = None,
) -> None:
    """Execute a suite and print a one-line summary; exit 0/1/2 per result."""
    repo = _open_repo(db)
    suite, yaml_text = load_suite(suite_path)
    dataset_path = (suite_path.parent / suite.dataset).resolve()
    if not dataset_path.exists():
        raise UsageError(f"dataset not found: {dataset_path}")
    dataset = load_dataset(dataset_path)

    configure_logging()
    outcome = asyncio.run(
        run_suite(
            suite=suite,
            suite_yaml_text=yaml_text,
            suite_path=suite_path,
            dataset=dataset,
            repo=repo,
        )
    )
    typer.echo(
        f"run_id={outcome.run_id} cases={outcome.case_count} "
        f"passed={outcome.pass_count} failed={outcome.fail_count} "
        f"errored={outcome.error_count} exit={outcome.exit_code}"
    )
    raise typer.Exit(code=outcome.exit_code)


# ----- list runs ---------------------------------------------------------


@list_app.command("runs")
def cmd_list_runs(
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 20,
    db: Annotated[Path | None, typer.Option("--db")] = None,
) -> None:
    """List the most recent runs (newest first)."""
    repo = _open_repo(db)
    runs = repo.list_runs(limit=limit)
    if not runs:
        typer.echo("(no runs yet)")
        return
    for run in runs:
        ts = run.started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        typer.echo(
            f"{run.id}  {ts}  {run.status:8s}  "
            f"cases={run.case_count} passed={run.pass_count} "
            f"failed={run.fail_count} errored={run.error_count}  {run.suite_name}"
        )


# ----- show --------------------------------------------------------------


@app.command("show")
def cmd_show(
    run_id: Annotated[str, typer.Argument(help="Run ID (ULID).")],
    db: Annotated[Path | None, typer.Option("--db")] = None,
) -> None:
    """Render one run as a plain-text report."""
    repo = _open_repo(db)
    run = repo.get_run(run_id)
    if run is None:
        typer.echo(f"run not found: {run_id}", err=True)
        raise typer.Exit(code=64)
    started = run.started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    finished = run.finished_at.strftime("%Y-%m-%dT%H:%M:%SZ") if run.finished_at else "-"
    typer.echo(f"run_id   : {run.id}")
    typer.echo(f"suite    : {run.suite_name}")
    typer.echo(f"dataset  : {run.dataset_path}")
    typer.echo(f"status   : {run.status}  exit={run.exit_code}")
    typer.echo(f"started  : {started}")
    typer.echo(f"finished : {finished}")
    typer.echo(
        f"summary  : cases={run.case_count} passed={run.pass_count} "
        f"failed={run.fail_count} errored={run.error_count}"
    )

    cases = repo.get_cases(run_id)
    evaluations = repo.get_evaluations(run_id)
    by_case: dict[str, list] = {}  # type: ignore[type-arg]
    for ev in evaluations:
        by_case.setdefault(ev.case_id, []).append(ev)

    typer.echo("")
    typer.echo("cases:")
    for case in cases:
        evs = by_case.get(case.id, [])
        if case.status != "ok":
            verdict = f"ERROR ({case.error_code})"
        elif evs and all(e.passed for e in evs):
            verdict = "PASS"
        else:
            verdict = "FAIL"
        typer.echo(
            f"  [{case.case_index:>3d}] {verdict:<6s}  "
            f"{case.case_id}  model={case.model_id}  latency_ms={case.latency_ms or 0}"
        )
        for ev in evs:
            typer.echo(
                f"        - {ev.evaluator_name}/{ev.evaluator_version}  "
                f"score={ev.score:.2f}  passed={ev.passed}"
            )


# ----- baseline ----------------------------------------------------------


@baseline_app.command("set")
def cmd_baseline_set(
    run_id: Annotated[str, typer.Argument(help="Run ID (ULID) to tag as baseline.")],
    name: Annotated[str, typer.Option("--name", help="Baseline label.")] = DEFAULT_BASELINE,
    db: Annotated[Path | None, typer.Option("--db")] = None,
) -> None:
    """Point a baseline label at a run id."""
    repo = _open_repo(db)
    if repo.get_run(run_id) is None:
        typer.echo(f"run not found: {run_id}", err=True)
        raise typer.Exit(code=64)
    repo.set_baseline(label=name, run_id=run_id)
    typer.echo(f"baseline {name!r} -> {run_id}")


@baseline_app.command("get")
def cmd_baseline_get(
    name: Annotated[str, typer.Option("--name", help="Baseline label.")] = DEFAULT_BASELINE,
    db: Annotated[Path | None, typer.Option("--db")] = None,
) -> None:
    """Print the run currently tagged as baseline ``name``."""
    repo = _open_repo(db)
    run = repo.get_baseline(name)
    if run is None:
        typer.echo(f"no baseline set for label {name!r}", err=True)
        raise typer.Exit(code=64)
    started = run.started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    pass_rate = (run.pass_count / run.case_count) if run.case_count else 0.0
    typer.echo(
        f"baseline={name} run_id={run.id} status={run.status} "
        f"started={started} cases={run.case_count} passed={run.pass_count} "
        f"failed={run.fail_count} errored={run.error_count} "
        f"pass_rate={pass_rate:.3f}"
    )


# ----- compare -----------------------------------------------------------


@app.command("compare")
def cmd_compare(
    run_a: Annotated[str, typer.Argument(help="Baseline run ID (or label via --baseline).")],
    run_b: Annotated[str, typer.Argument(help="Candidate run ID.")],
    threshold: Annotated[
        float,
        typer.Option(
            "--threshold",
            min=0.0,
            max=1.0,
            help="Maximum allowed pass-rate drop (fraction). Default 0 = no regression.",
        ),
    ] = 0.0,
    db: Annotated[Path | None, typer.Option("--db")] = None,
) -> None:
    """Compare two runs; exit 1 if the pass-rate drop exceeds threshold."""
    repo = _open_repo(db)
    baseline = repo.get_run(run_a)
    candidate = repo.get_run(run_b)
    if baseline is None:
        typer.echo(f"run not found: {run_a}", err=True)
        raise typer.Exit(code=64)
    if candidate is None:
        typer.echo(f"run not found: {run_b}", err=True)
        raise typer.Exit(code=64)

    def _pass_rate(case_count: int, pass_count: int) -> float:
        return (pass_count / case_count) if case_count else 0.0

    base_rate = _pass_rate(baseline.case_count, baseline.pass_count)
    cand_rate = _pass_rate(candidate.case_count, candidate.pass_count)
    delta = cand_rate - base_rate
    regression = -delta > threshold

    typer.echo(f"baseline  : {baseline.id}  pass_rate={base_rate:.3f}")
    typer.echo(f"candidate : {candidate.id}  pass_rate={cand_rate:.3f}")
    typer.echo(f"delta     : {delta:+.3f} (threshold drop allowed: {threshold:.3f})")
    typer.echo("verdict   : REGRESSION" if regression else "verdict   : OK")
    raise typer.Exit(code=1 if regression else 0)


# ----- shared -----------------------------------------------------------


def _open_repo(db_override: Path | None) -> Repo:
    db_path = db_override or db_path_from_env()
    engine = engine_for(db_path)
    ensure_schema(engine)
    return Repo(session_factory_for(engine))


# ----- top-level error handler ------------------------------------------


def main() -> None:  # pragma: no cover - thin wrapper, exercised via subprocess test
    try:
        app()
    except UsageError as exc:
        typer.echo(f"error: {exc.user_message()}", err=True)
        raise typer.Exit(code=64) from exc
    except EvalKitError as exc:
        typer.echo(f"error: {exc.user_message()}", err=True)
        raise typer.Exit(code=2) from exc


# Quiet `unused` warnings on `shutil` if a future cleanup path needs it.
_ = shutil
