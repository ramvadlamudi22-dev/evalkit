"""Evaluator implementations and lookup.

Phase 1 ships two deterministic evaluators (`exact_match`, `contains`); the
remaining built-ins from doc 07 land in Phase 3. Like providers, the registry
is intentionally a small built-in map for Phase 1; entry-point-based discovery
arrives with Phase 3.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from evalkit.core.protocols import Evaluator
from evalkit.errors import ConfigError
from evalkit.evaluators.contains import ContainsEvaluator
from evalkit.evaluators.exact_match import ExactMatchEvaluator

_BUILTIN: dict[str, Callable[..., Evaluator]] = {
    "exact_match": ExactMatchEvaluator,
    "contains": ContainsEvaluator,
}


def get_evaluator(name: str, **kwargs: Any) -> Evaluator:
    """Construct an evaluator by name. Raises `ConfigError` for unknown names."""
    factory = _BUILTIN.get(name)
    if factory is None:
        raise ConfigError(f"unknown evaluator: {name!r}")
    return factory(**kwargs)


__all__ = ["ContainsEvaluator", "ExactMatchEvaluator", "get_evaluator"]
