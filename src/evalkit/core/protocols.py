"""Provider and Evaluator protocols.

The protocols are deliberately small. Phase 1 implementations (mock provider,
exact_match / contains evaluators) satisfy them trivially.

We use synchronous interfaces for now. The planning doc anticipates async
providers, but Phase 1 only ships a deterministic mock that has no I/O, so
forcing async would be premature complexity. Phase 2 (real providers) is the
right time to introduce async at this seam.
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

    def complete(self, request: ProviderRequest, *, timeout_s: float) -> ProviderResponse: ...


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
