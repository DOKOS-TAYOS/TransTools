"""Tests for the process tab layout in the unified data view."""

from __future__ import annotations

from frontend.ui_dialogs.data_view_dialog import (
    build_process_appointments_tree_specs,
    build_process_roadmap_tree_specs,
    get_process_tab_table_rows,
)


def test_process_tab_uses_stacked_table_rows() -> None:
    """Roadmap and appointments tables should be stacked one above the other."""
    rows = get_process_tab_table_rows()

    assert rows == {"roadmap": 2, "appointments": 4}


def test_process_roadmap_tree_specs_allow_horizontal_scrolling() -> None:
    """Roadmap table should expose enough width to stay readable with a horizontal scrollbar."""
    specs = build_process_roadmap_tree_specs()

    assert sum(spec.width for spec in specs) >= 1050
    assert next(spec for spec in specs if spec.name == "title").stretch is True
    assert next(spec for spec in specs if spec.name == "completed").width >= 120


def test_process_appointments_tree_specs_allow_horizontal_scrolling() -> None:
    """Appointments table should keep date/type/title/status clearly separated."""
    specs = build_process_appointments_tree_specs()

    assert sum(spec.width for spec in specs) >= 1000
    assert next(spec for spec in specs if spec.name == "title").stretch is True
    assert next(spec for spec in specs if spec.name == "done").width >= 120
