# EvalKit

> A pytest-shaped LLM evaluation toolkit: declarative suites, reproducible runs, regression gates, OpenTelemetry-ready.

[![CI](https://github.com/ramvadlamudi22-dev/evalkit/actions/workflows/ci.yml/badge.svg)](https://github.com/ramvadlamudi22-dev/evalkit/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ramvadlamudi22-dev/evalkit.svg)](LICENSE)

EvalKit is a command-line tool for evaluating LLM outputs. Suites are declarative YAML; runs are reproducible and persisted to SQLite; regressions are caught against a baseline before merge.

## Status

**Phase 1 — core evaluation flow with a deterministic mock provider.** Runs are persisted in SQLite, the CLI returns standardized exit codes (0 / 1 / 2), and a starter project ships with the package.

The [phased roadmap](docs/architecture/21_PHASED_ROADMAP.md) shows what lands when. Phase 2 introduces the first real provider and an async runner. The full design docset lives in [`docs/architecture/`](docs/architecture/).

## Quickstart

```bash
git clone https://github.com/ramvadlamudi22-dev/evalkit.git
cd evalkit
make install              # uv sync + pre-commit install
make ci                   # ruff + mypy + pytest

# scaffold and run a suite end-to-end (mock provider; no API keys required)
uv run evalkit init demo
uv run evalkit run demo/suite.yaml --db demo/evalkit.db
uv run evalkit list runs --db demo/evalkit.db
uv run evalkit show <RUN_ID> --db demo/evalkit.db
```

`evalkit run` exits **0** when every case passes every evaluator, **1** when at least one case fails, **2** on infrastructure errors (per the [CLI contract](docs/architecture/06_CLI_API_CONTRACT.md)).

## Documentation

- [Specification](docs/architecture/01_SPEC.md)
- [Product requirements](docs/architecture/02_PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/architecture/03_SYSTEM_ARCHITECTURE.md)
- [CLI / API contract](docs/architecture/06_CLI_API_CONTRACT.md)
- [Phased roadmap](docs/architecture/21_PHASED_ROADMAP.md)
- [All design docs](docs/architecture/00_INDEX.md)

## License

[Apache-2.0](LICENSE).
