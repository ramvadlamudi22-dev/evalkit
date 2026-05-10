# Contributing to EvalKit

Thanks for considering a contribution. EvalKit aims for a small, opinionated
codebase; the project values **fewer high-quality features over many unfinished
features**.

## Development setup

```bash
git clone https://github.com/ramvadlamudi22-dev/evalkit.git
cd evalkit
make install    # uv sync + pre-commit install
make ci         # lint + type + test
```

You need:

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (`pip install uv` if you don't have it)
- Docker (only for `make docker-build`)

## Testing

See [`docs/architecture/11_TESTING_STRATEGY.md`](docs/architecture/11_TESTING_STRATEGY.md).

Run tests:

```bash
make test         # pytest with coverage
make cov          # html coverage report at htmlcov/
```

## Commits and pull requests

- We use **conventional commits**: `feat(scope): subject`, `fix(scope): subject`, etc.
- See [`docs/architecture/20_COMMIT_STRATEGY.md`](docs/architecture/20_COMMIT_STRATEGY.md)
  for full rules.
- PRs target <300 lines changed; **<600 lines is the ceiling**.
- Every PR description fills the *What*, *Why*, and *How tested* sections.
- Bug fixes start with a failing test that reproduces the bug.

## What lands easily

- Bug fixes with a failing test.
- New evaluators that follow the `Evaluator` protocol (Phase 3+).
- Provider adapters that follow the `Provider` protocol (Phase 2+).
- Docs improvements.
- CI hardening.

## What needs discussion first

- Public API or CLI changes.
- New top-level dependencies.
- Database schema changes.
- Anything that crosses an explicit non-goal in
  [`docs/architecture/01_SPEC.md`](docs/architecture/01_SPEC.md).

Open an issue to discuss before sending a PR for these.

## Code of conduct

Participants in this project are expected to follow our
[Code of Conduct](CODE_OF_CONDUCT.md).
