# 23 — RISK_ANALYSIS.md

## Top risks, by severity × likelihood

### R1 — LiteLLM API drift breaks provider adapter
**Likelihood**: Medium. **Severity**: High (blocks releases).
**Mitigation**: Pin LiteLLM in `uv.lock`. CI matrix tests against the pinned version only. A separate scheduled weekly job tests against `litellm@latest` and files an issue on drift; never gates main.

### R2 — Real-provider tests break CI when keys expire / are revoked
**Likelihood**: Medium. **Severity**: Medium.
**Mitigation**: Real-provider tests are opt-in (`EVALKIT_TEST_REAL_PROVIDERS=1`) and never run in `ci.yml`. They run in a separate `nightly-real-providers.yml` workflow with `continue-on-error: true`; their failure files an issue, never blocks merges.

### R3 — Flaky tests in async runner under load
**Likelihood**: Medium. **Severity**: Medium.
**Mitigation**: Property tests for the runner explicitly use deterministic time and a deterministic mock provider. We never use `time.sleep` in tests; `asyncio.Event` and freezegun. Three-strikes rule: a test that flakes 3 times is quarantined with a tracking issue, not retried.

### R4 — SQLite write contention if a future use case adds parallel writers
**Likelihood**: Low. **Severity**: Medium.
**Mitigation**: Documented assumption in `05_DATABASE_SCHEMA.md`: single writer per run. Engine swap path to Postgres is preserved by SQLAlchemy abstraction. Trigger to switch is documented (multi-writer requirement); we do not pre-empt it.

### R5 — Prompt injection via dataset content into `llm_judge` rubric
**Likelihood**: Medium. **Severity**: Low (effect is bad scores, not RCE).
**Mitigation**: Judge prompt template is hard-coded in code, not user-controlled. Rubric is markdown rendered into a fixed-shape prompt; user content flows in via clearly labelled sections. Tests assert that injected content cannot reorder prompt sections.

### R6 — Docker image bloat
**Likelihood**: Medium. **Severity**: Low.
**Mitigation**: Distroless final stage. Image-size budget asserted in CI; release blocked if image grows >10% without justification.

### R7 — README drift (claims that no longer match the code)
**Likelihood**: High (this is the #1 portfolio smell). **Severity**: High.
**Mitigation**: `make readme-verify` runs every command in the README's Quickstart and parses the output for expected markers. CI runs `make readme-verify` on every PR. Screenshots have metadata files validated against current `evalkit --version`.

### R8 — Devin runs into infinite fix loops
**Likelihood**: Medium. **Severity**: Medium (wasted credits + bad PRs).
**Mitigation**: Three-strikes rule per failure mode. Hypothesis-required-by-second-fix-attempt (see `META.md`). Devin sessions auto-pause on third failure and surface the failure to the human with a written hypothesis.

### R9 — Dependency vulnerability disclosed near a release
**Likelihood**: Medium. **Severity**: Medium.
**Mitigation**: `pip-audit` in CI. Dependabot weekly. `SECURITY.md` documents 30-day mitigation SLA. We tolerate a delayed release more than a vulnerable one.

### R10 — Scope creep into "AI agent" features
**Likelihood**: High (shiny). **Severity**: High (kills credibility).
**Mitigation**: SPEC's non-goals section is binding. Any feature suggestion that crosses a non-goal needs an ADR explaining why the non-goal changed. No exceptions for "small additions".

### R11 — Migration backwards-incompatibility surprises a user
**Likelihood**: Low (we have one app, one DB). **Severity**: Medium.
**Mitigation**: Every Alembic migration ships with both `upgrade()` and `downgrade()`. CHANGELOG calls out schema changes explicitly. A migration cannot drop a column in the same release that adds it; staged via a multi-release deprecation when needed.

### R12 — Security: secret leaks in logs/reports
**Likelihood**: Medium without discipline. **Severity**: High.
**Mitigation**: Redactor processor in structlog pipeline tested on every release. Reports never include API keys (negative tests). `gitleaks` in CI. `evalkit doctor` validates env presence without printing values.

### R13 — Premature dashboard ships before CLI is solid
**Likelihood**: Medium (visual progress is tempting). **Severity**: Medium.
**Mitigation**: Phase 8 is gated. Phase 7 review must pass first. Dashboard is explicitly "if there's an ask," not a default v1 deliverable.

### R14 — "Open source signal" but the repo is dead
**Likelihood**: Medium. **Severity**: Medium (recruiters prefer recent activity).
**Mitigation**: Cadence — at least one merged PR per week through release. `CHANGELOG.md` updated per release. Weekly `chore(deps)` PRs are fine signal. After v1.0, no commits is acceptable for short windows; >60 days dark requires a deliberate "hibernation" note in README.

### R15 — Portfolio looks single-tool / one-trick
**Likelihood**: High in v1 (only EvalKit exists). **Severity**: Low if Project #2 ships on cadence.
**Mitigation**: 90-day plan in `META.md` explicitly addresses portfolio shape. Project #2 (TraceForge recommended) is chosen to be complementary to EvalKit, so the portfolio tells a system story.
