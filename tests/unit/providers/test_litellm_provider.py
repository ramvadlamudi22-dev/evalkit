"""LiteLLMProvider unit tests with scripted ``acompletion`` callables.

CI never hits the network. The provider accepts an ``acompletion`` arg in its
constructor; tests pass a coroutine factory that returns either a ModelResponse
look-alike or raises a specific LiteLLM exception.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from litellm import exceptions as litellm_exc

from evalkit.core.models import Message, ProviderRequest
from evalkit.errors import (
    AuthProviderError,
    PermanentProviderError,
    ProviderConfigError,
    RateLimitProviderError,
    TimeoutProviderError,
    TransientProviderError,
)
from evalkit.providers.litellm_provider import LiteLLMProvider


# ---------- helpers --------------------------------------------------------


def _request(case_id: str = "c1", *, model: str = "gpt-4o-mini") -> ProviderRequest:
    return ProviderRequest(
        model_id=model,
        messages=[Message(role="user", content="hello")],
        params={"_case_id": case_id, "temperature": 0.0},
    )


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeUsage:
    def __init__(self, prompt: int = 10, completion: int = 5) -> None:
        self.prompt_tokens = prompt
        self.completion_tokens = completion
        self.total_tokens = prompt + completion


class _FakeModelResponse:
    """Mimic the surface of litellm.ModelResponse the adapter actually reads."""

    def __init__(self, content: str = "ok") -> None:
        self.choices = [_FakeChoice(content)]
        self.usage = _FakeUsage()

    def model_dump(self) -> dict[str, Any]:
        return {
            "choices": [{"message": {"content": self.choices[0].message.content}}],
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
            },
        }


def _scripted(*responses: Any) -> Callable[..., Awaitable[Any]]:
    """Build an async callable that yields the given items in order.

    Each item is either a value to return or an Exception to raise.
    """
    seq = iter(responses)

    async def _call(**_: Any) -> Any:
        try:
            item = next(seq)
        except StopIteration as exc:
            raise AssertionError("scripted acompletion exhausted") from exc
        if isinstance(item, BaseException):
            raise item
        return item

    return _call


def _make_litellm_exc(cls: type[Exception]) -> Exception:
    """Construct a LiteLLM exception with the keyword args its __init__ wants."""
    return cls(
        message="boom",
        model="gpt-4o-mini",
        llm_provider="openai",
    )


# ---------- happy path -----------------------------------------------------


@pytest.mark.unit
class TestLiteLLMProviderHappyPath:
    async def test_returns_text_usage_and_raw_on_success(self) -> None:
        provider = LiteLLMProvider(acompletion=_scripted(_FakeModelResponse("HELLO")))
        response = await provider.complete(_request(), timeout_s=5.0)
        assert response.text == "HELLO"
        assert response.usage.tokens_prompt == 10
        assert response.usage.tokens_completion == 5
        assert "choices" in response.raw

    async def test_strips_runner_internal_params_from_call_kwargs(self) -> None:
        captured: list[dict[str, Any]] = []

        async def _capture(**kwargs: Any) -> Any:
            captured.append(kwargs)
            return _FakeModelResponse("ok")

        provider = LiteLLMProvider(acompletion=_capture)
        await provider.complete(_request(case_id="c-secret"), timeout_s=5.0)
        kwargs = captured[0]
        assert "_case_id" not in kwargs
        assert kwargs["temperature"] == 0.0
        assert kwargs["model"] == "gpt-4o-mini"


# ---------- error classification ------------------------------------------


@pytest.mark.unit
class TestLiteLLMProviderClassification:
    async def test_authentication_error_becomes_auth_provider_error(self) -> None:
        provider = LiteLLMProvider(
            acompletion=_scripted(_make_litellm_exc(litellm_exc.AuthenticationError))
        )
        with pytest.raises(AuthProviderError):
            await provider.complete(_request(), timeout_s=5.0)

    async def test_rate_limit_error_becomes_rate_limit_provider_error(self) -> None:
        provider = LiteLLMProvider(
            acompletion=_scripted(_make_litellm_exc(litellm_exc.RateLimitError)),
            max_attempts=1,
        )
        with pytest.raises(RateLimitProviderError):
            await provider.complete(_request(), timeout_s=5.0)

    async def test_bad_request_becomes_permanent(self) -> None:
        bad = litellm_exc.BadRequestError(
            message="bad", model="gpt-4o-mini", llm_provider="openai"
        )
        provider = LiteLLMProvider(acompletion=_scripted(bad))
        with pytest.raises(PermanentProviderError):
            await provider.complete(_request(), timeout_s=5.0)

    async def test_not_found_becomes_provider_config_error(self) -> None:
        nf = litellm_exc.NotFoundError(
            message="missing", model="nope", llm_provider="openai"
        )
        provider = LiteLLMProvider(acompletion=_scripted(nf))
        with pytest.raises(ProviderConfigError):
            await provider.complete(_request(), timeout_s=5.0)


# ---------- retry / timeout -----------------------------------------------


@pytest.mark.unit
class TestLiteLLMProviderRetry:
    async def test_retries_on_transient_then_succeeds(self) -> None:
        provider = LiteLLMProvider(
            acompletion=_scripted(
                _make_litellm_exc(litellm_exc.ServiceUnavailableError),
                _make_litellm_exc(litellm_exc.APIConnectionError),
                _FakeModelResponse("recovered"),
            ),
            max_attempts=3,
            backoff_initial_seconds=0.0,
            backoff_max_seconds=0.0,
        )
        response = await provider.complete(_request(), timeout_s=5.0)
        assert response.text == "recovered"

    async def test_gives_up_after_max_attempts_with_last_transient_error(self) -> None:
        provider = LiteLLMProvider(
            acompletion=_scripted(
                _make_litellm_exc(litellm_exc.ServiceUnavailableError),
                _make_litellm_exc(litellm_exc.ServiceUnavailableError),
            ),
            max_attempts=2,
            backoff_initial_seconds=0.0,
            backoff_max_seconds=0.0,
        )
        with pytest.raises(TransientProviderError):
            await provider.complete(_request(), timeout_s=5.0)

    async def test_permanent_errors_are_not_retried(self) -> None:
        call_count = 0

        async def _explode(**_: Any) -> Any:
            nonlocal call_count
            call_count += 1
            raise _make_litellm_exc(litellm_exc.AuthenticationError)

        provider = LiteLLMProvider(
            acompletion=_explode,
            max_attempts=5,
            backoff_initial_seconds=0.0,
            backoff_max_seconds=0.0,
        )
        with pytest.raises(AuthProviderError):
            await provider.complete(_request(), timeout_s=5.0)
        assert call_count == 1, "auth failures must not consume retry budget"


@pytest.mark.unit
class TestLiteLLMProviderTimeout:
    async def test_timeout_raises_timeout_provider_error(self) -> None:
        async def _hang(**_: Any) -> Any:
            await asyncio.sleep(10.0)
            return _FakeModelResponse("never")

        provider = LiteLLMProvider(
            acompletion=_hang,
            max_attempts=1,
            backoff_initial_seconds=0.0,
            backoff_max_seconds=0.0,
        )
        with pytest.raises(TimeoutProviderError):
            await provider.complete(_request(), timeout_s=0.05)
