"""Helpers for compatibility-safe text and identifier normalization."""

from __future__ import annotations

import unicodedata

_MOJIBAKE_MARKERS: tuple[str, ...] = ("Ã", "Â", "â")


def repair_mojibake_text(value: str) -> str:
    """Best-effort repair for common UTF-8/Latin-1 mojibake sequences."""
    if not any(marker in value for marker in _MOJIBAKE_MARKERS):
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return value


def normalize_habit_id(value: str) -> str:
    """Normalize persisted habit identifiers to a stable ASCII form."""
    repaired = repair_mojibake_text(value)
    normalized = unicodedata.normalize("NFKD", repaired)
    return normalized.encode("ascii", "ignore").decode("ascii")
