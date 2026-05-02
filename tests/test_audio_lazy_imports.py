"""Regression tests for lazy audio backend imports."""

from __future__ import annotations

import builtins
import importlib
import sys
from collections.abc import Sequence
from typing import Any


def test_recording_dialog_import_does_not_require_sounddevice(monkeypatch) -> None:
    """Importing the dialog should not eagerly require the recording backend."""
    real_import = builtins.__import__

    def guarded_import(
        name: str,
        globals_: dict[str, Any] | None = None,
        locals_: dict[str, Any] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> Any:
        if name == "sounddevice":
            raise AssertionError("sounddevice should load lazily during dialog import")
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for module_name in ("frontend.ui_dialogs.recording_dialog", "audio", "audio.recorder"):
        sys.modules.pop(module_name, None)

    module = importlib.import_module("frontend.ui_dialogs.recording_dialog")

    assert hasattr(module, "_collect_record_form_state")
