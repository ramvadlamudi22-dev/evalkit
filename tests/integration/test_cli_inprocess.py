"""In-process CLI tests via Typer's CliRunner.

The e2e tests in tests/e2e/test_cli_run.py drive the installed wheel via
subprocess and are the source of truth for shipping behaviour. These
in-process variants are added so coverage tracks the CLI module and edge
cases (missing run-id, error paths) are exercised directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from evalkit.cli import app

_SUITE = """\
version: 1
name: cli-inproc
dataset: data.jsonl
models:
  - id: mock-1
    provider: mock
evaluators:
  - name: exact_match
"""

_DATA_PASS = (
    '{"case_id":"a","input":{"messages":[{"role":"user","content":"hi"}]},'
    '"expected":{"text":"hi"}}\n'
)
_DATA_FAIL = (
    '{"case_id":"b","input":{"messages":[{"role":"user","content":"hi"}]},'
    '"expected":{"text":"WRONG"}}\n'
)


def _seed(tmp_path: Path, *, data: str) -> tuple[Path, Path]:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text(_SUITE, encoding="utf-8")
    (tmp_path / "data.jsonl").write_text(data, encoding="utf-8")
    return suite_path, tmp_path / "evalkit.db"


@pytest.mark.integration
class TestCliRun:
    def test_run_passing_exits_zero_and_prints_summary(self, tmp_path: Path) -> None:
        suite_path, db = _seed(tmp_path, data=_DATA_PASS)
        result = CliRunner().invoke(app, ["run", str(suite_path), "--db", str(db)])
        assert result.exit_code == 0, result.output
        assert "passed=1" in result.output
        assert "failed=0" in result.output

    def test_run_failing_exits_one(self, tmp_path: Path) -> None:
        suite_path, db = _seed(tmp_path, data=_DATA_FAIL)
        result = CliRunner().invoke(app, ["run", str(suite_path), "--db", str(db)])
        assert result.exit_code == 1, result.output
        assert "failed=1" in result.output


@pytest.mark.integration
class TestCliListAndShow:
    def test_list_runs_empty(self, tmp_path: Path) -> None:
        db = tmp_path / "evalkit.db"
        result = CliRunner().invoke(app, ["list", "runs", "--db", str(db)])
        assert result.exit_code == 0, result.output
        assert "(no runs yet)" in result.output

    def test_show_unknown_run_exits_64(self, tmp_path: Path) -> None:
        db = tmp_path / "evalkit.db"
        result = CliRunner().invoke(app, ["show", "01ABCDEFGH", "--db", str(db)])
        assert result.exit_code == 64

    def test_show_existing_run(self, tmp_path: Path) -> None:
        suite_path, db = _seed(tmp_path, data=_DATA_PASS)
        CliRunner().invoke(app, ["run", str(suite_path), "--db", str(db)])
        listing = CliRunner().invoke(app, ["list", "runs", "--db", str(db)])
        run_id = listing.output.split()[0]
        show = CliRunner().invoke(app, ["show", run_id, "--db", str(db)])
        assert show.exit_code == 0, show.output
        assert "PASS" in show.output
        assert "exact_match/1.0" in show.output


@pytest.mark.integration
class TestCliInit:
    def test_init_scaffolds_starter_project(self, tmp_path: Path) -> None:
        proj = tmp_path / "demo"
        result = CliRunner().invoke(app, ["init", str(proj)])
        assert result.exit_code == 0, result.output
        assert (proj / "suite.yaml").exists()
        assert (proj / "datasets" / "sample.jsonl").exists()

    def test_init_refuses_to_overwrite_without_force(self, tmp_path: Path) -> None:
        proj = tmp_path / "demo"
        first = CliRunner().invoke(app, ["init", str(proj)])
        assert first.exit_code == 0
        # The CliRunner skips the top-level main() wrapper that maps
        # UsageError -> exit 64; the wrapped subprocess test in
        # tests/e2e/test_cli_run.py exercises the full mapping.
        second = CliRunner().invoke(app, ["init", str(proj)])
        assert second.exit_code != 0
        assert "refusing to overwrite" in str(second.exception or "")


@pytest.mark.integration
class TestCliBaselineErrors:
    def test_set_unknown_run_exits_64(self, tmp_path: Path) -> None:
        db = tmp_path / "evalkit.db"
        result = CliRunner().invoke(
            app, ["baseline", "set", "01NOPENOPENOPE", "--db", str(db)]
        )
        assert result.exit_code == 64

    def test_compare_unknown_run_exits_64(self, tmp_path: Path) -> None:
        db = tmp_path / "evalkit.db"
        result = CliRunner().invoke(
            app, ["compare", "01A", "01B", "--db", str(db)]
        )
        assert result.exit_code == 64


@pytest.mark.integration
class TestCliVersion:
    def test_version_flag_prints_version(self) -> None:
        result = CliRunner().invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "evalkit" in result.output
