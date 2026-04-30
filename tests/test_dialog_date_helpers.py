"""Tests for optional date helpers and recording form state."""

from __future__ import annotations

from datetime import date
from typing import Any

from frontend.date_widgets import DateEntryAdapter
from frontend.ui_dialogs.data_view_dialog import _get_optional_date_iso, _set_optional_date_entry
from frontend.ui_dialogs.recording_dialog import _collect_record_form_state


class FakeDateWidget:
    """Small in-memory widget used to test DateEntryAdapter behavior."""

    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        """Return the current raw value."""
        return self.value

    def delete(self, _start: int, _end: Any) -> None:
        """Clear the current value."""
        self.value = ""

    def insert(self, _index: int, value: str) -> None:
        """Insert a new raw value."""
        self.value = value


class FakeRequiredDateEntry:
    """Minimal date entry exposing the API used by the recording dialog."""

    def __init__(self, selected_date: date) -> None:
        self._selected_date = selected_date

    def get_date(self) -> date:
        """Return the selected date."""
        return self._selected_date


def test_set_optional_date_entry_clears_empty_values() -> None:
    """Empty optional dates should stay visually blank instead of becoming today."""
    adapter = DateEntryAdapter(FakeDateWidget(), fallback=True)

    _set_optional_date_entry(adapter, None)

    assert adapter.widget.get() == ""
    assert _get_optional_date_iso(adapter) is None


def test_get_optional_date_iso_returns_date_for_filled_value() -> None:
    """Filled optional dates should still round-trip to ISO strings."""
    adapter = DateEntryAdapter(FakeDateWidget("2026-05-02"), fallback=True)

    assert _get_optional_date_iso(adapter) == "2026-05-02"


def test_collect_record_form_state_uses_selected_target_date() -> None:
    """Recording form state should preserve the date chosen in the UI."""
    target_date, mood_self, should_save_audio = _collect_record_form_state(
        target_date_entry=FakeRequiredDateEntry(date(2026, 4, 12)),
        mood_happy=4,
        mood_sad=1,
        mood_angry=0,
        should_save_audio=True,
    )

    assert target_date == date(2026, 4, 12)
    assert mood_self["happy"] == 0.8
    assert should_save_audio is True
