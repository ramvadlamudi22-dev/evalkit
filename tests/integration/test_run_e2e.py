"""End-to-end runner integration test (no subprocess; in-process)."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalkit.loaders import load_dataset, load_suite
from evalkit.runner import run_suite
from evalkit.storage import engine_for, ensure_schema, session_factory_for
from evalkit.storage.repo import Repo

SUITE = """
version: 1
name: e2e
dataset: data.jsonl
models:
  - id: mock-1
    provider: mock
evaluators:
  - name: exact_match
    case_insensitive: true
  - name: contains
"""

DATASET = (
    '{"case_id":"a","input":{"messages":[{"role":"user","content":"hello"}]},'
    '"expected":{"text":"hello","must_contain":["hello"]}}\n'
    '{"case_id":"b","input":{"messages":[{"role":"user","content":"world"}]},'
    '"expected":{"text":"world","must_contain":["world"]}}\n'
)


@pytest.mark.integration
def test_full_passing_run_persists_results(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text(SUITE, encoding="utf-8")
    dataset_path = tmp_path / "data.jsonl"
    dataset_path.write_text(DATASET, encoding="utf-8")

    suite, raw = load_suite(suite_path)
    dataset = load_dataset(dataset_path)

    engine = engine_for(tmp_path / "evalkit.db")
    ensure_schema(engine)
    repo = Repo(session_factory_for(engine))

    outcome = run_suite(
        suite=suite,
        suite_yaml_text=raw,
        suite_path=suite_path,
        dataset=dataset,
        repo=repo,
    )
    assert outcome.exit_code == 0
    assert outcome.case_count == 2
    assert outcome.pass_count == 2

    run = repo.get_run(outcome.run_id)
    assert run is not None
    assert run.status == "passed"
    assert run.dataset_path.endswith("data.jsonl")
    cases = repo.get_cases(outcome.run_id)
    assert {c.case_id for c in cases} == {"a", "b"}
    evaluations = repo.get_evaluations(outcome.run_id)
    assert {e.evaluator_name for e in evaluations} == {"exact_match", "contains"}
