"""Export and import helpers for full local user profiles."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TypeAlias
from uuid import uuid4

from config.paths import get_output_dir
from core.privacy import VoicePrivacyService
from utils import DataStoreError, get_logger

logger = get_logger(__name__)

_EXPORT_PREFIX = "transtools_export_"
_REQUIRED_PROFILE_FILES: tuple[str, ...] = (
    "patient_profile.json",
    "patient_history.json",
    ".voice_metrics.key",
)
_OPTIONAL_PROFILE_DIRS: tuple[str, ...] = ("audio",)
ManagedEntryKind: TypeAlias = Literal["file", "dir"]
ManagedEntry: TypeAlias = tuple[ManagedEntryKind, str]


def export_user_profile(
    export_root: Path,
    source_dir: Path | None = None,
    now: datetime | None = None,
) -> Path:
    """Copy the managed user profile files into a timestamped export folder.

    Args:
        export_root: Folder chosen by the user for the export.
        source_dir: Optional profile source directory for tests.
        now: Optional fixed timestamp for deterministic tests.

    Returns:
        Created export directory path.

    Raises:
        DataStoreError: If required profile files are missing or copying fails.
    """
    source = (source_dir or get_output_dir()).expanduser().resolve()
    missing = _missing_required_files(source)
    if missing:
        raise DataStoreError(_missing_files_message(missing))

    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    destination_root = export_root.expanduser().resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    export_dir = destination_root / f"{_EXPORT_PREFIX}{timestamp}"
    if export_dir.exists():
        raise DataStoreError(f"La carpeta de exportación ya existe: {export_dir}")

    try:
        export_dir.mkdir(parents=False, exist_ok=False)
        for file_name in _REQUIRED_PROFILE_FILES:
            shutil.copy2(source / file_name, export_dir / file_name)
        for dir_name in _OPTIONAL_PROFILE_DIRS:
            source_path = source / dir_name
            if source_path.exists():
                shutil.copytree(source_path, export_dir / dir_name)
    except Exception as exc:
        logger.exception("Profile export failed: %s", exc)
        shutil.rmtree(export_dir, ignore_errors=True)
        raise DataStoreError(f"No se pudo exportar el perfil: {exc}") from exc

    return export_dir


def import_user_profile(import_dir: Path, target_dir: Path | None = None) -> None:
    """Replace the local managed profile files with a previously exported profile.

    Args:
        import_dir: Folder containing an exported profile bundle.
        target_dir: Optional local destination directory for tests.

    Raises:
        DataStoreError: If the import folder is incomplete or copying fails.
    """
    source = import_dir.expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise DataStoreError("La carpeta seleccionada no existe o no es válida.")

    missing = _missing_required_files(source)
    if missing:
        raise DataStoreError(_missing_files_message(missing))

    destination = (target_dir or get_output_dir()).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    try:
        _validate_import_bundle(source)
        _import_user_profile_transactionally(source, destination)
    except DataStoreError:
        raise
    except Exception as exc:
        logger.exception("Profile import failed: %s", exc)
        raise DataStoreError(f"No se pudo importar el perfil: {exc}") from exc


def delete_user_profile(target_dir: Path | None = None) -> None:
    """Delete all managed local user-profile files and directories.

    Args:
        target_dir: Optional local destination directory for tests.

    Raises:
        DataStoreError: If any managed path cannot be removed.
    """
    destination = (target_dir or get_output_dir()).expanduser().resolve()
    try:
        for file_name in _REQUIRED_PROFILE_FILES:
            (destination / file_name).unlink(missing_ok=True)
        for dir_name in _OPTIONAL_PROFILE_DIRS:
            shutil.rmtree(destination / dir_name, ignore_errors=True)
    except Exception as exc:
        logger.exception("Profile deletion failed: %s", exc)
        raise DataStoreError(f"No se pudo borrar el perfil: {exc}") from exc


def _managed_profile_entries() -> tuple[ManagedEntry, ...]:
    """Return managed files and directories that belong to one profile."""
    return (
        *(("file", file_name) for file_name in _REQUIRED_PROFILE_FILES),
        *(("dir", dir_name) for dir_name in _OPTIONAL_PROFILE_DIRS),
    )


def _validate_import_bundle(source: Path) -> None:
    """Validate that an imported bundle can be loaded before touching the target."""
    _load_json_dict(source / "patient_profile.json", "patient_profile.json")
    history_payload = _load_json_dict(source / "patient_history.json", "patient_history.json")
    privacy = _build_profile_privacy_service(source / ".voice_metrics.key")
    _validate_voice_history_tokens(history_payload, privacy)


def _load_json_dict(path: Path, label: str) -> dict[str, Any]:
    """Load one JSON file and ensure it contains a top-level object."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataStoreError(f"El archivo {label} no contiene JSON válido.") from exc
    except OSError as exc:
        raise DataStoreError(f"No se pudo leer el archivo {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DataStoreError(f"El archivo {label} no tiene el formato esperado.")
    return payload


def _build_profile_privacy_service(key_path: Path) -> VoicePrivacyService:
    """Build a privacy service from an imported bundle key file."""
    try:
        return VoicePrivacyService(key_path=key_path)
    except Exception as exc:
        raise DataStoreError("La clave local del perfil exportado no es válida.") from exc


def _validate_voice_history_tokens(
    history_payload: dict[str, Any],
    privacy: VoicePrivacyService,
) -> None:
    """Ensure encrypted voice rows can be decrypted with the imported key."""
    records = history_payload.get("records")
    if not isinstance(records, dict):
        raise DataStoreError("El historial exportado no tiene el formato esperado.")

    voice_rows = records.get("voice", [])
    if not isinstance(voice_rows, list):
        raise DataStoreError("El historial exportado no tiene el formato esperado.")

    for row in voice_rows:
        if not isinstance(row, dict):
            raise DataStoreError("El historial exportado no tiene el formato esperado.")
        token = row.get("tone_encrypted")
        if token in (None, ""):
            continue
        if not isinstance(token, str) or privacy.decrypt_metrics(token) is None:
            raise DataStoreError(
                "Las métricas de voz exportadas no se pueden descifrar con la clave incluida."
            )


def _import_user_profile_transactionally(source: Path, destination: Path) -> None:
    """Import a profile bundle with rollback if any managed replacement fails."""
    staged_root = (destination.parent / f".transtools_import_staged_{uuid4().hex}").resolve()
    backup_root = (destination.parent / f".transtools_import_backup_{uuid4().hex}").resolve()
    backed_up_items: list[ManagedEntry] = []
    applied_items: list[ManagedEntry] = []
    cleanup_transaction_root = True

    try:
        _stage_import_bundle(source, staged_root)
        _backup_existing_profile(
            destination=destination,
            backup_root=backup_root,
            backed_up_items=backed_up_items,
        )
        _apply_staged_bundle(
            staged_root=staged_root,
            destination=destination,
            applied_items=applied_items,
        )
    except Exception:
        try:
            _rollback_import(
                destination=destination,
                backup_root=backup_root,
                backed_up_items=backed_up_items,
                applied_items=applied_items,
            )
        except Exception as rollback_exc:
            cleanup_transaction_root = False
            logger.exception("Profile import rollback failed: %s", rollback_exc)
            raise DataStoreError(
                "No se pudo importar el perfil y tampoco restaurar el estado anterior. "
                f"Copia temporal disponible en: {backup_root}"
            ) from rollback_exc
        raise
    finally:
        if cleanup_transaction_root:
            shutil.rmtree(staged_root, ignore_errors=True)
            shutil.rmtree(backup_root, ignore_errors=True)


def _stage_import_bundle(source: Path, staged_root: Path) -> None:
    """Copy the imported bundle into a local staging directory first."""
    staged_root.mkdir(parents=True, exist_ok=False)
    for file_name in _REQUIRED_PROFILE_FILES:
        shutil.copy2(source / file_name, staged_root / file_name)
    for dir_name in _OPTIONAL_PROFILE_DIRS:
        source_path = source / dir_name
        if source_path.exists():
            shutil.copytree(source_path, staged_root / dir_name)


def _backup_existing_profile(
    destination: Path,
    backup_root: Path,
    backed_up_items: list[ManagedEntry],
) -> None:
    """Move existing managed profile paths into a backup area before replacing them."""
    backup_root.mkdir(parents=True, exist_ok=False)
    for kind, name in _managed_profile_entries():
        source_path = destination / name
        if not source_path.exists():
            continue
        backup_path = backup_root / name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.replace(backup_path)
        backed_up_items.append((kind, name))


def _apply_staged_bundle(
    staged_root: Path,
    destination: Path,
    applied_items: list[ManagedEntry],
) -> None:
    """Replace managed profile paths from the staged bundle."""
    for file_name in _REQUIRED_PROFILE_FILES:
        _replace_file(staged_root / file_name, destination / file_name)
        applied_items.append(("file", file_name))
    for dir_name in _OPTIONAL_PROFILE_DIRS:
        _replace_directory(staged_root / dir_name, destination / dir_name)
        applied_items.append(("dir", dir_name))


def _rollback_import(
    destination: Path,
    backup_root: Path,
    backed_up_items: list[ManagedEntry],
    applied_items: list[ManagedEntry],
) -> None:
    """Restore the managed profile paths that existed before a failed import."""
    for kind, name in reversed(applied_items):
        _remove_managed_path(destination / name, kind)

    for kind, name in backed_up_items:
        backup_path = backup_root / name
        if kind == "file":
            _replace_file(backup_path, destination / name)
        else:
            _replace_directory(backup_path, destination / name)


def _remove_managed_path(path: Path, kind: ManagedEntryKind) -> None:
    """Remove one managed path if present."""
    if kind == "dir":
        shutil.rmtree(path, ignore_errors=True)
        return
    path.unlink(missing_ok=True)


def _replace_file(source: Path, destination: Path) -> None:
    """Replace one managed file with an imported version."""
    temp_path = destination.with_name(f"{destination.name}.import_tmp")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path.unlink(missing_ok=True)
    shutil.copy2(source, temp_path)
    temp_path.replace(destination)


def _replace_directory(source: Path, destination: Path) -> None:
    """Replace one managed directory with an imported version or remove it when absent."""
    temp_path = destination.with_name(f"{destination.name}.import_tmp")
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)

    if source.exists():
        shutil.copytree(source, temp_path)

    if destination.exists():
        shutil.rmtree(destination, ignore_errors=True)

    if temp_path.exists():
        temp_path.replace(destination)


def _missing_required_files(base_dir: Path) -> list[str]:
    """Return the required profile files missing from a directory."""
    return [
        file_name for file_name in _REQUIRED_PROFILE_FILES if not (base_dir / file_name).exists()
    ]


def _missing_files_message(missing: list[str]) -> str:
    """Build a concise error message for incomplete profile bundles."""
    return "Faltan archivos necesarios del perfil: " + ", ".join(missing)
