"""Shared domain types for TransTools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class VoiceAnalysisResult:
    """Result of voice analysis.

    Attributes:
        pitch_mean_hz: Mean pitch (F0) in Hz.
        pitch_std_hz: Pitch standard deviation in Hz.
        pitch_min_hz: Minimum pitch in Hz.
        pitch_max_hz: Maximum pitch in Hz.
        energy_rms: RMS energy value.
        mood: [happy, sad, angry] scores in 0..1 range.
    """

    pitch_mean_hz: float
    pitch_std_hz: float
    pitch_min_hz: float
    pitch_max_hz: float
    energy_rms: float
    mood: list[float]


JourneyStage = Literal["transitioning", "post_transition"]
AppointmentType = Literal["medical", "psychology", "general"]


@dataclass(frozen=True)
class RoadmapItem:
    """Editable roadmap item for the personal transition companion."""

    id: str
    category: str
    title: str
    details: str | None
    target_date: str | None
    is_active: bool
    is_hidden: bool
    completed: bool
    source: str
    created_at: str
    updated_at: str
    completed_at: str | None = None


@dataclass(frozen=True)
class AppointmentPrepRecord:
    """Preparation record for a future or completed appointment."""

    id: str
    target_date: str
    appointment_type: AppointmentType
    title: str
    questions: str | None
    talking_points: str | None
    follow_up_step: str | None
    outcome_notes: str | None
    is_completed: bool
    created_at: str
    updated_at: str
    completed_at: str | None = None


@dataclass(frozen=True)
class WellbeingLog:
    """Simple wellbeing check-in linked to daily care."""

    id: str
    target_date: str
    mood: int
    energy: int
    sleep: int
    side_effects: str | None
    notes: str | None
    linked_source: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Milestone:
    """Timeline milestone in the user's process."""

    id: str
    target_date: str
    title: str
    details: str | None
    source: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DashboardSnapshot:
    """Action-oriented summary shown in the main entry flow."""

    pending_alerts: list[str]
    overdue_roadmap_items: list[RoadmapItem]
    upcoming_appointments: list[AppointmentPrepRecord]
    open_roadmap_items: list[RoadmapItem]
    completed_recent_roadmap_items: list[RoadmapItem]
    weekly_completed_steps: int
    weekly_wellbeing_logs: int
    weekly_voice_samples: int
    recommended_action: str
    journey_stage: JourneyStage
