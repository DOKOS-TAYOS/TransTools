"""Medication reminder behavior tests."""

from __future__ import annotations

from datetime import date


def test_due_medication_alert_when_not_taken(app_service) -> None:
    """App should alert for expected medication days not logged as taken."""
    app_service.complete_onboarding(
        first_name="Alex",
        next_medication_date="2026-03-01",
        medication_every_days=2,
        medication_dose="2 mg",
    )

    alerts = app_service.get_due_alerts(today=date(2026, 3, 6))
    joined = "\n".join(alerts)
    assert "2026-03-01" in joined
    assert "2026-03-03" in joined
    assert "2026-03-05" in joined


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

