# 10 — SECURITY_REVIEW.md

## Threat model (v1)

EvalKit runs on a developer's laptop, in CI, or in a container they control. There is **no multi-tenant trust boundary**, no public network surface (the optional dashboard is local-only), and no managed service.

| Asset | Threat | Mitigation |
|---|---|---|
| API keys (provider credentials) | Leak via logs, reports, error messages, DB. | Redaction in log pipeline; never persisted to DB; never rendered in reports; explicit unit tests for each path. |
| Suite YAML | Code execution via `!python` tags or eval. | We use `yaml.safe_load` exclusively. No Jinja templating in v1 (templates are a future hook with an explicit sandbox). |
| Dataset content | Path traversal, symlink shenanigans. | Canonicalize and confine paths under the suite directory by default; explicit opt-in for absolute paths. |
| LLM responses | Prompt-injection content reaching the judge. | Judge prompt is hard-coded; rubric content is the only operator-controlled string. We scrub stop-sequence injection by truncation. |
| SQLite DB | Sensitive prompt/response content at rest. | Documented behavior. Optional future opt-in to hash inputs. Users with PII concerns scrub upstream. |
| Dependencies | Supply-chain (typosquats, compromised wheels). | Dependabot, pip-audit in CI, locked deps via `uv.lock`, signed commits, minimal dependency surface. |
| Container image | Vulnerabilities in base image. | Distroless final stage, Trivy scan in CI, fail on HIGH/CRITICAL. |
| Local dashboard (Phase 8) | Unauthenticated access from browser to local DB. | Bind 127.0.0.1 only, localhost auth token in URL, no remote exposure. |

## Secrets handling

- Keys come from environment variables, period. Never from suite YAML, never from CLI args, never from the DB.
- A scanner check (`scripts/scan_secrets.sh` invoking `gitleaks`) runs in CI on every PR.
- `.env.example` is the canonical list of expected vars; `.env` is gitignored.
- The `evalkit doctor` command lists which provider envs are present (names only, never values) and exits 0 only if at least one configured provider has its key set.

## Input validation

- All YAML/JSON inputs pass through Pydantic models with strict mode. Unknown fields raise.
- Dataset row size is capped (default 256 KB; configurable). Larger rows error with file:line.
- Provider responses are size-capped (default 4 MB). The runner records `truncated=true` and continues.

## Output safety

- Markdown reports are sanitized when rendering user content: angle brackets escaped, no `<script>`, no raw HTML pass-through.
- JSON reports never include API keys. We test the negative case.

## Supply chain

- Pinned via `uv.lock`. CI re-resolves only on lockfile changes.
- Dependabot weekly for both pip and GitHub Actions.
- `pip-audit` in CI on every push.
- `cargo-audit` style: any HIGH/CRITICAL fails CI; the team has 7 days to remediate before the build is paused.

## Container

- Multi-stage Dockerfile.
- Build stage: `python:3.12-slim`, installs deps with uv into a `/venv`.
- Final stage: `gcr.io/distroless/python3-debian12:nonroot`, copies `/venv` and `src/evalkit`.
- Runs as `nonroot` UID. No shell. No package manager.
- Image labels include `org.opencontainers.image.source`, `revision`, `version`, `licenses`.

## CI

- Workflows pinned to commit SHAs, not tags (`actions/checkout@<sha> # v4.x`).
- Minimum permissions per job (`permissions: contents: read`); only `release.yml` gets `contents: write`.
- No third-party actions outside `actions/*`, `astral-sh/setup-uv`, and pinned community ones we vet.
- Secrets exposed only to jobs that need them, via environments with required reviewers for `release`.

## Anti-features

- No telemetry phone-home. EvalKit makes zero outbound calls except to the LLM providers the user configures.
- No bundled API keys. No "free tier" calls to any provider.
- No automatic update checks. The user updates with `pip` or by pulling a new image.

## SECURITY.md (file in the repo)

A real `SECURITY.md` ships in the repo with: supported versions, how to report a vulnerability (private email or GitHub Security Advisory), expected response time (7 days to acknowledge, 30 days to fix or mitigate). No GPG key theater unless we actually use one.
