# 13 — DEPLOYMENT_PLAN.md

## What "deploy" means for EvalKit

EvalKit is a CLI. There is no service to host. "Deploy" means three distribution targets:

1. **PyPI** — `pip install evalkit`. Primary install path.
2. **GHCR Docker image** — `docker run ghcr.io/<owner>/evalkit:vX.Y.Z run suite.yaml`. For CI users who don't want a Python toolchain.
3. **Pre-built standalone binary** *(optional, Phase 8)* — `pyinstaller`-built single binary. Only if there is a real ask. We do not ship a binary just to brag.

## Local

The default `make demo` flow:

```
git clone …
cd evalkit
make install      # uv sync
make demo         # runs `evalkit init demo && cd demo && evalkit run suite.yaml`
make report       # writes docs/images/sample_report.md from the demo run
```

Verified by an integration test that runs `make demo` in CI.

## Docker

Single Dockerfile, multi-stage. Phases 0–5 use `python:3.12-slim` for the runtime stage; distroless migration is gated to Phase 6 (release hardening). Rationale: stable distroless `python3-debian12` ships Python 3.11, not 3.12, which would create a version drift between local development (3.12) and the runtime container. Chainguard distroless 3.12 is a candidate at Phase 6. See [ADR-0002](../adr/0002-runtime-image-uses-python-3.12-slim-not-distroless.md).

```
# build stage
FROM python:3.12-slim AS build
RUN pip install --no-cache-dir "uv==<pinned>"
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN uv sync --no-dev --no-install-project
RUN uv pip install --no-cache --no-deps -e .

# runtime stage (Phase 0-5)
FROM python:3.12-slim AS runtime
RUN groupadd --system --gid 10001 evalkit \
 && useradd  --system --uid 10001 --gid evalkit --no-create-home --shell /usr/sbin/nologin evalkit
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src   /app/src
ENV PATH="/app/.venv/bin:${PATH}"
USER evalkit
ENTRYPOINT ["evalkit"]
CMD ["--help"]
```

Image budget:
- Compressed: <80 MB target. Phase 0 image is ~50–60 MB compressed (verified at PR time; current value lives in CI logs and is asserted in Phase 6 once we have a baseline file).
- Verified by `docker image inspect` in the CI `docker` job; the release workflow holds the release if the image grows >10% between releases without cause.

## docker-compose for the optional dashboard (Phase 8)

```
# docker-compose.yml — Phase 8 only, gated behind explicit roadmap approval
services:
  dashboard:
    image: ghcr.io/<owner>/evalkit:vX.Y.Z
    command: ["serve", "--bind", "0.0.0.0:8080"]
    ports: ["127.0.0.1:8080:8080"]
    volumes: ["./.evalkit:/data/.evalkit:ro"]
    environment:
      EVALKIT_DB: /data/.evalkit/evalkit.db
```

Bound to `127.0.0.1` only. We do not provide a "production deployment" recipe because EvalKit is not a multi-tenant service.

## Optional Render demo

Only if Phase 8 ships and we want a public read-only demo of the dashboard. Render config:

- Static service running the dashboard image.
- Read-only seeded SQLite baked into the image (cleansed of any real data).
- Basic auth in front via Render middleware.
- Demo URL is added to the README **only after** it's verified live.

If we don't ship a public demo, the README does not claim one. Honesty over flash.

## Release checklist (per tagged version)

Manual checklist run before tagging:

- [ ] `make ci` is green locally.
- [ ] `make demo` produces an up-to-date `docs/images/sample_report.md`.
- [ ] `make benchmark` produces numbers; the README's benchmark section is regenerated and committed.
- [ ] `CHANGELOG.md` is updated; `pyproject.toml` version bumped.
- [ ] No deprecation warnings in `pytest -W error`.
- [ ] `evalkit doctor` exits 0 in a clean container.

After tag push, `release.yml` does the rest.

## Rollback

- PyPI: `pip install evalkit==<previous>`. We yank a release with `pypi yank` only for security issues.
- GHCR: previous tags remain immutable.
- DB: every migration has a working `downgrade()`. A rollback to an older EvalKit version requires a downgrade migration step, documented in the changelog of any release that adds a migration.

## What we are NOT deploying

- A SaaS. Not now, not as a stretch goal in v1.
- A managed dashboard. Self-host or nothing.
- A "free hosted eval" tier. Out of scope.
