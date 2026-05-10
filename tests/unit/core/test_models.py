"""Domain-model validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from evalkit.core.models import DatasetItem, Suite


@pytest.mark.unit
class TestSuite:
    def test_minimal_valid_suite(self) -> None:
        suite = Suite.model_validate(
            {
                "version": 1,
                "name": "ok",
                "dataset": "datasets/d.jsonl",
                "models": [{"id": "m1", "provider": "mock"}],
                "evaluators": [{"name": "exact_match"}],
            }
        )
        assert suite.name == "ok"
        assert suite.run.concurrency == 1  # default

    def test_rejects_unknown_top_level_key(self) -> None:
        with pytest.raises(ValidationError):
            Suite.model_validate(
                {
                    "version": 1,
                    "name": "ok",
                    "dataset": "d.jsonl",
                    "models": [{"id": "m", "provider": "mock"}],
                    "evaluators": [{"name": "exact_match"}],
                    "extra_field": True,
                }
            )

    def test_rejects_empty_models(self) -> None:
        with pytest.raises(ValidationError):
            Suite.model_validate(
                {
                    "version": 1,
                    "name": "ok",
                    "dataset": "d.jsonl",
                    "models": [],
                    "evaluators": [{"name": "exact_match"}],
                }
            )

    def test_rejects_empty_evaluators(self) -> None:
        with pytest.raises(ValidationError):
            Suite.model_validate(
                {
                    "version": 1,
                    "name": "ok",
                    "dataset": "d.jsonl",
                    "models": [{"id": "m", "provider": "mock"}],
                    "evaluators": [],
                }
            )

    def test_rejects_wrong_version(self) -> None:
        with pytest.raises(ValidationError):
            Suite.model_validate(
                {
                    "version": 2,
                    "name": "ok",
                    "dataset": "d.jsonl",
                    "models": [{"id": "m", "provider": "mock"}],
                    "evaluators": [{"name": "exact_match"}],
                }
            )


@pytest.mark.unit
class TestDatasetItem:
    def test_valid_item(self) -> None:
        item = DatasetItem.model_validate(
            {
                "case_id": "c1",
                "input": {
                    "messages": [{"role": "user", "content": "hi"}],
                },
                "expected": {"text": "hi", "must_contain": ["hi"]},
            }
        )
        assert item.case_id == "c1"
        assert item.expected.text == "hi"
        assert item.tags == []  # default

    def test_rejects_missing_case_id(self) -> None:
        with pytest.raises(ValidationError):
            DatasetItem.model_validate(
                {
                    "input": {"messages": [{"role": "user", "content": "hi"}]},
                    "expected": {},
                }
            )

    def test_rejects_unknown_role(self) -> None:
        with pytest.raises(ValidationError):
            DatasetItem.model_validate(
                {
                    "case_id": "c",
                    "input": {"messages": [{"role": "junk", "content": "hi"}]},
                    "expected": {},
                }
            )
