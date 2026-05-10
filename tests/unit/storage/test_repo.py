"""Storage `Repo` tests."""

from __future__ import annotations

import pytest

from evalkit.core.ids import new_id
from evalkit.core.models import (
    CaseExpected,
    CaseInput,
    DatasetItem,
    EvaluationRecord,
    Message,
    Suite,
)
from evalkit.errors import StorageError
from evalkit.storage.repo import Repo

SAMPLE_YAML = """
version: 1
name: ok
dataset: d.jsonl
models:
  - id: m
    provider: mock
evaluators:
  - name: exact_match
"""


def _suite() -> Suite:
    return Suite.model_validate(
        {
            "version": 1,
            "name": "ok",
            "dataset": "d.jsonl",
            "models": [{"id": "m", "provider": "mock"}],
            "evaluators": [{"name": "exact_match"}],
        }
    )


def _item(case_id: str = "c1") -> DatasetItem:
    return DatasetItem(
        case_id=case_id,
        input=CaseInput(messages=[Message(role="user", content="hi")]),
        expected=CaseExpected(text="hi"),
    )


@pytest.mark.unit
class TestRepoLifecycle:
    def test_upsert_suite_is_idempotent(self, repo: Repo) -> None:
        first = repo.upsert_suite(_suite(), yaml_text=SAMPLE_YAML)
        second = repo.upsert_suite(_suite(), yaml_text=SAMPLE_YAML)
        assert first == second

    def test_upsert_dataset_is_idempotent(self, repo: Repo) -> None:
        a = repo.upsert_dataset(path="d.jsonl", sha256="abc", row_count=2)
        b = repo.upsert_dataset(path="d.jsonl", sha256="abc", row_count=2)
        assert a == b

    def test_full_run_lifecycle(self, repo: Repo) -> None:
        suite_id = repo.upsert_suite(_suite(), yaml_text=SAMPLE_YAML)
        dataset_id = repo.upsert_dataset(path="d.jsonl", sha256="x", row_count=1)
        run_id = repo.start_run(suite_id=suite_id, dataset_id=dataset_id)

        case_pk = repo.record_case(
            run_id,
            item=_item(),
            case_index=0,
            model_id="m",
            provider="mock",
            output_text="hi",
            latency_ms=5,
            status="ok",
        )
        repo.record_evaluation(
            EvaluationRecord(
                id=new_id(),
                case_id=case_pk,
                evaluator_name="exact_match",
                evaluator_version="1.0",
                score=1.0,
                passed=True,
                duration_ms=1,
            )
        )
        repo.finish_run(run_id, status="passed", exit_code=0)

        run = repo.get_run(run_id)
        assert run is not None
        assert run.status == "passed"
        assert run.case_count == 1
        assert run.pass_count == 1
        assert run.fail_count == 0
        assert run.error_count == 0

        cases = repo.get_cases(run_id)
        assert len(cases) == 1
        evaluations = repo.get_evaluations(run_id)
        assert len(evaluations) == 1
        assert evaluations[0].evaluator_name == "exact_match"

    def test_finish_unknown_run_raises(self, repo: Repo) -> None:
        with pytest.raises(StorageError):
            repo.finish_run("01ARZ3NDEKTSV4RRFFQ69G5FAV", status="passed", exit_code=0)

    def test_list_runs_orders_newest_first(self, repo: Repo) -> None:
        suite_id = repo.upsert_suite(_suite(), yaml_text=SAMPLE_YAML)
        dataset_id = repo.upsert_dataset(path="d.jsonl", sha256="y", row_count=1)
        first = repo.start_run(suite_id=suite_id, dataset_id=dataset_id)
        second = repo.start_run(suite_id=suite_id, dataset_id=dataset_id)
        runs = repo.list_runs()
        assert [r.id for r in runs[:2]] == [second, first]
