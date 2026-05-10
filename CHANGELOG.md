# Changelog

All notable changes to EvalKit are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Phase 0 repo skeleton: build tooling (uv, Ruff, Mypy, Pytest), pre-commit hooks, Makefile,
  multi-stage Dockerfile, GitHub Actions CI (lint + test + audit + docker + e2e-cli),
  repository hygiene files, and a Typer CLI exposing `evalkit --version` and `evalkit --help`.
- 25 design documents and a META operating manual under `docs/architecture/`.
- ADR-0001: Architecture decisions are recorded as ADRs.
- ADR-0002: Use `python:3.12-slim` for the runtime container in Phase 0; revisit distroless
  in Phase 6.

### Notes

This is a pre-1.0 build. The CLI does not yet evaluate anything; that lands in Phase 1.

[Unreleased]: https://github.com/ramvadlamudi22-dev/evalkit/compare/...HEAD
