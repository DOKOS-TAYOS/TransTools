"""Generate simulated patient history from Jan 1 to today."""

from __future__ import annotations

import json
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Add src to path for imports
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config.paths import get_output_dir, get_patient_history_path  # noqa: E402
from core.privacy import VoicePrivacyService  # noqa: E402


def _random_id() -> str:
    return uuid4().hex


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_date(d: date) -> str:
    return d.isoformat()


def generate_voice_records(
    start: date,
    end: date,
    privacy: VoicePrivacyService,
) -> list[dict]:
    """Generate voice records with consistent pitch and mood."""
    records: list[dict] = []
    # Base pitch coherente con grabaciones reales (~116-122 Hz)
    pitch_base = 120.0
    pitch_std_base = 8.0
    energy_base = 0.0034
    # Mood base similar al actual: más sad que happy
    mood_base = {"happy": 0.18, "sad": 0.65, "angry": 0.17}

    current = start
    while current <= end:
        # 2-4 grabaciones por semana, días aleatorios
        if random.random() < 0.45:
            n_samples = random.randint(1, 2)
            for _ in range(n_samples):
                # Variación suave del pitch (tendencia coherente con reales)
                drift = random.gauss(0, 2)
                pitch_mean = max(105, min(135, pitch_base + drift * (current - start).days / 30))
                pitch_std = max(4, min(15, pitch_std_base + random.gauss(0, 1.5)))
                pitch_min = pitch_mean - pitch_std * 1.5
                pitch_max = pitch_mean + pitch_std * 1.5

                mood_h = max(0.05, min(0.5, mood_base["happy"] + random.gauss(0, 0.08)))
                mood_s = max(0.2, min(0.9, mood_base["sad"] + random.gauss(0, 0.08)))
                mood_a = max(0.05, min(0.4, mood_base["angry"] + random.gauss(0, 0.05)))
                # Normalizar para que sumen ~1
                total = mood_h + mood_s + mood_a
                mood_h, mood_s, mood_a = mood_h / total, mood_s / total, mood_a / total

                energy = max(0.001, energy_base * (0.8 + random.random() * 0.4))
                mood_self_h = round(0.4 + random.random() * 0.4, 1)
                mood_self_s = round(0.3 + random.random() * 0.3, 1)
                mood_self_a = round(0.1 + random.random() * 0.2, 1)

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
                        "recorded_at": _iso_now(),
                        "target_date": _iso_date(current),
                        "energy_rms": round(energy, 16),
                        "mood_auto": {
                            "happy": round(mood_h, 16),
                            "sad": round(mood_s, 16),
                            "angry": round(mood_a, 16),
                        },
                        "mood_self": {
                            "happy": mood_self_h,
                            "sad": mood_self_s,
                            "angry": mood_self_a,
                        },
                        "tone_encrypted": encrypted,
                        "audio_saved_path": None,
                    }
                )
        current += timedelta(days=1)

    return sorted(records, key=lambda r: (r["target_date"], r["recorded_at"]))


def generate_medication_records(start: date, end: date) -> list[dict]:
    """Medication every 2 days (from health_config)."""
    records: list[dict] = []
    current = start
    while current <= end:
        records.append(
            {
                "id": _random_id(),
                "date": _iso_date(current),
                "taken": True,
                "hour": "09:00" if random.random() < 0.7 else "10:30",
                "dose": "0.3",
                "notes": None,
                "created_at": _iso_now(),
            }
        )
        current += timedelta(days=2)
    return records


def generate_visits(start: date, end: date) -> list[dict]:
    """Medical and psychology visits."""
    records: list[dict] = []
    # Psicología ~cada 2 semanas, médico ~cada mes
    psych_dates = [
        date(2026, 1, 8),
        date(2026, 1, 22),
        date(2026, 2, 5),
        date(2026, 2, 19),
        date(2026, 3, 5),
    ]
    med_dates = [date(2026, 1, 15), date(2026, 2, 12), date(2026, 3, 9)]
    for d in psych_dates:
        if start <= d <= end:
            next_d = d + timedelta(days=14)
            records.append(
                {
                    "id": _random_id(),
                    "date": _iso_date(d),
                    "visit_type": "psychology",
                    "completed": True,
                    "next_visit_date": (
                        _iso_date(next_d) if next_d <= end + timedelta(days=30) else None
                    ),
                    "notes": "Sesión de seguimiento" if random.random() < 0.5 else None,
                    "created_at": _iso_now(),
                }
            )
    for d in med_dates:
        if start <= d <= end:
            next_d = d + timedelta(days=28)
            records.append(
                {
                    "id": _random_id(),
                    "date": _iso_date(d),
                    "visit_type": "medical",
                    "completed": True,
                    "next_visit_date": (
                        _iso_date(next_d) if next_d <= end + timedelta(days=60) else None
                    ),
                    "notes": "Control hormonal" if random.random() < 0.5 else None,
                    "created_at": _iso_now(),
                }
            )
    return sorted(records, key=lambda r: r["date"])


def generate_habits(start: date, end: date, catalog_ids: list[str]) -> list[dict]:
    """Habit logs ~4-5 days per week."""
    records: list[dict] = []
    current = start
    while current <= end:
        if random.random() < 0.65:
            n_shown = random.randint(3, 6)
            start_idx = current.toordinal() % len(catalog_ids)
            shown = (catalog_ids[start_idx:] + catalog_ids[:start_idx])[:n_shown]
            n_completed = random.randint(1, len(shown))
            completed = random.sample(shown, n_completed)
            records.append(
                {
                    "id": _random_id(),
                    "date": _iso_date(current),
                    "shown_habits": shown,
                    "completed_habits": completed,
                    "created_at": _iso_now(),
                }
            )
        current += timedelta(days=1)
    return records


def generate_other_events(start: date, end: date) -> list[dict]:
    """Occasional events."""
    events = [
        (date(2026, 1, 6), "general", "inicio_año, objetivos"),
        (date(2026, 1, 20), "general", "terapia_voz"),
        (date(2026, 2, 14), "general", "autocuidado"),
        (date(2026, 2, 28), "general", "revisión_progreso"),
        (date(2026, 3, 8), "general", "día_internacional"),
    ]
    records: list[dict] = []
    for d, cat, tags in events:
        if start <= d <= end:
            records.append(
                {
                    "id": _random_id(),
                    "date": _iso_date(d),
                    "category": cat,
                    "tags": [t.strip() for t in tags.split(",")],
                    "notes": f"Evento registrado el {d.isoformat()}",
                    "created_at": _iso_now(),
                }
            )
    return sorted(records, key=lambda r: r["date"])


def main() -> None:
    start = date(2026, 1, 1)
    end = date(2026, 3, 11)

    output_dir = get_output_dir()
    key_path = output_dir / ".voice_metrics.key"
    privacy = VoicePrivacyService(key_path=key_path)

    # Load existing: solo conservar registros reales (con audio guardado)
    history_path = get_patient_history_path()
    if history_path.exists():
        existing = json.loads(history_path.read_text(encoding="utf-8"))
        all_voice = existing.get("records", {}).get("voice", [])
        existing_voice = [r for r in all_voice if r.get("audio_saved_path")]
    else:
        existing_voice = []

    profile_path = output_dir / "patient_profile.json"
    if profile_path.exists():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        catalog = profile.get("habit_catalog", [])
    else:
        catalog = []
    catalog_ids = (
        [h["id"] for h in catalog]
        if catalog
        else [
            "hidratarse",
            "dormir",
            "caminar",
            "respirar",
            "diario",
            "desconexion",
        ]
    )

    voice = generate_voice_records(start, end, privacy)
    # Append existing voice records (they are from Mar 10-11)
    voice.extend(existing_voice)
    voice = sorted(voice, key=lambda r: (r["target_date"], r.get("recorded_at", "")))

    medication = generate_medication_records(start, end)
    visits = generate_visits(start, end)
    habits = generate_habits(start, end, catalog_ids)
    other_events = generate_other_events(start, end)

    history = {
        "schema_version": 1,
        "records": {
            "voice": voice,
            "medication": medication,
            "visits": visits,
            "other_events": other_events,
            "habits": habits,
        },
    }

    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Generated history: {len(voice)} voice, {len(medication)} medication, "
        f"{len(visits)} visits, {len(habits)} habits, {len(other_events)} events"
    )
    print(f"Saved to {history_path}")


if __name__ == "__main__":
    main()
