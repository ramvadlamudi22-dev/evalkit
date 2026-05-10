# 01 — SPEC.md

## What EvalKit is

A **command-line LLM evaluation toolkit** that runs locally, in Docker, and in CI. It executes a declarative *suite* (dataset × models × evaluators) and produces reproducible run records, regression diffs, and shareable reports.

It is **not** a SaaS, not a web platform, not an "AI agent". It is a serious, narrowly-scoped piece of AI infrastructure modelled on tools engineers actually use (pytest, dbt, alembic).

## Why this exists

Teams shipping LLM features need the same primitives they have for traditional software: deterministic test runs, regression detection, CI gating, shareable reports. Most existing OSS in this space is either (a) a notebook-grade harness, (b) a heavyweight platform with vendor lock-in, or (c) a thin wrapper around a single provider. EvalKit fills the gap as a pytest-shaped tool focused exclusively on evaluation discipline.

## Primary use cases

1. A developer adds an evaluator to their PR and runs `evalkit run suite.yaml --baseline main` to gate on regressions before merge.
2. A team runs nightly `evalkit run` against multiple models, stores results in SQLite, and exports a markdown report attached to a Slack message.
3. A reviewer inspects a single run with `evalkit show <run-id>` to investigate a regression.
4. An operator promotes a passing run to baseline with `evalkit baseline set <run-id>`.

## Success criteria

EvalKit is successful when:

1. A new user can `pip install evalkit`, run `evalkit init`, and get a green sample run in **under 5 minutes**.
2. CI in this repo runs the full suite (lint, types, unit, integration, e2e against a mock provider) in **under 3 minutes** on GitHub-hosted runners.
3. A second engineer can read this docset, clone the repo, and ship a new evaluator in **under 1 hour** without asking questions.
4. Every claim in the README (commands, screenshots, numbers) is reproducible by `make demo` and `make benchmark`.
5. A senior engineer reviewing the repo cannot find: dead folders, unused scaffolding, TODOs in committed code, mocked-but-unused dependencies, or boilerplate without tests.

## Non-goals (v1)

- No web UI in v1. (Optional Streamlit/HTMX dashboard is Phase 8, gated.)
- No managed/SaaS deployment. No multi-tenant auth.
- No fine-tuning, training, RLHF, or dataset generation.
- No prompt-engineering IDE.
- No Kubernetes, no Kafka, no microservices.
- No Postgres in v1 (SQLite is sufficient; Postgres is an extensibility hook, not a requirement).
- No support for streaming chat UIs.
- No agent orchestration (that is Project #9, AgentFlow).

## Out of scope explicitly

- LangChain / LlamaIndex integration. (LiteLLM is sufficient; we do not import frameworks we do not need.)
- Hosted LLM judge models. (Judges run through the same provider abstraction.)
- Auto-generation of test cases.
- "AI explains your eval failures" features. Those are gimmicks; reviewers see them as smell.

## Constraints

| Constraint | Value |
|---|---|
| Language | Python 3.12 |
| CLI | Typer |
| Models | Pydantic v2 |
| Storage | SQLite via SQLAlchemy 2.x + Alembic |
| HTTP | httpx |
| LLM adapter | LiteLLM (covers OpenAI, Anthropic, Ollama, etc. without per-provider code) |
| Logging | structlog (JSON in non-TTY, human in TTY) |
| Tracing | OpenTelemetry SDK (opt-in via env var) |
| Lint | Ruff |
| Types | Mypy strict |
| Tests | Pytest + Hypothesis (for evaluators) |
| Container | Single Dockerfile, multi-stage, distroless final |
| CI | GitHub Actions |
| License | Apache 2.0 |

## What "done" looks like for v1

A developer runs:

```bash
pip install evalkit
evalkit init demo
cd demo
export OPENAI_API_KEY=sk-...
evalkit run suite.yaml
evalkit report latest --format markdown > report.md
```

…and gets: a green run, a SQLite db with the run record, a markdown report with per-case scores, an OTel span tree if `OTEL_EXPORTER_OTLP_ENDPOINT` is set, and a non-zero exit code if any evaluator fails.

That is the entire bar.
