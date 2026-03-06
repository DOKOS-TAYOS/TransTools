"""Date widget helpers for Tkinter dialogs."""

from __future__ import annotations

from datetime import date, datetime

from config import UI_STYLE
from frontend.input_widgets import create_entry


class DateEntryAdapter:
    """Small adapter over tkcalendar DateEntry with fallback Entry."""

    def __init__(self, widget, fallback: bool = False) -> None:
        """Initialize adapter.

        Args:
            widget: Underlying widget object.
            fallback: True when using plain ttk.Entry.
        """
        self.widget = widget
        self.fallback = fallback

    def grid(self, **kwargs) -> None:
        """Proxy grid call to widget."""
        self.widget.grid(**kwargs)

    def get_date(self) -> date:
        """Read selected date.

        Returns:
            Selected date object.
        """
        if self.fallback:
            value = self.widget.get().strip()
            return datetime.strptime(value, "%Y-%m-%d").date()
        return self.widget.get_date()

    def set_date(self, value: date) -> None:
        """Set selected date.

        Args:
            value: Date value.
        """
        if self.fallback:
            self.widget.delete(0, "end")
            self.widget.insert(0, value.isoformat())
            return
        self.widget.set_date(value)


def _calendar_font() -> tuple[str, int]:
    """Get calendar/input font from project theme."""
    return (UI_STYLE["font_family"], int(UI_STYLE["font_size"]))


def _apply_dateentry_dropdown_font(date_entry) -> None:
    """Apply font to DateEntry dropdown calendar when available."""
    font = _calendar_font()
    for attr_name in ("_calendar", "calendar"):
        calendar_widget = getattr(date_entry, attr_name, None)
        if calendar_widget is None:
            continue
        try:
            calendar_widget.configure(font=font, headersfont=font)
        except Exception:
            pass


def create_date_entry(parent, width: int = 12) -> DateEntryAdapter:
    """Create a date selection widget.

    Uses tkcalendar.DateEntry when available and falls back to ttk.Entry
    using ISO format YYYY-MM-DD.

    Args:
        parent: Parent widget.
        width: Widget width in chars.

    Returns:
        Adapter with get_date and set_date methods.
    """
    try:
        from tkcalendar import DateEntry

        widget = DateEntry(
            parent,
            width=width,
            date_pattern="yyyy-mm-dd",
            locale="es_ES",
            font=_calendar_font(),
        )
        _apply_dateentry_dropdown_font(widget)
        return DateEntryAdapter(widget, fallback=False)
    except Exception:
        entry = create_entry(parent, width=width)
        adapter = DateEntryAdapter(entry, fallback=True)
        adapter.set_date(date.today())
        return adapter
