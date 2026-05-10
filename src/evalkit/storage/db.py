"""Engine + session factory for the SQLite-backed store.

We use SQLAlchemy 2.x with WAL mode. WAL is set on every new connection rather
than once per database; SQLite stores the journal_mode persistently after the
first set, but doing it on each connect is harmless and tolerates fresh files.

`ensure_schema()` runs the Alembic migration chain up to head. The runner and
CLI call it before they read or write so first-run users do not have to invoke
a separate setup step.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DB_PATH = Path.home() / ".evalkit" / "evalkit.db"
"""Default SQLite location; overridable via env or `--db PATH`."""


def db_path_from_env() -> Path:
    """Resolve the DB path from `EVALKIT_DB_PATH`, falling back to the default."""
    raw = os.environ.get("EVALKIT_DB_PATH")
    return Path(raw) if raw else DEFAULT_DB_PATH


def engine_for(db_path: Path) -> Engine:
    """Create a SQLAlchemy Engine for the given SQLite file.

    Parents of `db_path` are created on demand. `:memory:` is supported
    transparently — pass `Path(":memory:")` for an in-memory engine.
    """
    if str(db_path) == ":memory:":
        url = "sqlite:///:memory:"
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{db_path}"

    engine = create_engine(url, future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def session_factory_for(engine: Engine) -> sessionmaker[Session]:
    """Return a sessionmaker bound to the given engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Yield a session, committing on success and rolling back on error."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_schema(engine: Engine) -> None:
    """Run Alembic migrations up to head against `engine`.

    Imported lazily because Alembic pulls in a substantial dependency tree we do
    not want imported on every CLI invocation.
    """
    from alembic import command
    from alembic.config import Config

    migrations_dir = Path(__file__).parent / "migrations"
    cfg = Config()
    cfg.set_main_option("script_location", str(migrations_dir))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    command.upgrade(cfg, "head")
