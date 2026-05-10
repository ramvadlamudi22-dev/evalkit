# 12 — CICD_PLAN.md

## Workflows

Three workflows. No more.

### `.github/workflows/ci.yml` (push, pull_request)

| Job | Steps | Time budget |
|---|---|---|
| `lint` | checkout → setup-uv → `uv sync --frozen --extra dev` → `ruff check` → `ruff format --check` → `mypy` | 60s |
| `test` (matrix: py3.12 on ubuntu-latest, macos-latest) | checkout → setup-uv → `uv sync --frozen --extra dev` → `uv run pytest -q` → upload coverage | 120s |
| `audit` | checkout → setup-uv → `uv run pip-audit` → `gitleaks detect --no-banner` | 60s |
| `docker` | docker build (multi-arch via buildx, cache via gha) → Trivy scan, fail on HIGH/CRITICAL | 180s |
| `e2e-cli` | install built wheel → run `evalkit init demo && evalkit run demo/suite.yaml` against mock provider | 60s |

All jobs run in parallel where possible; `e2e-cli` depends on a successful build artifact from `test`.

Concurrency: `cancel-in-progress: true` on `pull_request`.

Caching: `astral-sh/setup-uv` handles the venv cache; the docker job uses `actions/cache` for buildx.

Branch protection requires: `lint`, `test (ubuntu)`, `audit`, `docker`, `e2e-cli`. macOS test is informational (allowed to fail without blocking) for cost reasons; if it ever flakes, the failure is investigated, not normalized.

### `.github/workflows/release.yml` (tag `v*.*.*`)

- Verify the tag matches `pyproject.toml` version.
- Build wheel + sdist with `uv build`.
- Build and push Docker image to GHCR (`ghcr.io/<owner>/evalkit:vX.Y.Z` and `:latest`).
- Generate SBOM (`syft`) and attach to the release.
- Sign image with `cosign` (keyless via OIDC).
- Publish to PyPI via OIDC trusted publisher (no API token in repo secrets).
- Generate changelog from conventional commits since previous tag, attach to release notes.

This workflow has elevated permissions (`contents: write`, `id-token: write`, `packages: write`) and runs only from a protected `release` environment requiring a manual approver.

### `.github/workflows/codeql.yml` (weekly + push to main)

Standard GitHub-provided CodeQL for Python. Runs once on schedule, once on push to main. Findings are surfaced as security alerts.

## Local parity

`make ci` runs the same commands the CI workflow runs, in the same order. We do not hide CI logic behind GitHub-only constructs (no inline shell scripts longer than 5 lines in YAML — extract to `scripts/`).

## Caching policy

- We cache the uv venv keyed on `uv.lock`.
- We cache pre-commit envs keyed on `.pre-commit-config.yaml`.
- We do not cache pytest because reproducibility > 5-second savings.

## Secrets in CI

- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` etc. are configured **only** in the optional `nightly-real-providers.yml` job — not present in `ci.yml`. PRs from forks therefore have zero access to provider keys. (Phase 5 deliverable; not blocking v1 release.)

## Failure handling

- A failing `lint`, `test`, or `audit` blocks merge. No bypass.
- A failing `docker` blocks merge.
- A failing `e2e-cli` blocks merge — this is the canary that the install path works.
- We never add `if: failure()` workarounds to convert failures into warnings. If a check is too noisy to gate on, it's deleted, not muted.

## Devin-specific guardrails

- Devin sessions implementing CI changes must run `act` (or our `make ci`) locally before pushing.
- Three-strikes rule: if a Devin PR fails the same check 3 times, the session stops and surfaces the failure to the human reviewer with a written hypothesis. (Cross-reference: `META.md`.)

## What we are NOT doing in v1

- No "deploy on merge to main" — there is nothing to deploy at v1.
- No nightly fuzzing job — overkill for v1's scope.
- No multi-Python-version matrix beyond 3.12 (we say "Python 3.12" in SPEC; we don't pretend to support 3.10 we haven't tested).
- No artifact promotion pipeline. The release workflow is straight-through.
