# 11 — TESTING_STRATEGY.md

## Layers

| Layer | What | Speed target | Determinism |
|---|---|---|---|
| **Unit** | Pure functions, evaluators, parsers, validators, redactors. | <2s total | Fully deterministic. |
| **Property** | Hypothesis tests for evaluators (e.g. exact_match commutativity, regex evaluator never crashes on adversarial inputs). | <5s | Seeded. |
| **Integration** | Runner against `mock` provider, storage round-trip with real SQLite + Alembic, report renderers vs golden files. | <30s | Deterministic. |
| **E2E (CLI)** | `subprocess.run(["evalkit", ...])` smoke tests; covers exit codes, stderr format, file outputs. | <30s | Deterministic. |
| **Real-provider smoke** | Opt-in, gated by `EVALKIT_TEST_REAL_PROVIDERS=1`. Never blocks CI. | n/a | Non-deterministic; recorded but not asserted on outputs. |

Total CI test time target: **under 90 seconds** on GitHub-hosted runners.

## Test layout

`tests/` mirrors `src/evalkit/` at the unit level (one test file per source module). Integration / e2e tests are organized by scenario, not source layout. Golden files live under `tests/golden/`.

## Mocking discipline

- **Mock at the boundary, not in the middle.** The `mock` provider is a real `Provider` implementation that returns deterministic responses. It's used in production-style integration tests, not as a `unittest.mock` patch.
- **Patch only at module-level imports**, never at class-attribute level inside other modules. Prefer dependency injection over patching.
- **No `unittest.mock` for SQLAlchemy, httpx, or pydantic.** Always use real instances against ephemeral resources.

## Fixtures

- `tmp_path` for filesystem.
- `db_url` fixture creates a fresh SQLite file per test, runs Alembic head, yields, drops.
- `mock_provider` fixture with parametrizable response policies.
- `suite_factory` builds suite Pydantic objects with sensible defaults; tests override only what they care about.

## Golden testing for reports

Markdown and JSON reports are compared against committed goldens in `tests/golden/reports/`. To regenerate: `pytest --update-goldens`. The flag is gated by `EVALKIT_UPDATE_GOLDENS=1` to avoid accidental updates.

Goldens are reviewed in PR diffs like any other file. A regression that "just" changes the report is therefore a deliberate, code-reviewed change.

## Property tests for evaluators

For each evaluator, Hypothesis verifies:

- It never raises on any string input (only `EvaluatorError` for declared invalid configs).
- Its output is in `[0, 1]`.
- Its output is invariant under whitespace tweaks where the evaluator claims so.
- Its `passed` boolean is consistent with `score` and threshold.

## Coverage

- Coverage tool: `coverage.py` via `pytest-cov`.
- Target: **≥85% line coverage on `src/evalkit/`**, **≥95% on `evalkit/evaluators/` and `evalkit/runner/`** (the high-risk surfaces).
- Coverage is reported but does not gate the build alone. We gate on a *floor*: a PR that drops coverage by more than 1 point requires explicit approval.
- Branch coverage on `runner/` is reported in CI summary.

## Determinism in CI

- ULIDs are seeded to a fixed value in tests.
- `time` is frozen via `freezegun` only at boundaries that need it. Most tests are time-agnostic.
- Random in evaluators is forbidden (and lint-checked: no `import random` in `evaluators/`).

## What we don't test

- Behavior of provider APIs themselves.
- LiteLLM's internals.
- SQLAlchemy's internals.
- We test our **adapters** to those, with mocks of their nearest interface.

## Pre-commit (developer machine)

- `ruff check`, `ruff format --check`, `mypy`, `pytest -m unit`.
- Full test suite runs on push, not on every save.
- Hooks are fast (<5s) so no one disables them.

## Bug-fix discipline

Every reported bug becomes:

1. A failing test reproducing the bug, committed first.
2. The fix.
3. The same test now passing.

Reviewers reject fix PRs that lack a test demonstrating the bug existed.
