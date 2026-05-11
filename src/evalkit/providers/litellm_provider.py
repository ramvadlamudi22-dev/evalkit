"""LiteLLM-backed provider adapter.

Wraps ``litellm.acompletion`` so any model LiteLLM speaks (OpenAI, Anthropic,
Ollama, Bedrock, OpenAI-compatible local servers, ...) is reachable from
EvalKit through one adapter and one error taxonomy. The design choice is
recorded in ADR-0004.

Three responsibilities live here:

1. **Translation.** Map :class:`ProviderRequest` to LiteLLM's call shape and
   the response back into :class:`ProviderResponse` (text + usage + raw).
2. **Timeout enforcement.** Every call is wrapped in :func:`asyncio.wait_for`
   using the per-call deadline from the suite. A wall-clock timeout becomes
   :class:`TimeoutProviderError` (transient -> retryable).
3. **Retry orchestration.** :mod:`tenacity`'s ``AsyncRetrying`` retries only
   transient failures (network, 5xx, 429, timeout) with exponential, jittered
   backoff. :class:`PermanentProviderError` subclasses (auth/config/bad
   request) propagate immediately. The policy lives in ADR-0005.

Tests use the ``acompletion`` constructor argument to inject a scripted
callable. CI never hits the network.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from litellm import exceptions as litellm_exc
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from evalkit.core.models import ProviderRequest, ProviderResponse, ProviderUsage
from evalkit.errors import (
    AuthProviderError,
    PermanentProviderError,
    ProviderConfigError,
    ProviderError,
    RateLimitProviderError,
    TimeoutProviderError,
    TransientProviderError,
)
from evalkit.logging import get_logger

AcompletionCallable = Callable[..., Awaitable[Any]]


def _default_acompletion() -> AcompletionCallable:
    # Imported lazily so the module is import-safe even if litellm decides to
    # do heavy work on import (it sometimes does).
    import litellm

    fn: AcompletionCallable = litellm.acompletion
    return fn


class LiteLLMProvider:
    """Real-provider adapter routed through LiteLLM.

    Parameters
    ----------
    max_attempts:
        Total attempts including the first call. ``1`` disables retry.
    backoff_initial_seconds / backoff_max_seconds:
        Bounds for exponential backoff with full jitter (0..wait window).
    api_base / api_key:
        Forwarded to LiteLLM. ``api_key=None`` lets LiteLLM resolve the key
        from the provider's standard environment variable (``OPENAI_API_KEY``
        etc.), which is what you almost always want.
    extra_kwargs:
        Anything LiteLLM accepts and we don't model explicitly (custom
        headers, ``api_version``, etc.).
    acompletion:
        Injection seam used by tests. Defaults to :func:`litellm.acompletion`.
    """

    name: str = "litellm"

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        backoff_initial_seconds: float = 0.5,
        backoff_max_seconds: float = 8.0,
        api_base: str | None = None,
        api_key: str | None = None,
        extra_kwargs: dict[str, Any] | None = None,
        acompletion: AcompletionCallable | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ProviderConfigError("max_attempts must be >= 1")
        self._max_attempts = max_attempts
        self._backoff_initial = backoff_initial_seconds
        self._backoff_max = backoff_max_seconds
        self._api_base = api_base
        self._api_key = api_key
        self._extra_kwargs = dict(extra_kwargs or {})
        self._acompletion = acompletion or _default_acompletion()
        self._log = get_logger("evalkit.provider.litellm", provider=self.name)

    async def complete(
        self,
        request: ProviderRequest,
        *,
        timeout_s: float,
    ) -> ProviderResponse:
        """Send a chat-completion request through LiteLLM with retry + timeout."""
        case_id = str(request.params.get("_case_id", ""))
        log = self._log.bind(model_id=request.model_id, case_id=case_id)
        # ``params`` may carry runner-internal keys (prefixed with "_"); strip
        # them so we don't forward them to the upstream provider.
        clean_params = {k: v for k, v in request.params.items() if not k.startswith("_")}
        call_kwargs: dict[str, Any] = {
            "model": request.model_id,
            "messages": [m.model_dump() for m in request.messages],
            **self._extra_kwargs,
            **clean_params,
        }
        if self._api_base is not None:
            call_kwargs["api_base"] = self._api_base
        if self._api_key is not None:
            call_kwargs["api_key"] = self._api_key

        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential_jitter(
                initial=self._backoff_initial,
                max=self._backoff_max,
            ),
            retry=retry_if_exception_type(TransientProviderError),
            reraise=True,
        )
        attempt_no = 0
        try:
            async for attempt in retryer:
                with attempt:
                    attempt_no += 1
                    started = time.perf_counter()
                    try:
                        raw = await asyncio.wait_for(
                            self._acompletion(**call_kwargs),
                            timeout=timeout_s,
                        )
                    except TimeoutError as exc:
                        latency_ms = int((time.perf_counter() - started) * 1000)
                        log.warning(
                            "provider.timeout",
                            attempt=attempt_no,
                            latency_ms=latency_ms,
                            timeout_s=timeout_s,
                        )
                        raise TimeoutProviderError(
                            f"Call exceeded {timeout_s:.1f}s deadline"
                        ) from exc
                    except Exception as exc:
                        latency_ms = int((time.perf_counter() - started) * 1000)
                        mapped = _classify_litellm_error(exc)
                        log.warning(
                            "provider.error",
                            attempt=attempt_no,
                            latency_ms=latency_ms,
                            error_code=mapped.code,
                            error_kind=type(exc).__name__,
                        )
                        raise mapped from exc
                    latency_ms = int((time.perf_counter() - started) * 1000)
                    log.info(
                        "provider.ok",
                        attempt=attempt_no,
                        latency_ms=latency_ms,
                        status="ok",
                    )
                    return _build_response(raw, latency_ms)
        except RetryError as exc:  # pragma: no cover - reraise=True bypasses this
            inner = exc.last_attempt.exception()
            if isinstance(inner, ProviderError):
                raise inner from exc
            raise

        # ``AsyncRetrying`` always yields at least once; this is unreachable.
        raise ProviderError("retry loop exited without result")  # pragma: no cover


# ---------- helpers --------------------------------------------------------


def _classify_litellm_error(exc: BaseException) -> ProviderError:
    """Translate a LiteLLM exception into our taxonomy.

    Order matters: subclasses come before parents. Anything we don't recognise
    is treated as permanent, on the principle that "don't retry what you don't
    understand" is the safer default than burning retry budget on a bug.
    """
    if isinstance(exc, litellm_exc.AuthenticationError | litellm_exc.PermissionDeniedError):
        return AuthProviderError(str(exc))
    if isinstance(exc, litellm_exc.RateLimitError):
        return RateLimitProviderError(str(exc))
    if isinstance(exc, litellm_exc.Timeout):
        return TimeoutProviderError(str(exc))
    if isinstance(
        exc,
        litellm_exc.ServiceUnavailableError
        | litellm_exc.InternalServerError
        | litellm_exc.APIConnectionError,
    ):
        return TransientProviderError(str(exc))
    if isinstance(exc, litellm_exc.ContextWindowExceededError | litellm_exc.BadRequestError):
        return PermanentProviderError(str(exc))
    if isinstance(exc, litellm_exc.NotFoundError):
        return ProviderConfigError(str(exc))
    return PermanentProviderError(str(exc))


def _build_response(raw: Any, latency_ms: int) -> ProviderResponse:
    """Pull the text + usage out of a LiteLLM ModelResponse."""
    text = _extract_text(raw)
    usage = _extract_usage(raw)
    raw_payload = _to_serialisable(raw)
    return ProviderResponse(
        text=text,
        raw=raw_payload,
        usage=usage,
        latency_ms=latency_ms,
    )


def _extract_text(raw: Any) -> str:
    """Best-effort text extraction tolerant of dict-, attr-, or mock-shaped responses."""
    choices = _get(raw, "choices") or []
    if not choices:
        return ""
    first = choices[0]
    message = _get(first, "message")
    if message is None:
        return str(_get(first, "text") or "")
    content = _get(message, "content")
    return "" if content is None else str(content)


def _extract_usage(raw: Any) -> ProviderUsage:
    usage = _get(raw, "usage")
    if usage is None:
        return ProviderUsage()
    return ProviderUsage(
        tokens_prompt=_int_or_none(_get(usage, "prompt_tokens")),
        tokens_completion=_int_or_none(_get(usage, "completion_tokens")),
    )


def _get(obj: Any, name: str) -> Any:
    """Attribute access that falls back to ``__getitem__`` for dict-shaped payloads."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_serialisable(raw: Any) -> dict[str, Any]:
    """Persist a stable, JSON-friendly summary of the raw response."""
    if isinstance(raw, dict):
        return dict(raw)
    model_dump = getattr(raw, "model_dump", None)
    if callable(model_dump):
        out = model_dump()
        if isinstance(out, dict):
            return out
    return {"repr": repr(raw)}
