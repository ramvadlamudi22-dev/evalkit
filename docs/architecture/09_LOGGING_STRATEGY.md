# 09 — LOGGING_STRATEGY.md

## Library: structlog

Why structlog over stdlib `logging` alone:
- First-class structured fields and context vars, no `extra={}` ergonomic taxes.
- Renders human-readable in TTY, JSON otherwise — zero ceremony.
- Integrates cleanly with stdlib `logging` so third-party libraries (httpx, sqlalchemy) flow into the same pipeline.

## Format

| Environment | Renderer |
|---|---|
| TTY (stderr is a tty) | `ConsoleRenderer(colors=True)` — human-readable, level-colored, key=value tail. |
| Non-TTY (CI, Docker, redirected) | `JSONRenderer()` — one JSON object per line. |
| `--log-format json` | Force JSON. |
| `--log-format console` | Force console. |

Sinks: stderr only. We do **not** write to files in v1. Users pipe to whatever they want.

## Required fields on every record

- `timestamp` (UTC, ISO8601)
- `level` (`debug|info|warning|error`)
- `event` (the message — short, present-tense, no punctuation)
- `module` (e.g. `evalkit.runner.execute`)

## Context fields (added when relevant via context vars)

- `run_id`
- `case_id`
- `case_index`
- `model_id`
- `provider`
- `evaluator_name`
- `attempt`
- `trace_id`, `span_id` (when OTel is enabled)

These are bound on entry to a logical scope (`with bound_contextvars(run_id=...)`), so handlers don't need to plumb them by hand.

## Log levels — the rule

- `DEBUG`: anything that would help a developer reproduce a problem. Verbose by design. Off by default.
- `INFO`: lifecycle events (run started/finished, case completed, baseline set). One human-readable line per event.
- `WARNING`: degraded but recoverable (retry happened, cache miss when expected, slow DB write). Pair with the recovery action.
- `ERROR`: a thing that should not happen, with enough context to triage. Always includes exception class.
- We do **not** use `CRITICAL`. There is no operator on call.

## Redaction

A redactor processor runs before any renderer:

- Headers matching `(?i)(authorization|x-api-key|cookie)` → `***REDACTED***`.
- Values for keys in a denylist (`api_key`, `secret`, `token`, `password`) → `***REDACTED***`.
- Long strings (>16KB) are truncated with `len=` annotation.

Redaction is tested explicitly: `tests/unit/observability/test_redaction.py`.

## Third-party noise

- `httpx` set to WARNING by default; DEBUG when EvalKit is at DEBUG.
- `sqlalchemy.engine` set to WARNING; DEBUG only via `--log-level debug --sql-echo`.
- LiteLLM internal prints are captured and demoted to DEBUG.

## What never goes in logs

- API keys, secrets, tokens.
- Full prompts in INFO/WARNING (they can be huge). DEBUG-only with truncation.
- Full responses in INFO/WARNING (same reason). The DB has them.
- Stacktraces at INFO. Stacktraces are ERROR-level.

## Example records

**Console (TTY):**
```
2026-05-10T18:42:11Z [info ] case completed module=evalkit.runner.execute run_id=01HZ... case_id=news-014 model_id=gpt-4o-mini latency_ms=812 attempt=1
```

**JSON (CI):**
```json
{"timestamp":"2026-05-10T18:42:11Z","level":"info","event":"case completed","module":"evalkit.runner.execute","run_id":"01HZ...","case_id":"news-014","model_id":"gpt-4o-mini","latency_ms":812,"attempt":1,"trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"00f067aa0ba902b7"}
```

## Performance

structlog with bound context vars and JSON rendering is well under 10µs per record. The runner emits at most a few records per case. There is no logging-induced bottleneck at any realistic suite size.
