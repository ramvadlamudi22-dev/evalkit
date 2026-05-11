# ADR-0005: Retry policy (tenacity, exponential backoff with full jitter)

- Status: accepted
- Date: 2025-11-26
- Deciders: maintainers
- Supersedes: --
- Related: ADR-0004 (LiteLLM as provider seam)

## Context

Real providers fail intermittently — 429s under load, 5xx during deploys, transient
TCP/TLS hiccups, and per-call deadlines we set ourselves. We need a retry policy that:

- only retries what's classified as transient (never auth, never bad request);
- bounds the total wait so a slow case can't hold up the suite indefinitely;
- adds jitter to avoid synchronised retry storms across the suite's concurrent tasks;
- is easy to test deterministically (no real sleeps in CI).

## Decision

Use **tenacity 9.x** via `AsyncRetrying` inside `LiteLLMProvider.complete()`:

| knob | value | rationale |
| --- | --- | --- |
| max attempts | 3 (default; configurable via constructor) | First attempt + 2 retries. Beyond that, latency cost outweighs success-probability gain for typical 429/5xx patterns. |
| backoff | exponential with full jitter | `tenacity.wait_random_exponential(multiplier=initial, max=max)`. `initial=0.5s`, `max=8s` by default. Full jitter prevents thundering herd across concurrent suite cases. |
| retry condition | transient subclasses of `ProviderError` only | `retry_if_exception_type((TransientProviderError, RateLimitProviderError, TimeoutProviderError))`. Never `AuthProviderError`, `PermanentProviderError`, or `ProviderConfigError`. |
| reraise | True | After the budget is exhausted, the **classified** EvalKit exception propagates (not a tenacity `RetryError`). |
| sleep | `asyncio.sleep` | Yields the event loop; respects concurrency. |
| testing | inject `acompletion` callable + use `asyncio.sleep` no-op in tests | Tests assert call counts on the scripted callable; no wall-clock sleeps. |

Retry orchestration is **inside** the provider adapter, not in the runner. Two reasons:
(a) different providers may have different retry budgets in the future (already a Phase 5
hook); (b) the runner stays oblivious to retry mechanics and just sees `result` or
`raise EvalKitError`.

## Consequences

**Positive**

- Predictable bounded latency: a single case can spend at most `initial * (2^0 + 2^1) +
  2 * timeout_s` before the budget is exhausted (rough upper bound; jitter usually halves
  the wait).
- Errors that are *guaranteed not to succeed on retry* (auth, config, bad request) fail
  fast — we save budget for cases that might.
- Structured-log line per attempt (`attempt_no`, `outcome`, `error_code`,
  `latency_ms`) so a recruiter or auditor can reconstruct the call sequence from logs.

**Negative / accepted risk**

- A genuinely stuck provider can still spend ~`max_attempts * timeout_s` per case before
  giving up. With default `timeout_s=30s` and 3 attempts that's 90s worst-case per case.
  Setting `concurrency` correctly (default 4) and reducing `timeout_s` for fast models
  mitigates this; we don't otherwise short-circuit because the user explicitly chose those
  values in the suite YAML.
- Tenacity's `AsyncRetrying` is slightly more verbose than a hand-rolled loop, but the
  jitter/policy plumbing is exactly the kind of thing we don't want to maintain
  ourselves.

## Alternatives considered

- **Hand-rolled retry loop**: ~50 lines, but you reinvent jitter, type-aware retry,
  exponential math, and the test seam. Not worth it.
- **`backoff` library**: similar feature set; tenacity has wider adoption and a slightly
  cleaner async surface. Either would work.
- **Retries in the runner**: rejected — see "Consequences" above. The runner shouldn't
  know how a provider chooses to recover.
- **No retries (let the runner re-enqueue the case)**: rejected — it forces all retry
  policy into the orchestrator and makes `Provider` implementations responsible for
  knowing they'll be retried, defeating the "stable error surface" goal of ADR-0004.
