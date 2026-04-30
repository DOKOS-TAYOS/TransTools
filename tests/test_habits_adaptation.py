"""Adaptive habits checklist tests."""

from __future__ import annotations

from datetime import date, timedelta


def test_habits_increase_with_high_completion(app_service) -> None:
    """Checklist size should increase when recent completion is high."""
    app_service.complete_onboarding(first_name="Alex")
    base_day = date(2026, 3, 8)

    # Simulate a week with high completion ratio.
    for i in range(1, 7):
        day = base_day - timedelta(days=i)
        selection = app_service.get_habit_selection_for_date(day)
        shown_ids = [habit["id"] for habit in selection.shown_habits]
        app_service.save_habit_log(day, shown_habits=shown_ids, completed_habits=shown_ids)

    next_selection = app_service.get_habit_selection_for_date(base_day)
    assert len(next_selection.shown_habits) >= 4


def test_habits_decrease_with_low_completion(app_service) -> None:
    """Checklist size should not exceed minimum trend when completion is low."""
    app_service.complete_onboarding(first_name="Alex")
    state = app_service.get_state()
    state["meta"]["last_habit_count"] = 6
    app_service.repository.save(state)

    base_day = date(2026, 3, 15)
    for i in range(1, 7):
        day = base_day - timedelta(days=i)
        selection = app_service.get_habit_selection_for_date(day)
        shown_ids = [habit["id"] for habit in selection.shown_habits]
        app_service.save_habit_log(day, shown_habits=shown_ids, completed_habits=[])

    next_selection = app_service.get_habit_selection_for_date(base_day)
    assert len(next_selection.shown_habits) <= 5
    assert len(next_selection.shown_habits) >= 3
