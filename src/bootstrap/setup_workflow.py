"""Shared setup workflow for Windows and Linux wrappers."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from bootstrap.messages import get_python_requirement_text, get_run_command
from bootstrap.runtime import (
    ProjectPaths,
    build_project_paths,
    get_platform_name,
    python_version_is_supported,
)
from bootstrap.types import CommandRunner, Reporter, SetupOptions


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


def _copy_env_file(paths: ProjectPaths, reporter: Reporter) -> None:
    """Create .env from .env.example only when it does not exist already."""
    env_file = paths.env_file
    env_example_file = paths.env_example_file
    if env_file.exists():
        _write_line(reporter, ".env already exists, leaving it unchanged.")
        return
    if not env_example_file.exists():
        _write_line(reporter, "Warning: .env.example was not found, skipping .env creation.")
        return
    shutil.copyfile(env_example_file, env_file)
    _write_line(reporter, ".env created from .env.example.")


def _create_windows_shortcut(
    paths: ProjectPaths,
    runner: CommandRunner,
    reporter: Reporter,
) -> None:
    """Try to create a desktop shortcut on Windows without failing setup."""
    desktop_dir = Path.home() / "Desktop"
    shortcut_path = desktop_dir / "TransTools.lnk"
    run_script = paths.root_dir / "bin" / "run.bat"
    powershell_command = (
        "$WshShell = New-Object -ComObject WScript.Shell; "
        f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path.as_posix()}'); "
        f"$Shortcut.TargetPath = '{run_script.as_posix()}'; "
        f"$Shortcut.WorkingDirectory = '{paths.root_dir.as_posix()}'; "
        "$Shortcut.Description = 'TransTools'; "
        "$Shortcut.Save()"
    )
    result = runner(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_command],
        paths.root_dir,
    )
    if result.returncode != 0:
        _write_line(reporter, "Warning: desktop shortcut could not be created.")
        _write_process_output(reporter, result)
        return
    _write_line(reporter, "Desktop shortcut created.")


def run_setup(
    options: SetupOptions,
    runner: CommandRunner | None = None,
    reporter: Reporter | None = None,
    platform_name: str | None = None,
) -> int:
    """Run the shared setup workflow and return a process-style exit code."""
    effective_runner = runner or _default_runner
    effective_reporter = reporter or sys.stdout
    platform_key = get_platform_name(platform_name)
    paths = build_project_paths(options.project_root, platform_name=platform_key)

    _write_line(effective_reporter, "TransTools setup")
    _write_line(effective_reporter, "----------------")
    if not python_version_is_supported((sys.version_info.major, sys.version_info.minor)):
        _write_line(effective_reporter, f"ERROR: {get_python_requirement_text()}")
        return 1
    if not paths.requirements_file.exists():
        _write_line(effective_reporter, "ERROR: requirements.txt was not found.")
        return 1

    if paths.venv_python.exists():
        _write_line(effective_reporter, "Virtual environment already exists.")
    else:
        _write_line(effective_reporter, "Creating virtual environment...")
        venv_result = effective_runner(
            [str(options.bootstrap_python), "-m", "venv", ".venv"],
            paths.root_dir,
        )
        if venv_result.returncode != 0:
            _write_line(effective_reporter, "ERROR: could not create the virtual environment.")
            _write_process_output(effective_reporter, venv_result)
            return 1

    if not paths.venv_python.exists():
        _write_line(effective_reporter, "ERROR: the virtual environment interpreter is missing.")
        return 1

    _write_line(effective_reporter, "Upgrading pip...")
    pip_upgrade_result = effective_runner(
        [str(paths.venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        paths.root_dir,
    )
    if pip_upgrade_result.returncode != 0:
        _write_line(effective_reporter, "ERROR: could not upgrade pip inside .venv.")
        _write_process_output(effective_reporter, pip_upgrade_result)
        return 1

    _write_line(effective_reporter, "Installing dependencies...")
    dependency_result = effective_runner(
        [str(paths.venv_python), "-m", "pip", "install", "-r", "requirements.txt"],
        paths.root_dir,
    )
    if dependency_result.returncode != 0:
        _write_line(effective_reporter, "ERROR: dependency installation failed.")
        _write_process_output(effective_reporter, dependency_result)
        _write_line(
            effective_reporter,
            f"Retry with: {paths.venv_python} -m pip install -r requirements.txt",
        )
        return 1

    _copy_env_file(paths, effective_reporter)

    if platform_key.startswith("win") and options.create_windows_shortcut:
        _create_windows_shortcut(paths, effective_runner, effective_reporter)

    _write_line(effective_reporter, "Setup complete.")
    _write_line(
        effective_reporter,
        f"Run TransTools with: {get_run_command(platform_key)}",
    )
    return 0
