"""Provider and Evaluator protocols.

The protocols are deliberately small. Phase 1 introduced sync versions;
Phase 2 promotes :class:`Provider.complete` to async so concurrent runs and
real providers (LiteLLM et al.) can yield while waiting on the network.

Evaluators stay sync: Phase 1-3 evaluators are pure CPU. If/when we add
``llm_judge`` we'll either run it in a thread or expose an async surface.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from evalkit.core.models import (
    DatasetItem,
    EvaluationRecord,
    ProviderRequest,
    ProviderResponse,
)


@runtime_checkable
class Provider(Protocol):
    """Anything that can complete a `ProviderRequest`."""

    name: str

    async def complete(
        self, request: ProviderRequest, *, timeout_s: float
    ) -> ProviderResponse: ...


@runtime_checkable
class Evaluator(Protocol):
    """Anything that can score a (case, response) pair.

    Phase 1 evaluators are pure-sync; later evaluators (e.g. `llm_judge`) wrap
    an async call internally but expose the same sync surface.
    """

    name: str
    version: str

    def evaluate(
        self,
        case: DatasetItem,
        response: ProviderResponse,
        *,
        evaluation_id: str,
    ) -> EvaluationRecord: ...
