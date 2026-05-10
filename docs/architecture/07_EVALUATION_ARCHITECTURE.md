# 07 — EVALUATION_ARCHITECTURE.md

## Core abstractions

Two Protocols, both deliberately small.

```python
# evalkit/core/protocols.py

class Provider(Protocol):
    name: str
    async def complete(
        self,
        request: ProviderRequest,
        *,
        timeout_s: float,
    ) -> ProviderResponse: ...

class Evaluator(Protocol):
    name: str
    version: str
    def evaluate(
        self,
        case: Case,
        response: ProviderResponse,
    ) -> Evaluation: ...
```

`Evaluator.evaluate` is **synchronous and pure** by default. An evaluator that needs I/O (like `llm_judge`) wraps an internal async call but exposes a sync surface that runs `asyncio.run` only when not already in a loop. Most evaluators don't need I/O at all; making the common case sync keeps the test surface trivial.

## Built-in evaluators (v1)

| Name | Inputs | Output | Notes |
|---|---|---|---|
| `exact_match` | `expected.text`, `actual.text`, optional `case_insensitive`, `strip` | `passed`, `score ∈ {0,1}` | Cheap, deterministic, the right baseline. |
| `contains` | `expected.must_contain: List[str]` | `passed`, `score = matched/total` | Substring containment. |
| `regex_match` | `pattern`, `flags` | `passed`, `score ∈ {0,1}` | Captures named groups in `details`. |
| `json_schema` | `schema` (JSON Schema doc) | `passed`, `score ∈ {0,1}` | For tool-calling / structured output. Uses `jsonschema`. |
| `cosine_similarity` | `embedding_model`, `expected.text`, `threshold` | `score ∈ [0,1]`, `passed = score >= threshold` | Embeddings via configured provider. |
| `llm_judge` | `judge_model`, `rubric_path`, `pass_threshold` | `score ∈ [0,1]`, `passed`, structured rubric scores in `details` | Rubric is markdown with explicit dimensions. |

Each evaluator declares `version: str` (e.g. `"1.0"`). Bumping the version is required when scoring behavior changes; old runs preserve the old version string for fair comparisons.

## Scoring

- **Per-evaluator** `score ∈ [0, 1]` and `passed: bool`. Mixing scales is forbidden; it makes aggregation unintelligible.
- **Per-case aggregate** is the **product of `passed`** over evaluators (i.e., a case passes only if every evaluator passes). Average score is reported alongside but never used as the gate.
- **Per-run aggregate** is the pass-rate across cases per `(model, evaluator)`. The "headline" pass rate is the per-case pass rate.

Why pass rate and not score average: score averages reward partial credit and hide regressions in tail cases. Pass rate is what humans actually argue about in PR review.

## Regression detection (`compare`)

Given runs A (baseline) and B (current):

1. Match cases by `case_id`. Cases present in only one run are reported separately, not silently dropped.
2. For each `(case_id, model_id, evaluator_name)`:
   - **Newly failing**: passed in A, failed in B. *Headline regression.*
   - **Newly passing**: failed in A, passed in B. *Improvement.*
   - **Score regression**: passed in both, but `score(B) < score(A) - threshold`. Soft signal.
   - **Latency regression**: `p95(B) > p95(A) * (1 + tolerance)`. Reported, never gates by default.
3. Exit code rules in `--baseline` mode:
   - Any `newly failing` → exit 1.
   - Score regressions and latency regressions do not gate by default. They can be gated explicitly via `run.regression_gates` in the suite.

The diff output (markdown) includes a one-line summary, a regressions table, an improvements table, and per-case drill-down for regressions.

## Pluggability

Evaluators are discovered through:

1. Built-in registry (hard-coded list).
2. Python entry-point group `evalkit.evaluators`. Third-party packages register their evaluators by entry-point; users `pip install evalkit-myorg-evaluators` and reference them by name.

We do **not** support arbitrary code in suite YAML (no `python: import …`). It's a security risk and an anti-pattern; if you need custom logic, write a package.

## LLM-as-judge details

`llm_judge` is the most error-prone evaluator. Discipline:

- Rubric is markdown with explicit numbered dimensions (e.g., factuality, conciseness, format adherence). Each dimension is scored 0–4 by the judge; dimensions are averaged and normalized to `[0,1]`.
- Judge prompt is fixed in code; rubric content is the only user-controlled input. This keeps prompt-injection surface narrow.
- Judge calls retry with the same policy as primary calls.
- Judge model id is recorded with each evaluation, so old runs are interpretable when you upgrade judges.

A worked rubric example ships in `_resources/rubrics/quality.md` as part of `evalkit init`.

## Determinism stance

We do not promise deterministic provider responses (we don't control the provider). We *do* promise:

- Deterministic case ordering.
- Deterministic ID generation given the same inputs.
- Deterministic markdown report given the same DB state.
- Deterministic test suite (CI uses `mock` provider exclusively; real-provider tests are opt-in via env flag, never gating).

## Anti-features

- No "auto-improve your prompt" feature. That belongs in a different tool.
- No automatic dataset generation. Data quality is the user's responsibility; we are the inspector, not the generator.
- No silent retries that hide failures from the report. Every retry is recorded.
- No global "passed=true if score > 0.5" defaults. Thresholds are explicit per evaluator.
