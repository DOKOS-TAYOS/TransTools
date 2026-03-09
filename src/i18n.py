"""Internationalization for TransTools."""

import json
from pathlib import Path

from config.env import get_env_from_schema

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
_CACHE: dict[str, dict[str, str]] = {}
_DEFAULT_LANG = "es"
_current_lang = "es"


def _load_locale(lang: str) -> dict[str, str]:
    """Load locale from JSON file. Uses in-memory cache per language.

    Args:
        lang: Language code (e.g., 'es', 'en').

    Returns:
        Dictionary of translation key -> translated string.
    """
    if lang in _CACHE:
        return _CACHE[lang]
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        if lang == _DEFAULT_LANG:
            _CACHE[lang] = {}
            return {}
        return _load_locale(_DEFAULT_LANG)
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    _CACHE[lang] = data
    return data


def initialize_i18n() -> None:
    """Initialize i18n with current language from config.

    Reads LANGUAGE from environment schema and sets the active locale.
    """
    global _current_lang
    _current_lang = get_env_from_schema("LANGUAGE")


def t(key: str, **kwargs: str) -> str:
    """Translate key. Use {key} for interpolation.

    Args:
        key: Translation key (e.g., 'menu.title').
        **kwargs: Optional format placeholders for string interpolation.

    Returns:
        Translated string, or key if translation not found.
    """
    translations = _load_locale(_current_lang)
    text = translations.get(key, key)
    return text.format(**kwargs) if kwargs else text
