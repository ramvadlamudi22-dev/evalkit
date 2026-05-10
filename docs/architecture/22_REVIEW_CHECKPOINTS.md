# 22 — REVIEW_CHECKPOINTS.md

Devin **stops and blocks for explicit human approval** at every checkpoint below. Devin does not auto-progress between phases.

| # | Checkpoint | When | Block-on-user prompt |
|---|---|---|---|
| C0 | **Plan approval** | Now (this docset). | "Approved — proceed to Phase 0" / "Approved with changes: …" / "Rework section X". |
| C1 | **Phase 0 — Skeleton review** | After tooling skeleton merges to `main`. | "Skeleton merged: link to PR. Continue to Phase 1?" Devin attaches: `tree` of repo, `make ci` log, Docker image size. |
| C2 | **Phase 1 — Domain & CLI review** | After core run loop with mock provider works. | "Mock e2e green. Demo: <attached terminal recording>. Continue to Phase 2?" Devin attaches: domain model diff summary, CLI `--help` output, sample SQLite row dumps. |
| C3 | **Phase 2 — Real provider review** | After LiteLLM provider + retry policy. | "Real-provider smoke ran on your machine? Continue to Phase 3?" Devin pauses for the user to run `EVALKIT_TEST_REAL_PROVIDERS=1 pytest -m real_providers` locally and confirm. |
| C4 | **Phase 3 — Evaluator review** | After all built-in evaluators. | "Evaluators implemented: list. Rubric for llm_judge: <link>. Continue to Phase 4?" |
| C5 | **Phase 4 — Reports & regression review** | After compare + reports. | "Sample regression report: <link>. Confirm format and continue?" |
| C6 | **Phase 5 — Observability review** | After OTel + redaction tests. | "Jaeger screenshot: <link>. Confirm spans/metrics and continue?" |
| C7 | **Phase 6 — Release pipeline review** | After PyPI/GHCR release pipeline. | "RC published: <PyPI link>, <GHCR link>. Install in a fresh env on your side and confirm." Devin pauses. |
| C8 | **Phase 7 — Final repo review** | After README, screenshots, video, benchmarks. | "Anti-smell checklist results: <attached>. Approve `v1.0.0` tag?" |
| C9 | **Phase 8 decision** | After v1.0.0. | "Ship dashboard (Phase 8) or move to Project #2?" |
| C10 | **Project #2 gate** | Strict. | Before *any* work on Project #2 starts, Devin asks: "Project #1 (EvalKit) is shipped at <tag>. You explicitly authorized starting Project #2 (<name>). Confirm?" |

## What "blocking" looks like in practice

At each checkpoint, Devin sends a `message_user(block_on_user=true)` with:

- A one-line headline of what was done.
- Links to PRs, releases, screenshots.
- A specific question with a small set of clickable answers (`Approved` / `Approved with changes` / `Rework`).
- An "evidence pack" attachment: command logs, screenshots, JSON exports.

## Anti-pattern Devin must not perform

- Auto-merging its own PRs.
- Skipping a checkpoint because "the work is similar to last phase".
- Bundling two phases into one PR to save a checkpoint.
- Treating a non-blocking status update as approval.
- Resuming Phase N+1 because the user hasn't responded for hours. Silence is not consent.

## Re-entry after long pauses

If a checkpoint review sits more than 7 days, Devin (when next invoked) re-validates the prior phase before proceeding:

1. Pull latest `main`.
2. Run `make ci`.
3. Re-execute the prior phase's exit criteria.
4. Surface any drift in the next message.

This catches "the world moved while you waited" — dependency churn, expired API keys, GitHub Actions deprecations.
