# 04 — FOLDER_STRUCTURE.md

```
evalkit/
├── README.md
├── LICENSE                       # Apache-2.0
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── pyproject.toml                # uv-managed, ruff/mypy/pytest config
├── uv.lock
├── Makefile                      # thin wrappers: install, lint, test, demo, benchmark, docker
├── Dockerfile                    # multi-stage, distroless final
├── docker-compose.yml            # only for optional dashboard (Phase 8)
├── .python-version               # 3.12
├── .editorconfig
├── .gitignore
├── .gitattributes
├── .pre-commit-config.yaml
├── .dockerignore
├── .env.example
│
├── docs/                         # the planning set lives here, plus user docs
│   ├── architecture/
│   │   ├── 01_SPEC.md
│   │   ├── 02_PRODUCT_REQUIREMENTS.md
│   │   ├── 03_SYSTEM_ARCHITECTURE.md
│   │   └── ...                   # all 25 docs from this planning set
│   ├── adr/                      # Architecture Decision Records, one per significant choice
│   │   └── 0001-record-architecture-decisions.md
│   ├── user/
│   │   ├── quickstart.md
│   │   ├── suites.md
│   │   ├── evaluators.md
│   │   ├── providers.md
│   │   ├── ci.md
│   │   └── faq.md
│   └── images/                   # diagrams + screenshots used by README
│
├── src/
│   └── evalkit/
│       ├── __init__.py           # __version__
│       ├── __main__.py           # `python -m evalkit`
│       ├── cli.py                # Typer app
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py         # Pydantic: Suite, Case, Result, RunRecord
│       │   ├── protocols.py      # Provider, Evaluator Protocols
│       │   └── ids.py            # ULID generation
│       ├── config.py             # Settings via pydantic-settings
│       ├── errors.py             # Exception hierarchy
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── logging.py        # structlog setup
│       │   ├── tracing.py        # OTel setup
│       │   └── metrics.py        # OTel meter helpers
│       ├── providers/
│       │   ├── __init__.py       # registry + get_provider()
│       │   ├── base.py
│       │   ├── mock.py
│       │   └── litellm_provider.py
│       ├── evaluators/
│       │   ├── __init__.py       # registry + entry-point loader
│       │   ├── base.py
│       │   ├── exact_match.py
│       │   ├── contains.py
│       │   ├── regex_match.py
│       │   ├── json_schema.py
│       │   ├── cosine_similarity.py
│       │   └── llm_judge.py
│       ├── runner/
│       │   ├── __init__.py
│       │   ├── plan.py
│       │   ├── execute.py        # async runner with semaphore
│       │   ├── retry.py          # tenacity policies
│       │   └── cache.py          # response cache
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── repo.py           # DAO façade
│       │   ├── models.py         # SQLAlchemy mapped classes
│       │   └── migrations/       # Alembic
│       │       ├── env.py
│       │       └── versions/
│       ├── reports/
│       │   ├── __init__.py
│       │   ├── markdown.py
│       │   └── json.py
│       ├── diff/
│       │   ├── __init__.py
│       │   └── compare.py
│       └── _resources/
│           ├── init_template/    # files copied by `evalkit init`
│           │   ├── suite.yaml
│           │   ├── datasets/sample.jsonl
│           │   └── README.md
│           └── rubrics/          # default judge rubrics
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── core/
│   │   ├── evaluators/           # one file per evaluator
│   │   ├── providers/
│   │   ├── runner/
│   │   ├── storage/
│   │   ├── reports/
│   │   └── diff/
│   ├── integration/
│   │   ├── test_runner_e2e.py    # uses mock provider
│   │   └── test_storage_alembic.py
│   ├── e2e/
│   │   └── test_cli.py           # subprocess-level
│   ├── golden/
│   │   ├── reports/              # golden markdown
│   │   └── fixtures/
│   └── property/                 # Hypothesis tests for evaluators
│
├── benchmarks/
│   ├── README.md
│   ├── suite.yaml
│   ├── datasets/
│   └── run.sh                    # produces numbers used in README
│
├── scripts/
│   ├── demo.sh                   # what `make demo` runs; produces screenshots
│   └── release.sh
│
└── .github/
    ├── workflows/
    │   ├── ci.yml
    │   ├── release.yml
    │   └── codeql.yml
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   ├── feature_request.md
    │   └── config.yml
    ├── PULL_REQUEST_TEMPLATE.md
    ├── CODEOWNERS
    └── dependabot.yml
```

## Rules of the layout

1. **No empty folders.** A folder exists only when it has at least one file with real content.
2. **`src/` layout** is mandatory. Avoids the import-from-cwd footgun and matches the modern Python standard.
3. **One Pydantic model file per concern.** `core/models.py` only holds domain models. Storage models live in `storage/models.py` and are translated to/from `core/models.py` at the repo boundary.
4. **No `utils.py`.** Anything tempting that name belongs in a named module.
5. **No `helpers/`.** Same reason.
6. **Tests mirror source 1:1** at the unit level. Integration and e2e tests are organized by scenario, not by source file.
7. **Resources** (templates, rubrics) live under `src/evalkit/_resources/` and are loaded via `importlib.resources`, never via filesystem-relative paths.
8. **Migrations are committed.** Generated, not handwritten. Renaming a column requires a new migration, not editing an old one.
