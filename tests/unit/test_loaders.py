"""Suite + dataset loader tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalkit.errors import DatasetValidationError, SuiteValidationError
from evalkit.loaders import load_dataset, load_suite

VALID_SUITE = """
version: 1
name: t
dataset: data.jsonl
models:
  - id: m
    provider: mock
    params: {}
evaluators:
  - name: exact_match
"""

VALID_DATASET = (
    '{"case_id":"a","input":{"messages":[{"role":"user","content":"hi"}]},'
    '"expected":{"text":"hi"}}\n'
    '{"case_id":"b","input":{"messages":[{"role":"user","content":"yo"}]},'
    '"expected":{"text":"yo"}}\n'
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.unit
class TestLoadSuite:
    def test_loads_valid_suite(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "s.yaml", VALID_SUITE)
        suite, raw = load_suite(path)
        assert suite.name == "t"
        assert raw == VALID_SUITE

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "s.yaml", "name: [unbalanced")
        with pytest.raises(SuiteValidationError, match="invalid YAML"):
            load_suite(path)

    def test_yaml_must_be_a_mapping(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "s.yaml", "- a\n- b\n")
        with pytest.raises(SuiteValidationError, match="must be a YAML mapping"):
            load_suite(path)

    def test_validation_error_surfaced(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "s.yaml", "version: 1\nname: t\n")  # missing fields
        with pytest.raises(SuiteValidationError):
            load_suite(path)


@pytest.mark.unit
class TestLoadDataset:
    def test_loads_valid_dataset(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "d.jsonl", VALID_DATASET)
        ds = load_dataset(path)
        assert len(ds.items) == 2
        assert ds.items[0].case_id == "a"
        assert len(ds.sha256) == 64

    def test_empty_dataset_rejected(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "d.jsonl", "")
        with pytest.raises(DatasetValidationError, match="empty"):
            load_dataset(path)

    def test_invalid_json_line_pinpoints_line(self, tmp_path: Path) -> None:
        good = (
            '{"case_id":"a","input":{"messages":[{"role":"user","content":"x"}]},"expected":{}}\n'
        )
        path = _write(tmp_path, "d.jsonl", good + "{not json}\n")
        with pytest.raises(DatasetValidationError, match=":2:"):
            load_dataset(path)

    def test_duplicate_case_id_rejected(self, tmp_path: Path) -> None:
        dup = (
            '{"case_id":"a","input":{"messages":[{"role":"user","content":"x"}]},'
            '"expected":{}}\n'
            '{"case_id":"a","input":{"messages":[{"role":"user","content":"y"}]},'
            '"expected":{}}\n'
        )
        path = _write(tmp_path, "d.jsonl", dup)
        with pytest.raises(DatasetValidationError, match="duplicate case_id"):
            load_dataset(path)
