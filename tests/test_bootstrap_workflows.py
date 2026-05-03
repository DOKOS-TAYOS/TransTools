"""Tests for shared bootstrap setup and run workflows."""

from __future__ import annotations

import io
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from bootstrap.run_workflow import run_application
from bootstrap.runtime import build_project_paths
from bootstrap.setup_workflow import run_setup
from bootstrap.types import RunOptions, SetupOptions

ROOT = Path(__file__).resolve().parent.parent


def _create_project(project_root: Path) -> None:
    """Create the minimal project structure needed by bootstrap tests."""
    (project_root / "src").mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (project_root / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (project_root / ".env.example").write_text("APP_MODE=dev\n", encoding="utf-8")


def _create_venv_python(project_root: Path, platform_name: str) -> Path:
    """Create a fake venv interpreter for the requested platform."""
    paths = build_project_paths(project_root, platform_name=platform_name)
    paths.venv_python.parent.mkdir(parents=True, exist_ok=True)
    paths.venv_python.write_text("", encoding="utf-8")
    if paths.venv_pythonw is not None:
        paths.venv_pythonw.write_text("", encoding="utf-8")
    return paths.venv_python


def _make_workspace_temp_dir() -> Path:
    """Create a temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"bootstrap_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_run_setup_bootstraps_venv_and_env_file() -> None:
    """Setup should create the venv, install dependencies, and create .env once."""
    base_dir = _make_workspace_temp_dir()
    try:
        project_root = base_dir / "project"
        project_root.mkdir()
        _create_project(project_root)
        output = io.StringIO()
        commands: list[tuple[str, ...]] = []

        def fake_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            commands.append(tuple(command))
            if list(command[-3:]) == ["-m", "venv", ".venv"]:
                _create_venv_python(cwd, platform_name="win32")
            return subprocess.CompletedProcess(command, 0, "", "")

        exit_code = run_setup(
            SetupOptions(
                project_root=project_root,
                bootstrap_python=Path("C:/Python312/python.exe"),
                create_windows_shortcut=False,
            ),
            runner=fake_runner,
            reporter=output,
            platform_name="win32",
        )

        assert exit_code == 0
        assert commands == [
            (str(Path("C:/Python312/python.exe")), "-m", "venv", ".venv"),
            (
                str(project_root / ".venv" / "Scripts" / "python.exe"),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ),
            (
                str(project_root / ".venv" / "Scripts" / "python.exe"),
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt",
            ),
        ]
        assert (project_root / ".env").read_text(encoding="utf-8") == "APP_MODE=dev\n"
        assert "Setup complete." in output.getvalue()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_run_setup_reuses_existing_venv() -> None:
    """Setup should skip venv creation when the interpreter already exists."""
    base_dir = _make_workspace_temp_dir()
    try:
        project_root = base_dir / "project"
        project_root.mkdir()
        _create_project(project_root)
        _create_venv_python(project_root, platform_name="linux")
        output = io.StringIO()
        commands: list[tuple[str, ...]] = []

        def fake_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            commands.append(tuple(command))
            return subprocess.CompletedProcess(command, 0, "", "")

        exit_code = run_setup(
            SetupOptions(
                project_root=project_root,
                bootstrap_python=Path("/usr/bin/python3"),
                create_windows_shortcut=False,
            ),
            runner=fake_runner,
            reporter=output,
            platform_name="linux",
        )

        assert exit_code == 0
        assert commands == [
            (
                str(project_root / ".venv" / "bin" / "python"),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ),
            (
                str(project_root / ".venv" / "bin" / "python"),
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt",
            ),
        ]
        assert "Virtual environment already exists." in output.getvalue()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_run_application_check_mode_reports_missing_venv() -> None:
    """Check mode should fail fast with a recovery command when .venv is missing."""
    base_dir = _make_workspace_temp_dir()
    try:
        project_root = base_dir / "project"
        project_root.mkdir()
        _create_project(project_root)
        output = io.StringIO()

        exit_code = run_application(
            RunOptions(project_root=project_root, check_only=True),
            reporter=output,
            platform_name="win32",
        )

        assert exit_code == 1
        assert "Virtual environment not found" in output.getvalue()
        assert "setup.bat" in output.getvalue()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_run_application_uses_pythonw_then_falls_back_to_console() -> None:
    """Windows run should retry in console mode if pythonw exits with an error."""
    base_dir = _make_workspace_temp_dir()
    try:
        project_root = base_dir / "project"
        project_root.mkdir()
        _create_project(project_root)
        _create_venv_python(project_root, platform_name="win32")
        output = io.StringIO()
        commands: list[tuple[str, ...]] = []

        def fake_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            commands.append(tuple(command))
            if command[0].endswith("pythonw.exe"):
                return subprocess.CompletedProcess(command, 1, "", "pythonw failed")
            return subprocess.CompletedProcess(command, 0, "", "")

        exit_code = run_application(
            RunOptions(project_root=project_root),
            runner=fake_runner,
            reporter=output,
            platform_name="win32",
        )

        assert exit_code == 0
        assert commands == [
            (
                str(project_root / ".venv" / "Scripts" / "pythonw.exe"),
                str(project_root / "src" / "main.py"),
            ),
            (
                str(project_root / ".venv" / "Scripts" / "python.exe"),
                str(project_root / "src" / "main.py"),
            ),
        ]
        assert "Retrying in console mode" in output.getvalue()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_run_application_check_mode_passes_when_installation_is_ready() -> None:
    """Check mode should confirm a healthy installation without launching the app."""
    base_dir = _make_workspace_temp_dir()
    try:
        project_root = base_dir / "project"
        project_root.mkdir()
        _create_project(project_root)
        _create_venv_python(project_root, platform_name="linux")
        output = io.StringIO()

        exit_code = run_application(
            RunOptions(project_root=project_root, check_only=True),
            reporter=output,
            platform_name="linux",
        )

        assert exit_code == 0
        assert "Installation looks ready." in output.getvalue()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
