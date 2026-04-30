"""Medication reminder behavior tests."""

from __future__ import annotations

from datetime import date


def test_due_medication_alerts_show_today_and_compact_history(app_service) -> None:
    """App should show today's due message plus one compact overdue summary."""
    app_service.complete_onboarding(
        first_name="Alex",
        next_medication_date="2026-03-01",
        medication_every_days=1,
        medication_dose="2 mg",
    )

    alerts = app_service.get_due_alerts(today=date(2026, 3, 6))
    assert len(alerts) == 2
    assert "Hoy te toca medicación" in alerts[0]
    assert "5" in alerts[1]
    assert "2026-03-01" in alerts[1]


def test_due_medication_alerts_stay_bounded_for_long_backlogs(app_service) -> None:
    """Long overdue medication history should not create one message per missed day."""
    app_service.complete_onboarding(
        first_name="Alex",
        next_medication_date="2026-01-01",
        medication_every_days=1,
        medication_dose="2 mg",
    )

    alerts = app_service.get_due_alerts(today=date(2026, 3, 6))

    assert len(alerts) == 2
    assert "2026-01-01" in alerts[1]


def test_no_alert_for_taken_day(app_service) -> None:
    """Taken medication day should not trigger overdue warning."""
    app_service.complete_onboarding(
        first_name="Alex",
        next_medication_date="2026-03-06",
        medication_every_days=1,
        medication_dose="2 mg",
    )
    app_service.add_medication_record(
        target_date=date(2026, 3, 6),
        taken=True,
        hour="09:00",
        dose="2 mg",
        notes=None,
    )
    alerts = app_service.get_due_alerts(today=date(2026, 3, 6))
    assert not any("medicación" in a.lower() for a in alerts)
