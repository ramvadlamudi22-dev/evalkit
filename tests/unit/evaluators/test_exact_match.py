"""Exact-match evaluator tests."""

from __future__ import annotations

import pytest

from evalkit.core.models import (
    CaseExpected,
    CaseInput,
    DatasetItem,
    Message,
    ProviderResponse,
)
from evalkit.evaluators.exact_match import ExactMatchEvaluator


def _item(expected_text: str) -> DatasetItem:
    return DatasetItem(
        case_id="t",
        input=CaseInput(messages=[Message(role="user", content="x")]),
        expected=CaseExpected(text=expected_text),
    )


def _resp(text: str) -> ProviderResponse:
    return ProviderResponse(text=text, latency_ms=1)


@pytest.mark.unit
class TestExactMatch:
    def test_pass_on_identical_text(self) -> None:
        ev = ExactMatchEvaluator()
        result = ev.evaluate(_item("hello"), _resp("hello"))
        assert result.passed is True
        assert result.score == 1.0

    def test_fail_on_different_text(self) -> None:
        ev = ExactMatchEvaluator()
        result = ev.evaluate(_item("hello"), _resp("hi"))
        assert result.passed is False
        assert result.score == 0.0

    def test_strip_default_true(self) -> None:
        ev = ExactMatchEvaluator()
        result = ev.evaluate(_item("hello"), _resp("  hello  "))
        assert result.passed is True

    def test_strip_disabled(self) -> None:
        ev = ExactMatchEvaluator(strip=False)
        result = ev.evaluate(_item("hello"), _resp("  hello  "))
        assert result.passed is False

    def test_case_insensitive(self) -> None:
        ev = ExactMatchEvaluator(case_insensitive=True)
        result = ev.evaluate(_item("Hello"), _resp("HELLO"))
        assert result.passed is True

    def test_records_evaluator_metadata(self) -> None:
        ev = ExactMatchEvaluator()
        result = ev.evaluate(_item("h"), _resp("h"))
        assert result.evaluator_name == "exact_match"
        assert result.evaluator_version == "1.0"
        assert result.duration_ms >= 0
