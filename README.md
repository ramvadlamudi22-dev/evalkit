# EvalKit

> A pytest-shaped LLM evaluation toolkit: declarative suites, reproducible runs, regression gates, OpenTelemetry-ready.

[![CI](https://github.com/ramvadlamudi22-dev/evalkit/actions/workflows/ci.yml/badge.svg)](https://github.com/ramvadlamudi22-dev/evalkit/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ramvadlamudi22-dev/evalkit.svg)](LICENSE)

EvalKit is a command-line tool for evaluating LLM outputs. Suites are declarative YAML; runs are reproducible and persisted to SQLite; regressions are caught against a baseline before merge.

## Status

**Phase 2 — real provider via LiteLLM, async runner, retry/timeout, regression comparison.** Suites can target any LiteLLM-supported model (OpenAI, Anthropic, Ollama, vLLM, ...). Runs are concurrent, retries on transients are bounded and jittered, and `evalkit compare` gates a candidate run against a baseline.

The [phased roadmap](docs/architecture/21_PHASED_ROADMAP.md) shows what lands when. Phase 3 adds more evaluators (regex, JSON schema, llm-judge) and report rendering. The full design docset lives in [`docs/architecture/`](docs/architecture/).

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

### Regression comparison

```bash
# tag a known-good run as the baseline
uv run evalkit baseline set <RUN_ID> --name release-1.0 --db demo/evalkit.db

# later, compare a candidate against the baseline (or any two run IDs)
uv run evalkit compare <BASELINE_RUN_ID> <CANDIDATE_RUN_ID> \
    --threshold 0.0 --db demo/evalkit.db
```

`evalkit compare` exits **1** if the candidate's pass-rate drop exceeds `--threshold`, **0** otherwise. Suitable for `if evalkit compare ...; then ...` in CI.

### Real providers (LiteLLM)

```yaml
# suite.yaml
version: 1
name: my-eval
dataset: data.jsonl
models:
  - id: gpt-4o-mini
    provider: litellm
    config:
      model: openai/gpt-4o-mini
      timeout_s: 30
evaluators:
  - name: exact_match
run:
  concurrency: 4
```

Set the relevant API key in the environment (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`); LiteLLM picks the right credential per model. Retries on rate-limit/transient/timeout are bounded (3 attempts, exponential backoff with full jitter); auth and bad-request errors fail fast. See [ADR-0004](docs/adr/0004-litellm-as-provider-seam.md) and [ADR-0005](docs/adr/0005-retry-policy.md) for the rationale.

## Documentation

- [Specification](docs/architecture/01_SPEC.md)
- [Product requirements](docs/architecture/02_PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/architecture/03_SYSTEM_ARCHITECTURE.md)
- [CLI / API contract](docs/architecture/06_CLI_API_CONTRACT.md)
- [Phased roadmap](docs/architecture/21_PHASED_ROADMAP.md)
- [All design docs](docs/architecture/00_INDEX.md)

## License

[Apache-2.0](LICENSE).
