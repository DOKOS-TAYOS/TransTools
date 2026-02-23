"""Custom exceptions for TransTools."""


class TransToolsError(Exception):
    """Base exception for TransTools application errors."""

    pass


class RecordingError(TransToolsError):
    """Error during audio recording."""

    pass


class AnalysisError(TransToolsError):
    """Error during audio analysis."""

    pass


class DataStoreError(TransToolsError):
    """Error during data load/save operations."""

    pass


class ConfigError(TransToolsError):
    """Error in configuration."""

    pass
