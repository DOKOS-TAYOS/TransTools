"""Tests for final polish: habit-id migration and mojibake cleanup."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

from conftest import ROOT

from core.repository import RepositoryPaths, StateRepository
from i18n import _load_locale


def _make_workspace_temp_dir() -> Path:
    """Create a temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"polish_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_repository_normalizes_legacy_habit_ids_and_drops_help_flag() -> None:
    """Legacy mojibake habit IDs should be normalized without losing useful state."""
    temp_dir = _make_workspace_temp_dir()
    try:
        profile_file = temp_dir / "profile.json"
        history_file = temp_dir / "history.json"
        legacy_file = temp_dir / "legacy.json"

        broken_stretch = "estiramientos_ma\u00c3\u00b1ana"
        broken_bath = "ba\u00c3\u00b1o_relajante"

        profile_file.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "created_at": "2026-04-01T10:00:00Z",
                    "updated_at": "2026-04-01T10:00:00Z",
                    "profile": {
                        "first_name": "Alex",
                        "onboarding_completed": True,
                        "created_at": "2026-04-01T10:00:00Z",
                        "updated_at": "2026-04-01T10:00:00Z",
                    },
                    "health_config": {
                        "next_medication_date": None,
                        "medication_every_days": None,
                        "medication_dose": None,
                        "next_medical_visit_date": None,
                        "next_psych_visit_date": None,
                    },
                    "habit_catalog": [
                        {"id": broken_stretch, "kind": "fisico", "min_level": 2},
                        {"id": broken_bath, "kind": "psicologico", "min_level": 2},
                    ],
                    "meta": {
                        "last_habit_count": 5,
                        "help_shown": True,
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
                                "date": "2026-04-02",
                                "shown_habits": [broken_stretch, broken_bath],
                                "completed_habits": [broken_bath],
                                "created_at": "2026-04-02T10:00:00Z",
                                "updated_at": "2026-04-02T10:00:00Z",
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

        catalog_ids = [habit["id"] for habit in state["habit_catalog"]]
        assert "estiramientos_manana" in catalog_ids
        assert "bano_relajante" in catalog_ids
        assert broken_stretch not in catalog_ids
        assert broken_bath not in catalog_ids
        assert state["records"]["habits"][0]["shown_habits"] == [
            "estiramientos_manana",
            "bano_relajante",
        ]
        assert state["records"]["habits"][0]["completed_habits"] == ["bano_relajante"]
        assert state["meta"]["last_habit_count"] == 5
        assert "help_shown" not in state["meta"]

        repo.save(state)
        saved_profile = json.loads(profile_file.read_text(encoding="utf-8"))
        reloaded = repo.load()

        assert "help_shown" not in saved_profile["meta"]
        assert reloaded["records"]["habits"][0]["shown_habits"] == [
            "estiramientos_manana",
            "bano_relajante",
        ]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_locales_and_user_messages_are_exposed_without_mojibake(app_service) -> None:
    """Visible text should no longer leak mojibake sequences."""
    locale_es = _load_locale("es")
    locale_en = _load_locale("en")

    assert locale_es["menu.welcome"] == (
        "Herramientas de apoyo para transición (uso local y privado)"
    )
    assert locale_es["data.no_value"] == "—"
    assert locale_es["habit.name.estiramientos_manana"] == "Estiramientos matutinos"
    assert locale_en["data.no_value"] == "—"
    assert "Ã" not in json.dumps(locale_es, ensure_ascii=False)
    assert "â" not in json.dumps(locale_es, ensure_ascii=False)

    app_service.complete_onboarding(
        first_name="Alex",
        next_medical_visit_date="2026-04-01",
        next_psych_visit_date="2026-04-02",
    )
    alerts = app_service.get_due_alerts(today=__import__("datetime").date(2026, 4, 3))

    assert any("consulta médica pendiente" in alert for alert in alerts)
    assert any("consulta de psicología/especialista pendiente" in alert for alert in alerts)
