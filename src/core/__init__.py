"""Core domain services for TransTools.

This package intentionally avoids eager imports to keep startup light and
prevent importing heavy optional dependencies through transitive imports.
"""

__all__ = [
    "AppService",
    "StateRepository",
    "VoicePrivacyService",
    "VoiceAnalysisResult",
    "get_app_service",
    "export_to_csv",
    "export_to_excel",
    "export_to_pdf",
    "export_to_png",
]


def __getattr__(name: str):
    """Lazily expose common symbols without eager submodule imports."""
    if name == "AppService":
        from .service import AppService

        return AppService
    if name == "StateRepository":
        from .repository import StateRepository

        return StateRepository
    if name == "VoicePrivacyService":
        from .privacy import VoicePrivacyService

        return VoicePrivacyService
    if name == "VoiceAnalysisResult":
        from .types import VoiceAnalysisResult

        return VoiceAnalysisResult
    if name == "get_app_service":
        from .context import get_app_service

        return get_app_service
    if name in {"export_to_csv", "export_to_excel", "export_to_pdf", "export_to_png"}:
        from .exporters import (
            export_to_csv,
            export_to_excel,
            export_to_pdf,
            export_to_png,
        )

        return {
            "export_to_csv": export_to_csv,
            "export_to_excel": export_to_excel,
            "export_to_pdf": export_to_pdf,
            "export_to_png": export_to_png,
        }[name]
    raise AttributeError(name)
