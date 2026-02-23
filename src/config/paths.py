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
