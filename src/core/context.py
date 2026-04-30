"""Application service singleton context."""

from __future__ import annotations

from .service import AppService

_SERVICE: AppService | None = None


def get_app_service() -> AppService:
    """Return process-wide AppService singleton."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = AppService()
    return _SERVICE
