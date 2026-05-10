"""ULID helper tests."""

from __future__ import annotations

import pytest

from evalkit.core.ids import new_id


@pytest.mark.unit
def test_new_id_is_26_char_string() -> None:
    value = new_id()
    assert isinstance(value, str)
    assert len(value) == 26


@pytest.mark.unit
def test_new_id_is_unique_across_calls() -> None:
    seen = {new_id() for _ in range(1000)}
    assert len(seen) == 1000
