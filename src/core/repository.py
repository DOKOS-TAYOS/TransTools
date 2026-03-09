"""Persistent state repository for TransTools."""

from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from config.paths import get_data_file_path, get_output_dir
from utils import DataStoreError, get_logger
from utils.datetime_utils import utc_now_iso

logger = get_logger(__name__)

SCHEMA_VERSION = 1
ISO_DATE = "%Y-%m-%d"


@dataclass(frozen=True)
class RepositoryPaths:
    """File paths used by the repository.

    Attributes:
        state_file: Main versioned state JSON file.
        legacy_file: Previous voice-focused JSON file.
    """

    state_file: Path
    legacy_file: Path


def _default_habit_catalog() -> list[dict[str, Any]]:
    """Default habit set for adaptive checklist."""
    return [
        {"id": "hidratarse", "name": "Beber agua suficiente", "kind": "fisico", "min_level": 1},
        {"id": "dormir", "name": "Dormir al menos 7 horas", "kind": "fisico", "min_level": 1},
        {"id": "caminar", "name": "Caminar 15-30 minutos", "kind": "fisico", "min_level": 1},
        {
            "id": "respirar",
            "name": "Ejercicio breve de respiración",
            "kind": "psicologico",
            "min_level": 1,
        },
        {
            "id": "diario",
            "name": "Escribir una nota breve del día",
            "kind": "psicologico",
            "min_level": 1,
        },
        {
            "id": "desconexion",
            "name": "Pausa sin pantallas de 20 minutos",
            "kind": "psicologico",
            "min_level": 2,
        },
        {"id": "estiramientos", "name": "Estiramientos suaves", "kind": "fisico", "min_level": 2},
        {"id": "alimentacion", "name": "Comida equilibrada", "kind": "fisico", "min_level": 2},
        {
            "id": "red_apoyo",
            "name": "Hablar con alguien de confianza",
            "kind": "psicologico",
            "min_level": 2,
        },
        {
            "id": "autocuidado",
            "name": "Actividad de autocuidado",
            "kind": "psicologico",
            "min_level": 3,
        },
    ]


def default_state() -> dict[str, Any]:
    """Create a new default state object.

    Returns:
        Default schema-compliant state dictionary.
    """
    now = utc_now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": now,
        "updated_at": now,
        "profile": {
            "first_name": "",
            "onboarding_completed": False,
            "created_at": None,
            "updated_at": None,
        },
        "health_config": {
            "next_medication_date": None,
            "medication_every_days": None,
            "medication_dose": None,
            "next_medical_visit_date": None,
            "next_psych_visit_date": None,
        },
        "records": {
            "voice": [],
            "medication": [],
            "visits": [],
            "other_events": [],
            "habits": [],
        },
        "habit_catalog": _default_habit_catalog(),
        "contacts": {"national": [], "regional": {}},
        "meta": {
            "last_habit_count": 3,
            "help_shown": False,
        },
    }


def _deep_merge_defaults(
    base: dict[str, Any],
    default: dict[str, Any],
) -> dict[str, Any]:
    """Merge missing keys from defaults recursively.

    Args:
        base: Existing state.
        default: Default state.

    Returns:
        Merged state dictionary.
    """
    merged = deepcopy(base)
    for key, value in default.items():
        if key not in merged:
            merged[key] = deepcopy(value)
            continue
        if isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key] = _deep_merge_defaults(merged[key], value)
    return merged


def _safe_json_load(path: Path) -> dict[str, Any]:
    """Load JSON from file with DataStoreError conversion."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.exception("Failed loading JSON from %s: %s", path, exc)
        raise DataStoreError(f"No se pudo cargar el estado: {exc}") from exc


class StateRepository:
    """Versioned JSON repository with atomic writes."""

    def __init__(self, paths: RepositoryPaths | None = None) -> None:
        """Initialize repository.

        Args:
            paths: Optional custom paths for testing.
        """
        if paths is None:
            out_dir = get_output_dir()
            paths = RepositoryPaths(
                state_file=(out_dir / "trans_tools_state.json"),
                legacy_file=get_data_file_path(),
            )
        self.paths = paths
        self.paths.state_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        """Load state from disk, creating it if needed.

        Returns:
            State dictionary.
        """
        if not self.paths.state_file.exists():
            state = default_state()
            state = self._apply_legacy_bootstrap_if_available(state)
            self.save(state)
            return state

        raw = _safe_json_load(self.paths.state_file)
        migrated = self._migrate(raw)
        if migrated != raw:
            self.save(migrated)
        return migrated

    def save(self, state: dict[str, Any]) -> None:
        """Persist state atomically.

        Args:
            state: State dictionary.
        """
        state["updated_at"] = utc_now_iso()
        payload = json.dumps(state, ensure_ascii=False, indent=2)
        dst = self.paths.state_file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                dir=str(dst.parent),
                encoding="utf-8",
                suffix=".tmp",
            ) as handle:
                handle.write(payload)
                tmp_name = handle.name
            Path(tmp_name).replace(dst)
        except Exception as exc:
            logger.exception("Atomic save failed: %s", exc)
            raise DataStoreError(f"No se pudo guardar el estado: {exc}") from exc

    def _migrate(self, state: dict[str, Any]) -> dict[str, Any]:
        """Apply lightweight migrations to current schema.

        Args:
            state: Raw loaded state.

        Returns:
            Migrated state.
        """
        if not isinstance(state, dict):
            logger.warning("Invalid state format found; resetting to defaults")
            return default_state()
        current = _deep_merge_defaults(state, default_state())
        current["schema_version"] = SCHEMA_VERSION
        return current

    def _apply_legacy_bootstrap_if_available(self, state: dict[str, Any]) -> dict[str, Any]:
        """Bootstrap from legacy voice JSON if present.

        Args:
            state: Fresh default state.

        Returns:
            Updated state with imported voice records if possible.
        """
        legacy = self.paths.legacy_file
        if not legacy.exists():
            return state

        try:
            data = _safe_json_load(legacy)
        except DataStoreError:
            return state

        imported = 0
        for date_key, day_data in data.items():
            day_dt = self._parse_legacy_day(date_key)
            if day_dt is None:
                continue
            audio = day_data.get("Audio", {})
            for sample_name, sample in audio.items():
                if sample_name == "Day Global" or not isinstance(sample, dict):
                    continue
                state["records"]["voice"].append(
                    {
                        "id": f"legacy_{date_key}_{sample_name.replace(' ', '_')}",
                        "recorded_at": f"{day_dt.isoformat()}T12:00:00Z",
                        "target_date": day_dt.isoformat(),
                        "energy_rms": float(sample.get("energy", 0.0)),
                        "mood_auto": {
                            "happy": float((sample.get("mood", [0.0, 0.0, 0.0]) + [0, 0, 0])[0]),
                            "sad": float((sample.get("mood", [0.0, 0.0, 0.0]) + [0, 0, 0])[1]),
                            "angry": float((sample.get("mood", [0.0, 0.0, 0.0]) + [0, 0, 0])[2]),
                        },
                        "mood_self": None,
                        "tone_encrypted": None,
                        "audio_saved_path": None,
                        "legacy_tone_plain": {
                            "pitch_mean_hz": float(sample.get("pitch_mean", 0.0)),
                            "pitch_std_hz": float(sample.get("pitch_std", 0.0)),
                            "pitch_min_hz": float(sample.get("pitch_min", 0.0)),
                            "pitch_max_hz": float(sample.get("pitch_max", 0.0)),
                        },
                    }
                )
                imported += 1
        if imported:
            logger.info("Imported %s legacy voice entries into state", imported)
        return state

    @staticmethod
    def _parse_legacy_day(value: str) -> date | None:
        """Parse legacy DD/MM/YYYY day key."""
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None
