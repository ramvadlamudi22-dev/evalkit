"""End-to-end regression-comparison test using baseline + candidate runs.

Drives the same code path the CLI exercises: run a passing suite, tag it as
baseline, run a degraded suite, then call ``cmd_compare`` and expect exit 1.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from evalkit.cli import app
from evalkit.loaders import load_dataset, load_suite
from evalkit.runner import run_suite
from evalkit.storage import engine_for, ensure_schema, session_factory_for
from evalkit.storage.repo import Repo

SUITE_TMPL = """\
version: 1
name: compare-{tag}
dataset: data.jsonl
models:
  - id: mock-1
    provider: mock
evaluators:
  - name: exact_match
"""


def _write_suite(path: Path, tag: str) -> None:
    path.write_text(SUITE_TMPL.format(tag=tag), encoding="utf-8")


def _write_dataset(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


_PASS_LINE_A = (
    '{"case_id":"a","input":{"messages":[{"role":"user","content":"hello"}]},'
    '"expected":{"text":"hello"}}'
)
_PASS_LINE_C = (
    '{"case_id":"c","input":{"messages":[{"role":"user","content":"hello"}]},'
    '"expected":{"text":"hello"}}'
)
_FAIL_LINE_B = (
    '{"case_id":"b","input":{"messages":[{"role":"user","content":"hello"}]},'
    '"expected":{"text":"WRONG"}}'
)


async def _run_and_return_id(repo: Repo, suite_path: Path) -> str:
    suite, raw = load_suite(suite_path)
    dataset = load_dataset(suite_path.parent / suite.dataset)
    outcome = await run_suite(
        suite=suite,
        suite_yaml_text=raw,
        suite_path=suite_path,
        dataset=dataset,
        repo=repo,
    )
    return outcome.run_id


@pytest.mark.integration
async def test_compare_detects_pass_rate_regression(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    _write_suite(suite_path, tag="x")
    dataset_path = tmp_path / "data.jsonl"

    db_path = tmp_path / "evalkit.db"
    engine = engine_for(db_path)
    ensure_schema(engine)
    repo = Repo(session_factory_for(engine))

    # Baseline: both cases pass.
    _write_dataset(dataset_path, [_PASS_LINE_A, _PASS_LINE_C])
    baseline_id = await _run_and_return_id(repo, suite_path)

    # Candidate: one case fails.
    _write_dataset(dataset_path, [_PASS_LINE_A, _FAIL_LINE_B])
    candidate_id = await _run_and_return_id(repo, suite_path)
    engine.dispose()

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["compare", baseline_id, candidate_id, "--db", str(db_path), "--threshold", "0.0"],
    )
    assert result.exit_code == 1, result.output
    assert "REGRESSION" in result.output


@pytest.mark.integration
async def test_compare_passes_when_pass_rate_holds(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    _write_suite(suite_path, tag="y")
    dataset_path = tmp_path / "data.jsonl"

    db_path = tmp_path / "evalkit.db"
    engine = engine_for(db_path)
    ensure_schema(engine)
    repo = Repo(session_factory_for(engine))

    _write_dataset(dataset_path, [_PASS_LINE_A])
    a = await _run_and_return_id(repo, suite_path)
    # Same dataset -> same pass rate.
    b = await _run_and_return_id(repo, suite_path)
    engine.dispose()

    runner = CliRunner()
    result = runner.invoke(app, ["compare", a, b, "--db", str(db_path)])
    assert result.exit_code == 0, result.output
    assert "OK" in result.output


@pytest.mark.integration
async def test_baseline_set_and_get_roundtrip(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    _write_suite(suite_path, tag="b")
    dataset_path = tmp_path / "data.jsonl"
    _write_dataset(dataset_path, [_PASS_LINE_A])

    db_path = tmp_path / "evalkit.db"
    engine = engine_for(db_path)
    ensure_schema(engine)
    repo = Repo(session_factory_for(engine))
    run_id = await _run_and_return_id(repo, suite_path)
    engine.dispose()

    runner = CliRunner()
    set_result = runner.invoke(
        app,
        ["baseline", "set", run_id, "--name", "release-1", "--db", str(db_path)],
    )
    assert set_result.exit_code == 0, set_result.output
    assert run_id in set_result.output

    get_result = runner.invoke(
        app, ["baseline", "get", "--name", "release-1", "--db", str(db_path)]
    )
    assert get_result.exit_code == 0, get_result.output
    assert run_id in get_result.output
    assert "pass_rate=1.000" in get_result.output


@pytest.mark.integration
def test_baseline_get_missing_label_exits_64(tmp_path: Path) -> None:
    db_path = tmp_path / "evalkit.db"
    engine = engine_for(db_path)
    ensure_schema(engine)
    engine.dispose()

    runner = CliRunner()
    result = runner.invoke(app, ["baseline", "get", "--name", "nope", "--db", str(db_path)])
    assert result.exit_code == 64
