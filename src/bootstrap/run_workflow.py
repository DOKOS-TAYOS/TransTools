"""Shared run workflow for Windows and Linux wrappers."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from bootstrap.messages import get_setup_command
from bootstrap.runtime import build_project_paths, get_platform_name
from bootstrap.types import CommandRunner, Reporter, RunOptions


def _default_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command with captured text output."""
    return subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_line(reporter: Reporter, message: str) -> None:
    """Write one line to the selected reporter."""
    reporter.write(f"{message}\n")


def _write_process_output(reporter: Reporter, result: subprocess.CompletedProcess[str]) -> None:
    """Write non-empty subprocess output back to the reporter."""
    for chunk in (result.stdout, result.stderr):
        text = chunk.strip()
        if text:
            _write_line(reporter, text)


def run_application(
    options: RunOptions,
    runner: CommandRunner | None = None,
    reporter: Reporter | None = None,
    platform_name: str | None = None,
) -> int:
    """Validate and run the application, or only validate when check mode is enabled."""
    effective_runner = runner or _default_runner
    effective_reporter = reporter or sys.stdout
    platform_key = get_platform_name(platform_name)
    paths = build_project_paths(options.project_root, platform_name=platform_key)

    if not paths.venv_dir.exists():
        _write_line(effective_reporter, "ERROR: Virtual environment not found.")
        _write_line(
            effective_reporter,
            f"Run {get_setup_command(platform_key)} to finish the installation.",
        )
        return 1
    if not paths.venv_python.exists():
        _write_line(
            effective_reporter,
            "ERROR: .venv exists but its Python interpreter is missing.",
        )
        _write_line(
            effective_reporter,
            f"Run {get_setup_command(platform_key)} to recreate the environment.",
        )
        return 1
    if not paths.main_script.exists():
        _write_line(effective_reporter, "ERROR: src/main.py was not found.")
        return 1

    if options.check_only:
        _write_line(effective_reporter, "Installation looks ready.")
        return 0

    launch_commands: list[list[str]] = []
    if (
        platform_key.startswith("win")
        and not options.force_console
        and paths.venv_pythonw is not None
    ):
        if paths.venv_pythonw.exists():
            launch_commands.append([str(paths.venv_pythonw), str(paths.main_script), *options.args])
    launch_commands.append([str(paths.venv_python), str(paths.main_script), *options.args])

    for index, command in enumerate(launch_commands):
        result = effective_runner(command, paths.root_dir)
        if result.returncode == 0:
            return 0
        if index == 0 and len(launch_commands) > 1:
            _write_line(
                effective_reporter,
                "Retrying in console mode after a windowed launch error.",
            )
            _write_process_output(effective_reporter, result)
            continue
        _write_line(effective_reporter, "ERROR: TransTools could not be started.")
        _write_process_output(effective_reporter, result)
        return result.returncode or 1
    return 1
