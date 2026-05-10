"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from evalkit.storage import engine_for, ensure_schema, session_factory_for
from evalkit.storage.repo import Repo


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Path to a fresh SQLite file inside the per-test tmp dir."""
    return tmp_path / "evalkit.db"


@pytest.fixture
def repo(tmp_db_path: Path) -> Iterator[Repo]:
    """A `Repo` bound to a freshly-migrated SQLite file."""
    engine = engine_for(tmp_db_path)
    ensure_schema(engine)
    yield Repo(session_factory_for(engine))
    engine.dispose()
