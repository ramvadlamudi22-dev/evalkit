# 03 — SYSTEM_ARCHITECTURE.md

## Components (logical)

```
+------------------+       +-------------------+       +------------------+
|   Suite YAML     | --->  |   Suite Loader    | --->  |   Run Planner    |
+------------------+       +-------------------+       +------------------+
                                                              |
                                                              v
+------------------+       +-------------------+       +------------------+
|  Dataset (JSONL) | --->  |  Dataset Loader   | --->  |     Runner       |
+------------------+       +-------------------+       +------------------+
                                                          |        |
                                       +------------------+        +------------------+
                                       v                                              v
                          +---------------------+                        +-------------------------+
                          |  Provider Adapter   |                        |   Evaluator Pipeline    |
                          |  (LiteLLM)          |                        |   (built-ins + plugins) |
                          +---------------------+                        +-------------------------+
                                       |                                              |
                                       +-----------------+        +-------------------+
                                                         v        v
                                                  +-------------------+
                                                  |   Result Writer   |
                                                  +-------------------+
                                                          |
                                                          v
                                                +------------------+
                                                |   SQLite (file)  |
                                                +------------------+
                                                          |
                                                          v
                                                +------------------+
                                                |  Report Renderer |
                                                +------------------+
```

Cross-cutting:

- **Observability bus** — structlog + OpenTelemetry tracer/meter, threaded through every component via context.
- **Config** — pydantic-settings, single source of truth, env > file > defaults.
- **Errors** — single exception hierarchy in `evalkit.errors`; CLI maps to exit codes.

## Module map

| Module | Responsibility | Public surface |
|---|---|---|
| `evalkit.core` | Domain models (Pydantic), Protocols | `Suite`, `Dataset`, `Case`, `Result`, `Evaluator`, `Provider` |
| `evalkit.config` | Settings, env loading | `Settings.load()` |
| `evalkit.providers` | LLM adapters | `get_provider(name) -> Provider` |
| `evalkit.evaluators` | Built-ins + registry | `get_evaluator(name) -> Evaluator` |
| `evalkit.runner` | Orchestration | `run_suite(suite) -> RunRecord` |
| `evalkit.storage` | SQLAlchemy + Alembic | `Repo` (DAO façade) |
| `evalkit.reports` | Markdown / JSON renderers | `render(run, format) -> str` |
| `evalkit.diff` | Run-vs-run regression analysis | `compare(a, b) -> Diff` |
| `evalkit.cli` | Typer entrypoint | `main()` |
| `evalkit.observability` | structlog + OTel setup | `setup(settings)` |
| `evalkit.errors` | Exception hierarchy | `EvalKitError`, subclasses |

## Data flow (single run)

1. CLI parses args, loads `Settings`, calls `runner.run_suite(suite_path)`.
2. Suite loader validates YAML against pydantic model `Suite`.
3. Dataset loader streams JSONL, validates each row against `Case`.
4. Run Planner materializes the cartesian product `cases × models × evaluators` into a list of `WorkItems`, deduped against the response cache if enabled.
5. Runner executes WorkItems with `asyncio.Semaphore`-bounded concurrency. Each item: provider call (with retry/timeout) → evaluator pipeline → `Result` row.
6. Writer batch-inserts rows in transactions of N (default 50).
7. Report renderer reads the run from `Repo` and emits markdown/json.

## Concurrency model

- **Async-first.** Provider calls are I/O bound; we use `httpx.AsyncClient` and `asyncio.gather` with a semaphore.
- **Single event loop**, no threads except for SQLite writes (SQLite is fine on the main thread for our load; we only fan out for HTTP).
- **Backpressure** is the semaphore. No queues, no workers, no Celery.

## Decision log (selected)

| Decision | Choice | Why | Reversibility |
|---|---|---|---|
| DB | SQLite + SQLAlchemy 2.x | Single-file, zero ops, fast enough for any one team's usage. SQLAlchemy gives us a Postgres path if ever needed. | Easy — swap engine URL. |
| HTTP | httpx | First-class async, sane defaults, retries via tenacity layered on top. | Easy. |
| LLM client | LiteLLM | One dependency, dozens of providers, well-maintained. Avoids per-provider code drift. | Medium — would need adapters per provider. |
| CLI | Typer | Thin wrapper around Click + type hints; matches our type-strict posture. | Easy. |
| Logs | structlog | JSON + dev-friendly + context vars + integrates with OTel. | Easy. |
| Tracing | OTel SDK | Industry standard; opt-in by env var avoids overhead in CI. | Easy. |
| Migrations | Alembic | Boring, correct, audited. | N/A. |
| Lockfile | uv | Fast, deterministic, modern. (Fallback: pip-tools.) | Easy. |
| License | Apache 2.0 | Permissive, patent grant, recruiter-friendly. | Hard once published. |

## What we explicitly chose NOT to use, and why

- **LangChain / LlamaIndex** — too heavy, too opinionated, churn-prone, recruiter signal is negative for serious infra work.
- **FastAPI** in v1 — we have no HTTP surface yet; adding one without a need is theater.
- **Postgres** in v1 — solves no problem we have; SQLite is the pragmatic, honest choice.
- **Docker Compose for runtime** — EvalKit is a CLI; Compose is for the optional dashboard only.
- **Pydantic v1** — v2 is faster and the standard.
- **Black + isort + flake8** — Ruff replaces all three.
- **Poetry** — uv is faster, simpler, has a better lockfile story.
- **Make** as the only entrypoint — we provide a `Makefile` for muscle memory but every target is a one-line wrapper around a real command.
