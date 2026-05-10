# 02 — PRODUCT_REQUIREMENTS.md

## Personas

**P1 — IC engineer shipping an LLM feature.** Wants `evalkit run` in CI to fail their PR if quality regresses. Cares about: speed, deterministic CI, clear failure messages.

**P2 — Tech lead reviewing eval results.** Wants to compare two runs, see which cases regressed, drill into a single case's prompt/response/score. Cares about: legibility of reports, reproducibility, audit trail.

**P3 — Platform/infra engineer adopting EvalKit org-wide.** Cares about: extensibility (custom evaluators), observability hooks, secret hygiene, container images, no surprise dependencies.

**Anti-persona — non-technical stakeholder.** Not a target user. They consume the markdown report; they do not run the tool. Build for engineers; reports are a side effect.

## Functional requirements

### Must-have (v1)

- F1. Declarative **suite YAML** describes dataset, models, evaluators, concurrency, retry policy.
- F2. **Dataset loader** for JSONL with schema validation.
- F3. **Provider abstraction** with at minimum: `mock`, `openai`, `anthropic`, `ollama` (all via LiteLLM where possible).
- F4. **Evaluator abstraction** with built-ins: `exact_match`, `contains`, `regex`, `json_schema`, `cosine_similarity`, `llm_judge`.
- F5. **Runner** executes (case × model × evaluator) with bounded concurrency, per-call timeout, and retry-with-jitter on retryable errors.
- F6. **Storage**: every run persists to SQLite — run metadata, per-case results, raw provider responses (gzipped blob), evaluator scores, suite snapshot.
- F7. **Reports**: `evalkit report <run-id> --format {markdown,json}` produces a reproducible artifact.
- F8. **Compare**: `evalkit compare <a> <b>` produces a regression diff (cases that newly fail, score deltas, latency deltas).
- F9. **Baseline**: `evalkit baseline set <run-id>` and `evalkit run --baseline current` for CI gating.
- F10. **Exit codes**: 0 success, 1 evaluator failure(s), 2 infrastructure error, 64 usage error.
- F11. **Structured logs** (JSON) on stderr when not a TTY.
- F12. **`--dry-run`** flag that loads suite + dataset and validates without calling providers.

### Should-have (v1)

- F13. Caching of provider responses by `(model, prompt_hash, params_hash)` to make re-runs cheap.
- F14. Deterministic seed propagation where providers accept a seed parameter.
- F15. Pluggable evaluator entry-point group (`evalkit.evaluators`) so external packages can register evaluators without forking.
- F16. Sample suite + sample dataset shipped with `evalkit init`.

### Nice-to-have (Phase 8, gated)

- F17. Local read-only dashboard for browsing runs (Streamlit or FastAPI+HTMX, single binary).
- F18. SARIF export for surfacing eval failures in GitHub PR annotations.

### Won't have (v1)

- No multi-user auth.
- No remote storage backend.
- No background scheduler.
- No cost optimizer.

## Non-functional requirements

| Category | Requirement |
|---|---|
| Performance | A 100-case suite with `mock` provider completes in <2s on a laptop. |
| Reliability | Single transient provider error must not abort the run; retried per policy, then recorded as a per-case error. |
| Reproducibility | `run_id` + suite snapshot + dataset hash + dependency lockfile is sufficient to explain any past run. |
| Observability | All public CLI commands emit one root span; runner emits child spans per case and per evaluator call. |
| Security | No secrets in DB, no secrets in logs, no secrets in reports. Redaction of API keys from any captured headers. |
| Portability | Works on Linux, macOS, and inside the official Docker image. Windows is best-effort, not blocking. |
| Backwards compatibility | Suite YAML schema is versioned (`version: 1`); breaking changes bump the version and provide a migration. |
| Footprint | Default install adds <30 dependencies. No accidental import of huge frameworks. |

## Acceptance scenarios

1. **Green path.** Given a valid suite, when I run `evalkit run`, then a run row is inserted, all cases recorded, exit code is 0 if all evaluators pass, and the markdown report exists.
2. **Regression gate.** Given a baseline and a current run with one newly-failing case, when I run `evalkit run --baseline current`, then exit code is 1 and the diff highlights the regressed case.
3. **Provider outage.** Given a provider that returns 429 for 2 calls then 200, when retry policy is `max_attempts=3, backoff=exponential`, then the case succeeds on attempt 3 and the run records 2 retried events.
4. **Hard failure.** Given a provider that returns 500 for all attempts, when the run completes, then that case is recorded as `error`, run exit code is 1, but the run does not crash.
5. **Dry run.** Given a suite with a missing dataset file, when I run `evalkit run --dry-run`, then exit code is 64 and the error names the file and line.
