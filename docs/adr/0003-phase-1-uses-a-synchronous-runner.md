# ADR-0003: Phase 1 ships a synchronous runner; concurrency lands in Phase 2

* Status: Accepted
* Date: 2026-05-10
* Phase: 1
* Supersedes: -
* Superseded-by: -

## Context

The evaluation architecture document (`docs/architecture/07_EVALUATION_ARCHITECTURE.md`)
describes a runner that calls providers concurrently, governed by a per-suite
`run.concurrency` knob, with retries and timeouts. The phased roadmap
(`docs/architecture/21_PHASED_ROADMAP.md`) places that runner in Phases 2-4
alongside the first real provider, the retry policy, and the cache.

Phase 1's only provider is the deterministic `MockProvider`. It has no I/O —
it is a pure dictionary lookup with an optional `time.sleep` for latency
shaping in tests. There is no race condition surface to test, no rate limit to
back off from, and no API key to misuse.

## Decision

The Phase 1 runner is **synchronous and single-threaded**. It walks the
`suite x dataset x evaluators` matrix in a deterministic order:

1. Persist suite + dataset snapshots.
2. Open a `running` row in `runs`.
3. For each `(case, model)` pair: call the provider, record the case row, run
   each evaluator in order, record the evaluation rows.
4. Aggregate counts and write the terminal status.

The `run.concurrency` field exists in the suite schema (it is part of the
public contract) but Phase 1 ignores it. The `Provider` protocol exposes a
synchronous `complete()` rather than a coroutine.

## Alternatives considered

1. **Ship the async/concurrent runner in Phase 1.** Rejected: it adds
   `asyncio` plumbing, semaphore management, ordering tests, and timeout
   handling that no caller currently exercises. With one in-process mock
   provider, concurrency is overhead with no observable benefit.
2. **Synchronous runner in Phase 1, then a parallel async runner in Phase 2.**
   Rejected: maintaining two runners is a maintenance hazard; the protocol
   would need both shapes; "is this a sync or async evaluator?" would become a
   question in every PR.
3. **Synchronous now, swap to a single async runner in Phase 2.** **Accepted.**
   The seam is the `Provider.complete` signature. Promoting it to async at the
   same time as we add the first real provider keeps the change atomic and
   makes the migration visible in one PR rather than two.

## Consequences

* `run.concurrency` is documented as effective from Phase 2 onward.
* Tests are simpler: no `pytest-asyncio`, no event-loop fixtures, deterministic
  ordering without sorting.
* Phase 2 will be a non-trivial diff: it changes the `Provider` protocol to
  async and rewires the runner. ADR-0003 will be referenced from that PR's
  description so the rationale is visible at review time.
* The 91% Phase-1 coverage on the runner is meaningful because there are no
  hidden async paths.
