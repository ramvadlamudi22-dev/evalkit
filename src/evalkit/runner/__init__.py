"""Run orchestration.

Phase 1 ships a synchronous, single-threaded runner. Bounded concurrency,
retries, and async live in Phases 2-4 once a real provider exists where
concurrency actually pays for the testing complexity it introduces.
"""

from evalkit.runner.execute import RunOutcome, run_suite

__all__ = ["RunOutcome", "run_suite"]
