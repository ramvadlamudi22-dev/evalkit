"""Contains evaluator tests."""

from __future__ import annotations

import pytest

from evalkit.core.models import (
    CaseExpected,
    CaseInput,
    DatasetItem,
    Message,
    ProviderResponse,
)
from evalkit.evaluators.contains import ContainsEvaluator


def _item(must_contain: list[str]) -> DatasetItem:
    return DatasetItem(
        case_id="t",
        input=CaseInput(messages=[Message(role="user", content="x")]),
        expected=CaseExpected(must_contain=must_contain),
    )


def _resp(text: str) -> ProviderResponse:
    return ProviderResponse(text=text, latency_ms=1)


@pytest.mark.unit
class TestContains:
    def test_pass_when_all_present(self) -> None:
        ev = ContainsEvaluator()
        result = ev.evaluate(_item(["alpha", "beta"]), _resp("alpha and beta walk in"))
        assert result.passed is True
        assert result.score == 1.0
        assert result.details["missing"] == []

    def test_partial_match_reports_score_but_fails(self) -> None:
        ev = ContainsEvaluator()
        result = ev.evaluate(_item(["alpha", "beta"]), _resp("only alpha here"))
        assert result.passed is False
        assert result.score == 0.5
        assert result.details["missing"] == ["beta"]

    def test_no_required_substrings_passes_trivially(self) -> None:
        ev = ContainsEvaluator()
        result = ev.evaluate(_item([]), _resp(""))
        assert result.passed is True
        assert result.score == 1.0

    def test_case_insensitive(self) -> None:
        ev = ContainsEvaluator(case_insensitive=True)
        result = ev.evaluate(_item(["ALPHA"]), _resp("alpha is here"))
        assert result.passed is True
