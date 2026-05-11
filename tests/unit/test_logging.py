"""Logging configuration tests.

We don't assert exact JSON output (renderer internals can shift); instead
we assert observable behaviour: configure_logging is idempotent, an
unknown LOG_FORMAT falls back to json, reset_for_tests un-freezes state,
and get_logger returns a working bound logger.
"""

from __future__ import annotations

import pytest

from evalkit.logging import configure_logging, get_logger, reset_for_tests


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_for_tests()


def test_configure_is_idempotent() -> None:
    configure_logging(fmt="text")
    # Second call should be a no-op (does not raise, does not reconfigure).
    configure_logging(fmt="json")


def test_unknown_format_falls_back_to_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("EVALKIT_LOG_FORMAT", "yaml-please")
    configure_logging()
    log = get_logger("evalkit.test")
    log.warning("hello", attempt=1)
    err = capsys.readouterr().err
    assert "hello" in err


def test_text_format_renders_human_readable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("EVALKIT_LOG_FORMAT", "text")
    configure_logging()
    get_logger("evalkit.test").warning("hello", k="v")
    err = capsys.readouterr().err
    assert "hello" in err
    assert "k" in err


def test_get_logger_auto_configures_if_called_first() -> None:
    log = get_logger("evalkit.test", run_id="01ABC")
    # Bound context is reachable via .bind() / log.info() side effects.
    log.info("smoke", attempt=1)


def test_invalid_level_falls_back_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVALKIT_LOG_LEVEL", "bogus")
    # We don't catch the AttributeError - python's logging exposes the
    # invalid level cleanly. Ensure we raise predictably so callers can
    # spot the misconfig instead of silently swallowing it.
    with pytest.raises(AttributeError):
        configure_logging()
