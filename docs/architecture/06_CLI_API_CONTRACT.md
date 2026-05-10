# 06 — CLI_API_CONTRACT.md

## Top-level

```
evalkit [OPTIONS] COMMAND [ARGS]...
```

Global options:

| Flag | Default | Effect |
|---|---|---|
| `--config PATH` | `./evalkit.toml` | Override config file. |
| `--db PATH` | `~/.evalkit/evalkit.db` | Override DB path. |
| `--log-level LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR. |
| `--log-format {auto,json,console}` | `auto` | `auto`= JSON when not a TTY. |
| `--no-color` | off | Disable ANSI in console output. |
| `--version` | — | Print `evalkit X.Y.Z`. |
| `--help` | — | Typer-generated help. |

Exit codes:

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | One or more evaluations failed (this is "the test failed", not a crash) |
| 2 | Infrastructure error (provider down after retries, DB unreachable, etc.) |
| 64 | Usage error (bad flags, missing file, schema validation failure) |
| 70 | Internal error (a bug — these should never happen in CI) |

These match the BSD sysexits convention where it makes sense.

## Commands

### `evalkit init [DIRECTORY]`

Scaffolds a starter project (suite.yaml, sample dataset, .env.example, README). Idempotent; refuses to overwrite without `--force`.

### `evalkit run SUITE [OPTIONS]`

Executes a suite.

| Flag | Effect |
|---|---|
| `--baseline LABEL_OR_RUN_ID` | Compare against this baseline; non-zero exit if regression. |
| `--filter EXPR` | Filter cases (e.g. `--filter 'tag=summarization'`). |
| `--max-cases N` | Cap dataset for fast iteration. |
| `--concurrency N` | Override suite concurrency. |
| `--cache {on,off,refresh}` | Default `on`. |
| `--dry-run` | Validate without calling providers. |
| `--report-format {markdown,json,none}` | Default `markdown`; print to stdout. |
| `--out PATH` | Write report to file instead of stdout. |
| `--seed INT` | Propagate to providers that accept seeds. |

### `evalkit list [OPTIONS]`

| Flag | Effect |
|---|---|
| `--limit N` | Default 20. |
| `--status FILTER` | `passed,failed,error,running,aborted`. |
| `--suite NAME` | Filter by suite name. |
| `--format {table,json}` | Default `table`. |

### `evalkit show RUN_ID [OPTIONS]`

Renders a single run.

| Flag | Effect |
|---|---|
| `--format {table,markdown,json}` | Default `table`. |
| `--cases` | Include per-case breakdown. |
| `--evaluator NAME` | Filter to one evaluator. |

### `evalkit compare RUN_A RUN_B [OPTIONS]`

Regression diff.

| Flag | Effect |
|---|---|
| `--format {markdown,json}` | Default `markdown`. |
| `--threshold FLOAT` | Score-delta threshold to flag (default 0.0). |
| `--out PATH` | Write to file. |

### `evalkit baseline {set,get,list,unset}`

```
evalkit baseline set <run_id> [--label LABEL]    # default label = "current"
evalkit baseline get [--label LABEL]
evalkit baseline list
evalkit baseline unset <label>
```

### `evalkit report RUN_ID [OPTIONS]`

Same renderer used by `run`, but standalone.

| Flag | Effect |
|---|---|
| `--format {markdown,json}` | Default `markdown`. |
| `--out PATH` | Write to file. |

### `evalkit storage {init,upgrade,downgrade,vacuum}`

Alembic wrappers + maintenance.

### `evalkit cache {info,clear}`

### `evalkit doctor`

Diagnostic. Prints: Python version, evalkit version, DB path & size, configured providers, missing API keys, suspected misconfiguration. Exit 0 if healthy.

## Suite YAML schema (v1)

```yaml
version: 1
name: summarization-quality
description: Eval pipeline for the news-summarization feature.

dataset: datasets/news.jsonl

models:
  - id: gpt-4o-mini
    provider: openai
    params:
      temperature: 0.0
      max_tokens: 256
  - id: claude-3-5-haiku-latest
    provider: anthropic
    params:
      temperature: 0.0

evaluators:
  - name: exact_match
    on_field: summary
  - name: cosine_similarity
    embedding_model: text-embedding-3-small
    threshold: 0.82
  - name: llm_judge
    judge_model: gpt-4o
    rubric_path: rubrics/quality.md
    pass_threshold: 0.75

run:
  concurrency: 8
  per_call_timeout_seconds: 30
  retry:
    max_attempts: 3
    backoff: exponential
    initial_seconds: 0.5
    max_seconds: 8
    retry_on:
      - provider.rate_limit
      - provider.transient
  cache: on
```

The schema is a Pydantic model with `version: Literal[1]`. Future versions are additive or bumped.

## Dataset JSONL schema

Each line:

```json
{
  "case_id": "news-001",
  "tags": ["summarization", "short"],
  "input": {
    "messages": [
      {"role": "system", "content": "You are a concise summarizer."},
      {"role": "user", "content": "<article>...</article>"}
    ]
  },
  "expected": {
    "summary": "Reference summary...",
    "must_contain": ["Q3 earnings"]
  },
  "metadata": {"source": "internal-corpus-v1"}
}
```

`case_id` is required and must be unique within a dataset.

## Stable interfaces

The following are part of the **public contract**; breaking changes require a major version bump:

- Suite YAML schema (versioned).
- Dataset JSONL row schema.
- CLI command names, flags, and exit codes.
- Markdown report top-level sections (the inner formatting can evolve).
- The `evalkit.evaluators` Python entry-point group used by external evaluator plugins.

Internal: SQLite schema, Pydantic class layouts, module imports beyond what `__init__` exports. We do not promise stability there.
