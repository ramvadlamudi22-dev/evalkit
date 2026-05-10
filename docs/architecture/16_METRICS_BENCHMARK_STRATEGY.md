# 16 — METRICS_BENCHMARK_STRATEGY.md

## Two distinct concepts

1. **Eval metrics** — what EvalKit *produces* about user models (pass rate, score, latency, cost).
2. **Self benchmarks** — what EvalKit *publishes about itself* (CLI overhead, throughput, image size).

Conflating them is a smell. We keep them separate.

## Eval metrics produced by EvalKit

Per run, derived from the DB:

| Metric | Definition |
|---|---|
| Pass rate | `passed_cases / total_cases` per `(model, evaluator)`. |
| Aggregate pass rate | `passed_cases / total_cases` per `model`, where a case passes only if all evaluators pass. |
| Score average | Mean of `score` per `(model, evaluator)`. Reported alongside pass rate, never used as a gate. |
| p50 / p95 latency | Per `model`, in milliseconds. |
| Token usage | Sum of prompt + completion tokens per `model`. |
| Cost (USD) | Sum from LiteLLM per `model`. Best-effort, labelled "approx". |
| Retry rate | `retries / total_calls` per `model`. |
| Error rate | `error_cases / total_cases` per `model`. |

These show up in the markdown report and in the JSON report.

## Self benchmarks (`benchmarks/`)

We publish three numbers in the README, all reproducible with `make benchmark`:

| Benchmark | What it measures | Method |
|---|---|---|
| **CLI cold-start** | Time from `evalkit --version` to exit. | `hyperfine 'evalkit --version'` × 10 runs. |
| **Mock-provider throughput** | Cases/sec on a 200-case suite with mock provider, concurrency=8. | `time evalkit run benchmarks/suite-mock.yaml`, average over 5 runs. |
| **Storage write throughput** | Rows/sec into SQLite during a typical run. | derived from the runner's structured logs in benchmark mode. |

All three numbers are produced by `benchmarks/run.sh`, which writes a JSON file consumed by `scripts/update_readme_benchmarks.py`. The README's benchmark section is regenerated from that JSON on every release. **The README never contains hand-typed benchmark numbers.**

## Reproducibility rules

- Every benchmark records: `evalkit_version`, `python_version`, `host_os`, `host_arch`, `commit_sha`, `timestamp`. The JSON output includes these fields.
- A benchmark run that doesn't record provenance is not valid; the script refuses to overwrite the published numbers.
- Benchmarks run on a documented baseline (the `make benchmark` target documents: GitHub Actions `ubuntu-latest` runner; locally, the user's machine spec is captured from `/proc/cpuinfo` + `uname`).

## What we will NOT publish

- Provider-specific quality numbers ("GPT-4 scores 92% on our suite"). Quality is a function of the dataset, not the tool. Such numbers would be misleading and recruiter-bait.
- Comparisons against other eval tools. We don't have time to do those fairly. We describe positioning in prose, not in fake benchmark tables.
- Cost-per-eval claims that depend on volatile provider pricing.

## How metrics are surfaced

- Markdown report: prose summary + per-model table + per-evaluator table + (if `--baseline`) a regression table.
- JSON report: the same data, machine-readable.
- OTel meters (see `OBSERVABILITY_STRATEGY.md`): live metrics for users running EvalKit in CI with telemetry on.
- CLI `evalkit show <run-id>`: same content as the markdown report, in a terminal-friendly table.

## Numbers in the README — the rule

Every number in the README has one of:

1. A reproducibility command in the same paragraph.
2. A link to the benchmark JSON file in the repo.
3. A timestamped screenshot from `make demo`.

If a number can't be backed by one of those, it doesn't go in the README. This is the single biggest tell that an "AI portfolio repo" is fake — confident numbers with no provenance.
