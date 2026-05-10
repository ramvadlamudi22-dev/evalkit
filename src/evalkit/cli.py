"""EvalKit command-line interface.

Phase 0 surface:
    evalkit --version   Print version and exit.
    evalkit --help      Show help and exit.

Subcommands (init, run, list, show, compare, baseline, report, doctor)
land in subsequent phases per docs/architecture/21_PHASED_ROADMAP.md.
"""

from typing import Annotated

import typer

from evalkit import __version__

app = typer.Typer(
    name="evalkit",
    help="A pytest-shaped LLM evaluation toolkit.",
    no_args_is_help=True,
    add_completion=False,
)


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
    """EvalKit — declarative LLM evaluation suites with reproducible runs."""
