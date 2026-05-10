"""Suite (YAML) and dataset (JSONL) loaders.

Both loaders translate Pydantic `ValidationError` to our `SuiteValidationError`
/ `DatasetValidationError` so the rest of the codebase can `except` on the
EvalKit hierarchy without touching Pydantic.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from evalkit.core.models import Dataset, DatasetItem, Suite
from evalkit.errors import DatasetValidationError, SuiteValidationError
from evalkit.storage.repo import hash_file


def load_suite(path: Path) -> tuple[Suite, str]:
    """Load and validate a suite YAML file.

    Returns a `(Suite, yaml_text)` pair so callers can persist the original
    bytes alongside the parsed model (per the suite-snapshot policy in the
    schema doc).
    """
    yaml_text = path.read_text(encoding="utf-8")
    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise SuiteValidationError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise SuiteValidationError(f"{path}: suite must be a YAML mapping")
    try:
        suite = Suite.model_validate(raw)
    except ValidationError as exc:
        raise SuiteValidationError(f"{path}: {exc.errors(include_url=False)}") from exc
    return suite, yaml_text


def load_dataset(path: Path) -> Dataset:
    """Load and validate a JSONL dataset file."""
    items: list[DatasetItem] = []
    case_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetValidationError(f"{path}:{line_no}: invalid JSON: {exc.msg}") from exc
            try:
                item = DatasetItem.model_validate(row)
            except ValidationError as exc:
                raise DatasetValidationError(
                    f"{path}:{line_no}: {exc.errors(include_url=False)}"
                ) from exc
            if item.case_id in case_ids:
                raise DatasetValidationError(
                    f"{path}:{line_no}: duplicate case_id {item.case_id!r}"
                )
            case_ids.add(item.case_id)
            items.append(item)
    if not items:
        raise DatasetValidationError(f"{path}: dataset is empty")
    return Dataset(path=str(path), sha256=hash_file(path), items=items)
