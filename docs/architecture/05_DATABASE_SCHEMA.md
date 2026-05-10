# 05 — DATABASE_SCHEMA.md

## Storage choice

SQLite, single file, default path `~/.evalkit/evalkit.db` (configurable). WAL mode enabled. SQLAlchemy 2.x ORM, Alembic migrations. Postgres is a future swap, not a v1 dependency.

## Identity

All primary keys are **ULIDs** rendered as 26-char strings. Reasons: sortable by creation time, no auto-increment coupling, safe to expose, easy to grep in logs.

## Tables

### `suites`

Snapshots of suite YAML at run time. We never trust the on-disk file to remain unchanged.

| Column | Type | Notes |
|---|---|---|
| id | TEXT PRIMARY KEY | ULID |
| name | TEXT NOT NULL | from YAML `name` |
| version | INTEGER NOT NULL | from YAML `version` |
| yaml_text | TEXT NOT NULL | exact original YAML, post-resolution |
| yaml_sha256 | TEXT NOT NULL | for dedup |
| created_at | TIMESTAMP NOT NULL | UTC |

Index: `(yaml_sha256)` unique.

### `datasets`

Snapshots of dataset content hash (we don't copy rows; we hash them).

| Column | Type | Notes |
|---|---|---|
| id | TEXT PK | ULID |
| path | TEXT NOT NULL | as referenced from suite |
| sha256 | TEXT NOT NULL | streaming hash of file bytes |
| row_count | INTEGER NOT NULL |
| created_at | TIMESTAMP NOT NULL |

Index: `(sha256)` unique.

### `runs`

| Column | Type | Notes |
|---|---|---|
| id | TEXT PK | ULID, this is the human-shareable `run_id` |
| suite_id | TEXT FK suites.id |
| dataset_id | TEXT FK datasets.id |
| started_at | TIMESTAMP NOT NULL |
| finished_at | TIMESTAMP | NULL while in progress / on crash |
| status | TEXT NOT NULL | `running`, `passed`, `failed`, `error`, `aborted` |
| exit_code | INTEGER | populated on finish |
| evalkit_version | TEXT NOT NULL |
| python_version | TEXT NOT NULL |
| host_os | TEXT NOT NULL |
| git_sha | TEXT | best-effort capture |
| ci_provider | TEXT | `github`, `local`, etc. |
| baseline_run_id | TEXT FK runs.id | null unless `--baseline` was used |

Indexes: `(status)`, `(started_at DESC)`, `(suite_id)`.

### `cases`

One row per `(run_id, case_index, model_id)` — the unit of inference.

| Column | Type | Notes |
|---|---|---|
| id | TEXT PK | ULID |
| run_id | TEXT FK runs.id |
| case_index | INTEGER NOT NULL | position in dataset |
| case_id | TEXT NOT NULL | from dataset row, or derived hash |
| model_id | TEXT NOT NULL |
| provider | TEXT NOT NULL |
| input_json | TEXT NOT NULL | the prompt/messages as JSON |
| output_text | TEXT | NULL if errored |
| output_json | TEXT | structured response (tool calls, etc.) |
| latency_ms | INTEGER |
| tokens_prompt | INTEGER |
| tokens_completion | INTEGER |
| cost_usd | REAL | best-effort from LiteLLM |
| status | TEXT NOT NULL | `ok`, `error`, `timeout`, `skipped` |
| error_kind | TEXT | populated on error |
| error_message | TEXT |
| attempts | INTEGER NOT NULL DEFAULT 1 |

Indexes: `(run_id)`, `(run_id, model_id)`, `(status)`.

Note: the raw provider response payload is stored gzipped in a sibling table `case_blobs(case_id, gz BLOB)` to keep the main table indexable and small.

### `case_blobs`

| Column | Type | Notes |
|---|---|---|
| case_id | TEXT PK FK cases.id |
| gz | BLOB NOT NULL | gzipped raw provider JSON response |

### `evaluations`

One row per `(case_id, evaluator_name)`.

| Column | Type | Notes |
|---|---|---|
| id | TEXT PK | ULID |
| case_id | TEXT FK cases.id |
| evaluator_name | TEXT NOT NULL |
| evaluator_version | TEXT NOT NULL |
| score | REAL NOT NULL | normalized to [0, 1] when meaningful |
| passed | BOOLEAN NOT NULL |
| details_json | TEXT | evaluator-specific details (rubric scores, regex group, etc.) |
| duration_ms | INTEGER NOT NULL |
| error_message | TEXT |

Indexes: `(case_id)`, `(evaluator_name, passed)`.

### `baselines`

A baseline is just a labelled pointer to a run. We do not denormalize.

| Column | Type | Notes |
|---|---|---|
| label | TEXT PK | e.g. `current`, `prod`, `nightly` |
| run_id | TEXT FK runs.id |
| set_at | TIMESTAMP NOT NULL |
| set_by | TEXT | username or CI actor |

### `cache`

Optional response cache.

| Column | Type | Notes |
|---|---|---|
| key | TEXT PK | sha256 of `(provider, model_id, prompt_canonical, params_canonical)` |
| response_gz | BLOB NOT NULL |
| usage_json | TEXT NOT NULL |
| created_at | TIMESTAMP NOT NULL |
| size_bytes | INTEGER NOT NULL |

LRU eviction managed in code, not SQL.

## Migrations

- Alembic, autogenerate with manual review.
- Every migration has both `upgrade()` and `downgrade()`.
- Initial migration in Phase 1 establishes the entire schema above. We do not ship "evolutionary" migrations during v1 development; we ship one clean initial migration when v1 stabilizes.
- A migration is required for every schema change; never edit an old migration after release.
- `evalkit storage upgrade` runs migrations on a user's DB.

## Sizing

Conservative back-of-envelope: 10k cases × 4 evaluators per run, 2KB avg payload (gzipped). 10 runs/day × 30 days = 1.2 GB/year. Well within SQLite's comfort zone.

## Concurrency

WAL mode + single-writer assumption. The runner is the only writer during a run; readers (CLI `show`, `list`, `report`) use a fresh connection. We do not need `PRAGMA busy_timeout` heroics; if a future use case demands multi-writer, that's the trigger to move to Postgres.

## Privacy

- We store prompts and completions verbatim. Users with PII concerns must scrub upstream — we are explicit about this in `docs/user/faq.md` and in `SECURITY.md`.
- A future opt-in flag `storage.redact_prompts: true` can hash inputs instead of storing them. Out of v1 scope.
