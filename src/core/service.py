"""High-level application services for TransTools."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import pandas as pd

from config.paths import get_contacts_path
from i18n import t
from utils import DataStoreError, get_logger
from utils.datetime_utils import utc_now_iso

from .privacy import VoicePrivacyService
from .repository import ISO_DATE, StateRepository
from .types import (
    AppointmentPrepRecord,
    AppointmentType,
    DashboardSnapshot,
    JourneyStage,
    Milestone,
    RoadmapItem,
    VoiceAnalysisResult,
    WellbeingLog,
)

logger = get_logger(__name__)

_MIN_HABITS = 3
_MAX_HABITS = 8
_POST_TRANSITION_PRIORITY = {"salud": 0, "bienestar": 1, "cirugias_recuperacion": 2}


def _parse_iso_date(value: str | None) -> date | None:
    """Parse an ISO date string.

    Args:
        value: Candidate date string.

    Returns:
        Parsed date if valid, else None.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, ISO_DATE).date()
    except ValueError:
        return None


@dataclass(frozen=True)
class HabitSelection:
    """Habit list selected for a specific day.

    Attributes:
        target_date: Selected date.
        shown_habits: Habits shown in checklist.
        completed_habits: Habit IDs marked complete.
    """

    target_date: date
    shown_habits: list[dict[str, Any]]
    completed_habits: list[str]


class AppService:
    """Application-level service facade for UI modules."""

    def __init__(
        self,
        repository: StateRepository | None = None,
        privacy: VoicePrivacyService | None = None,
        contacts_path: Path | None = None,
    ) -> None:
        """Initialize service facade.

        Args:
            repository: Optional custom repository for tests.
            privacy: Optional privacy service.
            contacts_path: Optional contacts file path (default: src/data/contacts.json).
        """
        self.repository = repository or StateRepository()
        self.privacy = privacy or VoicePrivacyService()
        self.contacts_path = contacts_path or get_contacts_path()
        self._initialize_state()

    def _initialize_state(self) -> None:
        """Ensure state has required defaults and migrate legacy voice entries."""
        state = self.repository.load()
        updated = False

        for entry in state["records"]["voice"]:
            if entry.get("tone_encrypted"):
                continue
            legacy_plain = entry.pop("legacy_tone_plain", None)
            if legacy_plain:
                entry["tone_encrypted"] = self.privacy.encrypt_metrics(legacy_plain)
                updated = True

        if updated:
            self.repository.save(state)

    def get_state(self) -> dict[str, Any]:
        """Get current persisted state."""
        return self.repository.load()

    def needs_onboarding(self) -> bool:
        """Check whether onboarding is still pending."""
        state = self.repository.load()
        return not bool(state["profile"].get("onboarding_completed"))

    def complete_onboarding(
        self,
        first_name: str,
        next_medication_date: str | None = None,
        medication_every_days: int | None = None,
        medication_dose: str | None = None,
        next_medical_visit_date: str | None = None,
        next_psych_visit_date: str | None = None,
    ) -> None:
        """Finalize first-run onboarding and save optional health fields.

        Args:
            first_name: User first name.
            next_medication_date: Optional next medication date in ISO format.
            medication_every_days: Optional medication interval in days.
            medication_dose: Optional medication dose text.
            next_medical_visit_date: Optional next medical visit date in ISO format.
            next_psych_visit_date: Optional next psychology/specialist visit date.
        """
        state = self.repository.load()
        now = utc_now_iso()
        state["profile"]["first_name"] = first_name.strip()
        state["profile"]["onboarding_completed"] = True
        state["profile"]["created_at"] = state["profile"].get("created_at") or now
        state["profile"]["updated_at"] = now
        self._update_health_fields(
            state=state,
            next_medication_date=next_medication_date,
            medication_every_days=medication_every_days,
            medication_dose=medication_dose,
            next_medical_visit_date=next_medical_visit_date,
            next_psych_visit_date=next_psych_visit_date,
        )
        self.repository.save(state)

    def update_profile_and_health(
        self,
        first_name: str,
        next_medication_date: str | None,
        medication_every_days: int | None,
        medication_dose: str | None,
        next_medical_visit_date: str | None,
        next_psych_visit_date: str | None,
    ) -> None:
        """Update profile and health settings from configuration UI."""
        state = self.repository.load()
        state["profile"]["first_name"] = first_name.strip()
        state["profile"]["updated_at"] = utc_now_iso()
        self._update_health_fields(
            state=state,
            next_medication_date=next_medication_date,
            medication_every_days=medication_every_days,
            medication_dose=medication_dose,
            next_medical_visit_date=next_medical_visit_date,
            next_psych_visit_date=next_psych_visit_date,
        )
        self.repository.save(state)

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        """Normalize optional string values."""
        if value is None:
            return None
        text = value.strip()
        return text or None

    @staticmethod
    def _coerce_journey_stage(value: str | None) -> JourneyStage:
        """Normalize the persisted journey stage."""
        if value == "post_transition":
            return "post_transition"
        return "transitioning"

    @staticmethod
    def _clamp_wellbeing_score(value: int) -> int:
        """Clamp wellbeing score into the supported 0..5 range."""
        return max(0, min(5, int(value)))

    @staticmethod
    def _record_collection(state: dict[str, Any], key: str) -> list[dict[str, Any]]:
        """Return a typed record collection from state."""
        collection = state["records"].setdefault(key, [])
        return collection

    @staticmethod
    def _require_record(
        collection: list[dict[str, Any]],
        record_id: str,
        label: str,
    ) -> dict[str, Any]:
        """Find a persisted record by ID or raise a domain error."""
        for item in collection:
            if item.get("id") == record_id:
                return item
        raise DataStoreError(f"No se encontró {label}.")

    @staticmethod
    def _roadmap_priority(item: RoadmapItem, stage: JourneyStage) -> tuple[int, str, str]:
        """Sort roadmap items according to the current journey stage."""
        if stage == "post_transition":
            priority = _POST_TRANSITION_PRIORITY.get(item.category, 5)
        else:
            priority = 0
        target = item.target_date or "9999-12-31"
        return (priority, target, item.title.lower())

    @staticmethod
    def _build_roadmap_item(raw: dict[str, Any]) -> RoadmapItem:
        """Convert raw roadmap payload into a typed domain object."""
        return RoadmapItem(
            id=str(raw.get("id", "")),
            category=str(raw.get("category", "bienestar")),
            title=str(raw.get("title", "")).strip(),
            details=AppService._normalize_optional_text(raw.get("details")),
            target_date=AppService._normalize_optional_text(raw.get("target_date")),
            is_active=bool(raw.get("is_active", True)),
            is_hidden=bool(raw.get("is_hidden", False)),
            completed=bool(raw.get("completed", False)),
            source=str(raw.get("source", "custom")),
            created_at=str(raw.get("created_at", "")),
            updated_at=str(raw.get("updated_at", "")),
            completed_at=AppService._normalize_optional_text(raw.get("completed_at")),
        )

    @staticmethod
    def _build_appointment_prep(raw: dict[str, Any]) -> AppointmentPrepRecord:
        """Convert raw appointment payload into a typed domain object."""
        appointment_type = str(raw.get("appointment_type", "general"))
        if appointment_type not in {"medical", "psychology", "general"}:
            appointment_type = "general"
        return AppointmentPrepRecord(
            id=str(raw.get("id", "")),
            target_date=str(raw.get("target_date", "")),
            appointment_type=appointment_type,  # type: ignore[arg-type]
            title=str(raw.get("title", "")).strip(),
            questions=AppService._normalize_optional_text(raw.get("questions")),
            talking_points=AppService._normalize_optional_text(raw.get("talking_points")),
            follow_up_step=AppService._normalize_optional_text(raw.get("follow_up_step")),
            outcome_notes=AppService._normalize_optional_text(raw.get("outcome_notes")),
            is_completed=bool(raw.get("is_completed", False)),
            created_at=str(raw.get("created_at", "")),
            updated_at=str(raw.get("updated_at", "")),
            completed_at=AppService._normalize_optional_text(raw.get("completed_at")),
        )

    @staticmethod
    def _build_wellbeing_log(raw: dict[str, Any]) -> WellbeingLog:
        """Convert raw wellbeing payload into a typed domain object."""
        return WellbeingLog(
            id=str(raw.get("id", "")),
            target_date=str(raw.get("target_date", "")),
            mood=AppService._clamp_wellbeing_score(int(raw.get("mood", 0))),
            energy=AppService._clamp_wellbeing_score(int(raw.get("energy", 0))),
            sleep=AppService._clamp_wellbeing_score(int(raw.get("sleep", 0))),
            side_effects=AppService._normalize_optional_text(raw.get("side_effects")),
            notes=AppService._normalize_optional_text(raw.get("notes")),
            linked_source=AppService._normalize_optional_text(raw.get("linked_source")),
            created_at=str(raw.get("created_at", "")),
            updated_at=str(raw.get("updated_at", "")),
        )

    @staticmethod
    def _build_milestone(raw: dict[str, Any]) -> Milestone:
        """Convert raw milestone payload into a typed domain object."""
        return Milestone(
            id=str(raw.get("id", "")),
            target_date=str(raw.get("target_date", "")),
            title=str(raw.get("title", "")).strip(),
            details=AppService._normalize_optional_text(raw.get("details")),
            source=str(raw.get("source", "manual")),
            created_at=str(raw.get("created_at", "")),
            updated_at=str(raw.get("updated_at", "")),
        )

    def _update_health_fields(
        self,
        state: dict[str, Any],
        next_medication_date: str | None,
        medication_every_days: int | None,
        medication_dose: str | None,
        next_medical_visit_date: str | None,
        next_psych_visit_date: str | None,
    ) -> None:
        """Apply health field updates to state."""
        cfg = state["health_config"]
        cfg["next_medication_date"] = (
            next_medication_date if _parse_iso_date(next_medication_date) is not None else None
        )
        cfg["medication_every_days"] = (
            int(medication_every_days)
            if medication_every_days and int(medication_every_days) > 0
            else None
        )
        cfg["medication_dose"] = self._normalize_optional_text(medication_dose)
        cfg["next_medical_visit_date"] = (
            next_medical_visit_date
            if _parse_iso_date(next_medical_visit_date) is not None
            else None
        )
        cfg["next_psych_visit_date"] = (
            next_psych_visit_date if _parse_iso_date(next_psych_visit_date) is not None else None
        )

    def get_profile(self) -> dict[str, Any]:
        """Get current profile dictionary."""
        return self.repository.load()["profile"]

    def get_health_config(self) -> dict[str, Any]:
        """Get current health config dictionary."""
        return self.repository.load()["health_config"]

    def update_journey_stage(self, stage: Literal["transitioning", "post_transition"]) -> None:
        """Update the current journey stage shown by the companion."""
        state = self.repository.load()
        state["profile"]["journey_stage"] = self._coerce_journey_stage(stage)
        state["profile"]["updated_at"] = utc_now_iso()
        self.repository.save(state)

    def list_roadmap_items(self) -> list[RoadmapItem]:
        """Return editable roadmap items sorted for the current journey stage."""
        state = self.repository.load()
        stage = self._coerce_journey_stage(state["profile"].get("journey_stage"))
        items = [
            self._build_roadmap_item(item)
            for item in self._record_collection(state, "roadmap_items")
        ]
        return sorted(items, key=lambda item: self._roadmap_priority(item, stage))

    def save_roadmap_item(
        self,
        item_id: str | None,
        category: str,
        title: str,
        details: str | None,
        target_date: str | None,
        is_active: bool,
        is_hidden: bool,
    ) -> None:
        """Create or update a roadmap item."""
        normalized_title = title.strip()
        if not normalized_title:
            raise DataStoreError("El paso de la hoja de ruta necesita un título.")

        state = self.repository.load()
        records = self._record_collection(state, "roadmap_items")
        now = utc_now_iso()
        normalized_target = target_date if _parse_iso_date(target_date) else None

        if item_id is None:
            records.append(
                {
                    "id": uuid4().hex,
                    "category": category.strip() or "bienestar",
                    "title": normalized_title,
                    "details": self._normalize_optional_text(details),
                    "target_date": normalized_target,
                    "is_active": bool(is_active),
                    "is_hidden": bool(is_hidden),
                    "completed": False,
                    "source": "custom",
                    "created_at": now,
                    "updated_at": now,
                    "completed_at": None,
                }
            )
        else:
            existing = self._require_record(records, item_id, "el paso de la hoja de ruta")
            existing.update(
                {
                    "category": category.strip() or "bienestar",
                    "title": normalized_title,
                    "details": self._normalize_optional_text(details),
                    "target_date": normalized_target,
                    "is_active": bool(is_active),
                    "is_hidden": bool(is_hidden),
                    "updated_at": now,
                }
            )
        self.repository.save(state)

    def toggle_roadmap_item_completed(self, item_id: str, completed: bool) -> None:
        """Mark a roadmap item as completed or reopen it."""
        state = self.repository.load()
        records = self._record_collection(state, "roadmap_items")
        item = self._require_record(records, item_id, "el paso de la hoja de ruta")
        now = utc_now_iso()
        item["completed"] = bool(completed)
        item["completed_at"] = now if completed else None
        item["updated_at"] = now
        self.repository.save(state)

    def list_appointment_preps(self) -> list[AppointmentPrepRecord]:
        """List appointment preparation records sorted by target date."""
        state = self.repository.load()
        records = [
            self._build_appointment_prep(item)
            for item in self._record_collection(state, "appointment_preps")
        ]
        return sorted(records, key=lambda item: (item.target_date, item.title.lower()))

    def save_appointment_prep(
        self,
        prep_id: str | None,
        target_date: str,
        appointment_type: AppointmentType,
        title: str,
        questions: str | None,
        talking_points: str | None,
        follow_up_step: str | None,
    ) -> None:
        """Create or update an appointment preparation record."""
        if _parse_iso_date(target_date) is None:
            raise DataStoreError("La cita necesita una fecha válida.")
        normalized_title = title.strip()
        if not normalized_title:
            raise DataStoreError("La cita necesita un título.")
        if appointment_type not in {"medical", "psychology", "general"}:
            raise DataStoreError("Tipo de cita no válido.")

        state = self.repository.load()
        records = self._record_collection(state, "appointment_preps")
        now = utc_now_iso()
        payload = {
            "target_date": target_date,
            "appointment_type": appointment_type,
            "title": normalized_title,
            "questions": self._normalize_optional_text(questions),
            "talking_points": self._normalize_optional_text(talking_points),
            "follow_up_step": self._normalize_optional_text(follow_up_step),
            "updated_at": now,
        }

        if prep_id is None:
            records.append(
                {
                    "id": uuid4().hex,
                    **payload,
                    "outcome_notes": None,
                    "is_completed": False,
                    "created_at": now,
                    "completed_at": None,
                }
            )
        else:
            existing = self._require_record(records, prep_id, "la preparación de cita")
            existing.update(payload)
        self.repository.save(state)

    def complete_appointment_prep(
        self,
        prep_id: str,
        outcome_notes: str | None,
        follow_up_step: str | None,
    ) -> None:
        """Mark an appointment preparation as completed and save outcome notes."""
        state = self.repository.load()
        records = self._record_collection(state, "appointment_preps")
        existing = self._require_record(records, prep_id, "la preparación de cita")
        now = utc_now_iso()
        existing.update(
            {
                "outcome_notes": self._normalize_optional_text(outcome_notes),
                "follow_up_step": self._normalize_optional_text(follow_up_step),
                "is_completed": True,
                "completed_at": now,
                "updated_at": now,
            }
        )
        self.repository.save(state)

    def list_wellbeing_logs(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[WellbeingLog]:
        """List wellbeing logs filtered by optional date range."""
        state = self.repository.load()
        records = [
            self._build_wellbeing_log(item)
            for item in self._record_collection(state, "wellbeing_logs")
        ]

        def _in_range(item: WellbeingLog) -> bool:
            parsed = _parse_iso_date(item.target_date)
            if parsed is None:
                return False
            if date_from is not None and parsed < date_from:
                return False
            if date_to is not None and parsed > date_to:
                return False
            return True

        filtered = (
            [item for item in records if _in_range(item)] if (date_from or date_to) else records
        )
        return sorted(filtered, key=lambda item: item.target_date, reverse=True)

    def save_wellbeing_log(
        self,
        log_id: str | None,
        target_date: str,
        mood: int,
        energy: int,
        sleep: int,
        side_effects: str | None,
        notes: str | None,
        linked_source: str | None,
    ) -> None:
        """Create or update a simple daily wellbeing check-in."""
        if _parse_iso_date(target_date) is None:
            raise DataStoreError("El bienestar necesita una fecha válida.")

        state = self.repository.load()
        records = self._record_collection(state, "wellbeing_logs")
        now = utc_now_iso()
        payload = {
            "target_date": target_date,
            "mood": self._clamp_wellbeing_score(mood),
            "energy": self._clamp_wellbeing_score(energy),
            "sleep": self._clamp_wellbeing_score(sleep),
            "side_effects": self._normalize_optional_text(side_effects),
            "notes": self._normalize_optional_text(notes),
            "linked_source": self._normalize_optional_text(linked_source),
            "updated_at": now,
        }

        if log_id is None:
            records.append({"id": uuid4().hex, **payload, "created_at": now})
        else:
            existing = self._require_record(records, log_id, "el check-in de bienestar")
            existing.update(payload)
        self.repository.save(state)

    def list_milestones(self) -> list[Milestone]:
        """List milestones sorted by date."""
        state = self.repository.load()
        milestones = [
            self._build_milestone(item) for item in self._record_collection(state, "milestones")
        ]
        return sorted(milestones, key=lambda item: (item.target_date, item.title.lower()))

    def save_milestone(
        self,
        milestone_id: str | None,
        target_date: str,
        title: str,
        details: str | None,
        source: str = "manual",
    ) -> None:
        """Create or update a personal milestone."""
        if _parse_iso_date(target_date) is None:
            raise DataStoreError("El hito necesita una fecha válida.")
        normalized_title = title.strip()
        if not normalized_title:
            raise DataStoreError("El hito necesita un título.")

        state = self.repository.load()
        records = self._record_collection(state, "milestones")
        now = utc_now_iso()
        payload = {
            "target_date": target_date,
            "title": normalized_title,
            "details": self._normalize_optional_text(details),
            "source": source.strip() or "manual",
            "updated_at": now,
        }
        if milestone_id is None:
            records.append({"id": uuid4().hex, **payload, "created_at": now})
        else:
            existing = self._require_record(records, milestone_id, "el hito")
            existing.update(payload)
        self.repository.save(state)

    def get_contacts(self) -> dict[str, Any]:
        """Get contacts by national and regional groups (loads from src/data/contacts)."""
        if not self.contacts_path.exists():
            return {"national": [], "regional": {}}
        try:
            import json

            return json.loads(self.contacts_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not load contacts from %s: %s", self.contacts_path, exc)
            return {"national": [], "regional": {}}

    def add_voice_record(
        self,
        target_date: date,
        analysis: VoiceAnalysisResult,
        mood_self: dict[str, float] | None,
        audio_saved_path: str | None,
    ) -> None:
        """Add voice record and encrypt sensitive tone metrics.

        Args:
            target_date: Selected logical record day.
            analysis: Audio analysis result.
            mood_self: Optional self-reported mood values.
            audio_saved_path: Optional path to persisted WAV.
        """
        state = self.repository.load()
        mood_auto = {
            "happy": float((analysis.mood + [0, 0, 0])[0]),
            "sad": float((analysis.mood + [0, 0, 0])[1]),
            "angry": float((analysis.mood + [0, 0, 0])[2]),
        }
        sensitive = {
            "pitch_mean_hz": float(analysis.pitch_mean_hz),
            "pitch_std_hz": float(analysis.pitch_std_hz),
            "pitch_min_hz": float(analysis.pitch_min_hz),
            "pitch_max_hz": float(analysis.pitch_max_hz),
        }
        encrypted = self.privacy.encrypt_metrics(sensitive)
        state["records"]["voice"].append(
            {
                "id": uuid4().hex,
                "recorded_at": utc_now_iso(),
                "target_date": target_date.isoformat(),
                "energy_rms": float(analysis.energy_rms),
                "mood_auto": mood_auto,
                "mood_self": mood_self,
                "tone_encrypted": encrypted,
                "audio_saved_path": self._normalize_optional_text(audio_saved_path),
            }
        )
        self.repository.save(state)

    @staticmethod
    def _sort_rows(
        rows: list[dict[str, Any]],
        date_key: str,
        secondary_key: str | None = None,
    ) -> list[dict[str, Any]]:
        """Sort records by date and optional secondary key."""
        if secondary_key is None:
            return sorted(rows, key=lambda row: row.get(date_key) or "")
        return sorted(
            rows,
            key=lambda row: (row.get(date_key) or "", row.get(secondary_key) or ""),
        )

    @staticmethod
    def _group_rows_by_date(
        rows: list[dict[str, Any]],
        date_key: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Group rows by the provided date key."""
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            day_key = row.get(date_key)
            if not day_key:
                continue
            grouped.setdefault(day_key, []).append(row)
        return grouped

    def _build_state_snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        """Build sorted/indexed record snapshot from current state."""
        records = state["records"]
        voice = self._sort_rows(
            records["voice"],
            date_key="target_date",
            secondary_key="recorded_at",
        )
        medication = self._sort_rows(records["medication"], date_key="date")
        visits = self._sort_rows(records["visits"], date_key="date")
        events = self._sort_rows(records["other_events"], date_key="date")
        habits = self._sort_rows(records["habits"], date_key="date")
        roadmap_items = self._sort_rows(records["roadmap_items"], date_key="target_date")
        appointment_preps = self._sort_rows(records["appointment_preps"], date_key="target_date")
        wellbeing_logs = self._sort_rows(records["wellbeing_logs"], date_key="target_date")
        milestones = self._sort_rows(records["milestones"], date_key="target_date")

        voice_by_date = self._group_rows_by_date(voice, "target_date")
        medication_by_date = self._group_rows_by_date(medication, "date")
        visits_by_date = self._group_rows_by_date(visits, "date")
        events_by_date = self._group_rows_by_date(events, "date")
        habits_by_date = self._group_rows_by_date(habits, "date")
        wellbeing_by_date = self._group_rows_by_date(wellbeing_logs, "target_date")

        all_dates = sorted(
            key
            for key in {
                *voice_by_date.keys(),
                *medication_by_date.keys(),
                *visits_by_date.keys(),
                *events_by_date.keys(),
                *habits_by_date.keys(),
                *wellbeing_by_date.keys(),
            }
            if _parse_iso_date(key) is not None
        )

        return {
            "voice": voice,
            "medication": medication,
            "visits": visits,
            "events": events,
            "habits": habits,
            "roadmap_items": roadmap_items,
            "appointment_preps": appointment_preps,
            "wellbeing_logs": wellbeing_logs,
            "milestones": milestones,
            "voice_by_date": voice_by_date,
            "medication_by_date": medication_by_date,
            "visits_by_date": visits_by_date,
            "events_by_date": events_by_date,
            "habits_by_date": habits_by_date,
            "wellbeing_by_date": wellbeing_by_date,
            "all_dates": all_dates,
        }

    def _hydrate_voice_rows(
        self,
        rows: list[dict[str, Any]],
        include_sensitive: bool,
    ) -> list[dict[str, Any]]:
        """Optionally enrich voice rows with decrypted tone metrics."""
        if not include_sensitive:
            return list(rows)
        hydrated: list[dict[str, Any]] = []
        for row in rows:
            enriched = dict(row)
            enriched["tone"] = self.privacy.decrypt_metrics(row.get("tone_encrypted"))
            hydrated.append(enriched)
        return hydrated

    def list_voice_records(self, include_sensitive: bool = False) -> list[dict[str, Any]]:
        """List voice records sorted by date."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        return self._hydrate_voice_rows(snapshot["voice"], include_sensitive=include_sensitive)

    def _build_weekly_voice_summary(
        self,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build weekly aggregated voice metrics from hydrated voice rows."""
        buckets: dict[str, dict[str, Any]] = {}
        for row in rows:
            target = _parse_iso_date(row.get("target_date"))
            if target is None:
                continue
            week_start = (target - timedelta(days=target.weekday())).isoformat()
            tone = row.get("tone") or {}
            bucket = buckets.setdefault(
                week_start,
                {
                    "week_start": week_start,
                    "samples": 0,
                    "pitch_mean_hz": [],
                    "pitch_min_hz": [],
                    "pitch_max_hz": [],
                    "pitch_std_hz": [],
                    "energy_rms": [],
                    "mood_happy": [],
                    "mood_sad": [],
                    "mood_angry": [],
                },
            )
            bucket["samples"] += 1
            if tone:
                bucket["pitch_mean_hz"].append(float(tone.get("pitch_mean_hz", 0.0)))
                bucket["pitch_min_hz"].append(float(tone.get("pitch_min_hz", 0.0)))
                bucket["pitch_max_hz"].append(float(tone.get("pitch_max_hz", 0.0)))
                bucket["pitch_std_hz"].append(float(tone.get("pitch_std_hz", 0.0)))
            bucket["energy_rms"].append(float(row.get("energy_rms", 0.0)))
            mood = row.get("mood_auto", {})
            bucket["mood_happy"].append(float(mood.get("happy", 0.0)))
            bucket["mood_sad"].append(float(mood.get("sad", 0.0)))
            bucket["mood_angry"].append(float(mood.get("angry", 0.0)))

        result: list[dict[str, Any]] = []
        for week_start, values in sorted(buckets.items()):
            result.append(
                {
                    "week_start": week_start,
                    "samples": values["samples"],
                    "pitch_mean_hz": self._safe_mean(values["pitch_mean_hz"]),
                    "pitch_min_hz": self._safe_mean(values["pitch_min_hz"]),
                    "pitch_max_hz": self._safe_mean(values["pitch_max_hz"]),
                    "pitch_std_hz": self._safe_mean(values["pitch_std_hz"]),
                    "energy_rms": self._safe_mean(values["energy_rms"]),
                    "mood_happy": self._safe_mean(values["mood_happy"]),
                    "mood_sad": self._safe_mean(values["mood_sad"]),
                    "mood_angry": self._safe_mean(values["mood_angry"]),
                }
            )
        return result

    def get_weekly_voice_summary(self) -> list[dict[str, Any]]:
        """Build weekly aggregated voice metrics."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        hydrated = self._hydrate_voice_rows(snapshot["voice"], include_sensitive=True)
        return self._build_weekly_voice_summary(hydrated)

    @staticmethod
    def _safe_mean(values: list[float]) -> float:
        """Mean helper returning 0 for empty arrays."""
        if not values:
            return 0.0
        return float(sum(values) / len(values))

    def add_medication_record(
        self,
        target_date: date,
        taken: bool,
        hour: str | None,
        dose: str | None,
        notes: str | None,
        next_medication_date: str | None = None,
        update_next_date: bool = True,
    ) -> None:
        """Save medication log for a day."""
        state = self.repository.load()
        record = {
            "id": uuid4().hex,
            "date": target_date.isoformat(),
            "taken": bool(taken),
            "hour": self._normalize_optional_text(hour),
            "dose": (
                self._normalize_optional_text(dose) or state["health_config"].get("medication_dose")
            ),
            "notes": self._normalize_optional_text(notes),
            "created_at": utc_now_iso(),
        }
        state["records"]["medication"].append(record)
        if taken:
            cfg = state["health_config"]
            if not update_next_date:
                pass
            elif next_medication_date and _parse_iso_date(next_medication_date):
                cfg["next_medication_date"] = next_medication_date
            else:
                period = cfg.get("medication_every_days")
                if period:
                    cfg["next_medication_date"] = (
                        target_date + timedelta(days=int(period))
                    ).isoformat()
        self.repository.save(state)

    def list_medication_records(self) -> list[dict[str, Any]]:
        """Return medication records sorted by date."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        return list(snapshot["medication"])

    def add_visit_record(
        self,
        target_date: date,
        visit_type: str,
        completed: bool,
        next_visit_date: str | None,
        notes: str | None,
    ) -> None:
        """Save medical/psychology visit record."""
        if visit_type not in {"medical", "psychology"}:
            raise DataStoreError("Tipo de visita no válido.")
        state = self.repository.load()
        record = {
            "id": uuid4().hex,
            "date": target_date.isoformat(),
            "visit_type": visit_type,
            "completed": bool(completed),
            "next_visit_date": next_visit_date if _parse_iso_date(next_visit_date) else None,
            "notes": self._normalize_optional_text(notes),
            "created_at": utc_now_iso(),
        }
        state["records"]["visits"].append(record)
        if completed:
            if visit_type == "medical":
                state["health_config"]["next_medical_visit_date"] = record["next_visit_date"]
            else:
                state["health_config"]["next_psych_visit_date"] = record["next_visit_date"]
            if record["next_visit_date"] is not None:
                self._ensure_follow_up_appointment_prep(
                    state=state,
                    visit_type=visit_type,
                    next_visit_date=record["next_visit_date"],
                )
        self.repository.save(state)

    def _ensure_follow_up_appointment_prep(
        self,
        state: dict[str, Any],
        visit_type: str,
        next_visit_date: str,
    ) -> None:
        """Create a follow-up preparation draft when a next visit is scheduled."""
        records = self._record_collection(state, "appointment_preps")
        existing = next(
            (
                item
                for item in records
                if item.get("target_date") == next_visit_date
                and item.get("appointment_type") == visit_type
                and not item.get("is_completed", False)
            ),
            None,
        )
        if existing is not None:
            return

        title = (
            "Próxima revisión médica"
            if visit_type == "medical"
            else "Próxima sesión de seguimiento"
        )
        now = utc_now_iso()
        records.append(
            {
                "id": uuid4().hex,
                "target_date": next_visit_date,
                "appointment_type": visit_type,
                "title": title,
                "questions": None,
                "talking_points": None,
                "follow_up_step": None,
                "outcome_notes": None,
                "is_completed": False,
                "created_at": now,
                "updated_at": now,
                "completed_at": None,
            }
        )

    def list_visit_records(self) -> list[dict[str, Any]]:
        """Return visit records sorted by date."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        return list(snapshot["visits"])

    def add_other_event(
        self,
        target_date: date,
        category: str,
        tags_raw: str | None,
        notes: str,
    ) -> None:
        """Save other event/note entry."""
        tags = []
        if tags_raw:
            tags = [token.strip() for token in tags_raw.split(",") if token.strip()]
        state = self.repository.load()
        state["records"]["other_events"].append(
            {
                "id": uuid4().hex,
                "date": target_date.isoformat(),
                "category": self._normalize_optional_text(category) or "general",
                "tags": tags,
                "notes": notes.strip(),
                "created_at": utc_now_iso(),
            }
        )
        self.repository.save(state)

    def list_other_events(self) -> list[dict[str, Any]]:
        """List free-form events sorted by date."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        return list(snapshot["events"])

    def get_habit_selection_for_date(self, target_date: date) -> HabitSelection:
        """Get adaptive checklist for day.

        Args:
            target_date: Day to display habits.

        Returns:
            HabitSelection with shown and completed habits.
        """
        state = self.repository.load()
        day_key = target_date.isoformat()
        existing = next(
            (item for item in state["records"]["habits"] if item.get("date") == day_key),
            None,
        )
        catalog = list(state["habit_catalog"])
        if not catalog:
            return HabitSelection(target_date=target_date, shown_habits=[], completed_habits=[])

        if existing:
            shown_ids = existing.get("shown_habits", [])
            shown = [habit for habit in catalog if habit["id"] in shown_ids]
            return HabitSelection(
                target_date=target_date,
                shown_habits=shown,
                completed_habits=list(existing.get("completed_habits", [])),
            )

        target_count = self._compute_target_habit_count(state=state, reference_date=target_date)
        start = target_date.toordinal() % len(catalog)
        rotated = catalog[start:] + catalog[:start]
        shown = rotated[:target_count]
        return HabitSelection(target_date=target_date, shown_habits=shown, completed_habits=[])

    def save_habit_log(
        self,
        target_date: date,
        shown_habits: list[str],
        completed_habits: list[str],
    ) -> None:
        """Persist checked habits for a day."""
        state = self.repository.load()
        day_key = target_date.isoformat()
        records = state["records"]["habits"]
        existing = next((item for item in records if item.get("date") == day_key), None)
        payload = {
            "id": existing.get("id") if existing else uuid4().hex,
            "date": day_key,
            "shown_habits": list(shown_habits),
            "completed_habits": list(completed_habits),
            "created_at": existing.get("created_at") if existing else utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        if existing:
            existing.update(payload)
        else:
            records.append(payload)
        state["meta"]["last_habit_count"] = len(shown_habits)
        self.repository.save(state)

    def _compute_target_habit_count(self, state: dict[str, Any], reference_date: date) -> int:
        """Calculate adaptive checklist size (3 to 8)."""
        last_count = int(state.get("meta", {}).get("last_habit_count", _MIN_HABITS))
        logs = state["records"]["habits"]
        cutoff = reference_date - timedelta(days=7)
        recent: list[dict[str, Any]] = []
        for row in logs:
            row_day = _parse_iso_date(row.get("date"))
            if row_day is None:
                continue
            if cutoff <= row_day < reference_date:
                recent.append(row)
        if not recent:
            return max(_MIN_HABITS, min(_MAX_HABITS, last_count))

        completion_ratios: list[float] = []
        for row in recent:
            shown = row.get("shown_habits", [])
            completed = row.get("completed_habits", [])
            if not shown:
                continue
            completion_ratios.append(len(completed) / max(1, len(shown)))
        if not completion_ratios:
            return max(_MIN_HABITS, min(_MAX_HABITS, last_count))

        ratio = sum(completion_ratios) / len(completion_ratios)
        if ratio >= 0.8:
            return min(_MAX_HABITS, last_count + 1)
        if ratio <= 0.4:
            return max(_MIN_HABITS, last_count - 1)
        return max(_MIN_HABITS, min(_MAX_HABITS, last_count))

    def list_habit_logs(self) -> list[dict[str, Any]]:
        """Return habit log entries sorted by date."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        return list(snapshot["habits"])

    def get_dashboard_snapshot(self, today: date | None = None) -> DashboardSnapshot:
        """Build an action-oriented dashboard snapshot for the companion."""
        today = today or date.today()
        state = self.repository.load()
        stage = self._coerce_journey_stage(state["profile"].get("journey_stage"))
        alerts = self.get_due_alerts(today=today)

        roadmap_items = [
            self._build_roadmap_item(item)
            for item in self._record_collection(state, "roadmap_items")
        ]
        visible_open_items = [
            item
            for item in roadmap_items
            if item.is_active and not item.is_hidden and not item.completed
        ]
        visible_open_items.sort(key=lambda item: self._roadmap_priority(item, stage))

        overdue_roadmap_items = [
            item
            for item in visible_open_items
            if item.target_date is not None and (_parse_iso_date(item.target_date) or today) < today
        ]

        completed_recent = [
            item
            for item in roadmap_items
            if item.completed
            and item.completed_at
            and (_parse_iso_date(item.target_date) or today) >= (today - timedelta(days=7))
        ]
        completed_recent.sort(key=lambda item: item.updated_at, reverse=True)

        appointments = [
            self._build_appointment_prep(item)
            for item in self._record_collection(state, "appointment_preps")
        ]
        upcoming_appointments = [
            item
            for item in appointments
            if not item.is_completed and (_parse_iso_date(item.target_date) or today) >= today
        ]
        upcoming_appointments.sort(key=lambda item: (item.target_date, item.title.lower()))

        week_start = today - timedelta(days=6)
        wellbeing_logs = self.list_wellbeing_logs(date_from=week_start, date_to=today)
        snapshot = self._build_state_snapshot(state)
        weekly_voice_samples = len(
            [
                row
                for row in snapshot["voice"]
                if (parsed := _parse_iso_date(row.get("target_date"))) is not None
                and week_start <= parsed <= today
            ]
        )
        weekly_completed_steps = len(
            [
                item
                for item in roadmap_items
                if item.completed
                and item.completed_at is not None
                and week_start
                <= datetime.strptime(item.completed_at[:10], ISO_DATE).date()
                <= today
            ]
        )

        recommended_action = self._recommend_dashboard_action(
            stage=stage,
            alerts=alerts,
            overdue_roadmap_items=overdue_roadmap_items,
            upcoming_appointments=upcoming_appointments,
            open_roadmap_items=visible_open_items,
        )

        return DashboardSnapshot(
            pending_alerts=alerts,
            overdue_roadmap_items=overdue_roadmap_items,
            upcoming_appointments=upcoming_appointments[:3],
            open_roadmap_items=visible_open_items[:5],
            completed_recent_roadmap_items=completed_recent[:3],
            weekly_completed_steps=weekly_completed_steps,
            weekly_wellbeing_logs=len(wellbeing_logs),
            weekly_voice_samples=weekly_voice_samples,
            recommended_action=recommended_action,
            journey_stage=stage,
        )

    def _recommend_dashboard_action(
        self,
        stage: JourneyStage,
        alerts: list[str],
        overdue_roadmap_items: list[RoadmapItem],
        upcoming_appointments: list[AppointmentPrepRecord],
        open_roadmap_items: list[RoadmapItem],
    ) -> str:
        """Suggest the next best action for the user."""
        if alerts:
            return alerts[0]
        if upcoming_appointments:
            return f"Preparar la cita: {upcoming_appointments[0].title}"
        if overdue_roadmap_items:
            return f"Retoma este paso pendiente: {overdue_roadmap_items[0].title}"
        if stage == "post_transition":
            for item in open_roadmap_items:
                if item.category in {"salud", "bienestar"}:
                    return f"Prioriza tu revisión: {item.title}"
        if open_roadmap_items:
            return f"Siguiente paso sugerido: {open_roadmap_items[0].title}"
        return "Hoy no hay pendientes importantes. Puedes registrar cómo te encuentras."

    def get_due_alerts(self, today: date | None = None) -> list[str]:
        """Build reminder messages for due/overdue items."""
        if today is None:
            today = date.today()
        state = self.repository.load()
        alerts: list[str] = []

        alerts.extend(self._get_medication_alerts(state, today))

        medical_due = _parse_iso_date(state["health_config"].get("next_medical_visit_date"))
        if medical_due and medical_due <= today:
            alerts.append(
                f"Tienes una consulta médica pendiente (fecha objetivo: {medical_due.isoformat()})."
            )

        psych_due = _parse_iso_date(state["health_config"].get("next_psych_visit_date"))
        if psych_due and psych_due <= today:
            alerts.append(
                f"Tienes una consulta de psicología/especialista pendiente "
                f"(fecha objetivo: {psych_due.isoformat()})."
            )
        return alerts

    def _get_medication_alerts(self, state: dict[str, Any], today: date) -> list[str]:
        """Compute medication due/overdue messages."""
        cfg = state["health_config"]
        start = _parse_iso_date(cfg.get("next_medication_date"))
        period = cfg.get("medication_every_days")
        if start is None:
            return []

        expected_dates: list[date] = []
        if period and int(period) > 0:
            cursor = start
            while cursor <= today:
                expected_dates.append(cursor)
                cursor += timedelta(days=int(period))
        else:
            if start <= today:
                expected_dates.append(start)

        taken_days = {
            _parse_iso_date(row.get("date"))
            for row in state["records"]["medication"]
            if row.get("taken")
        }
        alerts: list[str] = []
        overdue_count = 0
        oldest_overdue: date | None = None
        for expected in expected_dates:
            if expected in taken_days:
                continue
            if expected == today:
                alerts.append(t("reminders.medication.today_due"))
                continue
            overdue_count += 1
            if oldest_overdue is None:
                oldest_overdue = expected
        if overdue_count and oldest_overdue is not None:
            alerts.append(
                t(
                    "reminders.medication.overdue_summary",
                    count=str(overdue_count),
                    date=oldest_overdue.isoformat(),
                )
            )
        return alerts

    def _build_daily_summary_from_snapshot(
        self,
        day_key: str,
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Build non-sensitive daily summary from a precomputed snapshot."""
        voice = list(snapshot["voice_by_date"].get(day_key, []))
        meds = list(snapshot["medication_by_date"].get(day_key, []))
        visits = list(snapshot["visits_by_date"].get(day_key, []))
        events = list(snapshot["events_by_date"].get(day_key, []))
        habits = list(snapshot["habits_by_date"].get(day_key, []))
        wellbeing = list(snapshot["wellbeing_by_date"].get(day_key, []))

        mood_h = [float(v.get("mood_auto", {}).get("happy", 0.0)) for v in voice]
        mood_s = [float(v.get("mood_auto", {}).get("sad", 0.0)) for v in voice]
        mood_a = [float(v.get("mood_auto", {}).get("angry", 0.0)) for v in voice]
        energy = [float(v.get("energy_rms", 0.0)) for v in voice]

        return {
            "date": day_key,
            "voice_samples": len(voice),
            "voice_energy_avg": self._safe_mean(energy),
            "voice_mood_happy_avg": self._safe_mean(mood_h),
            "voice_mood_sad_avg": self._safe_mean(mood_s),
            "voice_mood_angry_avg": self._safe_mean(mood_a),
            "medication": meds,
            "visits": visits,
            "other_events": events,
            "habits": habits,
            "wellbeing": wellbeing,
        }

    def get_daily_summary(self, target_date: date) -> dict[str, Any]:
        """Build non-sensitive daily summary for data view."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        return self._build_daily_summary_from_snapshot(target_date.isoformat(), snapshot)

    def build_daily_summaries(self) -> list[dict[str, Any]]:
        """Build summaries for all known days, sorted by date."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        return [
            self._build_daily_summary_from_snapshot(day_key, snapshot)
            for day_key in snapshot["all_dates"]
        ]

    def build_calendar_dates_with_activity(self) -> dict[str, set[str]]:
        """Return date -> activity tags map for calendar marks."""
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)
        tags: dict[str, set[str]] = {}

        for day_key in snapshot["voice_by_date"].keys():
            if _parse_iso_date(day_key) is None:
                continue
            tags.setdefault(day_key, set()).add("voice")
        for day_key in snapshot["medication_by_date"].keys():
            if _parse_iso_date(day_key) is None:
                continue
            tags.setdefault(day_key, set()).add("medication")
        for day_key in snapshot["visits_by_date"].keys():
            if _parse_iso_date(day_key) is None:
                continue
            tags.setdefault(day_key, set()).add("visit")
        for day_key in snapshot["events_by_date"].keys():
            if _parse_iso_date(day_key) is None:
                continue
            tags.setdefault(day_key, set()).add("event")
        for day_key in snapshot["habits_by_date"].keys():
            if _parse_iso_date(day_key) is None:
                continue
            tags.setdefault(day_key, set()).add("habit")
        return tags

    def to_export_frames(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Build export dataframes with privacy policy applied.

        Args:
            date_from: Optional start date for filtering (inclusive).
            date_to: Optional end date for filtering (inclusive).

        Returns:
            Dictionary of sheet name to DataFrame.
        """
        state = self.repository.load()
        snapshot = self._build_state_snapshot(state)

        def _in_range(day_key: str) -> bool:
            if date_from is None and date_to is None:
                return True
            parsed = _parse_iso_date(day_key)
            if parsed is None:
                return False
            if date_from is not None and parsed < date_from:
                return False
            if date_to is not None and parsed > date_to:
                return False
            return True

        voice_rows = snapshot["voice"]
        if date_from is not None or date_to is not None:
            voice_rows = [r for r in voice_rows if _in_range(r.get("target_date", ""))]
            snapshot = dict(snapshot)
            snapshot["medication"] = [
                r for r in snapshot["medication"] if _in_range(r.get("date", ""))
            ]
            snapshot["visits"] = [r for r in snapshot["visits"] if _in_range(r.get("date", ""))]
            snapshot["events"] = [r for r in snapshot["events"] if _in_range(r.get("date", ""))]
            snapshot["habits"] = [r for r in snapshot["habits"] if _in_range(r.get("date", ""))]
            snapshot["appointment_preps"] = [
                r for r in snapshot["appointment_preps"] if _in_range(r.get("target_date", ""))
            ]
            snapshot["wellbeing_logs"] = [
                r for r in snapshot["wellbeing_logs"] if _in_range(r.get("target_date", ""))
            ]
            snapshot["milestones"] = [
                r for r in snapshot["milestones"] if _in_range(r.get("target_date", ""))
            ]
            snapshot["roadmap_items"] = [
                r for r in snapshot["roadmap_items"] if _in_range(r.get("target_date", ""))
            ]
            snapshot["all_dates"] = [k for k in snapshot["all_dates"] if _in_range(k)]

        weekly_voice_rows = self._hydrate_voice_rows(voice_rows, include_sensitive=True)
        weekly_voice = pd.DataFrame(self._build_weekly_voice_summary(weekly_voice_rows))
        if weekly_voice.empty:
            weekly_voice = pd.DataFrame(
                columns=[
                    "week_start",
                    "samples",
                    "pitch_mean_hz",
                    "pitch_min_hz",
                    "pitch_max_hz",
                    "pitch_std_hz",
                    "energy_rms",
                    "mood_happy",
                    "mood_sad",
                    "mood_angry",
                ]
            )

        medication = pd.DataFrame(snapshot["medication"])
        visits = pd.DataFrame(snapshot["visits"])
        events = pd.DataFrame(snapshot["events"])
        habits = pd.DataFrame(snapshot["habits"])
        roadmap = pd.DataFrame(snapshot["roadmap_items"])
        appointment_preps = pd.DataFrame(snapshot["appointment_preps"])
        wellbeing = pd.DataFrame(snapshot["wellbeing_logs"])
        milestones = pd.DataFrame(snapshot["milestones"])

        daily_rows: list[dict[str, Any]] = []
        for key in snapshot["all_dates"]:
            summary = self._build_daily_summary_from_snapshot(key, snapshot)
            # Privacy rule: no daily pitch values here.
            daily_rows.append(
                {
                    "date": summary["date"],
                    "voice_samples": summary["voice_samples"],
                    "voice_energy_avg": summary["voice_energy_avg"],
                    "voice_mood_happy_avg": summary["voice_mood_happy_avg"],
                    "voice_mood_sad_avg": summary["voice_mood_sad_avg"],
                    "voice_mood_angry_avg": summary["voice_mood_angry_avg"],
                    "medication_entries": len(summary["medication"]),
                    "visit_entries": len(summary["visits"]),
                    "event_entries": len(summary["other_events"]),
                    "habit_entries": len(summary["habits"]),
                    "wellbeing_entries": len(summary["wellbeing"]),
                }
            )
        daily = pd.DataFrame(daily_rows)

        return {
            "resumen_diario": daily,
            "voz_semanal": weekly_voice,
            "medicacion": medication,
            "visitas": visits,
            "eventos": events,
            "habitos": habits,
            "hoja_ruta": roadmap,
            "citas_preparadas": appointment_preps,
            "bienestar": wellbeing,
            "hitos": milestones,
        }
