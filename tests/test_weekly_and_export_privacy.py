"""Weekly voice aggregation and export privacy tests."""

from __future__ import annotations

from datetime import date

from core.types import VoiceAnalysisResult


def _sample(mean: float, day: date) -> tuple[VoiceAnalysisResult, date]:
    return (
        VoiceAnalysisResult(
            pitch_mean_hz=mean,
            pitch_std_hz=10.0,
            pitch_min_hz=mean - 20,
            pitch_max_hz=mean + 20,
            energy_rms=0.07,
            mood=[0.5, 0.3, 0.2],
        ),
        day,
    )


def test_weekly_aggregation_groups_by_monday(app_service) -> None:
    """Voice entries in same ISO week should be aggregated together."""
    app_service.complete_onboarding(first_name="Alex")
    entries = [
        _sample(200.0, date(2026, 3, 2)),  # Monday
        _sample(220.0, date(2026, 3, 4)),  # Wednesday
    ]
    for analysis, day in entries:
        app_service.add_voice_record(day, analysis, mood_self=None, audio_saved_path=None)

    weekly = app_service.get_weekly_voice_summary()
    assert len(weekly) == 1
    assert weekly[0]["week_start"] == "2026-03-02"
    assert weekly[0]["samples"] == 2
    assert 209.0 <= weekly[0]["pitch_mean_hz"] <= 211.0


def test_daily_export_has_no_daily_pitch_columns(app_service) -> None:
    """Daily export must avoid per-day tone metrics."""
    app_service.complete_onboarding(first_name="Alex")
    analysis, day = _sample(205.0, date(2026, 3, 6))
    app_service.add_voice_record(day, analysis, mood_self=None, audio_saved_path=None)

    frames = app_service.to_export_frames()
    daily = frames["resumen_diario"]
    cols = set(daily.columns.tolist())

    assert "pitch_mean_hz" not in cols
    assert "pitch_min_hz" not in cols
    assert "pitch_max_hz" not in cols
    assert "voice_samples" in cols
