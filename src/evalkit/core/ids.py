"""ULID helpers.

ULIDs are 26-char Crockford-base32 strings. They are time-sortable and safe to
expose. We use a single helper to keep ID generation consistent across modules.
"""

from __future__ import annotations

from ulid import ULID


def new_id() -> str:
    """Return a new ULID as a 26-char string."""
    return str(ULID())
