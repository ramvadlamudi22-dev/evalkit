"""High-level data access used by the runner and CLI.

`Repo` is the *only* storage entry point the rest of the package uses; SQLAlchemy
types do not leak above this layer. Methods accept and return the domain
records from `evalkit.core.models`.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from evalkit import __version__ as evalkit_version
from evalkit.core.ids import new_id
from evalkit.core.models import (
    CaseRecord,
    DatasetItem,
    EvaluationRecord,
    RunRecord,
    Suite,
)
from evalkit.errors import StorageError
from evalkit.storage.db import session_scope
from evalkit.storage.models import (
    Case as CaseRow,
)
from evalkit.storage.models import (
    Dataset as DatasetRow,
)
from evalkit.storage.models import (
    Evaluation as EvaluationRow,
)
from evalkit.storage.models import (
    Run as RunRow,
)
from evalkit.storage.models import (
    Suite as SuiteRow,
)


class Repo:
    """High-level read/write API for runs, cases, and evaluations."""

    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    # ----- snapshot persistence ----------------------------------------

    def upsert_suite(self, suite: Suite, *, yaml_text: str) -> str:
        """Insert a suite snapshot if its yaml_sha256 is new; return its id."""
        sha = hashlib.sha256(yaml_text.encode("utf-8")).hexdigest()
        with session_scope(self._factory) as session:
            existing = session.scalar(select(SuiteRow).where(SuiteRow.yaml_sha256 == sha))
            if existing is not None:
                return existing.id
            suite_id = new_id()
            session.add(
                SuiteRow(
                    id=suite_id,
                    name=suite.name,
                    version=suite.version,
                    yaml_text=yaml_text,
                    yaml_sha256=sha,
                    created_at=datetime.now(tz=UTC),
                )
            )
            return suite_id

    def upsert_dataset(self, *, path: str, sha256: str, row_count: int) -> str:
        """Insert a dataset snapshot if its sha256 is new; return its id."""
        with session_scope(self._factory) as session:
            existing = session.scalar(select(DatasetRow).where(DatasetRow.sha256 == sha256))
            if existing is not None:
                return existing.id
            dataset_id = new_id()
            session.add(
                DatasetRow(
                    id=dataset_id,
                    path=path,
                    sha256=sha256,
                    row_count=row_count,
                    created_at=datetime.now(tz=UTC),
                )
            )
            return dataset_id

    # ----- run lifecycle ------------------------------------------------

    def start_run(self, *, suite_id: str, dataset_id: str) -> str:
        """Insert a `running` row and return its id."""
        run_id = new_id()
        with session_scope(self._factory) as session:
            session.add(
                RunRow(
                    id=run_id,
                    suite_id=suite_id,
                    dataset_id=dataset_id,
                    started_at=datetime.now(tz=UTC),
                    finished_at=None,
                    status="running",
                    exit_code=None,
                    evalkit_version=evalkit_version,
                    python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
                    host_os=platform.system(),
                )
            )
        return run_id

    def finish_run(self, run_id: str, *, status: str, exit_code: int) -> None:
        with session_scope(self._factory) as session:
            row = session.get(RunRow, run_id)
            if row is None:
                raise StorageError(f"run {run_id} not found")
            row.status = status
            row.exit_code = exit_code
            row.finished_at = datetime.now(tz=UTC)

    def record_case(
        self,
        run_id: str,
        *,
        item: DatasetItem,
        case_index: int,
        model_id: str,
        provider: str,
        output_text: str | None,
        latency_ms: int | None,
        status: str,
        error_kind: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> str:
        """Insert a case row and return its id."""
        case_pk = new_id()
        input_json = json.dumps(
            {
                "messages": [m.model_dump() for m in item.input.messages],
            },
            ensure_ascii=False,
        )
        with session_scope(self._factory) as session:
            session.add(
                CaseRow(
                    id=case_pk,
                    run_id=run_id,
                    case_index=case_index,
                    case_id=item.case_id,
                    model_id=model_id,
                    provider=provider,
                    input_json=input_json,
                    output_text=output_text,
                    latency_ms=latency_ms,
                    status=status,
                    error_kind=error_kind,
                    error_code=error_code,
                    error_message=error_message,
                    attempts=1,
                )
            )
        return case_pk

    def record_evaluation(self, evaluation: EvaluationRecord) -> None:
        with session_scope(self._factory) as session:
            session.add(
                EvaluationRow(
                    id=evaluation.id,
                    case_id=evaluation.case_id,
                    evaluator_name=evaluation.evaluator_name,
                    evaluator_version=evaluation.evaluator_version,
                    score=evaluation.score,
                    passed=evaluation.passed,
                    details_json=json.dumps(evaluation.details, ensure_ascii=False)
                    if evaluation.details
                    else None,
                    duration_ms=evaluation.duration_ms,
                )
            )

    # ----- reads --------------------------------------------------------

    def list_runs(self, *, limit: int = 20) -> list[RunRecord]:
        with session_scope(self._factory) as session:
            stmt = select(RunRow).order_by(desc(RunRow.started_at)).limit(limit)
            rows: Sequence[RunRow] = session.scalars(stmt).all()
            return [self._project_run(session, row) for row in rows]

    def get_run(self, run_id: str) -> RunRecord | None:
        with session_scope(self._factory) as session:
            row = session.get(RunRow, run_id)
            if row is None:
                return None
            return self._project_run(session, row)

    def get_cases(self, run_id: str) -> list[CaseRecord]:
        with session_scope(self._factory) as session:
            stmt = select(CaseRow).where(CaseRow.run_id == run_id).order_by(CaseRow.case_index)
            rows: Sequence[CaseRow] = session.scalars(stmt).all()
            return [
                CaseRecord(
                    id=row.id,
                    run_id=row.run_id,
                    case_index=row.case_index,
                    case_id=row.case_id,
                    model_id=row.model_id,
                    provider=row.provider,
                    input_json=row.input_json,
                    output_text=row.output_text,
                    latency_ms=row.latency_ms,
                    status=row.status,  # type: ignore[arg-type]
                    error_kind=row.error_kind,
                    error_code=row.error_code,
                    error_message=row.error_message,
                )
                for row in rows
            ]

    def get_evaluations(self, run_id: str) -> list[EvaluationRecord]:
        with session_scope(self._factory) as session:
            stmt = (
                select(EvaluationRow)
                .join(CaseRow, CaseRow.id == EvaluationRow.case_id)
                .where(CaseRow.run_id == run_id)
                .order_by(CaseRow.case_index, EvaluationRow.evaluator_name)
            )
            rows: Sequence[EvaluationRow] = session.scalars(stmt).all()
            return [
                EvaluationRecord(
                    id=row.id,
                    case_id=row.case_id,
                    evaluator_name=row.evaluator_name,
                    evaluator_version=row.evaluator_version,
                    score=row.score,
                    passed=row.passed,
                    details=json.loads(row.details_json) if row.details_json else {},
                    duration_ms=row.duration_ms,
                )
                for row in rows
            ]

    # ----- internal -----------------------------------------------------

    @staticmethod
    def _project_run(session: Session, row: RunRow) -> RunRecord:
        suite = session.get(SuiteRow, row.suite_id)
        dataset = session.get(DatasetRow, row.dataset_id)
        cases: Sequence[CaseRow] = session.scalars(
            select(CaseRow).where(CaseRow.run_id == row.id)
        ).all()
        case_count = len(cases)

        # A case "passes" if all its evaluations pass; "fails" if any evaluation
        # fails; "errors" if the case itself errored.
        pass_count = 0
        fail_count = 0
        error_count = sum(1 for c in cases if c.status != "ok")
        for case in cases:
            if case.status != "ok":
                continue
            evals: Sequence[EvaluationRow] = session.scalars(
                select(EvaluationRow).where(EvaluationRow.case_id == case.id)
            ).all()
            if evals and all(e.passed for e in evals):
                pass_count += 1
            else:
                fail_count += 1

        return RunRecord(
            id=row.id,
            suite_name=suite.name if suite is not None else "(unknown)",
            dataset_path=dataset.path if dataset is not None else "(unknown)",
            started_at=_aware(row.started_at),
            finished_at=_aware(row.finished_at) if row.finished_at is not None else None,
            status=row.status,  # type: ignore[arg-type]
            exit_code=row.exit_code,
            case_count=case_count,
            pass_count=pass_count,
            fail_count=fail_count,
            error_count=error_count,
        )


def _aware(dt: datetime) -> datetime:
    """SQLite stores naive datetimes; tag them as UTC on the way out."""
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def hash_file(path: Path) -> str:
    """Streaming sha256 of `path`. Used to fingerprint datasets."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
