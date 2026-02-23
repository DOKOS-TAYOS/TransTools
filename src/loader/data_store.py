"""Data storage for TransTools - JSON format."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config.paths import get_data_file_path
from utils import DataStoreError, get_logger

logger = get_logger(__name__)

DATE_FMT = "%d/%m/%Y"

# Columns for flattened DataFrame (history/export)
COLUMNS = [
    "date",
    "sample",
    "pitch_mean_hz",
    "pitch_std_hz",
    "pitch_min_hz",
    "pitch_max_hz",
    "energy_rms",
    "mood_happy",
    "mood_sad",
    "mood_angry",
]


def get_data_path() -> Path:
    """Path to data file.

    Creates parent directory if needed.

    Returns:
        Path to trans_tools_data.json.
    """
    path = get_data_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _date_key(dt: datetime) -> str:
    """Format datetime as DD/MM/YYYY."""
    return dt.strftime(DATE_FMT)


def _parse_date_key(key: str) -> datetime | None:
    """Parse DD/MM/YYYY to datetime."""
    try:
        return datetime.strptime(key, DATE_FMT)
    except ValueError:
        return None


def _default_day_entry(prev_day_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build default entry for a new day from previous day values."""
    med = prev_day_data.get("Medication", {}) if prev_day_data else {}
    ctrl = prev_day_data.get("Control Session", {}) if prev_day_data else {}
    psicho = prev_day_data.get("Psicho", {}) if prev_day_data else {}
    return {
        "Audio": {},
        "Medication": {
            "This day": False,
            "Period": med.get("Period", 7),
            "Hour": None,
        },
        "Control Session": {
            "This day": False,
            "Next": ctrl.get("Next"),
        },
        "Psicho": {
            "This day": False,
            "Next": psicho.get("Next"),
        },
        "Something special": None,
    }


def _get_previous_day_data(data: dict[str, Any], today_key: str) -> dict[str, Any] | None:
    """Get data from the most recent day before today."""
    today_dt = datetime.strptime(today_key, DATE_FMT)
    candidates = []
    for k in data.keys():
        d = _parse_date_key(k)
        if d is not None and d < today_dt:
            candidates.append((d, k))
    if not candidates:
        return None
    prev_dt, prev_key = max(candidates, key=lambda x: x[0])
    return data.get(prev_key)


def _sample_to_audio_entry(
    pitch_mean_hz: float,
    pitch_std_hz: float,
    pitch_min_hz: float,
    pitch_max_hz: float,
    energy_rms: float,
    mood: list[float],
) -> dict[str, Any]:
    """Build a single sample entry for Audio."""
    return {
        "pitch_mean": pitch_mean_hz,
        "pitch_min": pitch_min_hz,
        "pitch_max": pitch_max_hz,
        "pitch_std": pitch_std_hz,
        "energy": energy_rms,
        "mood": mood,
    }


def _recalc_day_global(samples: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compute Day Global as averages of all samples."""
    if not samples:
        return {}
    vals = list(samples.values())
    n = len(vals)
    return {
        "pitch_mean": sum(s["pitch_mean"] for s in vals) / n,
        "pitch_min": sum(s["pitch_min"] for s in vals) / n,
        "pitch_max": sum(s["pitch_max"] for s in vals) / n,
        "pitch_std": sum(s["pitch_std"] for s in vals) / n,
        "energy": sum(s["energy"] for s in vals) / n,
        "mood": [
            sum(s["mood"][i] for s in vals) / n
            for i in range(len(vals[0]["mood"]))
        ],
    }


def _load_json_data() -> dict[str, Any]:
    """Load full JSON data. Returns empty dict if file does not exist."""
    path = get_data_path()
    if not path.exists():
        return {}
    try:
        import json
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception as e:
        logger.exception("Failed to load JSON: %s", e)
        raise DataStoreError(f"Failed to load: {e}") from e


def _save_json_data(data: dict[str, Any]) -> None:
    """Save full JSON data."""
    path = get_data_path()
    try:
        import json
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.exception("Failed to save JSON: %s", e)
        raise DataStoreError(f"Failed to save: {e}") from e


def append_record(
    date: datetime,
    pitch_mean_hz: float,
    pitch_std_hz: float,
    pitch_min_hz: float,
    pitch_max_hz: float,
    energy_rms: float,
    mood: list[float] | None = None,
) -> None:
    """Append a recording to the JSON log for that day.

    Creates the day with defaults if it does not exist. Adds a new Sample N
    and recalculates Day Global.

    Args:
        date: Recording timestamp.
        pitch_mean_hz: Mean pitch in Hz.
        pitch_std_hz: Pitch standard deviation in Hz.
        pitch_min_hz: Minimum pitch in Hz.
        pitch_max_hz: Maximum pitch in Hz.
        energy_rms: RMS energy value.
        mood: [happy, sad, angry] scores (default [0, 0, 0]).

    Raises:
        DataStoreError: If save fails.
    """
    if mood is None:
        mood = [0.0, 0.0, 0.0]
    data = _load_json_data()
    today_key = _date_key(date)

    if today_key not in data:
        prev = _get_previous_day_data(data, today_key)
        data[today_key] = _default_day_entry(prev)

    day = data[today_key]
    audio = day["Audio"]

    # Exclude "Day Global" when counting samples
    sample_keys = [k for k in audio.keys() if k.startswith("Sample ")]
    n = len(sample_keys) + 1
    sample_name = f"Sample {n}"

    entry = _sample_to_audio_entry(
        pitch_mean_hz, pitch_std_hz, pitch_min_hz, pitch_max_hz, energy_rms, mood
    )
    audio[sample_name] = entry
    audio["Day Global"] = _recalc_day_global(
        {k: v for k, v in audio.items() if k != "Day Global"}
    )

    _save_json_data(data)
    logger.info("Record saved: %s %s", today_key, sample_name)


def load_records() -> pd.DataFrame:
    """Load all records as a flattened DataFrame for history/export.

    Each row is one sample (one recording). Columns: date, sample, pitch_mean_hz, etc.

    Returns:
        DataFrame with one row per sample.
        Empty DataFrame if file does not exist.

    Raises:
        DataStoreError: If load fails.
    """
    data = _load_json_data()
    rows: list[dict[str, Any]] = []
    for date_key, day in data.items():
        audio = day.get("Audio", {})
        for k, v in audio.items():
            if k == "Day Global" or not isinstance(v, dict):
                continue
            mood = v.get("mood", [0, 0, 0])
            rows.append({
                "date": date_key,
                "sample": k,
                "pitch_mean_hz": v.get("pitch_mean", 0),
                "pitch_std_hz": v.get("pitch_std", 0),
                "pitch_min_hz": v.get("pitch_min", 0),
                "pitch_max_hz": v.get("pitch_max", 0),
                "energy_rms": v.get("energy", 0),
                "mood_happy": mood[0] if len(mood) > 0 else 0,
                "mood_sad": mood[1] if len(mood) > 1 else 0,
                "mood_angry": mood[2] if len(mood) > 2 else 0,
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df["date"] = pd.to_datetime(df["date"], format=DATE_FMT)
    return df


def export_csv(dest_path: Path) -> None:
    """Export data to CSV at specified path.

    Args:
        dest_path: Destination file path for CSV export.
    """
    df = load_records()
    df.to_csv(dest_path, index=False)
    logger.info("Exported to %s", dest_path)
