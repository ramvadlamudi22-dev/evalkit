"""Contains evaluator.

Checks that the response text contains every string in `expected.must_contain`.
The score is `matched / total`; the case passes only when every required
substring is present (`passed == score == 1`).
"""

from __future__ import annotations

import time

from evalkit.core.ids import new_id
from evalkit.core.models import (
    DatasetItem,
    EvaluationRecord,
    ProviderResponse,
)


class ContainsEvaluator:
    """Substring-containment evaluator."""

    name: str = "contains"
    version: str = "1.0"

    def __init__(self, *, case_insensitive: bool = False) -> None:
        self._case_insensitive = case_insensitive

    def evaluate(
        self,
        case: DatasetItem,
        response: ProviderResponse,
        *,
        evaluation_id: str | None = None,
    ) -> EvaluationRecord:
        start = time.perf_counter()
        required = case.expected.must_contain
        haystack = response.text.lower() if self._case_insensitive else response.text
        matches = [
            (needle.lower() if self._case_insensitive else needle) in haystack
            for needle in required
        ]
        total = len(required)
        matched = sum(matches)
        if total == 0:
            score = 1.0
            passed = True
        else:
            score = matched / total
            passed = matched == total
        duration_ms = int((time.perf_counter() - start) * 1000)
        return EvaluationRecord(
            id=evaluation_id or new_id(),
            case_id="",
            evaluator_name=self.name,
            evaluator_version=self.version,
            score=score,
            passed=passed,
            details={
                "case_insensitive": self._case_insensitive,
                "matched": matched,
                "total": total,
                "missing": [required[i] for i, ok in enumerate(matches) if not ok],
            },
            duration_ms=duration_ms,
        )
