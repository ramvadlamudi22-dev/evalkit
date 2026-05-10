# EvalKit

> A pytest-shaped LLM evaluation toolkit: declarative suites, reproducible runs, regression gates, OpenTelemetry-ready.

[![CI](https://github.com/ramvadlamudi22-dev/evalkit/actions/workflows/ci.yml/badge.svg)](https://github.com/ramvadlamudi22-dev/evalkit/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ramvadlamudi22-dev/evalkit.svg)](LICENSE)

EvalKit is a command-line tool for evaluating LLM outputs. Suites are declarative YAML; runs are reproducible and persisted to SQLite; regressions are caught against a baseline before merge.

## Status

**Phase 0 — repo skeleton.** Tooling, CI, and a `--version` command. The CLI does not yet evaluate anything; that lands in Phase 1.

The [phased roadmap](docs/architecture/21_PHASED_ROADMAP.md) shows what ships when. The full design docset lives in [`docs/architecture/`](docs/architecture/).

## Quickstart (Phase 0)

```bash
git clone https://github.com/ramvadlamudi22-dev/evalkit.git
cd evalkit
make install
make ci
evalkit --version
```

## Documentation

- [Specification](docs/architecture/01_SPEC.md)
- [Product requirements](docs/architecture/02_PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/architecture/03_SYSTEM_ARCHITECTURE.md)
- [CLI / API contract](docs/architecture/06_CLI_API_CONTRACT.md)
- [Phased roadmap](docs/architecture/21_PHASED_ROADMAP.md)
- [All design docs](docs/architecture/00_INDEX.md)

## License

[Apache-2.0](LICENSE).
