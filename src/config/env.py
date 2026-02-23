"""Environment variable loading and .env schema for TransTools."""

import os
from pathlib import Path
from typing import Any, Type, Union

from config.constants import (
    LANGUAGE_ALIASES,
    SUPPORTED_LANGUAGE_CODES,
    VALID_LANGUAGE_INPUTS,
)

_EnvCastType = Type[Union[str, int, float, bool]]

try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path, override=True)
except ImportError:
    pass


def _validate_env_value(
    key: str,
    value: Any,
    schema_item: dict[str, Any],
) -> tuple[bool, Any]:
    """Validate env value against schema.

    Args:
        key: Environment variable name.
        value: Raw value to validate.
        schema_item: Schema entry with default, cast_type, options, etc.

    Returns:
        Tuple of (is_valid, corrected_value). If invalid, corrected_value is default.
    """
    default = schema_item["default"]
    cast_type = schema_item["cast_type"]

    if value is None:
        return False, default

    if key == "LANGUAGE" and cast_type is str:
        try:
            lang_lower = str(value).strip().lower()
            if lang_lower not in VALID_LANGUAGE_INPUTS:
                return False, default
            normalized = LANGUAGE_ALIASES.get(lang_lower, lang_lower)
            return True, normalized
        except (AttributeError, TypeError, ValueError):
            return False, default

    if key == "LOG_LEVEL" and cast_type is str:
        try:
            s = str(value).strip().upper()
            if s not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
                return False, default
            return True, s
        except (AttributeError, TypeError, ValueError):
            return False, default

    if "options" in schema_item:
        opts = schema_item["options"]
        try:
            if cast_type is str:
                if str(value).lower() not in [o.lower() for o in opts]:
                    return False, default
            elif value not in opts:
                return False, default
        except (AttributeError, TypeError, ValueError):
            return False, default

    if cast_type is int:
        try:
            iv = int(value)
            if key in (
                "UI_PADDING",
                "UI_BUTTON_WIDTH",
                "UI_BUTTON_WIDTH_WIDE",
                "UI_FONT_SIZE",
                "RECORD_DURATION_SEC",
            ):
                if iv <= 0 or (key == "RECORD_DURATION_SEC" and iv > 300):
                    return False, default
        except (TypeError, ValueError, OverflowError):
            return False, default

    if cast_type is str and key not in ("DONATIONS_URL",):
        try:
            if not str(value).strip():
                return False, default
        except (AttributeError, TypeError):
            return False, default

    return True, value


ENV_SCHEMA: list[dict[str, Any]] = [
    {"key": "LANGUAGE", "default": "es", "cast_type": str, "options": SUPPORTED_LANGUAGE_CODES},
    {"key": "UI_BACKGROUND", "default": "#181818", "cast_type": str},
    {"key": "UI_FOREGROUND", "default": "#CCCCCC", "cast_type": str},
    {"key": "UI_BUTTON_BG", "default": "#1F1F1F", "cast_type": str},
    {"key": "UI_BUTTON_WIDTH", "default": 12, "cast_type": int},
    {"key": "UI_BUTTON_WIDTH_WIDE", "default": 20, "cast_type": int},
    {"key": "UI_BUTTON_FG", "default": "lime green", "cast_type": str},
    {"key": "UI_BUTTON_FG_CANCEL", "default": "red2", "cast_type": str},
    {"key": "UI_BUTTON_FG_ACCENT2", "default": "yellow", "cast_type": str},
    {"key": "UI_FONT_SIZE", "default": 18, "cast_type": int},
    {"key": "UI_FONT_FAMILY", "default": "Bahnschrift", "cast_type": str},
    {"key": "UI_PADDING", "default": 8, "cast_type": int},
    {"key": "FILE_OUTPUT_DIR", "default": "output", "cast_type": str},
    {"key": "FILE_DATA_FORMAT", "default": "json", "cast_type": str, "options": ("json",)},
    {"key": "SAVE_AUDIO", "default": True, "cast_type": bool},
    {"key": "RECORD_DURATION_SEC", "default": 10, "cast_type": int},
    {
        "key": "LOG_LEVEL",
        "default": "INFO",
        "cast_type": str,
        "options": ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    },
    {"key": "LOG_FILE", "default": "transtools.log", "cast_type": str},
    {"key": "LOG_CONSOLE", "default": True, "cast_type": bool},
]

_ENV_SCHEMA_BY_KEY: dict[str, dict[str, Any]] = {i["key"]: i for i in ENV_SCHEMA}


def get_env(
    key: str,
    default: Any,
    cast_type: _EnvCastType = str,
) -> Union[str, int, float, bool]:
    """Get env var with casting and validation.

    Args:
        key: Environment variable name.
        default: Default value if not set or invalid.
        cast_type: Type to cast value to (str, int, float, bool).

    Returns:
        Cast and validated value.
    """
    value = os.getenv(key)
    if value is None:
        return default

    schema_item = _ENV_SCHEMA_BY_KEY.get(key)
    if schema_item is None:
        try:
            if cast_type is bool:
                return value.lower() in ("true", "1", "yes")
            return cast_type(value)
        except (ValueError, TypeError):
            return default

    try:
        if cast_type is bool:
            casted_value = value.lower() in ("true", "1", "yes")
        else:
            casted_value = cast_type(value)
    except (ValueError, TypeError):
        return default

    _, corrected = _validate_env_value(key, casted_value, schema_item)
    return corrected


def get_env_from_schema(key: str) -> Any:
    """Get env var using schema defaults.

    Args:
        key: Environment variable name (must exist in ENV_SCHEMA).

    Returns:
        Value from env or schema default.

    Raises:
        KeyError: If key is not in ENV_SCHEMA.
    """
    item = _ENV_SCHEMA_BY_KEY.get(key)
    if item is None:
        raise KeyError(f"Unknown env key: {key}")
    return get_env(key, item["default"], item["cast_type"])


def get_current_env_values() -> dict[str, str]:
    """Current env values as strings for writing to .env.

    Returns:
        Dictionary of key -> string value for all schema keys.
    """
    result: dict[str, str] = {}
    for item in ENV_SCHEMA:
        key, default, cast_type = item["key"], item["default"], item["cast_type"]
        val = get_env(key, default, cast_type)
        if cast_type is bool:
            result[key] = "true" if val else "false"
        else:
            result[key] = str(val)
    return result


def write_env_file(env_path: Path, values: dict[str, str]) -> None:
    """Write .env file with key=value pairs.

    Args:
        env_path: Path to .env file.
        values: Dictionary of key -> value strings.
    """
    lines = [
        "# TransTools Configuration",
        "# Edit this file or use the configuration dialog.",
        "",
    ]
    for item in ENV_SCHEMA:
        key = item["key"]
        if key not in values:
            continue
        value = values[key].strip()
        if " " in value or "#" in value or "\n" in value:
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def initialize_and_validate_config() -> None:
    """Validate config at startup.

    Loads and validates all schema keys. Invalid values fall back to defaults.
    """
    try:
        from utils import get_logger

        logger = get_logger(__name__)
    except ImportError:
        logger = None

    for item in ENV_SCHEMA:
        get_env(item["key"], item["default"], item["cast_type"])

    if logger:
        logger.debug("Configuration validated")
