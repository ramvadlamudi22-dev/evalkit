"""Synchronous run executor.

Walks the suite x dataset x evaluators matrix, calling the provider for each
case and the evaluators for each response, and persists everything via `Repo`.
Exit-code semantics match docs/architecture/06_CLI_API_CONTRACT.md:

    0 — every case passes every evaluator
    1 — at least one case failed an evaluator
    2 — at least one case errored at the provider/storage layer

The runner does not call `sys.exit`; the CLI translates `RunOutcome.exit_code`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from evalkit.core.ids import new_id
from evalkit.core.models import (
    Dataset,
    DatasetItem,
    EvaluationRecord,
    ProviderRequest,
    Suite,
)
from evalkit.core.protocols import Evaluator, Provider
from evalkit.errors import ProviderError
from evalkit.evaluators import get_evaluator
from evalkit.providers import get_provider
from evalkit.storage.repo import Repo


@dataclass(frozen=True)
class RunOutcome:
    """Summary returned by `run_suite` for the CLI to render and exit on."""

    run_id: str
    case_count: int
    pass_count: int
    fail_count: int
    error_count: int
    exit_code: int


def run_suite(
    *,
    suite: Suite,
    suite_yaml_text: str,
    suite_path: Path,
    dataset: Dataset,
    repo: Repo,
    provider_overrides: dict[str, Provider] | None = None,
) -> RunOutcome:
    """Execute one suite end-to-end and persist results.

    `provider_overrides` lets tests inject pre-built providers (e.g. a
    `MockProvider` with an inline mapping); production code constructs
    providers by name via the registry.
    """
    suite_id = repo.upsert_suite(suite, yaml_text=suite_yaml_text)
    dataset_id = repo.upsert_dataset(
        path=str(suite_path.parent / suite.dataset)
        if not Path(suite.dataset).is_absolute()
        else suite.dataset,
        sha256=dataset.sha256,
        row_count=len(dataset.items),
    )
    run_id = repo.start_run(suite_id=suite_id, dataset_id=dataset_id)

    overrides = provider_overrides or {}
    providers = _build_providers(suite, overrides)
    evaluators = [_build_evaluator(spec.model_dump()) for spec in suite.evaluators]

    pass_count = 0
    fail_count = 0
    error_count = 0
    case_index = 0

    for item in dataset.items:
        for model in suite.models:
            provider = providers[model.id]
            case_outcome = _run_case(
                run_id=run_id,
                case_index=case_index,
                item=item,
                model_id=model.id,
                provider_name=model.provider,
                provider=provider,
                evaluators=evaluators,
                params=model.params,
                timeout_s=suite.run.per_call_timeout_seconds,
                repo=repo,
            )
            case_index += 1
            if case_outcome == "ok":
                pass_count += 1
            elif case_outcome == "failed":
                fail_count += 1
            else:
                error_count += 1

    if error_count:
        status, exit_code = "error", 2
    elif fail_count:
        status, exit_code = "failed", 1
    else:
        status, exit_code = "passed", 0
    repo.finish_run(run_id, status=status, exit_code=exit_code)

    return RunOutcome(
        run_id=run_id,
        case_count=case_index,
        pass_count=pass_count,
        fail_count=fail_count,
        error_count=error_count,
        exit_code=exit_code,
    )


# ----- internals ----------------------------------------------------------


def _build_providers(suite: Suite, overrides: dict[str, Provider]) -> dict[str, Provider]:
    out: dict[str, Provider] = {}
    for model in suite.models:
        if model.id in overrides:
            out[model.id] = overrides[model.id]
        else:
            out[model.id] = get_provider(model.provider)
    return out


def _build_evaluator(spec: dict[str, object]) -> Evaluator:
    name = str(spec.pop("name"))
    return get_evaluator(name, **spec)


def _run_case(
    *,
    run_id: str,
    case_index: int,
    item: DatasetItem,
    model_id: str,
    provider_name: str,
    provider: Provider,
    evaluators: list[Evaluator],
    params: dict[str, object],
    timeout_s: float,
    repo: Repo,
) -> str:
    """Run one (case, model) pair. Returns "ok" | "failed" | "error"."""
    request = ProviderRequest(
        model_id=model_id,
        messages=item.input.messages,
        params={**params, "_case_id": item.case_id},
    )
    started = time.perf_counter()
    try:
        response = provider.complete(request, timeout_s=timeout_s)
    except ProviderError as exc:
        # Provider failure: record the case as errored and skip evaluators.
        repo.record_case(
            run_id,
            item=item,
            case_index=case_index,
            model_id=model_id,
            provider=provider_name,
            output_text=None,
            latency_ms=int((time.perf_counter() - started) * 1000),
            status="error",
            error_kind=type(exc).__name__,
            error_code=exc.code,
            error_message=exc.user_message(),
        )
        return "error"

    case_pk = repo.record_case(
        run_id,
        item=item,
        case_index=case_index,
        model_id=model_id,
        provider=provider_name,
        output_text=response.text,
        latency_ms=response.latency_ms,
        status="ok",
    )

    all_passed = True
    any_evaluator_ran = False
    for evaluator in evaluators:
        evaluation = evaluator.evaluate(item, response, evaluation_id=new_id())
        # Stamp the storage-level case_id onto the evaluation before persisting.
        evaluation = EvaluationRecord(**{**evaluation.model_dump(), "case_id": case_pk})
        repo.record_evaluation(evaluation)
        any_evaluator_ran = True
        if not evaluation.passed:
            all_passed = False

    return "ok" if (any_evaluator_ran and all_passed) else "failed"
