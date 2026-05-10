"""Exact-match evaluator.

Compares the provider response text to `expected.text`. Optional `strip` and
`case_insensitive` flags make the evaluator forgiving without changing the
contract: `score` is always 0 or 1 and `passed = score == 1`.
"""

from __future__ import annotations

import time

from evalkit.core.ids import new_id
from evalkit.core.models import (
    DatasetItem,
    EvaluationRecord,
    ProviderResponse,
)


class ExactMatchEvaluator:
    """Pass iff response text equals the expected text after normalization."""

    name: str = "exact_match"
    version: str = "1.0"

    def __init__(self, *, strip: bool = True, case_insensitive: bool = False) -> None:
        self._strip = strip
        self._case_insensitive = case_insensitive

    def evaluate(
        self,
        case: DatasetItem,
        response: ProviderResponse,
        *,
        evaluation_id: str | None = None,
    ) -> EvaluationRecord:
        start = time.perf_counter()
        expected = case.expected.text or ""
        actual = response.text
        a, b = self._normalize(actual), self._normalize(expected)
        passed = a == b
        score = 1.0 if passed else 0.0
        duration_ms = int((time.perf_counter() - start) * 1000)
        return EvaluationRecord(
            id=evaluation_id or new_id(),
            case_id="",  # set by the runner when persisting
            evaluator_name=self.name,
            evaluator_version=self.version,
            score=score,
            passed=passed,
            details={
                "strip": self._strip,
                "case_insensitive": self._case_insensitive,
                "expected_len": len(expected),
                "actual_len": len(actual),
            },
            duration_ms=duration_ms,
        )

    def _normalize(self, value: str) -> str:
        out = value.strip() if self._strip else value
        return out.lower() if self._case_insensitive else out
