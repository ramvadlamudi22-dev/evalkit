# Changelog

All notable changes to EvalKit are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Phase 1 core: Pydantic v2 domain models (`Suite`, `Dataset`, `DatasetItem`, `RunRecord`,
  `EvaluationRecord`, etc.), `Provider`/`Evaluator` protocols, ULID identifiers, and an
  EvalKit exception hierarchy with stable error codes.
- Phase 1 storage: SQLite via SQLAlchemy 2.x with WAL mode, an Alembic migration that
  establishes the entire v1 schema in one step, and a `Repo` facade that keeps SQLAlchemy
  types out of the rest of the package.
- Phase 1 providers: deterministic `MockProvider` driven by an inline mapping or a JSONL
  fixture; small built-in registry behind `evalkit.providers.get_provider`.
- Phase 1 evaluators: `exact_match` and `contains`, both pure-sync and versioned, registered
  via `evalkit.evaluators.get_evaluator`.
- Phase 1 runner: synchronous `run_suite()` that walks the suite x dataset x evaluators
  matrix, persists runs/cases/evaluations, and returns a `RunOutcome` carrying the CLI
  exit code (0/1/2 per the contract doc).
- Phase 1 CLI: `evalkit init [DIR]`, `evalkit run SUITE`, `evalkit list runs`, `evalkit
  show RUN_ID`. `evalkit init` ships a starter project (mock provider, two-case dataset)
  used by the integration tests.
- 49 tests across `tests/unit`, `tests/integration`, and `tests/e2e`. Coverage is 92% on
  `src/evalkit`.
- ADR-0003: Phase 1 ships a synchronous runner; concurrency lands in Phase 2 with the
  first real provider.

### Phase 0 (initial scaffold)

- Build tooling (uv, Ruff, Mypy, Pytest), pre-commit hooks, Makefile, multi-stage
  Dockerfile, GitHub Actions CI (lint + test + audit + docker + e2e-cli), repository
  hygiene files, and a Typer CLI exposing `evalkit --version` / `evalkit --help`.
- 25 design documents and a META operating manual under `docs/architecture/`.
- ADR-0001: architecture decisions are recorded as ADRs.
- ADR-0002: use `python:3.12-slim` for the runtime container in Phase 0; revisit
  distroless in Phase 6.

[Unreleased]: https://github.com/ramvadlamudi22-dev/evalkit/compare/...HEAD
