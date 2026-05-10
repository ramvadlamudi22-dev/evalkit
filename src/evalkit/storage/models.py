"""SQLAlchemy mapped classes for the EvalKit SQLite schema.

These classes mirror the tables in docs/architecture/05_DATABASE_SCHEMA.md and
are the single source of truth for schema *shape*. Migrations under
`evalkit.storage.migrations` are generated from these definitions.

Phase 1 only writes to a subset of these (suites, datasets, runs, cases,
evaluations); the rest are present so the v1 schema is established in a single
initial migration as the planning doc prescribes.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BLOB,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all storage models."""


class Suite(Base):
    __tablename__ = "suites"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    yaml_text: Mapped[str] = mapped_column(Text, nullable=False)
    yaml_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    suite_id: Mapped[str] = mapped_column(String(26), ForeignKey("suites.id"), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(26), ForeignKey("datasets.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evalkit_version: Mapped[str] = mapped_column(String(64), nullable=False)
    python_version: Mapped[str] = mapped_column(String(32), nullable=False)
    host_os: Mapped[str] = mapped_column(String(64), nullable=False)
    git_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ci_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    baseline_run_id: Mapped[str | None] = mapped_column(
        String(26), ForeignKey("runs.id"), nullable=True
    )


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("runs.id"), nullable=False, index=True
    )
    case_index: Mapped[int] = mapped_column(Integer, nullable=False)
    case_id: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_prompt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_completion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    error_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CaseBlob(Base):
    __tablename__ = "case_blobs"

    case_id: Mapped[str] = mapped_column(String(26), ForeignKey("cases.id"), primary_key=True)
    gz: Mapped[bytes] = mapped_column(BLOB, nullable=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("cases.id"), nullable=False, index=True
    )
    evaluator_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    evaluator_version: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Baseline(Base):
    __tablename__ = "baselines"

    label: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(26), ForeignKey("runs.id"), nullable=False)
    set_at: Mapped[datetime] = mapped_column(nullable=False)
    set_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class CacheEntry(Base):
    __tablename__ = "cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    response_gz: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    usage_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
