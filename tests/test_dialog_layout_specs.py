"""Regression tests for dense dialog layout specs."""

from __future__ import annotations

from frontend.ui_dialogs.companion_dialog import (
    build_appointment_form_text_heights,
    build_appointment_tree_column_specs,
)
from frontend.ui_dialogs.contacts_dialog import (
    build_contact_table_geometry,
    build_contact_tree_column_specs,
    get_contact_tree_rowheight,
)


def test_appointment_tree_specs_keep_status_column_clear() -> None:
    """Appointment table should reserve clear space for status and title columns."""
    specs = build_appointment_tree_column_specs()
    specs_by_name = {spec.name: spec for spec in specs}

    assert specs_by_name["date"].stretch is False
    assert specs_by_name["type"].stretch is False
    assert specs_by_name["done"].width >= 110
    assert specs_by_name["title"].stretch is True
    assert specs_by_name["title"].minwidth >= 260


def test_appointment_form_text_heights_give_more_room_for_writing() -> None:
    """Appointment notes fields should stay comfortable without forcing scroll too early."""
    heights = build_appointment_form_text_heights()

    assert heights["questions"] >= 4
    assert heights["talking_points"] >= 4
    assert heights["follow_up"] >= 3
    assert heights["outcome"] >= 3
    assert sum(heights.values()) <= 17


def test_contact_tree_specs_expect_horizontal_scrolling_room() -> None:
    """Contacts table should define a wider total content width than the viewport."""
    specs = build_contact_tree_column_specs()

    assert sum(spec.width for spec in specs) >= 1400
    assert next(spec for spec in specs if spec.name == "email").width >= 260
    assert next(spec for spec in specs if spec.name == "web").minwidth >= 240


def test_contact_tree_rowheight_supports_multiline_descriptions() -> None:
    """Dense contact descriptions should not clip within the table rows."""
    assert get_contact_tree_rowheight(font_size=13, description_lines=4) >= 80
    assert get_contact_tree_rowheight(font_size=13, description_lines=5) >= 100


def test_contact_table_geometry_expands_for_long_national_descriptions() -> None:
    """Longer national descriptions should request taller rows than shorter regional ones."""
    short_rows = [
        {"description": "Apoyo breve."},
    ]
    long_rows = [
        {
            "description": (
                "Servicio estatal del Ministerio de Igualdad. Informacion, asesoramiento "
                "juridico y atencion psicosocial inmediata frente a la LGTBIfobia, "
                "acompanamiento profesional y recursos coordinados durante todo el ano."
            )
        },
    ]

    short_geometry = build_contact_table_geometry(short_rows, font_size=13)
    long_geometry = build_contact_table_geometry(long_rows, font_size=13)

    assert long_geometry.description_lines > short_geometry.description_lines
    assert long_geometry.rowheight > short_geometry.rowheight
