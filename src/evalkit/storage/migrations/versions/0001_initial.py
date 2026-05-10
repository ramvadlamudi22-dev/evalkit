"""Initial schema (v1).

Establishes the entire v1 schema in a single migration as prescribed by
docs/architecture/05_DATABASE_SCHEMA.md. Phase 1 only writes to a subset of
these tables; later phases populate the rest. Schema changes after v1 ship as
new migrations and never edit this file.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "suites",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("yaml_text", sa.Text(), nullable=False),
        sa.Column("yaml_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("yaml_sha256", name="uq_suites_yaml_sha256"),
    )
    op.create_index("ix_suites_yaml_sha256", "suites", ["yaml_sha256"], unique=True)

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("sha256", name="uq_datasets_sha256"),
    )
    op.create_index("ix_datasets_sha256", "datasets", ["sha256"], unique=True)

    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("suite_id", sa.String(length=26), nullable=False),
        sa.Column("dataset_id", sa.String(length=26), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("evalkit_version", sa.String(length=64), nullable=False),
        sa.Column("python_version", sa.String(length=32), nullable=False),
        sa.Column("host_os", sa.String(length=64), nullable=False),
        sa.Column("git_sha", sa.String(length=64), nullable=True),
        sa.Column("ci_provider", sa.String(length=32), nullable=True),
        sa.Column("baseline_run_id", sa.String(length=26), nullable=True),
        sa.ForeignKeyConstraint(["suite_id"], ["suites.id"]),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.ForeignKeyConstraint(["baseline_run_id"], ["runs.id"]),
    )
    op.create_index("ix_runs_started_at", "runs", ["started_at"])
    op.create_index("ix_runs_status", "runs", ["status"])

    op.create_table(
        "cases",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("run_id", sa.String(length=26), nullable=False),
        sa.Column("case_index", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("model_id", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("output_json", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_prompt", sa.Integer(), nullable=True),
        sa.Column("tokens_completion", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_kind", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
    )
    op.create_index("ix_cases_run_id", "cases", ["run_id"])
    op.create_index("ix_cases_status", "cases", ["status"])

    op.create_table(
        "case_blobs",
        sa.Column("case_id", sa.String(length=26), primary_key=True),
        sa.Column("gz", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
    )

    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("case_id", sa.String(length=26), nullable=False),
        sa.Column("evaluator_name", sa.String(length=64), nullable=False),
        sa.Column("evaluator_version", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
    )
    op.create_index("ix_evaluations_case_id", "evaluations", ["case_id"])
    op.create_index("ix_evaluations_evaluator_name", "evaluations", ["evaluator_name"])

    op.create_table(
        "baselines",
        sa.Column("label", sa.String(length=64), primary_key=True),
        sa.Column("run_id", sa.String(length=26), nullable=False),
        sa.Column("set_at", sa.DateTime(), nullable=False),
        sa.Column("set_by", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
    )

    op.create_table(
        "cache",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("response_gz", sa.LargeBinary(), nullable=False),
        sa.Column("usage_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cache")
    op.drop_table("baselines")
    op.drop_index("ix_evaluations_evaluator_name", table_name="evaluations")
    op.drop_index("ix_evaluations_case_id", table_name="evaluations")
    op.drop_table("evaluations")
    op.drop_table("case_blobs")
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_index("ix_cases_run_id", table_name="cases")
    op.drop_table("cases")
    op.drop_index("ix_runs_status", table_name="runs")
    op.drop_index("ix_runs_started_at", table_name="runs")
    op.drop_table("runs")
    op.drop_index("ix_datasets_sha256", table_name="datasets")
    op.drop_table("datasets")
    op.drop_index("ix_suites_yaml_sha256", table_name="suites")
    op.drop_table("suites")
