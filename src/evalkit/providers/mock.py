"""Deterministic mock provider.

The mock returns a canned response for each request, looked up by `case_id`
plus `model_id`. Two strategies are supported:

1. **Fixture file** — `responses_path` points at a JSONL file with rows shaped
   as `{"case_id": ..., "model_id": ..., "response": ...}`. The same fixture
   that drives tests can drive the example invocation users run from the
   README, avoiding two sources of truth.
2. **Inline mapping** — `responses` is a `{(case_id, model_id): response}`
   dict, useful for unit tests that don't want a temp file.

If a request has no matching fixture, the mock returns the request's last user
message verbatim — handy for sanity-checking the runner without any fixtures.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from evalkit.core.models import ProviderRequest, ProviderResponse, ProviderUsage


class MockProvider:
    """Deterministic provider used in tests and examples."""

    name: str = "mock"

    def __init__(
        self,
        *,
        responses: dict[tuple[str, str], str] | None = None,
        responses_path: Path | str | None = None,
        latency_ms: int = 1,
    ) -> None:
        self._responses: dict[tuple[str, str], str] = dict(responses or {})
        if responses_path is not None:
            self._load_fixture(Path(responses_path))
        self._latency_ms = latency_ms

    async def complete(self, request: ProviderRequest, *, timeout_s: float) -> ProviderResponse:
        # Dispatch keyed by (case_id, model_id). The runner sets
        # `params["_case_id"]` so the mock can route requests deterministically;
        # the underscore prefix marks the field as runner-internal.
        case_id = str(request.params.get("_case_id", ""))
        key = (case_id, request.model_id)
        if key in self._responses:
            text = self._responses[key]
        else:
            # Fall back to echoing the last user message; this is what makes the
            # mock "just work" without fixtures.
            text = _last_user_message(request)
        await asyncio.sleep(self._latency_ms / 1000.0)
        return ProviderResponse(
            text=text,
            raw={"mock": True},
            usage=ProviderUsage(),
            latency_ms=self._latency_ms,
        )

    def _load_fixture(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                row: dict[str, Any] = json.loads(line)
                key = (str(row["case_id"]), str(row["model_id"]))
                if not isinstance(row["response"], str):
                    raise ValueError(f"{path}:{line_no}: 'response' must be a string")
                self._responses[key] = row["response"]


def _last_user_message(request: ProviderRequest) -> str:
    for msg in reversed(request.messages):
        if msg.role == "user":
            return msg.content
    return ""
