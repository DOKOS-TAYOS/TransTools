"""Generate a fuller fake patient history aligned with the current app schema."""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

# Add src to path for imports
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config.paths import get_output_dir, get_patient_history_path  # noqa: E402
from core.privacy import VoicePrivacyService  # noqa: E402
from core.repository import default_history_state  # noqa: E402

DEFAULT_HABIT_IDS = [
    "hidratarse",
    "dormir",
    "caminar",
    "respirar",
    "diario",
    "desconexion",
]


def _random_id() -> str:
    return uuid4().hex


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_date(value: date) -> str:
    return value.isoformat()


def _iso_datetime(value: date, hour: int, minute: int) -> str:
    recorded_at = datetime.combine(value, time(hour=hour, minute=minute), tzinfo=timezone.utc)
    return recorded_at.strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_catalog_ids(catalog_ids: Sequence[str]) -> list[str]:
    normalized = [habit_id for habit_id in catalog_ids if isinstance(habit_id, str) and habit_id]
    return normalized or list(DEFAULT_HABIT_IDS)


def generate_voice_records(
    start: date,
    end: date,
    privacy: VoicePrivacyService,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate fake voice records with stable tone and mood ranges."""
    records: list[dict[str, Any]] = []
    pitch_base = 120.0
    pitch_std_base = 8.0
    energy_base = 0.0034
    mood_base = {"happy": 0.18, "sad": 0.65, "angry": 0.17}

    current = start
    while current <= end:
        if rng.random() < 0.45:
            n_samples = rng.randint(1, 2)
            for _ in range(n_samples):
                drift = rng.gauss(0, 2)
                day_offset = (current - start).days
                pitch_mean = max(105.0, min(135.0, pitch_base + drift * day_offset / 30))
                pitch_std = max(4.0, min(15.0, pitch_std_base + rng.gauss(0, 1.5)))
                pitch_min = pitch_mean - pitch_std * 1.5
                pitch_max = pitch_mean + pitch_std * 1.5

                mood_h = max(0.05, min(0.5, mood_base["happy"] + rng.gauss(0, 0.08)))
                mood_s = max(0.2, min(0.9, mood_base["sad"] + rng.gauss(0, 0.08)))
                mood_a = max(0.05, min(0.4, mood_base["angry"] + rng.gauss(0, 0.05)))
                total = mood_h + mood_s + mood_a
                mood_h, mood_s, mood_a = mood_h / total, mood_s / total, mood_a / total

                sensitive = {
                    "pitch_mean_hz": round(pitch_mean, 2),
                    "pitch_std_hz": round(pitch_std, 2),
                    "pitch_min_hz": round(pitch_min, 2),
                    "pitch_max_hz": round(pitch_max, 2),
                }
                encrypted = privacy.encrypt_metrics(sensitive)

                records.append(
                    {
                        "id": _random_id(),
                        "recorded_at": _iso_datetime(
                            current,
                            rng.randint(9, 21),
                            rng.choice([0, 10, 20, 30, 40, 50]),
                        ),
                        "target_date": _iso_date(current),
                        "energy_rms": round(
                            max(0.001, energy_base * (0.8 + rng.random() * 0.4)),
                            16,
                        ),
                        "mood_auto": {
                            "happy": round(mood_h, 16),
                            "sad": round(mood_s, 16),
                            "angry": round(mood_a, 16),
                        },
                        "mood_self": {
                            "happy": round(0.4 + rng.random() * 0.4, 1),
                            "sad": round(0.3 + rng.random() * 0.3, 1),
                            "angry": round(0.1 + rng.random() * 0.2, 1),
                        },
                        "tone_encrypted": encrypted,
                        "audio_saved_path": None,
                    }
                )
        current += timedelta(days=1)

    return sorted(records, key=lambda row: (row["target_date"], row["recorded_at"]))


def generate_medication_records(
    start: date,
    end: date,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate medication records with a lightweight every-two-days pattern."""
    records: list[dict[str, Any]] = []
    current = start
    while current <= end:
        records.append(
            {
                "id": _random_id(),
                "date": _iso_date(current),
                "taken": True,
                "hour": rng.choice(["09:00", "10:30", "21:00"]),
                "dose": "0.3",
                "notes": "seguimiento habitual" if rng.random() < 0.2 else None,
                "created_at": _iso_now(),
            }
        )
        current += timedelta(days=2)

    if not records or records[-1]["date"] != _iso_date(end):
        records.append(
            {
                "id": _random_id(),
                "date": _iso_date(end),
                "taken": True,
                "hour": "09:00",
                "dose": "0.3",
                "notes": None,
                "created_at": _iso_now(),
            }
        )

    return records


def generate_visits(
    start: date,
    end: date,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate past psychology and medical follow-up visits."""
    records: list[dict[str, Any]] = []

    psychology_date = start + timedelta(days=7)
    while psychology_date <= end:
        next_visit_date = psychology_date + timedelta(days=14)
        records.append(
            {
                "id": _random_id(),
                "date": _iso_date(psychology_date),
                "visit_type": "psychology",
                "completed": True,
                "next_visit_date": _iso_date(next_visit_date),
                "notes": "seguimiento emocional" if rng.random() < 0.5 else None,
                "created_at": _iso_now(),
            }
        )
        psychology_date += timedelta(days=14)

    medical_date = start + timedelta(days=14)
    while medical_date <= end:
        next_visit_date = medical_date + timedelta(days=28)
        records.append(
            {
                "id": _random_id(),
                "date": _iso_date(medical_date),
                "visit_type": "medical",
                "completed": True,
                "next_visit_date": _iso_date(next_visit_date),
                "notes": "control general" if rng.random() < 0.5 else None,
                "created_at": _iso_now(),
            }
        )
        medical_date += timedelta(days=28)

    return sorted(records, key=lambda row: (row["date"], row["visit_type"]))


def generate_habits(
    start: date,
    end: date,
    catalog_ids: Sequence[str],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate habit logs for most days of the period."""
    normalized_catalog_ids = _normalize_catalog_ids(catalog_ids)
    records: list[dict[str, Any]] = []
    current = start

    while current <= end:
        should_log = rng.random() < 0.65 or current == end
        if should_log:
            max_shown = min(6, len(normalized_catalog_ids))
            n_shown = rng.randint(3, max_shown) if max_shown >= 3 else max_shown
            start_idx = current.toordinal() % len(normalized_catalog_ids)
            shown = (normalized_catalog_ids[start_idx:] + normalized_catalog_ids[:start_idx])[
                :n_shown
            ]
            n_completed = rng.randint(1, len(shown)) if shown else 0
            completed = rng.sample(shown, n_completed) if shown else []
            records.append(
                {
                    "id": _random_id(),
                    "date": _iso_date(current),
                    "shown_habits": shown,
                    "completed_habits": completed,
                    "created_at": _iso_now(),
                    "updated_at": _iso_now(),
                }
            )
        current += timedelta(days=1)

    return records


def generate_other_events(
    start: date,
    end: date,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate occasional free-form events across the current year."""
    tags_pool = [
        ("general", ["rutina", "organizacion"]),
        ("general", ["autocuidado"]),
        ("general", ["seguimiento", "progreso"]),
        ("general", ["descanso"]),
    ]
    records: list[dict[str, Any]] = []
    current = start + timedelta(days=5)

    while current <= end:
        category, tags = rng.choice(tags_pool)
        records.append(
            {
                "id": _random_id(),
                "date": _iso_date(current),
                "category": category,
                "tags": list(tags),
                "notes": f"Evento de seguimiento del {current.isoformat()}",
                "created_at": _iso_now(),
            }
        )
        current += timedelta(days=21)

    return records


def generate_wellbeing_logs(
    start: date,
    end: date,
    medication: Sequence[dict[str, Any]],
    visits: Sequence[dict[str, Any]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate recurring wellbeing check-ins tied to everyday care."""
    records: list[dict[str, Any]] = []
    medication_dates = {str(row.get("date")) for row in medication}
    visit_dates = {str(row.get("date")) for row in visits}
    current = start

    while current <= end:
        if rng.random() < 0.5 or current == end:
            day_key = _iso_date(current)
            linked_source = None
            if day_key in visit_dates:
                linked_source = "visit"
            elif day_key in medication_dates:
                linked_source = "medication"
            records.append(
                {
                    "id": _random_id(),
                    "target_date": day_key,
                    "mood": rng.randint(2, 5),
                    "energy": rng.randint(2, 5),
                    "sleep": rng.randint(1, 5),
                    "side_effects": "cansancio ligero" if rng.random() < 0.18 else None,
                    "notes": "seguimiento diario" if rng.random() < 0.3 else None,
                    "linked_source": linked_source,
                    "created_at": _iso_now(),
                    "updated_at": _iso_now(),
                }
            )
        current += timedelta(days=3)

    return sorted(records, key=lambda row: row["target_date"])


def generate_milestones(
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    """Generate milestone entries that make the process timeline less empty."""
    titles = [
        ("Inicio de rutina estable", "Se consolido una base de seguimiento."),
        ("Revision de objetivos", "Se ajustaron prioridades de las proximas semanas."),
        ("Mejor semana de autocuidado", "Se mantuvo mas continuidad en habitos y descanso."),
    ]
    records: list[dict[str, Any]] = []
    current = start + timedelta(days=18)

    for title, details in titles:
        if current > end:
            break
        records.append(
            {
                "id": _random_id(),
                "target_date": _iso_date(current),
                "title": title,
                "details": details,
                "source": "fake_generator",
                "created_at": _iso_now(),
                "updated_at": _iso_now(),
            }
        )
        current += timedelta(days=32)

    return records


def generate_roadmap_items(
    base_items: Sequence[dict[str, Any]],
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    """Generate a roadmap with both completed and open entries."""
    records = deepcopy(list(base_items))
    for index, item in enumerate(records):
        target_date = start + timedelta(days=7 + index * 16)
        item["updated_at"] = _iso_now()

        if index < 3 and target_date <= end:
            item["target_date"] = _iso_date(target_date)
            item["completed"] = True
            item["completed_at"] = _iso_datetime(target_date, 18, 0)
            item["is_active"] = False
        elif index < 5:
            item["target_date"] = _iso_date(end + timedelta(days=(index - 2) * 7 + 3))
            item["completed"] = False
            item["completed_at"] = None
            item["is_active"] = True
        else:
            item["target_date"] = _iso_date(end + timedelta(days=index + 5))
            item["completed"] = False
            item["completed_at"] = None
            item["is_active"] = False

    records.append(
        {
            "id": _random_id(),
            "category": "bienestar",
            "title": "Preparar siguiente revision personal",
            "details": "Revisar avances y decidir el siguiente foco pequeno.",
            "target_date": _iso_date(end + timedelta(days=10)),
            "is_active": True,
            "is_hidden": False,
            "completed": False,
            "source": "fake_generator",
            "created_at": _iso_now(),
            "updated_at": _iso_now(),
            "completed_at": None,
        }
    )
    return sorted(
        records,
        key=lambda row: (row.get("target_date") or "9999-12-31", row.get("title", "")),
    )


def generate_appointment_preps(
    visits: Sequence[dict[str, Any]],
    end: date,
) -> list[dict[str, Any]]:
    """Generate companion appointment preparation records from visits."""
    records: list[dict[str, Any]] = []
    seen_future: set[tuple[str, str]] = set()

    for visit in visits:
        visit_date = str(visit.get("date"))
        visit_type = str(visit.get("visit_type", "general"))
        title = "Revision medica" if visit_type == "medical" else "Sesion de seguimiento"
        records.append(
            {
                "id": _random_id(),
                "target_date": visit_date,
                "appointment_type": visit_type,
                "title": title,
                "questions": "Repasar dudas pendientes.",
                "talking_points": "Comentar evolucion reciente.",
                "follow_up_step": "Anotar siguientes pasos al cerrar la cita.",
                "outcome_notes": "Cita completada y registrada.",
                "is_completed": True,
                "created_at": _iso_now(),
                "updated_at": _iso_now(),
                "completed_at": _iso_now(),
            }
        )

        next_visit_date = str(visit.get("next_visit_date") or "")
        future_key = (next_visit_date, visit_type)
        if next_visit_date and future_key not in seen_future:
            seen_future.add(future_key)
            future_title = (
                "Proxima revision medica" if visit_type == "medical" else "Proxima sesion"
            )
            records.append(
                {
                    "id": _random_id(),
                    "target_date": next_visit_date,
                    "appointment_type": visit_type,
                    "title": future_title,
                    "questions": "Llevar preguntas concretas del ultimo periodo.",
                    "talking_points": "Resumir cambios desde la cita anterior.",
                    "follow_up_step": None,
                    "outcome_notes": None,
                    "is_completed": False,
                    "created_at": _iso_now(),
                    "updated_at": _iso_now(),
                    "completed_at": None,
                }
            )

    records.append(
        {
            "id": _random_id(),
            "target_date": _iso_date(end + timedelta(days=10)),
            "appointment_type": "general",
            "title": "Revision de objetivos del mes",
            "questions": "Que quiero priorizar ahora?",
            "talking_points": "Balance rapido de avances, energia y ritmo.",
            "follow_up_step": None,
            "outcome_notes": None,
            "is_completed": False,
            "created_at": _iso_now(),
            "updated_at": _iso_now(),
            "completed_at": None,
        }
    )

    return sorted(records, key=lambda row: (row["target_date"], row["title"]))


def build_fake_history(
    start: date,
    end: date,
    privacy: VoicePrivacyService,
    catalog_ids: Sequence[str],
    existing_voice: Sequence[dict[str, Any]],
    rng: random.Random,
) -> dict[str, Any]:
    """Build a fake patient-history payload without touching the filesystem."""
    history = default_history_state()
    normalized_catalog_ids = _normalize_catalog_ids(catalog_ids)

    voice = generate_voice_records(start, end, privacy, rng)
    voice.extend(existing_voice)
    voice = sorted(voice, key=lambda row: (row["target_date"], row.get("recorded_at", "")))

    medication = generate_medication_records(start, end, rng)
    visits = generate_visits(start, end, rng)
    habits = generate_habits(start, end, normalized_catalog_ids, rng)
    other_events = generate_other_events(start, end, rng)
    wellbeing_logs = generate_wellbeing_logs(start, end, medication, visits, rng)
    milestones = generate_milestones(start, end)
    roadmap_items = generate_roadmap_items(history["records"]["roadmap_items"], start, end)
    appointment_preps = generate_appointment_preps(visits, end)

    history["records"]["voice"] = voice
    history["records"]["medication"] = medication
    history["records"]["visits"] = visits
    history["records"]["other_events"] = other_events
    history["records"]["habits"] = habits
    history["records"]["roadmap_items"] = roadmap_items
    history["records"]["appointment_preps"] = appointment_preps
    history["records"]["wellbeing_logs"] = wellbeing_logs
    history["records"]["milestones"] = milestones
    return history


def load_existing_real_voice_records(history_path: Path) -> list[dict[str, Any]]:
    """Load only existing voice records that preserve a saved audio path."""
    if not history_path.exists():
        return []
    existing = json.loads(history_path.read_text(encoding="utf-8"))
    all_voice = existing.get("records", {}).get("voice", [])
    return [row for row in all_voice if row.get("audio_saved_path")]


def load_habit_catalog_ids(profile_path: Path) -> list[str]:
    """Load the saved habit catalog IDs, with a fallback to base IDs."""
    if not profile_path.exists():
        return list(DEFAULT_HABIT_IDS)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    catalog = profile.get("habit_catalog", [])
    if not isinstance(catalog, list):
        return list(DEFAULT_HABIT_IDS)
    ids = [row.get("id") for row in catalog if isinstance(row, dict)]
    return _normalize_catalog_ids([habit_id for habit_id in ids if isinstance(habit_id, str)])


def main() -> None:
    today = date.today()
    start = date(today.year, 1, 1)

    output_dir = get_output_dir()
    history_path = get_patient_history_path()
    profile_path = output_dir / "patient_profile.json"
    key_path = output_dir / ".voice_metrics.key"

    privacy = VoicePrivacyService(key_path=key_path)
    existing_voice = load_existing_real_voice_records(history_path)
    catalog_ids = load_habit_catalog_ids(profile_path)

    history = build_fake_history(
        start=start,
        end=today,
        privacy=privacy,
        catalog_ids=catalog_ids,
        existing_voice=existing_voice,
        rng=random.Random(),
    )

    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "Generated history: "
        f"{len(history['records']['voice'])} voice, "
        f"{len(history['records']['medication'])} medication, "
        f"{len(history['records']['visits'])} visits, "
        f"{len(history['records']['other_events'])} events, "
        f"{len(history['records']['habits'])} habits, "
        f"{len(history['records']['roadmap_items'])} roadmap, "
        f"{len(history['records']['appointment_preps'])} appointments, "
        f"{len(history['records']['wellbeing_logs'])} wellbeing, "
        f"{len(history['records']['milestones'])} milestones"
    )
    print(f"Saved to {history_path}")


if __name__ == "__main__":
    main()
