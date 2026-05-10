# 14 — ERROR_HANDLING_STRATEGY.md

## Exception hierarchy

A single root, narrow leaves. Defined in `evalkit/errors.py`:

```
EvalKitError                    # never raised directly; root for `except EvalKitError`
├── UsageError                  # CLI-level user mistake → exit 64
│   ├── ConfigError
│   ├── SuiteValidationError
│   └── DatasetValidationError
├── InfraError                  # outside our control → exit 2
│   ├── ProviderError
│   │   ├── RateLimitError       # retryable
│   │   ├── TransientProviderError  # retryable
│   │   ├── PermanentProviderError  # non-retryable
│   │   └── TimeoutError
│   └── StorageError
├── EvaluatorError              # inside an evaluator; logged, recorded per-case → run still completes
└── InternalError               # bug in EvalKit → exit 70
```

Rules:
- Every raised exception inherits from `EvalKitError`.
- Each leaf carries a stable `code: str` (e.g. `provider.rate_limit`) used in logs, metrics, and retry policies.
- No `Exception("string")` anywhere in `src/evalkit/`. Lint enforces.

## CLI exit-code mapping

```python
EXIT_MAP = {
    UsageError: 64,
    InfraError: 2,
    InternalError: 70,
}
# default success: 0
# default eval-failed: 1 (set explicitly by run command, not by an exception)
```

Unhandled exceptions in the CLI go through a single `try/except` at the top level that logs the exception with `level=error`, prints a one-line user-facing message to stderr, and exits 70. We never let a Python traceback escape to stdout.

## Error model in records

Per-case error rows store:

- `error_kind` — the leaf class name (e.g. `RateLimitError`).
- `error_code` — the stable string code.
- `error_message` — short, redacted, no stack trace.
- `attempts` — total attempts including the failing one.

This is the contract between runner and reports. Reports group cases by `error_code` for readability.

## Boundary policy

- **Network errors** (httpx) are caught at the provider adapter and translated to `ProviderError` subclasses. The runner never sees raw `httpx.HTTPError`.
- **DB errors** (SQLAlchemy) are caught at the repo and translated to `StorageError`. Callers never see raw SQLAlchemy exceptions.
- **Validation errors** (Pydantic) at the suite/dataset boundary are translated to `SuiteValidationError` / `DatasetValidationError` with the file path and JSON Pointer to the bad field.

This makes `except` blocks meaningful. If you `except ProviderError`, you know exactly what's covered.

## Logging on error

- Always include `error.code`, `error.kind`, and the structured context (`run_id`, `case_id`, etc.).
- ERROR-level for things that should not happen (`InternalError`, `StorageError` outside of init).
- WARNING-level for retried errors that ultimately succeeded.
- INFO-level for retried errors that ultimately failed but didn't crash the run.

## User-facing error messages

Every leaf class provides a `user_message()` that:
- Names the file, command, or config field at fault when applicable.
- Suggests the next action (e.g. "Set OPENAI_API_KEY", "Run `evalkit storage upgrade`").
- Is short (<200 chars).

Stack traces are reserved for `--log-level debug` or for `InternalError` where the traceback is genuinely the actionable info.

## Don't-do list

- No `except Exception: pass`. Ever.
- No swallowing exceptions to "be resilient." If you catch, you log and re-raise or translate.
- No magic recovery in the runner. Every error path is explicit.
- No `sys.exit(...)` outside of `cli.py`. Only the CLI exits.
