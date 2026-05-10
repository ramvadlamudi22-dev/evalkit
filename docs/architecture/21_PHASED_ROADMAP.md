# 21 — PHASED_ROADMAP.md

Each phase has: deliverables, exit criteria, and a manual review checkpoint where Devin stops and waits for the human. Phases are merged to `main` independently and tagged.

---

## Phase 0 — Repo & tooling skeleton (target: 0.5 day)

**Deliverables**

- `pyproject.toml` (uv-managed, deps for runtime + dev), `uv.lock`.
- `Ruff`, `Mypy`, `Pytest` configured.
- `pre-commit` hooks: ruff, mypy, basic file hygiene.
- `Makefile` with `install`, `lint`, `type`, `test`, `ci` targets.
- `Dockerfile` (multi-stage, distroless final). Builds; image runs `--version`.
- `.github/workflows/ci.yml` running lint + test + audit + docker. Green on a stub test.
- `LICENSE`, `README.md` (stub), `CHANGELOG.md` (Keep-a-Changelog format), `SECURITY.md`, `CONTRIBUTING.md`, `.editorconfig`, `.gitignore`, `.dockerignore`, `.env.example`.
- `src/evalkit/__init__.py` exposing `__version__`. `__main__.py` exits 0.
- `tests/unit/test_smoke.py` asserts `__version__` is set.
- Tag: `v0.0.1` after merge.

**Exit criteria**

- `make ci` green locally.
- Both CI workflow runs green on PR.
- Docker image builds and runs `evalkit --version` and exits 0.
- `pip install -e .` works in a fresh venv.

**Checkpoint**: STOP. Human reviews repo skeleton and confirms tooling choices.

---

## Phase 1 — Core domain + mock provider + exact_match + JSON storage (target: 1.5 days)

**Deliverables**

- `evalkit/core/models.py` — `Suite`, `Case`, `Result`, `RunRecord`, `Evaluation` (Pydantic v2).
- `evalkit/core/protocols.py` — `Provider`, `Evaluator` Protocols.
- `evalkit/errors.py` — full hierarchy.
- `evalkit/config.py` — `Settings` via pydantic-settings.
- `evalkit/providers/mock.py` — deterministic mock with configurable response policies.
- `evalkit/evaluators/exact_match.py` + `contains.py`.
- `evalkit/storage/` — SQLAlchemy models, repo façade, Alembic migration `0001_initial`.
- `evalkit/runner/` — bounded-concurrency runner, no retry yet.
- `evalkit/cli.py` — `evalkit init`, `evalkit run`, `evalkit list`, `evalkit show`. Exit codes wired.
- Suite YAML loader with strict pydantic validation.
- Tests: unit + integration + e2e (subprocess) covering happy + sad paths.

**Exit criteria**

- `evalkit init demo && cd demo && evalkit run suite.yaml` returns 0 with mock provider.
- A non-matching case causes exit 1.
- Run is persisted in SQLite; `evalkit list` shows it.
- ≥85% coverage; all tests pass.

**Checkpoint**: STOP. Demo to human; review domain model and CLI surface.

---

## Phase 2 — Real providers (LiteLLM) + retry/timeout (target: 1 day)

**Deliverables**

- `evalkit/providers/litellm_provider.py` — adapter over LiteLLM.
- `evalkit/runner/retry.py` — tenacity-based, error-code-driven (see `RETRY_STRATEGY.md`).
- Per-call timeout, total deadline.
- Provider registry + `get_provider()`.
- Documentation: `docs/user/providers.md` covering OpenAI, Anthropic, Ollama setup.

**Exit criteria**

- A fake provider that returns 429 for 2 attempts then 200 results in a passing case after 3 attempts; logs and DB show `attempts=3`.
- Permanent provider errors (4xx non-429) do not retry.
- Real-provider smoke tests opt-in (`EVALKIT_TEST_REAL_PROVIDERS=1`); they pass locally with a key.

**Checkpoint**: STOP. Human runs against a real key on their machine; confirms.

---

## Phase 3 — Evaluator suite (target: 1 day)

**Deliverables**

- `regex_match`, `json_schema`, `cosine_similarity`, `llm_judge`.
- Evaluator entry-point group `evalkit.evaluators` registered.
- Property tests (Hypothesis) for each evaluator.
- `docs/user/evaluators.md`.

**Exit criteria**

- Each evaluator has unit + property tests, full coverage.
- A custom evaluator can be added in an external package and discovered without forking (verified by an in-repo `examples/external_evaluator/`).

**Checkpoint**: STOP. Human reviews evaluator interface and rubric for `llm_judge`.

---

## Phase 4 — Reports, baselines, regression diff (target: 1 day)

**Deliverables**

- `evalkit/reports/markdown.py`, `json.py` with golden tests.
- `evalkit/diff/compare.py`.
- `evalkit baseline {set,get,list,unset}` and `--baseline` on `run`.
- `evalkit compare` and `evalkit report`.

**Exit criteria**

- A run with one regressed case vs baseline exits 1 and the diff names the case.
- Markdown report matches golden file.
- JSON report is valid against a published JSON Schema (committed).

**Checkpoint**: STOP. Human reviews a sample report and the comparison output.

---

## Phase 5 — Observability (target: 0.5 day)

**Deliverables**

- structlog setup (already wired through earlier phases; this phase finalizes redaction tests).
- OTel tracer/meter with span/metric set documented in `08_OBSERVABILITY_STRATEGY.md`.
- `OTEL_EXPORTER_OTLP_ENDPOINT` honored, off by default.
- Reference `docker-compose.observability.yml` (Jaeger + collector) for local users.
- `make demo` produces a Jaeger trace screenshot under `docs/images/`.

**Exit criteria**

- A run with `OTEL_EXPORTER_OTLP_ENDPOINT` set produces visible spans in Jaeger (verified locally; screenshot committed with metadata).
- Tracing overhead <5% on the mock benchmark.

**Checkpoint**: STOP. Human inspects Jaeger trace.

---

## Phase 6 — Docker, release, and CI hardening (target: 0.5 day)

**Deliverables**

- `release.yml` workflow finalised (PyPI trusted publisher, GHCR, SBOM, cosign).
- Image scanned by Trivy in CI; HIGH/CRITICAL fail.
- `gitleaks` + `pip-audit` running.
- CodeQL workflow.

**Exit criteria**

- A `v0.X.0-rc.1` tag produces a PyPI release candidate and a GHCR image.
- The released wheel installs and runs `evalkit run` against the demo suite in a fresh venv.
- The released image runs `evalkit run` against a mounted demo suite.

**Checkpoint**: STOP. Human installs from PyPI in a fresh environment; verifies.

---

## Phase 7 — README, screenshots, demo video, benchmarks (target: 1 day)

**Deliverables**

- README rewritten to the structure in `17_README_STRATEGY.md`.
- `make demo` produces all referenced screenshots.
- `make benchmark` produces real numbers; README's benchmark section auto-regenerated.
- 90-second demo video recorded per `18_DEMO_VIDEO_STRATEGY.md`.
- Architecture diagram (Mermaid + SVG) committed.
- ADR-0001 through ADR-000N committed for non-obvious choices.

**Exit criteria**

- Every command in the README has been executed by `make readme-verify` and exits 0.
- All referenced screenshots exist and have metadata.
- A reviewer can clone, `make install`, `make demo`, and reproduce the README's hero output.

**Checkpoint**: STOP. Human reviews repo top-to-bottom for "fake AI repo smell" against the checklist in `24_TECH_DEBT_STRATEGY.md`.

---

## Phase 8 (gated, optional) — Local dashboard (target: 1.5 days)

Only if the human says "yes" after Phase 7.

**Deliverables**

- `evalkit serve` command (FastAPI + HTMX, no SPA).
- Pages: runs list, run detail, compare two runs.
- Localhost-only bind, token auth.
- `docker-compose.yml` for the dashboard.

**Exit criteria**

- Dashboard renders a real run from the demo SQLite.
- All pages tested via Playwright.
- README updated *only after* the dashboard is verified working.

---

## Tag plan

| Tag | After |
|---|---|
| `v0.0.1` | Phase 0 |
| `v0.1.0` | Phase 1 |
| `v0.2.0` | Phase 2 |
| `v0.3.0` | Phase 3 |
| `v0.4.0` | Phase 4 |
| `v0.5.0` | Phase 5 |
| `v0.6.0` | Phase 6 |
| `v1.0.0-rc.1` | Phase 7 |
| `v1.0.0` | After human sign-off on Phase 7 review |
| `v1.1.0` | After Phase 8, only if Phase 8 ships |

Total target: 6–7 working days through Phase 7. Human review time at each checkpoint is on top.
