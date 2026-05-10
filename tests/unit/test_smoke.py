"""Phase 0 smoke tests: package imports and CLI exposes --version."""

from __future__ import annotations

import re
import subprocess
import sys

import pytest
from typer.testing import CliRunner

import evalkit
from evalkit.cli import app


@pytest.mark.unit
def test_version_is_set() -> None:
    assert isinstance(evalkit.__version__, str)
    assert evalkit.__version__ != ""


@pytest.mark.unit
def test_version_looks_semver_ish() -> None:
    # Either a real semver-shaped string (e.g. "0.0.1") or the editable fallback.
    assert re.match(r"^\d+\.\d+\.\d+(?:[+\-].*)?$", evalkit.__version__)


@pytest.mark.unit
def test_cli_version_flag_prints_version_and_exits_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert evalkit.__version__ in result.output
    assert "evalkit" in result.output.lower()


@pytest.mark.unit
def test_cli_help_lists_command_name() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert "evalkit" in result.output.lower()


@pytest.mark.unit
def test_cli_no_args_shows_help() -> None:
    # `no_args_is_help=True` prints the help screen on a bare invocation. Click's exit code
    # for this path differs across Typer/Click versions (some return 0, some return 2); we
    # assert on the visible behaviour (help text rendered) and tolerate either exit.
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert "Usage:" in result.output
    assert "evalkit" in result.output.lower()
    assert result.exit_code in {0, 2}


@pytest.mark.unit
def test_module_entry_point_prints_version() -> None:
    # Verify `python -m evalkit --version` works end-to-end via the __main__ entry point.
    result = subprocess.run(
        [sys.executable, "-m", "evalkit", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert evalkit.__version__ in result.stdout
