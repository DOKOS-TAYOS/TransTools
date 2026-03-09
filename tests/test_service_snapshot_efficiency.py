"""Service snapshot/read efficiency and activity-tag behavior tests."""

from __future__ import annotations

from datetime import date

from core.types import VoiceAnalysisResult


def _sample(mean: float) -> VoiceAnalysisResult:
    return VoiceAnalysisResult(
        pitch_mean_hz=mean,
        pitch_std_hz=10.0,
        pitch_min_hz=mean - 20,
        pitch_max_hz=mean + 20,
        energy_rms=0.07,
        mood=[0.5, 0.3, 0.2],
    )


def test_get_daily_summary_loads_state_once(app_service) -> None:
    """Daily summary should read state once (no cascading repository loads)."""
    app_service.complete_onboarding(first_name="Alex")
    app_service.add_voice_record(
        target_date=date(2026, 3, 6),
        analysis=_sample(205.0),
        mood_self=None,
        audio_saved_path=None,
    )

    load_calls = {"count": 0}
    orig_load = app_service.repository.load

    def _counted_load():
        load_calls["count"] += 1
        return orig_load()

    app_service.repository.load = _counted_load  # type: ignore[assignment]
    summary = app_service.get_daily_summary(date(2026, 3, 6))

    assert summary["voice_samples"] == 1
    assert load_calls["count"] == 1


def test_to_export_frames_loads_state_once(app_service) -> None:
    """Export frame build should read state once per invocation."""
    app_service.complete_onboarding(first_name="Alex")
    app_service.add_voice_record(
        target_date=date(2026, 3, 6),
        analysis=_sample(205.0),
        mood_self=None,
        audio_saved_path=None,
    )
    app_service.add_medication_record(
        target_date=date(2026, 3, 6),
        taken=True,
        hour="09:00",
        dose="2 mg",
        notes=None,
    )

    load_calls = {"count": 0}
    orig_load = app_service.repository.load

    def _counted_load():
        load_calls["count"] += 1
        return orig_load()

    app_service.repository.load = _counted_load  # type: ignore[assignment]
    frames = app_service.to_export_frames()

    assert "resumen_diario" in frames
    assert load_calls["count"] == 1


def test_calendar_activity_tags_are_domain_codes(app_service) -> None:
    """Calendar tags should be language-neutral domain codes."""
    app_service.complete_onboarding(first_name="Alex")
    day = date(2026, 3, 6)
    app_service.add_voice_record(
        target_date=day,
        analysis=_sample(205.0),
        mood_self=None,
        audio_saved_path=None,
    )
    app_service.add_medication_record(
        target_date=day,
        taken=True,
        hour="09:00",
        dose="2 mg",
        notes=None,
    )
    app_service.add_visit_record(
        target_date=day,
        visit_type="medical",
        completed=True,
        next_visit_date="2026-03-20",
        notes=None,
    )
    app_service.add_other_event(
        target_date=day,
        category="general",
        tags_raw=None,
        notes="note",
    )
    selection = app_service.get_habit_selection_for_date(day)
    shown = [habit["id"] for habit in selection.shown_habits]
    app_service.save_habit_log(day, shown_habits=shown, completed_habits=shown[:1])

    tags = app_service.build_calendar_dates_with_activity()
    day_tags = tags[day.isoformat()]

    assert {"voice", "medication", "visit", "event", "habit"} <= day_tags
