# 19 — GITHUB_REPO_STRATEGY.md

## Repo settings

| Setting | Value |
|---|---|
| Visibility | Public from day one. Private repos for portfolio work signal indecisiveness. |
| Default branch | `main`. |
| Branch protection on `main` | Required reviews: 1 (self-approve OK on solo, but PRs are still required); required status checks: `lint`, `test (ubuntu)`, `audit`, `docker`, `e2e-cli`; require linear history; require signed commits; disallow force pushes. |
| Merge strategy | Squash merge only. Branch deleted on merge. |
| Issues | Enabled. |
| Discussions | Disabled in v1 (no audience yet; enable later if traction warrants). |
| Wiki | Disabled. Docs live in `docs/`. |
| Actions | Enabled, fork PR workflows require approval. |
| Allow auto-merge | Yes (used with required checks). |

## Templates

`.github/ISSUE_TEMPLATE/`:
- `bug_report.md` — repro steps, expected, actual, environment, evalkit version, log excerpt.
- `feature_request.md` — problem, current workaround, proposed solution, alternatives.
- `config.yml` — `blank_issues_enabled: false`. Forces use of templates.

`.github/PULL_REQUEST_TEMPLATE.md` — sections: *What changed*, *Why*, *How tested*, *Risks*, *Linked issue*. Short. The PR description is required to fill at least the first three.

`CODEOWNERS` — single owner in v1 (you). Wired so reviews are automatically requested on PRs touching specific paths (e.g., `src/evalkit/storage/` requires a review even from yourself, which forces a re-read pass).

## Labels

A small, opinionated label set. Avoid label sprawl.

| Label | Use |
|---|---|
| `area:cli` | Touches `cli.py`. |
| `area:runner` | Touches `runner/`. |
| `area:storage` | Touches `storage/`. |
| `area:evaluators` | Touches `evaluators/`. |
| `area:observability` | Touches `observability/`, OTel, logs. |
| `area:docs` | Docs only. |
| `area:ci` | Touches `.github/workflows/`. |
| `kind:bug` | Reported bug. |
| `kind:feature` | New capability. |
| `kind:chore` | Refactor, deps, infra. |
| `phase:0` … `phase:8` | Roadmap phase tag. |
| `good first issue` | For external contributors after v1. |
| `breaking-change` | Any PR that changes public surface. |

No `priority:` labels in solo mode — they create false priority signals.

## Releases

- Semantic versioning, strict.
- Pre-1.0 releases tagged `v0.X.Y` until SPEC's "done for v1" is met.
- `v1.0.0` is tagged when **all** v1 acceptance scenarios are green and Phase 0–7 are complete.
- Release notes auto-generated from conventional commits, then *hand-edited* before publishing. AI-generated release notes are smell.

## README badges (links)

| Badge | Source |
|---|---|
| `CI` | `https://github.com/<owner>/evalkit/actions/workflows/ci.yml/badge.svg` |
| `Coverage` | Codecov badge or shields.io reading `coverage.json` from latest release. |
| `PyPI` | `https://img.shields.io/pypi/v/evalkit.svg` |
| `License` | `https://img.shields.io/github/license/<owner>/evalkit.svg` |
| `Image size` | `https://img.shields.io/docker/image-size/<owner>/evalkit/latest` (or GHCR equivalent). |

Stars badge is included only after we cross 100 stars; before that, it's pity-bait.

## SECURITY.md

- Statement of supported versions (latest minor only in v1).
- How to report (private GitHub Security Advisory preferred; backup email).
- SLA: acknowledge in 7 days, fix or mitigate in 30.
- No GPG keys unless we plan to rotate and use them.

## CONTRIBUTING.md

- Dev setup (4 commands).
- Test strategy summary (link to `docs/architecture/11_TESTING_STRATEGY.md`).
- Commit and PR conventions (link to `20_COMMIT_STRATEGY.md`).
- "How to add an evaluator" walkthrough.
- "How to add a provider" walkthrough.
- Code of conduct link.

## Repo description (single line on GitHub)

> "A pytest-shaped LLM evaluation toolkit: declarative suites, reproducible runs, regression gates, OpenTelemetry-ready."

Short. Concrete nouns. No "AI-powered". No "next-generation".

## Repo topics

`llm`, `evaluation`, `cli`, `python`, `pytest-friendly`, `opentelemetry`. Not `ai`, not `agents`, not `mlops` (we are not the second one and barely the third).
