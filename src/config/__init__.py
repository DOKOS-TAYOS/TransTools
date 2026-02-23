"""Configuration module for TransTools."""

from config.constants import __version__
from config.env import (
    get_current_env_values,
    get_env_from_schema,
    initialize_and_validate_config,
    write_env_file,
)
from config.paths import get_audio_dir, get_data_file_path, get_output_dir
from config.theme import UI_STYLE, refresh_theme

__all__ = [
    "__version__",
    "get_current_env_values",
    "get_env_from_schema",
    "initialize_and_validate_config",
    "write_env_file",
    "get_audio_dir",
    "get_data_file_path",
    "get_output_dir",
    "UI_STYLE",
    "refresh_theme",
]
