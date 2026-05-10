"""Pydantic v2 domain models for suites, datasets, runs, and results.

These are the *core* models — what the runner and CLI manipulate. Storage-layer
SQLAlchemy classes live in `evalkit.storage.models` and are translated at the
repo boundary; we deliberately do not let SQLAlchemy types bleed into the
domain.

Phase 1 only exercises a subset of these. Fields exist for v1 features that
land in later phases when the planning doc said the schema should be stable
from day one (`docs/architecture/05_DATABASE_SCHEMA.md`); the runner simply
leaves unused fields at their defaults.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------- Suite (YAML-loaded) -------------------------------------------


class ModelSpec(BaseModel):
    """One model entry in a suite's `models:` list."""

    model_config = ConfigDict(extra="forbid")

    id: str
    provider: str
    params: dict[str, Any] = Field(default_factory=dict)


class EvaluatorSpec(BaseModel):
    """One evaluator entry in a suite's `evaluators:` list."""

    model_config = ConfigDict(extra="allow")  # evaluators carry their own config keys

    name: str


class RunConfig(BaseModel):
    """The `run:` block of a suite. Phase 1 uses very little of this."""

    model_config = ConfigDict(extra="forbid")

    concurrency: int = 1
    per_call_timeout_seconds: float = 30.0


class Suite(BaseModel):
    """Top-level suite schema (v1)."""

    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    name: str
    description: str | None = None
    dataset: str
    models: list[ModelSpec]
    evaluators: list[EvaluatorSpec]
    run: RunConfig = Field(default_factory=RunConfig)

    @field_validator("models")
    @classmethod
    def _models_nonempty(cls, v: list[ModelSpec]) -> list[ModelSpec]:
        if not v:
            raise ValueError("suite must declare at least one model")
        return v

    @field_validator("evaluators")
    @classmethod
    def _evaluators_nonempty(cls, v: list[EvaluatorSpec]) -> list[EvaluatorSpec]:
        if not v:
            raise ValueError("suite must declare at least one evaluator")
        return v


# ---------- Dataset (JSONL-loaded) ----------------------------------------


class Message(BaseModel):
    """One chat-style message: role + content."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str


class CaseInput(BaseModel):
    """Input portion of a dataset row."""

    model_config = ConfigDict(extra="forbid")

    messages: list[Message]


class CaseExpected(BaseModel):
    """Expected portion of a dataset row.

    Only fields used by Phase 1 evaluators are typed; arbitrary extra keys are
    allowed because future evaluators consume their own custom keys.
    """

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    must_contain: list[str] = Field(default_factory=list)


class DatasetItem(BaseModel):
    """One row of a dataset JSONL file."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    tags: list[str] = Field(default_factory=list)
    input: CaseInput
    expected: CaseExpected
    metadata: dict[str, Any] = Field(default_factory=dict)


class Dataset(BaseModel):
    """A loaded dataset: an ordered list of items + a content hash."""

    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str
    items: list[DatasetItem]


# ---------- Provider request/response (in-memory only) --------------------


class ProviderRequest(BaseModel):
    """What the runner asks a provider to complete."""

    model_config = ConfigDict(extra="forbid")

    model_id: str
    messages: list[Message]
    params: dict[str, Any] = Field(default_factory=dict)


class ProviderUsage(BaseModel):
    """Token / cost accounting; all fields optional for providers that don't report."""

    model_config = ConfigDict(extra="forbid")

    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    cost_usd: float | None = None


class ProviderResponse(BaseModel):
    """What a provider returns."""

    model_config = ConfigDict(extra="forbid")

    text: str
    raw: dict[str, Any] = Field(default_factory=dict)
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    latency_ms: int


# ---------- Run-time records (CLI display + storage projection) -----------


class CaseRecord(BaseModel):
    """In-memory projection of one case as the runner produces it."""

    model_config = ConfigDict(extra="forbid")

    id: str
    run_id: str
    case_index: int
    case_id: str
    model_id: str
    provider: str
    input_json: str
    output_text: str | None
    latency_ms: int | None
    status: Literal["ok", "error", "timeout", "skipped"]
    error_kind: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class EvaluationRecord(BaseModel):
    """In-memory projection of one evaluation."""

    model_config = ConfigDict(extra="forbid")

    id: str
    case_id: str
    evaluator_name: str
    evaluator_version: str
    score: float
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int


class RunRecord(BaseModel):
    """In-memory projection of one run."""

    model_config = ConfigDict(extra="forbid")

    id: str
    suite_name: str
    dataset_path: str
    started_at: datetime
    finished_at: datetime | None
    status: Literal["running", "passed", "failed", "error", "aborted"]
    exit_code: int | None
    case_count: int
    pass_count: int
    fail_count: int
    error_count: int
