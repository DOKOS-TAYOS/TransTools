"""User-facing messages for bootstrap workflows."""

from __future__ import annotations


def get_setup_command(platform_name: str) -> str:
    """Return the platform-appropriate setup command for user guidance."""
    return "setup.bat" if platform_name.startswith("win") else "./setup.sh"


def get_run_command(platform_name: str) -> str:
    """Return the platform-appropriate run command for user guidance."""
    return r"bin\run.bat" if platform_name.startswith("win") else "./bin/run.sh"


def get_python_requirement_text() -> str:
    """Return the minimum supported Python requirement for setup workflows."""
    return "Python 3.12 or newer is required."
