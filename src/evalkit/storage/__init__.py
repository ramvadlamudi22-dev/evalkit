"""SQLite-backed storage for runs, cases, and evaluations.

Public surface used by the rest of the package:
    `engine_for(db_path)` and `session_factory_for(engine)` to obtain a session.
    `Repo` for high-level reads/writes used by the runner and CLI.

The schema is defined in `evalkit.storage.models` and matches
docs/architecture/05_DATABASE_SCHEMA.md. Migrations live under `migrations/`.
"""

from evalkit.storage.db import (
    DEFAULT_DB_PATH,
    db_path_from_env,
    engine_for,
    ensure_schema,
    session_factory_for,
)
from evalkit.storage.repo import Repo

__all__ = [
    "DEFAULT_DB_PATH",
    "Repo",
    "db_path_from_env",
    "engine_for",
    "ensure_schema",
    "session_factory_for",
]
