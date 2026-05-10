"""Runner unit tests using `MockProvider` overrides."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalkit.core.models import Dataset, DatasetItem, Suite
from evalkit.providers.mock import MockProvider
from evalkit.runner import run_suite
from evalkit.storage.repo import Repo

SUITE_YAML = """
version: 1
name: rt
dataset: d.jsonl
models:
  - id: m1
    provider: mock
evaluators:
  - name: exact_match
"""


def _suite() -> Suite:
    return Suite.model_validate(
        {
            "version": 1,
            "name": "rt",
            "dataset": "d.jsonl",
            "models": [{"id": "m1", "provider": "mock"}],
            "evaluators": [{"name": "exact_match"}],
        }
    )


def _dataset(items: list[DatasetItem]) -> Dataset:
    return Dataset(path="d.jsonl", sha256="z" * 64, items=items)


def _item(case_id: str, *, content: str, expected: str) -> DatasetItem:
    return DatasetItem.model_validate(
        {
            "case_id": case_id,
            "input": {"messages": [{"role": "user", "content": content}]},
            "expected": {"text": expected},
        }
    )


@pytest.mark.unit
def test_runner_persists_passing_run(repo: Repo, tmp_path: Path) -> None:
    suite = _suite()
    dataset = _dataset([_item("c1", content="hi", expected="hi")])
    provider = MockProvider(responses={("c1", "m1"): "hi"}, latency_ms=0)

    outcome = run_suite(
        suite=suite,
        suite_yaml_text=SUITE_YAML,
        suite_path=tmp_path / "s.yaml",
        dataset=dataset,
        repo=repo,
        provider_overrides={"m1": provider},
    )
    assert outcome.exit_code == 0
    assert outcome.case_count == 1
    assert outcome.pass_count == 1


@pytest.mark.unit
def test_runner_returns_exit_one_when_a_case_fails(repo: Repo, tmp_path: Path) -> None:
    suite = _suite()
    dataset = _dataset(
        [
            _item("c1", content="hi", expected="hi"),
            _item("c2", content="yo", expected="WRONG"),
        ]
    )
    provider = MockProvider(latency_ms=0)  # default echo

    outcome = run_suite(
        suite=suite,
        suite_yaml_text=SUITE_YAML,
        suite_path=tmp_path / "s.yaml",
        dataset=dataset,
        repo=repo,
        provider_overrides={"m1": provider},
    )
    assert outcome.exit_code == 1
    assert outcome.pass_count == 1
    assert outcome.fail_count == 1


@pytest.mark.unit
def test_runner_records_provider_error_as_exit_two(repo: Repo, tmp_path: Path) -> None:
    suite = _suite()
    dataset = _dataset([_item("c1", content="hi", expected="hi")])

    class ExplodingProvider:
        name = "boom"

        def complete(self, request, *, timeout_s):  # type: ignore[no-untyped-def]
            from evalkit.errors import TransientProviderError

            raise TransientProviderError("upstream gone")

    outcome = run_suite(
        suite=suite,
        suite_yaml_text=SUITE_YAML,
        suite_path=tmp_path / "s.yaml",
        dataset=dataset,
        repo=repo,
        provider_overrides={"m1": ExplodingProvider()},
    )
    assert outcome.exit_code == 2
    assert outcome.error_count == 1

    cases = repo.get_cases(outcome.run_id)
    assert cases[0].status == "error"
    assert cases[0].error_code == "provider.transient"
