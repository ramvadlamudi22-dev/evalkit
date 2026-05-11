"""Structured logging configuration.

EvalKit's logs are structured by default. Two formats are supported, selected
by ``EVALKIT_LOG_FORMAT``:

* ``json`` (default) - one JSON object per line, machine-readable, suitable for
  CI logs, Docker stdout, and downstream log shipping.
* ``text`` - human-friendly key=value rendering for interactive shells.

Levels follow ``EVALKIT_LOG_LEVEL`` (default ``info``). We never call
``basicConfig`` from import paths; ``configure_logging`` is invoked exactly
once at process entry (CLI ``main``, tests via fixture) so libraries that
``import evalkit`` at module scope don't get our root-logger settings.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog

_CONFIGURED = False


def configure_logging(
    *,
    level: str | None = None,
    fmt: str | None = None,
) -> None:
    """Configure structlog + stdlib logging once per process.

    Subsequent calls are no-ops; tests reset state via :func:`reset_for_tests`.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    chosen_level = (level or os.environ.get("EVALKIT_LOG_LEVEL") or "info").upper()
    chosen_fmt = (fmt or os.environ.get("EVALKIT_LOG_FORMAT") or "json").lower()
    if chosen_fmt not in {"json", "text"}:
        chosen_fmt = "json"

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    final_processor: structlog.types.Processor
    if chosen_fmt == "json":
        final_processor = structlog.processors.JSONRenderer(sort_keys=True)
    else:
        final_processor = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=[*shared_processors, final_processor],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, chosen_level)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def reset_for_tests() -> None:
    """Clear cached state so a test can reconfigure logging."""
    global _CONFIGURED
    _CONFIGURED = False
    structlog.reset_defaults()


def get_logger(name: str | None = None, /, **bound: Any) -> structlog.stdlib.BoundLogger:
    """Return a logger bound to ``name`` and any extra context."""
    if not _CONFIGURED:
        configure_logging()
    base = structlog.get_logger(name) if name else structlog.get_logger()
    if bound:
        base = base.bind(**bound)
    return base  # type: ignore[no-any-return]
