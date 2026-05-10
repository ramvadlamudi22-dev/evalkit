# EvalKit container image.
#
# Phase 0: python:3.12-slim multi-stage build. The planning doc originally
# specified `gcr.io/distroless/python3-debian12:nonroot` for the final stage,
# but stable distroless ships Python 3.11, not 3.12. We pin to 3.12 across
# dev and runtime to avoid version drift between local and container.
# Distroless migration is revisited in Phase 6 (release hardening) — see
# docs/architecture/13_DEPLOYMENT_PLAN.md.

# ---------- Build stage --------------------------------------------------
FROM python:3.12-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install uv (pinned).
RUN pip install --no-cache-dir "uv==0.7.9"

WORKDIR /app

# Install dependencies first for better cache hits, then copy source.
COPY pyproject.toml README.md uv.lock ./
COPY src ./src

# Install runtime deps + the package itself into a venv at /app/.venv.
RUN uv sync --no-dev --frozen --no-install-project
RUN uv pip install --no-cache --no-deps -e .

# ---------- Runtime stage ------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

# Create a non-root user.
RUN groupadd --system --gid 10001 evalkit \
 && useradd  --system --uid 10001 --gid evalkit --no-create-home --shell /usr/sbin/nologin evalkit

WORKDIR /app

# Copy the resolved venv and source from the build stage.
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src   /app/src

USER evalkit

# Image labels (OCI).
LABEL org.opencontainers.image.title="evalkit" \
      org.opencontainers.image.description="A pytest-shaped LLM evaluation toolkit." \
      org.opencontainers.image.source="https://github.com/ramvadlamudi22-dev/evalkit" \
      org.opencontainers.image.licenses="Apache-2.0"

ENTRYPOINT ["evalkit"]
CMD ["--help"]
