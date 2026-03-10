"""Path configuration for TransTools."""

from pathlib import Path

from config.env import get_env_from_schema


def get_output_dir() -> Path:
    """Output directory (audios, data, plots).

    Returns:
        Resolved path to output directory from FILE_OUTPUT_DIR.
    """
    base = Path(__file__).resolve().parent.parent.parent
    out = get_env_from_schema("FILE_OUTPUT_DIR")
    return (base / out).resolve()


def get_data_file_path() -> Path:
    """Path to data file (JSON).

    Returns:
        Path to trans_tools_data.json in output dir.
    """
    out = get_output_dir()
    return out / "trans_tools_data.json"


def get_audio_dir() -> Path:
    """Directory for saved audio files.

    Returns:
        Path to output/audio subdirectory.
    """
    return get_output_dir() / "audio"


def get_patient_profile_path() -> Path:
    """Path to patient static data (profile, health config, etc).

    Returns:
        Path to patient_profile.json in output dir.
    """
    return get_output_dir() / "patient_profile.json"


def get_patient_history_path() -> Path:
    """Path to patient historical records (voice, medication, visits, etc).

    Returns:
        Path to patient_history.json in output dir.
    """
    return get_output_dir() / "patient_history.json"


def get_contacts_path() -> Path:
    """Path to contacts JSON (app-level, in src)."""
    base = Path(__file__).resolve().parent.parent
    return base / "data" / "contacts.json"
