"""Data storage for TransTools - CSV and XLSX."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from config.env import get_env_from_schema
from config.paths import get_data_file_path
from utils import DataStoreError, get_logger

logger = get_logger(__name__)

COLUMNS = [
    "date",
    "pitch_mean_hz",
    "pitch_std_hz",
    "pitch_min_hz",
    "pitch_max_hz",
    "energy_rms",
    "mood_score",
    "audio_path",
]


def get_data_path() -> Path:
    """Path to data file.

    Creates parent directory if needed.

    Returns:
        Path to data file (CSV or XLSX).
    """
    path = get_data_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_record(
    date: datetime,
    pitch_mean_hz: float,
    pitch_std_hz: float,
    pitch_min_hz: float,
    pitch_max_hz: float,
    energy_rms: float,
    mood_score: str = "N/A",
    audio_path: str = "",
) -> None:
    """Append a record to the data file.

    Args:
        date: Recording timestamp.
        pitch_mean_hz: Mean pitch in Hz.
        pitch_std_hz: Pitch standard deviation in Hz.
        pitch_min_hz: Minimum pitch in Hz.
        pitch_max_hz: Maximum pitch in Hz.
        energy_rms: RMS energy value.
        mood_score: Mood/placeholder score (default "N/A").
        audio_path: Path to saved audio file (default "").

    Raises:
        DataStoreError: If save fails.
    """
    path = get_data_path()
    row = {
        "date": date,
        "pitch_mean_hz": pitch_mean_hz,
        "pitch_std_hz": pitch_std_hz,
        "pitch_min_hz": pitch_min_hz,
        "pitch_max_hz": pitch_max_hz,
        "energy_rms": energy_rms,
        "mood_score": mood_score,
        "audio_path": audio_path,
    }
    try:
        fmt = get_env_from_schema("FILE_DATA_FORMAT")
        if path.exists():
            if fmt == "csv":
                df = pd.read_csv(path, parse_dates=["date"])
            else:
                df = pd.read_excel(path)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        if fmt == "csv":
            df.to_csv(path, index=False)
        else:
            df.to_excel(path, index=False)
        logger.info("Record saved: %s", date)
    except Exception as e:
        logger.exception("Failed to save record: %s", e)
        raise DataStoreError(f"Failed to save: {e}") from e


def load_records() -> pd.DataFrame:
    """Load all records from data file.

    Returns:
        DataFrame with columns: date, pitch_mean_hz, pitch_std_hz, etc.
        Empty DataFrame if file does not exist.

    Raises:
        DataStoreError: If load fails.
    """
    path = get_data_path()
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    try:
        fmt = get_env_from_schema("FILE_DATA_FORMAT")
        if fmt == "csv":
            df = pd.read_csv(path, parse_dates=["date"])
        else:
            df = pd.read_excel(path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        logger.exception("Failed to load records: %s", e)
        raise DataStoreError(f"Failed to load: {e}") from e


def export_csv(dest_path: Path) -> None:
    """Export data to CSV at specified path.

    Args:
        dest_path: Destination file path for CSV export.
    """
    df = load_records()
    df.to_csv(dest_path, index=False)
    logger.info("Exported to %s", dest_path)
