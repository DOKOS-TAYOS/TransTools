"""Persistent state repository for TransTools."""

from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from config.paths import (
    get_data_file_path,
    get_legacy_output_dir,
    get_output_dir,
    get_patient_history_path,
    get_patient_profile_path,
    migrate_legacy_output_dir,
)
from utils import DataStoreError, get_logger
from utils.datetime_utils import utc_now_iso
from utils.text_normalization import normalize_habit_id

logger = get_logger(__name__)

SCHEMA_VERSION = 1
ISO_DATE = "%Y-%m-%d"
ATOMIC_SAVE_RETRIES = 5
ATOMIC_SAVE_RETRY_SECONDS = 0.05


@dataclass(frozen=True)
class RepositoryPaths:
    """File paths used by the repository.

    Attributes:
        profile_file: Patient static data (name, health config, appointments, etc).
        history_file: Patient historical records (voice, medication, visits, etc).
        legacy_file: Previous voice-focused JSON file for bootstrap.
    """

    profile_file: Path
    history_file: Path
    legacy_file: Path


def _default_habit_catalog() -> list[dict[str, Any]]:
    """Default habit set for adaptive checklist."""
    return _normalize_habit_catalog(
        [
            {"id": "hidratarse", "kind": "fisico", "min_level": 1},
            {"id": "dormir", "kind": "fisico", "min_level": 1},
            {"id": "caminar", "kind": "fisico", "min_level": 1},
            {"id": "respirar", "kind": "psicologico", "min_level": 1},
            {"id": "diario", "kind": "psicologico", "min_level": 1},
            {"id": "desconexion", "kind": "psicologico", "min_level": 2},
            {"id": "estiramientos", "kind": "fisico", "min_level": 2},
            {"id": "alimentacion", "kind": "fisico", "min_level": 2},
            {"id": "red_apoyo", "kind": "psicologico", "min_level": 2},
            {"id": "autocuidado", "kind": "psicologico", "min_level": 3},
            # Physical - Level 1
            {"id": "desayuno_saludable", "kind": "fisico", "min_level": 1},
            {"id": "subir_escaleras", "kind": "fisico", "min_level": 1},
            {"id": "postura_ergonomica", "kind": "fisico", "min_level": 1},
            {"id": "lavarse_dientes", "kind": "fisico", "min_level": 1},
            {"id": "dormir_horario", "kind": "fisico", "min_level": 1},
            {"id": "evitar_cafeina_tarde", "kind": "fisico", "min_level": 1},
            {"id": "comer_frutas", "kind": "fisico", "min_level": 1},
            {"id": "comer_verduras", "kind": "fisico", "min_level": 1},
            {"id": "evitar_azucar", "kind": "fisico", "min_level": 1},
            {"id": "comer_fibra", "kind": "fisico", "min_level": 1},
            {"id": "comer_lento", "kind": "fisico", "min_level": 1},
            {"id": "no_comer_tarde", "kind": "fisico", "min_level": 1},
            # Physical - Level 2
            {"id": "correr", "kind": "fisico", "min_level": 2},
            {"id": "yoga", "kind": "fisico", "min_level": 2},
            {"id": "pilates", "kind": "fisico", "min_level": 2},
            {"id": "estiramientos_mañana", "kind": "fisico", "min_level": 2},
            {"id": "cocinar_casero", "kind": "fisico", "min_level": 2},
            {"id": "merienda_saludable", "kind": "fisico", "min_level": 2},
            {"id": "evitar_alcohol", "kind": "fisico", "min_level": 2},
            {"id": "evitar_tabaco", "kind": "fisico", "min_level": 2},
            {"id": "revisar_medicacion", "kind": "fisico", "min_level": 2},
            # Physical - Level 3
            {"id": "entrenamiento_fuerza", "kind": "fisico", "min_level": 3},
            {"id": "sueno_consistente", "kind": "fisico", "min_level": 3},
            {"id": "rutina_nocturna", "kind": "fisico", "min_level": 3},
            # Psychological - Level 1
            {"id": "respirar_profundo", "kind": "psicologico", "min_level": 1},
            {"id": "escuchar_musica", "kind": "psicologico", "min_level": 1},
            {"id": "leer_10_min", "kind": "psicologico", "min_level": 1},
            {"id": "pausa_corta", "kind": "psicologico", "min_level": 1},
            {"id": "contacto_naturaleza", "kind": "psicologico", "min_level": 1},
            {"id": "decir_gracias", "kind": "psicologico", "min_level": 1},
            {"id": "felicitar_alguien", "kind": "psicologico", "min_level": 1},
            {"id": "limitar_noticias", "kind": "psicologico", "min_level": 1},
            {"id": "ordenar_espacio", "kind": "psicologico", "min_level": 1},
            {"id": "hacer_una_cosa", "kind": "psicologico", "min_level": 1},
            # Psychological - Level 2
            {"id": "meditacion", "kind": "psicologico", "min_level": 2},
            {"id": "diario_gratitud", "kind": "psicologico", "min_level": 2},
            {"id": "diario_emociones", "kind": "psicologico", "min_level": 2},
            {"id": "mindfulness", "kind": "psicologico", "min_level": 2},
            {"id": "pausa_pantallas", "kind": "psicologico", "min_level": 2},
            {"id": "hobby_creativo", "kind": "psicologico", "min_level": 2},
            {"id": "pintar_dibujar", "kind": "psicologico", "min_level": 2},
            {"id": "llamar_amigo", "kind": "psicologico", "min_level": 2},
            {"id": "quedar_persona", "kind": "psicologico", "min_level": 2},
            {"id": "decir_no", "kind": "psicologico", "min_level": 2},
            {"id": "pedir_ayuda", "kind": "psicologico", "min_level": 2},
            {"id": "perdonarse", "kind": "psicologico", "min_level": 2},
            {"id": "celebrar_logro", "kind": "psicologico", "min_level": 2},
            {"id": "listar_logros", "kind": "psicologico", "min_level": 2},
            {"id": "planificar_dia", "kind": "psicologico", "min_level": 2},
            {"id": "priorizar_tareas", "kind": "psicologico", "min_level": 2},
            {"id": "delegar", "kind": "psicologico", "min_level": 2},
            {"id": "aprender_algo", "kind": "psicologico", "min_level": 2},
            {"id": "limitar_redes", "kind": "psicologico", "min_level": 2},
            {"id": "modo_no_molestar", "kind": "psicologico", "min_level": 2},
            # Psychological - Level 3
            {"id": "retiro_digital", "kind": "psicologico", "min_level": 3},
            {"id": "revision_semanal", "kind": "psicologico", "min_level": 3},
            # Batch 2 - Physical Level 1
            {"id": "ventilar_habitacion", "kind": "fisico", "min_level": 1},
            {"id": "cambiar_sabanas", "kind": "fisico", "min_level": 1},
            {"id": "comer_legumbres", "kind": "fisico", "min_level": 1},
            {"id": "evitar_procesados", "kind": "fisico", "min_level": 1},
            # Batch 2 - Physical Level 2
            {"id": "senderismo", "kind": "fisico", "min_level": 2},
            {"id": "bailar", "kind": "fisico", "min_level": 2},
            {"id": "estiramiento_cuello", "kind": "fisico", "min_level": 2},
            {"id": "estiramiento_espalda", "kind": "fisico", "min_level": 2},
            {"id": "rodillo_espuma", "kind": "fisico", "min_level": 2},
            {"id": "dormir_siesta_corta", "kind": "fisico", "min_level": 2},
            # Batch 2 - Physical Level 3
            {"id": "sueno_ritual", "kind": "fisico", "min_level": 3},
            # Batch 2 - Psychological Level 1
            {"id": "cantar", "kind": "psicologico", "min_level": 1},
            {"id": "bailar_solo", "kind": "psicologico", "min_level": 1},
            {"id": "ver_comedia", "kind": "psicologico", "min_level": 1},
            {"id": "foto_bonita", "kind": "psicologico", "min_level": 1},
            {"id": "recordar_momento_feliz", "kind": "psicologico", "min_level": 1},
            {"id": "escribir_postal", "kind": "psicologico", "min_level": 1},
            {"id": "elogiar_trabajo", "kind": "psicologico", "min_level": 1},
            {"id": "escuchar_podcast", "kind": "psicologico", "min_level": 1},
            {"id": "audiobook", "kind": "psicologico", "min_level": 1},
            {"id": "limpiar_mesa", "kind": "psicologico", "min_level": 1},
            {"id": "tirar_objetos", "kind": "psicologico", "min_level": 1},
            {"id": "organizar_armario", "kind": "psicologico", "min_level": 1},
            {"id": "mirar_cielo", "kind": "psicologico", "min_level": 1},
            # Batch 2 - Psychological Level 2
            {"id": "tecnicas_respiracion", "kind": "psicologico", "min_level": 2},
            {"id": "body_scan", "kind": "psicologico", "min_level": 2},
            {"id": "diario_suenos", "kind": "psicologico", "min_level": 2},
            {"id": "escribir_carta", "kind": "psicologico", "min_level": 2},
            {"id": "fotografia", "kind": "psicologico", "min_level": 2},
            {"id": "escribir_poesia", "kind": "psicologico", "min_level": 2},
            {"id": "tocar_instrumento", "kind": "psicologico", "min_level": 2},
            {"id": "manualidades", "kind": "psicologico", "min_level": 2},
            {"id": "costura", "kind": "psicologico", "min_level": 2},
            {"id": "cocinar_nueva_receta", "kind": "psicologico", "min_level": 2},
            {"id": "rechazar_invitacion", "kind": "psicologico", "min_level": 2},
            {"id": "establecer_limite", "kind": "psicologico", "min_level": 2},
            {"id": "aceptar_elogio", "kind": "psicologico", "min_level": 2},
            {"id": "reconocer_error", "kind": "psicologico", "min_level": 2},
            {"id": "pedir_opinion", "kind": "psicologico", "min_level": 2},
            {"id": "feedback_constructivo", "kind": "psicologico", "min_level": 2},
            {"id": "lista_tareas", "kind": "psicologico", "min_level": 2},
            {"id": "bloquear_tiempo", "kind": "psicologico", "min_level": 2},
            {"id": "revisar_objetivos", "kind": "psicologico", "min_level": 2},
            {"id": "leer_articulo", "kind": "psicologico", "min_level": 2},
            {"id": "apagar_notificaciones", "kind": "psicologico", "min_level": 2},
            {"id": "horario_pantallas", "kind": "psicologico", "min_level": 2},
            {"id": "dormir_sin_movil", "kind": "psicologico", "min_level": 2},
            # Batch 2 - Psychological Level 3
            {"id": "diario_reflexion", "kind": "psicologico", "min_level": 3},
            {"id": "practicar_empatia", "kind": "psicologico", "min_level": 2},
            {"id": "escuchar_activamente", "kind": "psicologico", "min_level": 2},
            {"id": "celebrar_pequeno_logro", "kind": "psicologico", "min_level": 1},
        ]
    )


def _default_roadmap_items() -> list[dict[str, Any]]:
    """Return the editable base roadmap used by the companion."""
    now = utc_now_iso()
    items = [
        (
            "roadmap_salud_base",
            "salud",
            "Definir seguimiento de salud",
            "Anota revisiones, analíticas o temas médicos que quieras tener controlados.",
        ),
        (
            "roadmap_voz_base",
            "voz",
            "Decidir objetivo de voz",
            "Puedes usarlo para marcar práctica, seguimiento o descanso vocal.",
        ),
        (
            "roadmap_documentacion_base",
            "documentacion",
            "Revisar documentación importante",
            "Añade aquí cambios de nombre, tarjetas o trámites que quieras organizar.",
        ),
        (
            "roadmap_entorno_social_base",
            "entorno_social",
            "Pensar próximos pasos sociales",
            "Por ejemplo, conversaciones pendientes o apoyos que quieras activar.",
        ),
        (
            "roadmap_imagen_expresion_base",
            "imagen_expresion",
            "Definir un pequeño objetivo de expresión",
            "Úsalo para ropa, estilo, autocuidado o cualquier cambio que te ayude.",
        ),
        (
            "roadmap_cirugias_recuperacion_base",
            "cirugias_recuperacion",
            "Preparar cuidados o consultas futuras",
            "Solo si aplica para ti: cirugía, recuperación o seguimiento posterior.",
        ),
        (
            "roadmap_bienestar_base",
            "bienestar",
            "Mantener una rutina mínima de bienestar",
            "Puedes enfocarlo a sueño, energía, apoyo emocional o autocuidado.",
        ),
    ]
    return [
        {
            "id": item_id,
            "category": category,
            "title": title,
            "details": details,
            "target_date": None,
            "is_active": True,
            "is_hidden": False,
            "completed": False,
            "source": "base",
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }
        for item_id, category, title, details in items
    ]


def _merge_habit_catalog(
    existing: list[dict[str, Any]], default: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Sync the stored catalog to the currently reviewed default habit set."""
    default_by_id: dict[str, dict[str, Any]] = {
        habit["id"]: dict(habit)
        for habit in default
        if isinstance(habit, dict) and isinstance(habit.get("id"), str)
    }
    result: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for habit in existing:
        if not isinstance(habit, dict):
            continue
        habit_id = habit.get("id")
        if not isinstance(habit_id, str) or habit_id not in default_by_id or habit_id in seen_ids:
            continue
        result.append(dict(default_by_id[habit_id]))
        seen_ids.add(habit_id)
    for habit in default:
        if not isinstance(habit, dict):
            continue
        habit_id = habit.get("id")
        if not isinstance(habit_id, str) or habit_id in seen_ids:
            continue
        result.append(dict(habit))
        seen_ids.add(habit_id)
    return result


def _normalize_habit_catalog(catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize habit catalog IDs and drop duplicates created by migration."""
    normalized_catalog: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for habit in catalog:
        if not isinstance(habit, dict):
            continue
        raw_id = habit.get("id")
        if not isinstance(raw_id, str) or not raw_id:
            continue
        normalized_id = normalize_habit_id(raw_id)
        if not normalized_id or normalized_id in seen_ids:
            continue
        migrated_habit = dict(habit)
        migrated_habit["id"] = normalized_id
        normalized_catalog.append(migrated_habit)
        seen_ids.add(normalized_id)
    return normalized_catalog


def _normalize_habit_id_list(values: list[str], allowed_ids: set[str] | None = None) -> list[str]:
    """Normalize persisted habit ID lists while preserving order."""
    normalized_values: list[str] = []
    seen_ids: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized_id = normalize_habit_id(value)
        if not normalized_id or normalized_id in seen_ids:
            continue
        if allowed_ids is not None and normalized_id not in allowed_ids:
            continue
        normalized_values.append(normalized_id)
        seen_ids.add(normalized_id)
    return normalized_values


def _sanitize_meta(meta: dict[str, Any] | Any) -> dict[str, Any]:
    """Drop deprecated meta fields while keeping supported values intact."""
    if not isinstance(meta, dict):
        return dict(default_profile_state()["meta"])
    clean_meta = dict(meta)
    clean_meta.pop("help_shown", None)
    return clean_meta


def default_profile_state() -> dict[str, Any]:
    """Default patient static data (profile, health config, meta, habit catalog)."""
    now = utc_now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": now,
        "updated_at": now,
        "profile": {
            "first_name": "",
            "onboarding_completed": False,
            "journey_stage": "transitioning",
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
        "habit_catalog": _default_habit_catalog(),
        "meta": {
            "last_habit_count": 3,
        },
    }


def default_history_state() -> dict[str, Any]:
    """Default patient historical records."""
    return {
        "schema_version": SCHEMA_VERSION,
        "records": {
            "voice": [],
            "medication": [],
            "visits": [],
            "other_events": [],
            "habits": [],
            "roadmap_items": _default_roadmap_items(),
            "appointment_preps": [],
            "wellbeing_logs": [],
            "milestones": [],
        },
    }


def default_state() -> dict[str, Any]:
    """Create merged default state (profile + history)."""
    profile = default_profile_state()
    history = default_history_state()
    return {
        **profile,
        "records": history["records"],
    }


def _deep_merge_defaults(
    base: dict[str, Any],
    default: dict[str, Any],
) -> dict[str, Any]:
    """Merge missing keys from defaults recursively."""
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


def _replace_file_with_retry(
    source: Path,
    destination: Path,
    replace_func: Callable[[Path | str, Path | str], None] | None = None,
    sleep_func: Callable[[float], None] | None = None,
) -> None:
    """Replace a file with short retries for transient Windows file locks."""
    replacer = os.replace if replace_func is None else replace_func
    sleeper = time.sleep if sleep_func is None else sleep_func
    for attempt in range(ATOMIC_SAVE_RETRIES):
        try:
            replacer(source, destination)
            return
        except PermissionError:
            if attempt >= ATOMIC_SAVE_RETRIES - 1:
                raise
            sleeper(ATOMIC_SAVE_RETRY_SECONDS * (attempt + 1))


def _atomic_save(path: Path, data: dict[str, Any]) -> None:
    """Persist JSON atomically."""
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=str(path.parent),
            encoding="utf-8",
            suffix=".tmp",
        ) as handle:
            handle.write(payload)
            tmp_path = Path(handle.name)
        _replace_file_with_retry(tmp_path, path)
        return
    except Exception as exc:
        logger.exception("Atomic save failed: %s", exc)
        raise DataStoreError(f"No se pudo guardar: {exc}") from exc
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass


class StateRepository:
    """Versioned JSON repository with split profile/history storage."""

    def __init__(self, paths: RepositoryPaths | None = None) -> None:
        """Initialize repository.

        Args:
            paths: Optional custom paths for testing.
        """
        if paths is None:
            out_dir = get_output_dir()
            migrate_legacy_output_dir(
                legacy_dir=get_legacy_output_dir(),
                target_dir=out_dir,
            )
            paths = RepositoryPaths(
                profile_file=get_patient_profile_path(),
                history_file=get_patient_history_path(),
                legacy_file=get_data_file_path(),
            )
        self.paths = paths
        self.paths.profile_file.parent.mkdir(parents=True, exist_ok=True)
        self.paths.history_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        """Load state from disk (profile + history merged), creating if needed.

        Returns:
            Merged state dictionary (profile + records).
        """
        profile_exists = self.paths.profile_file.exists()
        history_exists = self.paths.history_file.exists()

        if not profile_exists and not history_exists:
            state = default_state()
            state = self._apply_legacy_bootstrap_if_available(state)
            self.save(state)
            return state

        profile = (
            _safe_json_load(self.paths.profile_file) if profile_exists else default_profile_state()
        )
        history = (
            _safe_json_load(self.paths.history_file) if history_exists else default_history_state()
        )

        profile = self._migrate_profile(profile)
        history = self._migrate_history(history)

        merged = {
            **profile,
            "records": history["records"],
        }
        return merged

    def save(self, state: dict[str, Any]) -> None:
        """Persist state atomically (splits into profile and history files).

        Args:
            state: Full state dictionary.
        """
        now = utc_now_iso()

        profile = {
            "schema_version": state.get("schema_version", SCHEMA_VERSION),
            "created_at": state.get("created_at", now),
            "updated_at": now,
            "profile": state.get("profile", default_profile_state()["profile"]),
            "health_config": state.get("health_config", default_profile_state()["health_config"]),
            "habit_catalog": state.get("habit_catalog", default_profile_state()["habit_catalog"]),
            "meta": _sanitize_meta(state.get("meta", default_profile_state()["meta"])),
        }
        _atomic_save(self.paths.profile_file, profile)

        history = {
            "schema_version": state.get("schema_version", SCHEMA_VERSION),
            "records": state.get("records", default_history_state()["records"]),
        }
        _atomic_save(self.paths.history_file, history)

    def _migrate_profile(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Apply migrations to profile data."""
        if not isinstance(raw, dict):
            return default_profile_state()
        current = _deep_merge_defaults(raw, default_profile_state())
        current["schema_version"] = SCHEMA_VERSION
        if isinstance(current.get("meta"), dict):
            current["meta"].pop("help_shown", None)
        current["habit_catalog"] = _merge_habit_catalog(
            _normalize_habit_catalog(current.get("habit_catalog", [])),
            _default_habit_catalog(),
        )
        return current

    def _migrate_history(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Apply migrations to history data."""
        if not isinstance(raw, dict):
            return default_history_state()
        current = _deep_merge_defaults(raw, default_history_state())
        current["schema_version"] = SCHEMA_VERSION
        allowed_habit_ids = {habit["id"] for habit in _default_habit_catalog()}
        for row in current["records"].get("habits", []):
            if not isinstance(row, dict):
                continue
            row["shown_habits"] = _normalize_habit_id_list(
                row.get("shown_habits", []),
                allowed_ids=allowed_habit_ids,
            )
            row["completed_habits"] = _normalize_habit_id_list(
                row.get("completed_habits", []),
                allowed_ids=allowed_habit_ids,
            )
        return current

    def _apply_legacy_bootstrap_if_available(self, state: dict[str, Any]) -> dict[str, Any]:
        """Bootstrap from legacy voice JSON if present."""
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
