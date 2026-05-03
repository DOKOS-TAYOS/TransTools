"""Regression tests for keeping the habit catalog broadly positive and non-weird."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

from conftest import ROOT

from core.repository import RepositoryPaths, StateRepository
from i18n import _load_locale

_REMOVED_HABIT_IDS: set[str] = {
    "abrazar_alguien",
    "aceite_oliva",
    "afirmaciones",
    "analitica_sangre",
    "ayuno_intermitente",
    "asistir_evento",
    "automasaje",
    "bici",
    "baño_relajante",
    "beber_infusion",
    "boxeo",
    "cardio_intenso",
    "coaching",
    "comer_fuera",
    "crema_hidratante",
    "crossfit",
    "cuidar_unas",
    "curso_online",
    "desayunar_proteina",
    "despertar_agradecido",
    "dieta_mediterranea",
    "dieta_plant_based",
    "diario_profundo",
    "documental",
    "donar_ropa",
    "ducha_fria",
    "enjuague_bucal",
    "ensenar_skill",
    "escalada",
    "exposicion_solar",
    "futbol",
    "frutos_secos",
    "gimnasio",
    "grupo_lectura",
    "grupo_apoyo",
    "hidratar_piel",
    "hidratarse_8_vasos",
    "hilo_dental",
    "jardineria",
    "levantarse_temprano",
    "limitar_sal",
    "maraton_entrenar",
    "masaje",
    "mascarilla_facial",
    "meditacion_larga",
    "merendar_fruta",
    "mentor_otros",
    "natacion",
    "objetivos_trimestre",
    "padel",
    "patinar",
    "pasear_perro",
    "peso_saludable",
    "pescado_azul",
    "peinar_cabello",
    "podcast_inspirador",
    "protector_solar",
    "proteina_vegetal",
    "regar_plantas",
    "regalar_algo",
    "remar",
    "revisar_dental",
    "revision_medica",
    "revisar_vista",
    "retiro_naturaleza",
    "retiro_meditacion",
    "retiro_silencio",
    "reunion_familiar",
    "sauna",
    "semillas",
    "sonreir",
    "suplementos_vitaminas",
    "tenis",
    "terapia",
    "triatlon",
    "unirse_club",
    "vacuna_actualizada",
    "valores_personales",
    "ver_ted_talk",
    "vela_relajante",
    "video_call_ser",
    "viaje_solo",
    "vision_board",
    "visualizar_positivo",
    "voluntariado",
    "vestirse_bien",
    "ayudar_vecino",
    "donar_ropa",
}

_ADDED_MICRO_HABITS: dict[str, tuple[str, str]] = {
    "descanso_visual": ("Descansar la vista 20 segundos", "Rest your eyes for 20 seconds"),
    "levantarse_2_min": ("Levantarse y moverse 2 minutos", "Stand up and move for 2 minutes"),
    "revisar_calendario": ("Revisar el calendario del día", "Review today's calendar"),
    "elegir_prioridad": ("Elegir una prioridad de hoy", "Choose one priority for today"),
    "anotar_siguiente_paso": (
        "Anotar el siguiente paso de una tarea",
        "Write down the next step for a task",
    ),
    "recoger_5_min": ("Ordenar durante 5 minutos", "Tidy up for 5 minutes"),
    "preparar_manana": ("Dejar preparada una cosa para mañana", "Prepare one thing for tomorrow"),
}


def _make_workspace_temp_dir() -> Path:
    """Create a temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"habit_review_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_default_catalog_excludes_dubious_or_extreme_habits(app_service) -> None:
    """Default habits should stay focused on broadly positive, low-risk wellbeing actions."""
    state = app_service.get_state()
    catalog_ids = {habit["id"] for habit in state["habit_catalog"]}
    locale_es = _load_locale("es")
    locale_en = _load_locale("en")

    assert _REMOVED_HABIT_IDS.isdisjoint(catalog_ids)
    for habit_id in _REMOVED_HABIT_IDS:
        assert f"habit.name.{habit_id}" not in locale_es
        assert f"habit.name.{habit_id}" not in locale_en


def test_default_catalog_includes_easy_micro_habits_for_basics_and_planning(app_service) -> None:
    """Default habits should include a few very easy routines and planning actions."""
    state = app_service.get_state()
    catalog_ids = {habit["id"] for habit in state["habit_catalog"]}
    locale_es = _load_locale("es")
    locale_en = _load_locale("en")

    for habit_id, (label_es, label_en) in _ADDED_MICRO_HABITS.items():
        assert habit_id in catalog_ids
        assert locale_es[f"habit.name.{habit_id}"] == label_es
        assert locale_en[f"habit.name.{habit_id}"] == label_en


def test_repository_prunes_removed_habits_from_existing_catalog_and_logs() -> None:
    """Older saved data should not keep habits that were removed from the reviewed catalog."""
    temp_dir = _make_workspace_temp_dir()
    try:
        profile_file = temp_dir / "profile.json"
        history_file = temp_dir / "history.json"
        legacy_file = temp_dir / "legacy.json"

        profile_file.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "created_at": "2026-05-01T10:00:00Z",
                    "updated_at": "2026-05-01T10:00:00Z",
                    "profile": {
                        "first_name": "Alex",
                        "onboarding_completed": True,
                        "created_at": "2026-05-01T10:00:00Z",
                        "updated_at": "2026-05-01T10:00:00Z",
                    },
                    "health_config": {
                        "next_medication_date": None,
                        "medication_every_days": None,
                        "medication_dose": None,
                        "next_medical_visit_date": None,
                        "next_psych_visit_date": None,
                    },
                    "habit_catalog": [
                        {"id": "caminar", "kind": "fisico", "min_level": 1},
                        {"id": "ayuno_intermitente", "kind": "fisico", "min_level": 3},
                        {"id": "coaching", "kind": "psicologico", "min_level": 3},
                        {"id": "crema_hidratante", "kind": "psicologico", "min_level": 2},
                        {"id": "vestirse_bien", "kind": "psicologico", "min_level": 2},
                        {"id": "pasear_perro", "kind": "psicologico", "min_level": 2},
                        {"id": "terapia", "kind": "psicologico", "min_level": 3},
                    ],
                    "meta": {
                        "last_habit_count": 3,
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        history_file.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "records": {
                        "voice": [],
                        "medication": [],
                        "visits": [],
                        "other_events": [],
                        "habits": [
                            {
                                "id": "habit-log-1",
                                "date": "2026-05-02",
                                "shown_habits": [
                                    "caminar",
                                    "ayuno_intermitente",
                                    "coaching",
                                    "crema_hidratante",
                                    "pasear_perro",
                                    "terapia",
                                    "vestirse_bien",
                                ],
                                "completed_habits": [
                                    "coaching",
                                    "crema_hidratante",
                                    "pasear_perro",
                                    "terapia",
                                    "vestirse_bien",
                                ],
                                "created_at": "2026-05-02T10:00:00Z",
                                "updated_at": "2026-05-02T10:00:00Z",
                            }
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        repo = StateRepository(
            RepositoryPaths(
                profile_file=profile_file,
                history_file=history_file,
                legacy_file=legacy_file,
            )
        )

        state = repo.load()

        catalog_ids = {habit["id"] for habit in state["habit_catalog"]}
        assert "caminar" in catalog_ids
        assert "ayuno_intermitente" not in catalog_ids
        assert "coaching" not in catalog_ids
        assert "crema_hidratante" not in catalog_ids
        assert "pasear_perro" not in catalog_ids
        assert "terapia" not in catalog_ids
        assert "vestirse_bien" not in catalog_ids
        assert state["records"]["habits"][0]["shown_habits"] == ["caminar"]
        assert state["records"]["habits"][0]["completed_habits"] == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
