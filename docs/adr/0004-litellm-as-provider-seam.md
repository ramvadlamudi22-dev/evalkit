# ADR-0004: LiteLLM as the provider seam

- Status: accepted
- Date: 2025-11-26
- Deciders: maintainers
- Supersedes: --
- Related: ADR-0003 (sync runner in Phase 1; async in Phase 2)

## Context

Phase 2 needs **one** real provider to prove the end-to-end loop: load a suite, hit a real
model, score the response, persist results, repeat. The portfolio direction is multi-model
benchmarking, so the provider seam will eventually need OpenAI, Anthropic, local OpenAI-
compatible endpoints (Ollama, vLLM), and at least one regional vendor.

Three concrete options were on the table:

1. **Per-vendor SDKs (`openai`, `anthropic`, ...)** — direct, version-stable, but we'd need
   a multiplexer of our own (config -> dispatch -> normalise messages -> normalise errors).
   For a single provider it's ~200 lines; per new vendor it grows.
2. **A thin internal abstraction over an HTTP client** — least magic, but reinvents OpenAI's
   tool-call/streaming/usage formats. Not worth it in a portfolio project.
3. **LiteLLM** (`litellm.acompletion`) — provider router + unified request/response shape +
   unified exception hierarchy + per-provider timeout/retry hooks. We adopt the hierarchy
   and skip the multiplexer.

## Decision

Use **LiteLLM 1.x** as the provider seam. Adapt it in a single module
(`src/evalkit/providers/litellm_provider.py`) that:

- exposes EvalKit's `Provider` protocol (`async complete(request, *, timeout_s)`);
- translates a `ProviderRequest` to LiteLLM's `messages` shape via the existing Pydantic
  serialisers (no separate DTO layer);
- enforces a per-call deadline via `asyncio.wait_for(...)` even though LiteLLM has its own
  `timeout=` argument, so an unresponsive provider can't outlive the deadline even if the
  SDK's internal timer misses;
- accepts an injectable `acompletion` callable in the constructor so unit tests can drive
  the success/retry/timeout/error-classification paths deterministically without touching
  the network.

Exception classification happens **once**, at the LiteLLM seam, in `_classify_litellm_error`.
Everything else in EvalKit (runner, retry logic, logging, tests) sees the stable EvalKit
taxonomy: `AuthProviderError`, `RateLimitProviderError`, `TimeoutProviderError`,
`TransientProviderError`, `PermanentProviderError`, `ProviderConfigError`.

Retries live in this adapter via tenacity (see ADR-0005), so callers of `provider.complete`
get the post-retry result and never have to know the retry policy exists.

## Consequences

**Positive**

- One adapter, one error classifier, one retry policy. Adding a second provider is
  "register a model_id pattern with LiteLLM" + a row in the registry, not a new code path.
- Tests stay hermetic: CI never needs API keys. Constructor injection > monkey-patching the
  litellm module at runtime.
- Unified request/response shape means evaluators don't branch on provider.

**Negative / accepted risk**

- LiteLLM is a moderately thick dependency (~5 MB installed, transitively pulls
  `tokenizers`, `httpx`, `tiktoken`, etc.). Image size grew ~38 MB in Phase 1 already;
  Phase 2 adds another ~12 MB. Still within the 250 MB design budget.
- LiteLLM occasionally changes its exception module path between minor versions. We pin
  `litellm>=1.50,<2`, snapshot the exception classes we classify in the test file, and
  treat any unknown LiteLLM exception as `PermanentProviderError` (safer than running the
  retry budget on an unrecognised condition).
- We don't get OTel spans out of the box. The seam emits structured `provider.call` events
  via structlog; an OTel exporter plugs into the same call site in Phase 5.

## Alternatives considered

- **Direct `openai` + `anthropic` SDKs**: rejected for the multiplexer cost above.
- **Plugin / entry-point provider discovery**: rejected as premature. Phase 2 has two
  providers (`mock`, `litellm`); a static registry is fine until there are >4.
- **LangChain `BaseChatModel`**: rejected. Too thick, too many transitive deps, dictates
  more of the message/tool surface than we want this early, and would compete with our own
  `Suite`/`Dataset` schema.
