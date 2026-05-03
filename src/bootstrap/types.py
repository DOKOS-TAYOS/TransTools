"""Shared types for bootstrap workflows."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO


class CommandRunner(Protocol):
    """Protocol for subprocess-like command runners."""

    def __call__(
        self,
        command: Sequence[str],
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        """Run a command and return a completed-process style result."""
        ...


@dataclass(frozen=True)
class SetupOptions:
    """Options for the shared setup workflow."""

    project_root: Path
    bootstrap_python: Path
    create_windows_shortcut: bool = True


@dataclass(frozen=True)
class RunOptions:
    """Options for the shared run workflow."""

    project_root: Path
    args: tuple[str, ...] = ()
    check_only: bool = False
    force_console: bool = False


Reporter = TextIO
