# 08 — OBSERVABILITY_STRATEGY.md

## Posture

OpenTelemetry-ready, **off by default**, on by env var. We never pay overhead in CI for telemetry no one collects. When a user sets `OTEL_EXPORTER_OTLP_ENDPOINT`, EvalKit installs the SDK and exports.

## What we instrument

### Spans (tracer name `evalkit`)

| Span | Parent | Attributes |
|---|---|---|
| `evalkit.command` | root | `command.name`, `evalkit.version`, `run_id` (if applicable) |
| `evalkit.run` | command | `suite.name`, `suite.sha256`, `dataset.sha256`, `run.id` |
| `evalkit.case` | run | `case.id`, `case.index`, `model.id`, `provider` |
| `evalkit.provider.call` | case | `provider`, `model.id`, `attempt`, `tokens.prompt`, `tokens.completion`, `latency.ms` |
| `evalkit.evaluation` | case | `evaluator.name`, `evaluator.version`, `passed`, `score` |
| `evalkit.storage.write` | run | `rows`, `table` |

Span names use the `evalkit.{component}.{operation}` convention. Attributes use lowercase dotted keys, matching OTel semantic conventions where they exist (e.g., `gen_ai.*`).

### Metrics (meter name `evalkit`)

| Metric | Type | Attributes | Purpose |
|---|---|---|---|
| `evalkit.runs.total` | Counter | `status` | Run outcomes. |
| `evalkit.cases.total` | Counter | `model.id`, `status` | Case-level counts. |
| `evalkit.evaluations.passed` | Counter | `evaluator.name`, `model.id` | Pass rate. |
| `evalkit.evaluations.failed` | Counter | `evaluator.name`, `model.id` | Fail rate. |
| `evalkit.provider.latency.ms` | Histogram | `provider`, `model.id` | Latency distribution. |
| `evalkit.provider.retries` | Counter | `provider`, `error.kind` | Retry pressure. |
| `evalkit.tokens.prompt` | Counter | `provider`, `model.id` | Cost proxy. |
| `evalkit.tokens.completion` | Counter | `provider`, `model.id` | Cost proxy. |
| `evalkit.cost.usd` | Counter | `provider`, `model.id` | Best-effort cost. |

Histograms use the OTel default boundaries; we don't customize without evidence.

### Logs

structlog-formatted, every log carries `run_id`, `case_id` (where applicable), `evaluator_name`, `model_id`, `attempt`. Trace-context propagation (`trace_id`, `span_id`) is added when tracing is on.

## Configuration

All standard OTel env vars are honored:

- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_EXPORTER_OTLP_HEADERS`
- `OTEL_SERVICE_NAME` (we default to `evalkit`)
- `OTEL_RESOURCE_ATTRIBUTES`
- `OTEL_TRACES_SAMPLER` (we default to `parentbased_always_on` when telemetry is enabled)

Plus EvalKit-specific:

- `EVALKIT_TELEMETRY_DISABLED=1` — hard kill switch even if OTel env vars are set.
- `EVALKIT_TELEMETRY_CONSOLE=1` — emit spans to stderr (developer convenience, never on in CI).

## Boundary rule

EvalKit emits OTel signals; it never bundles a backend. Users point at their own OTLP endpoint (Jaeger, Tempo, Honeycomb, Datadog, etc.). We document setup with `docker-compose.observability.yml` for local Jaeger, but it's a reference, not a dependency.

## Demo & dogfooding

The README's observability section will show:

- A real screenshot of a Jaeger trace from a `make demo` run, with spans for `evalkit.run → evalkit.case → evalkit.provider.call → evalkit.evaluation`.
- A real screenshot of a Grafana panel charting `evalkit.evaluations.failed` over time.

These screenshots are produced by `scripts/demo.sh` running against the local compose stack. No fake screenshots.

## Performance budget

Tracing overhead must be <5% on the `mock` provider benchmark (50-case suite). Verified by `benchmarks/run.sh --with-tracing` versus baseline.

## Anti-patterns we avoid

- No vendor-specific instrumentation libraries (no `datadog`, no `honeycomb-beeline`). OTel is the single integration point.
- No "add tracing later" comments. The hooks are designed in from Phase 0; the SDK setup is what's deferred to Phase 5.
- No metric sprawl. Every metric must be plotted in one of our reference dashboards or it doesn't ship.
