# 15 — RETRY_STRATEGY.md

## Library: tenacity

Why tenacity:
- Composable retry conditions (predicate-based on exception subclasses + custom `retry_if_*`).
- Built-in jittered exponential backoff.
- Hooks for telemetry callbacks (we wire these into structlog + OTel).
- Stable, widely-used, no surprises.

## Default policy

Configurable in suite YAML, defaults below:

```yaml
retry:
  max_attempts: 3
  backoff: exponential
  initial_seconds: 0.5
  max_seconds: 8
  jitter: full
  retry_on:
    - provider.rate_limit
    - provider.transient
  per_call_timeout_seconds: 30
  total_deadline_seconds: 90      # hard ceiling on (attempts × call) for one case
```

Policy fields:
- `retry_on` is a list of stable error codes (see `ERROR_HANDLING_STRATEGY.md`). We retry **only** on listed codes — not on every exception.
- `total_deadline_seconds` is a hard wall. If hit, the case errors with `code = retry.deadline_exceeded` regardless of attempts remaining.

## What we retry

| Code | Retried? | Notes |
|---|---|---|
| `provider.rate_limit` | yes | Honor `Retry-After` header when present (ceiling at `max_seconds`). |
| `provider.transient` | yes | 5xx, connection reset, DNS blip. |
| `provider.timeout` | yes (within deadline) | Each attempt gets full `per_call_timeout_seconds`. |
| `provider.permanent` | no | 4xx other than 429 → user error or unrecoverable. |
| `evaluator.error` | no | Evaluators are pure; retrying does nothing. |
| `storage.error` | no | These are bugs or full disks; user must intervene. |

## Idempotency

- Provider calls are idempotent from the provider's perspective for our usage (no streaming, no statefulness).
- DB writes are idempotent at the row level: the runner inserts a `case` row once; evaluator results inserted as separate rows. A retried call replaces the in-memory result for the case before the row is inserted; we do not insert intermediate failed-attempt rows.
- We track attempt count on the final row.

## Concurrency interaction

- Retry happens **inside** the semaphore-bounded worker. A retry does not release the slot. This caps concurrent retries naturally.
- A run-wide *circuit breaker* trips if `>50% of recent calls failed with provider.transient` over a sliding window of 30 calls. The runner pauses for 10 seconds, then resumes. This is a *belt-and-suspenders* check; the primary backpressure is the per-call retry policy.

## Telemetry

Every retry emits:
- A WARNING log: `retry attempt scheduled` with `attempt`, `next_delay_ms`, `error.code`.
- A counter increment: `evalkit.provider.retries{provider, error.kind}`.
- A span event on the active `evalkit.provider.call` span.

A successful call after retries logs INFO with `attempts > 1` so it's grep-able.

## Tests

- Each retryable error code has a unit test asserting the policy retries and eventually succeeds.
- A property test asserts: total wall time across retries ≤ `total_deadline_seconds + slack`.
- A test asserts non-retryable codes do not retry.
- A test asserts the circuit breaker trips and recovers.

## What we do NOT do

- No infinite retries. Hard cap on attempts and on wall time.
- No retries that cross runs. Each run is independent.
- No "smart retries that change the prompt." Retries are mechanical; prompt engineering is the user's job.
- No silent retries. Every retry shows up in logs and DB attempt count.
