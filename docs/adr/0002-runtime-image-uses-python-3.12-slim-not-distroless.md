# ADR-0002: Runtime image uses `python:3.12-slim`, not distroless (for now)

- Status: Accepted
- Date: 2026-05-10

## Context

[`13_DEPLOYMENT_PLAN.md`](../architecture/13_DEPLOYMENT_PLAN.md) originally specified
`gcr.io/distroless/python3-debian12:nonroot` as the runtime base for the EvalKit
container image. We pin Python 3.12 throughout the project (development,
test matrix, CI). However, the stable distroless `python3-debian12` image
ships Python 3.11, not 3.12. Using it would create a version drift between
local development and the runtime container.

Available alternatives at the time of this decision:

1. **`python:3.12-slim`** (Debian-based, official Python image, ~50 MB compressed,
   includes Python 3.12).
2. **Chainguard `cgr.dev/chainguard/python:latest`** (distroless-style, can be
   pinned to a 3.12 variant, small).
3. **Build distroless from source** (Bazel rules + custom toolchain).

## Decision

For Phase 0 (and through Phase 5), the EvalKit runtime image is built on
`python:3.12-slim`, multi-stage, with the application running as a non-root
`evalkit` user.

We will **revisit distroless in Phase 6** (release hardening), at which point we
will evaluate Chainguard's distroless 3.12 image against the maintenance cost
and image-size tradeoffs.

## Consequences

- The runtime image carries Debian's apt + a few system packages. Slightly
  larger attack surface than true distroless, but well-understood and supported.
- We avoid Python-version drift between dev and runtime, which is the most
  common cause of "works in CI, fails in container" bugs.
- We do not lose the option to migrate later — the Dockerfile is a single file
  and the migration path (swap the `runtime` stage) is small.
- Image-size budget remains under 80 MB compressed; we will assert this in CI
  in Phase 6.

## References

- `13_DEPLOYMENT_PLAN.md` (updated to match this ADR in the same PR).
