"""Tests for the Companion roadmap, appointments, wellbeing and dashboard."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from uuid import uuid4

from conftest import ROOT

from core.repository import RepositoryPaths, StateRepository


def _make_workspace_temp_dir() -> Path:
    """Create a temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"companion_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_repository_migrates_companion_defaults_into_existing_state() -> None:
    """Existing states should receive journey-stage and companion defaults."""
    temp_dir = _make_workspace_temp_dir()
    try:
        profile_file = temp_dir / "profile.json"
        history_file = temp_dir / "history.json"
        legacy_file = temp_dir / "legacy.json"

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
                    "habit_catalog": [],
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
                        "habits": [],
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

        assert state["profile"]["journey_stage"] == "transitioning"
        assert "roadmap_items" in state["records"]
        assert "appointment_preps" in state["records"]
        assert "wellbeing_logs" in state["records"]
        assert "milestones" in state["records"]
        assert any(item["category"] == "salud" for item in state["records"]["roadmap_items"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_companion_service_crud_and_dashboard_snapshot(app_service) -> None:
    """Companion service should persist editable roadmap, appointments and wellbeing."""
    app_service.complete_onboarding(
        first_name="Alex",
        next_medication_date="2026-05-09",
        medication_every_days=1,
        medication_dose="2 mg",
    )

    app_service.save_roadmap_item(
        item_id=None,
        category="documentacion",
        title="Actualizar nombre social",
        details="Preparar documentación para el cambio.",
        target_date="2026-05-08",
        is_active=True,
        is_hidden=False,
    )
    roadmap_items = app_service.list_roadmap_items()
    custom_item = next(item for item in roadmap_items if item.title == "Actualizar nombre social")
    app_service.toggle_roadmap_item_completed(custom_item.id, completed=True)
    updated_roadmap_items = app_service.list_roadmap_items()

    app_service.save_appointment_prep(
        prep_id=None,
        target_date="2026-05-11",
        appointment_type="medical",
        title="Control endocrino",
        questions="¿Seguimos con la misma pauta?",
        talking_points="Revisar analítica.",
        follow_up_step="Pedir próxima analítica",
    )
    appointment = app_service.list_appointment_preps()[0]
    app_service.complete_appointment_prep(
        appointment.id,
        outcome_notes="Todo bien.",
        follow_up_step="Subir resultados a la carpeta personal",
    )

    app_service.save_appointment_prep(
        prep_id=None,
        target_date="2026-05-12",
        appointment_type="psychology",
        title="Seguimiento emocional",
        questions="¿Cómo manejar semanas de más carga?",
        talking_points="Hablar de autocuidado.",
        follow_up_step="Mantener rutina breve",
    )
    upcoming_prep = next(
        prep
        for prep in app_service.list_appointment_preps()
        if prep.title == "Seguimiento emocional"
    )

    app_service.save_wellbeing_log(
        log_id=None,
        target_date="2026-05-09",
        mood=4,
        energy=3,
        sleep=2,
        side_effects="Algo de cansancio.",
        notes="Día aceptable.",
        linked_source="medication",
    )

    snapshot = app_service.get_dashboard_snapshot(today=date(2026, 5, 9))

    assert snapshot.journey_stage == "transitioning"
    assert any("medicación" in alert.lower() for alert in snapshot.pending_alerts)
    assert any(item.completed for item in updated_roadmap_items if item.id == custom_item.id)
    assert any(item.id == custom_item.id for item in snapshot.completed_recent_roadmap_items)
    assert any(prep.id == upcoming_prep.id for prep in snapshot.upcoming_appointments)
    assert snapshot.weekly_wellbeing_logs == 1


def test_post_transition_dashboard_prioritizes_health_and_wellbeing(app_service) -> None:
    """Post-transition dashboard should float health-related roadmap items first."""
    app_service.complete_onboarding(first_name="Alex")

    app_service.save_roadmap_item(
        item_id=None,
        category="documentacion",
        title="Archivar papeles antiguos",
        details=None,
        target_date="2026-05-20",
        is_active=True,
        is_hidden=False,
    )
    app_service.save_roadmap_item(
        item_id=None,
        category="salud",
        title="Programar revisión anual",
        details=None,
        target_date="2026-05-21",
        is_active=True,
        is_hidden=False,
    )
    app_service.update_journey_stage("post_transition")

    snapshot = app_service.get_dashboard_snapshot(today=date(2026, 5, 10))

    assert snapshot.journey_stage == "post_transition"
    assert snapshot.open_roadmap_items[0].category == "salud"
    assert "revisión" in snapshot.recommended_action.lower()


def test_visit_records_create_follow_up_appointment_prep(app_service) -> None:
    """A visit with a next date should prepare the follow-up appointment automatically."""
    app_service.complete_onboarding(first_name="Alex")

    app_service.add_visit_record(
        target_date=date(2026, 5, 10),
        visit_type="medical",
        completed=True,
        next_visit_date="2026-05-25",
        notes="Revisión correcta.",
    )

    preps = app_service.list_appointment_preps()

    assert len(preps) == 1
    assert preps[0].target_date == "2026-05-25"
    assert preps[0].appointment_type == "medical"
