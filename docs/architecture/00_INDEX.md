# EvalKit Planning Set — Index

This is the complete planning set produced **before** any implementation code. Nothing in `evalkit/` source exists yet. Approval gate is at the bottom of this file.

| # | Document | Purpose |
|---|----------|---------|
| 01 | SPEC.md | What EvalKit is, success criteria, non-goals |
| 02 | PRODUCT_REQUIREMENTS.md | Personas, user stories, functional/non-functional requirements |
| 03 | SYSTEM_ARCHITECTURE.md | Components, data flow, technology choices, decision log |
| 04 | FOLDER_STRUCTURE.md | Repository layout |
| 05 | DATABASE_SCHEMA.md | SQLite schema, migrations, indexes |
| 06 | CLI_API_CONTRACT.md | Typer command surface, exit codes, suite YAML schema |
| 07 | EVALUATION_ARCHITECTURE.md | Evaluator interface, built-ins, scoring, regression detection |
| 08 | OBSERVABILITY_STRATEGY.md | OpenTelemetry-ready design, spans, metrics |
| 09 | LOGGING_STRATEGY.md | structlog config, log model, redaction |
| 10 | SECURITY_REVIEW.md | Threat model, secrets, supply chain, prompt injection |
| 11 | TESTING_STRATEGY.md | Unit, integration, e2e, golden, eval-of-evals |
| 12 | CICD_PLAN.md | GitHub Actions matrix, caching, release flow |
| 13 | DEPLOYMENT_PLAN.md | Local, Docker Compose, optional Render demo |
| 14 | ERROR_HANDLING_STRATEGY.md | Exception hierarchy, error contracts |
| 15 | RETRY_STRATEGY.md | tenacity policy, idempotency, deadlines |
| 16 | METRICS_BENCHMARK_STRATEGY.md | What we measure, how we report, baselines |
| 17 | README_STRATEGY.md | README structure, badges, screenshots policy |
| 18 | DEMO_VIDEO_STRATEGY.md | Demo script, recording, hosting |
| 19 | GITHUB_REPO_STRATEGY.md | Repo settings, templates, branch protection |
| 20 | COMMIT_STRATEGY.md | Conventional commits, PR sizing, review |
| 21 | PHASED_ROADMAP.md | Phase 0 → Phase 8 deliverables and exit criteria |
| 22 | REVIEW_CHECKPOINTS.md | Explicit STOP points where Devin blocks for sign-off |
| 23 | RISK_ANALYSIS.md | Top risks and mitigations |
| 24 | TECH_DEBT_STRATEGY.md | Hygiene rules, deprecation policy |
| 25 | EXTENSIBILITY_STRATEGY.md | Plugin model, public interfaces, versioning |
| ★ | META.md | Credits, fix loops, spec writing, phasing, anti-smell, 90-day plan |

---

## Approval Gate

After reading these docs, reply with one of:

- **"Approved — proceed to Phase 0"** — Devin will scaffold the empty repo + tooling and stop again at the Phase 0 checkpoint.
- **"Approved with changes: …"** — list deltas; Devin updates docs and re-asks.
- **"Rework section X"** — Devin revises only that doc.

Devin will not create the GitHub repo, write source code, run tests, or modify the environment blueprint until you give one of the above.
