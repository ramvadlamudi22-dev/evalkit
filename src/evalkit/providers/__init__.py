"""Provider implementations and lookup.

Phase 1 ships a single provider, the deterministic `MockProvider`. A full
provider registry with entry-point discovery lands in Phase 2 alongside the
real-provider adapter. For Phase 1 we expose only what the runner needs:
construction by name with a small built-in mapping.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from evalkit.core.protocols import Provider
from evalkit.errors import ConfigError
from evalkit.providers.mock import MockProvider

_BUILTIN: dict[str, Callable[..., Provider]] = {
    "mock": MockProvider,
}


def get_provider(name: str, **kwargs: Any) -> Provider:
    """Construct a provider by name. Raises `ConfigError` for unknown names."""
    factory = _BUILTIN.get(name)
    if factory is None:
        raise ConfigError(f"unknown provider: {name!r}")
    return factory(**kwargs)


__all__ = ["MockProvider", "get_provider"]
