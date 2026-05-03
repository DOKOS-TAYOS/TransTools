"""Runtime helpers shared by bootstrap workflows."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

MINIMUM_PYTHON_VERSION: tuple[int, int] = (3, 12)


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved project paths used by setup and run workflows."""

    root_dir: Path
    env_file: Path
    env_example_file: Path
    main_script: Path
    requirements_file: Path
    venv_dir: Path
    venv_python: Path
    venv_pythonw: Path | None


def get_platform_name(platform_name: str | None = None) -> str:
    """Return the active platform name or a caller-provided override."""
    return platform_name or sys.platform


def is_windows_platform(platform_name: str | None = None) -> bool:
    """Return whether the active platform is Windows."""
    return get_platform_name(platform_name).startswith("win")


def build_project_paths(project_root: Path, platform_name: str | None = None) -> ProjectPaths:
    """Build normalized project paths for the requested platform."""
    root_dir = project_root.resolve()
    venv_dir = root_dir / ".venv"
    if is_windows_platform(platform_name):
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pythonw: Path | None = venv_dir / "Scripts" / "pythonw.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        venv_pythonw = None
    return ProjectPaths(
        root_dir=root_dir,
        env_file=root_dir / ".env",
        env_example_file=root_dir / ".env.example",
        main_script=root_dir / "src" / "main.py",
        requirements_file=root_dir / "requirements.txt",
        venv_dir=venv_dir,
        venv_python=venv_python,
        venv_pythonw=venv_pythonw,
    )


def python_version_is_supported(version_info: tuple[int, ...]) -> bool:
    """Return whether the provided version tuple satisfies the minimum Python version."""
    return tuple(version_info[:2]) >= MINIMUM_PYTHON_VERSION
