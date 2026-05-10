"""Mock provider tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalkit.core.models import Message, ProviderRequest
from evalkit.providers.mock import MockProvider


def _request(model_id: str, *, content: str, case_id: str = "") -> ProviderRequest:
    return ProviderRequest(
        model_id=model_id,
        messages=[Message(role="user", content=content)],
        params={"_case_id": case_id} if case_id else {},
    )


@pytest.mark.unit
class TestMockProvider:
    def test_inline_mapping_dispatches_by_case_and_model(self) -> None:
        provider = MockProvider(
            responses={("c1", "m1"): "RESPONSE-A", ("c1", "m2"): "RESPONSE-B"},
            latency_ms=0,
        )
        a = provider.complete(_request("m1", content="x", case_id="c1"), timeout_s=1)
        b = provider.complete(_request("m2", content="x", case_id="c1"), timeout_s=1)
        assert a.text == "RESPONSE-A"
        assert b.text == "RESPONSE-B"
        assert a.raw == {"mock": True}

    def test_falls_back_to_echoing_user_message(self) -> None:
        provider = MockProvider(latency_ms=0)
        response = provider.complete(_request("any", content="ping"), timeout_s=1)
        assert response.text == "ping"

    def test_loads_fixture_jsonl(self, tmp_path: Path) -> None:
        fixture = tmp_path / "fx.jsonl"
        fixture.write_text(
            '{"case_id":"x","model_id":"y","response":"FROM-FILE"}\n',
            encoding="utf-8",
        )
        provider = MockProvider(responses_path=fixture, latency_ms=0)
        response = provider.complete(_request("y", content="ignored", case_id="x"), timeout_s=1)
        assert response.text == "FROM-FILE"

    def test_rejects_non_string_response_in_fixture(self, tmp_path: Path) -> None:
        fixture = tmp_path / "bad.jsonl"
        fixture.write_text(
            '{"case_id":"x","model_id":"y","response":42}\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="must be a string"):
            MockProvider(responses_path=fixture)
