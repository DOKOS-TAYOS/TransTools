"""Path configuration for TransTools."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from config.env import get_env_from_schema
from utils import get_logger

logger = get_logger(__name__)

_LEGACY_DEFAULT_OUTPUT_DIR = "output"
_LEGACY_FILENAMES: tuple[str, ...] = (
    "patient_profile.json",
    "patient_history.json",
    ".voice_metrics.key",
    "trans_tools_data.json",
)


def _get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def _get_platform_default_output_dir() -> Path:
    """Return the user-scoped default data directory for this platform."""
    if sys.platform.startswith("win"):
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "TransTools"
        return Path.home() / "AppData" / "Roaming" / "TransTools"

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "transtools"
    return Path.home() / ".local" / "share" / "transtools"


def get_legacy_output_dir() -> Path:
    """Return the historical project-local output directory."""
    return (_get_project_root() / _LEGACY_DEFAULT_OUTPUT_DIR).resolve()


def migrate_legacy_output_dir(legacy_dir: Path, target_dir: Path) -> list[Path]:
    """Copy legacy output files into the new target directory once.

    Args:
        legacy_dir: Old project-local output directory.
        target_dir: New user-scoped output directory.

    Returns:
        List of migrated target file paths.
    """
    try:
        if legacy_dir.resolve() == target_dir.resolve():
            return []
    except FileNotFoundError:
        return []

    if not legacy_dir.exists():
        return []

    source_files = [legacy_dir / filename for filename in _LEGACY_FILENAMES]
    available_sources = [path for path in source_files if path.exists()]
    if not available_sources:
        return []

    target_dir.mkdir(parents=True, exist_ok=True)
    migrated: list[Path] = []
    skipped: list[Path] = []
    for source in available_sources:
        target = target_dir / source.name
        if target.exists():
            skipped.append(target)
            continue
        shutil.copy2(source, target)
        migrated.append(target)

    if migrated or skipped:
        logger.info(
            "Legacy output migration from %s to %s: copied=%s skipped=%s",
            legacy_dir,
            target_dir,
            len(migrated),
            len(skipped),
        )
    return migrated


def get_output_dir() -> Path:
    """Output directory (audios, data, plots).

    Returns:
        Resolved path to output directory from FILE_OUTPUT_DIR.
    """
    out = str(get_env_from_schema("FILE_OUTPUT_DIR")).strip()
    if not out or out == _LEGACY_DEFAULT_OUTPUT_DIR:
        return _get_platform_default_output_dir().resolve()

    output_path = Path(out).expanduser()
    if output_path.is_absolute():
        return output_path.resolve()
    return (_get_project_root() / output_path).resolve()


def get_data_file_path() -> Path:
    """Path to data file (JSON).

    Returns:
        Path to trans_tools_data.json in output dir.
    """
    out = get_output_dir()
    return out / "trans_tools_data.json"


def get_audio_dir() -> Path:
    """Directory for saved audio files.

    Returns:
        Path to output/audio subdirectory.
    """
    return get_output_dir() / "audio"


def get_patient_profile_path() -> Path:
    """Path to patient static data (profile, health config, etc).

    Returns:
        Path to patient_profile.json in output dir.
    """
    return get_output_dir() / "patient_profile.json"


def get_patient_history_path() -> Path:
    """Path to patient historical records (voice, medication, visits, etc).

    Returns:
        Path to patient_history.json in output dir.
    """
    return get_output_dir() / "patient_history.json"


def get_contacts_path() -> Path:
    """Path to contacts JSON (app-level, in src)."""
    base = Path(__file__).resolve().parent.parent
    return base / "data" / "contacts.json"
