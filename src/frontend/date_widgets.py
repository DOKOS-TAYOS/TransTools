"""Date widget helpers for Tkinter dialogs."""

from __future__ import annotations

from datetime import date, datetime
from types import MethodType

from config import UI_STYLE
from config.env import get_env_from_schema
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

    def pack(self, **kwargs) -> None:
        """Proxy pack call to widget."""
        self.widget.pack(**kwargs)

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


def get_calendar_locale() -> str:
    """Return tkcalendar locale from configured language."""
    language = str(get_env_from_schema("LANGUAGE")).strip().lower()
    if language == "en":
        return "en_US"
    return "es_ES"


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


def _disable_dateentry_focusout_close(date_entry) -> None:
    """Keep DateEntry popup open while navigating month/year controls.

    tkcalendar closes the popup on calendar focus loss. That also happens when
    the user interacts with month/year navigation widgets. Removing that
    binding keeps the popup open until a day is selected.
    """
    calendar_widget = getattr(date_entry, "_calendar", None)
    if calendar_widget is None:
        return
    try:
        calendar_widget.unbind("<FocusOut>")
    except Exception:
        pass


def _reposition_dateentry_popup(date_entry) -> None:
    """Reposition DateEntry popup above the input when it would overflow.

    tkcalendar always opens the popup below the widget. In dense forms near the
    bottom of the window that can place the calendar partially off-screen.
    """
    top_cal = getattr(date_entry, "_top_cal", None)
    if top_cal is None:
        return

    original_drop_down = date_entry.drop_down

    def _drop_down_with_reposition(self) -> None:
        """Wrap tkcalendar drop-down to keep the popup fully visible."""
        original_drop_down()
        if not top_cal.winfo_ismapped():
            return

        top_cal.update_idletasks()

        popup_width = top_cal.winfo_width() or top_cal.winfo_reqwidth()
        popup_height = top_cal.winfo_height() or top_cal.winfo_reqheight()
        screen_height = self.winfo_screenheight()
        screen_width = self.winfo_screenwidth()
        entry_x = self.winfo_rootx()
        entry_y = self.winfo_rooty()
        entry_height = self.winfo_height()

        default_y = entry_y + entry_height
        overflow_below = default_y + popup_height > screen_height
        space_above = entry_y

        if overflow_below and space_above >= popup_height:
            popup_y = max(0, entry_y - popup_height)
        else:
            popup_y = min(default_y, max(0, screen_height - popup_height))

        popup_x = min(entry_x, max(0, screen_width - popup_width))
        top_cal.geometry(f"+{popup_x}+{popup_y}")

    date_entry.drop_down = MethodType(_drop_down_with_reposition, date_entry)


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
            locale=get_calendar_locale(),
            font=_calendar_font(),
        )
        _apply_dateentry_dropdown_font(widget)
        _disable_dateentry_focusout_close(widget)
        _reposition_dateentry_popup(widget)
        return DateEntryAdapter(widget, fallback=False)
    except Exception:
        entry = create_entry(parent, width=width)
        adapter = DateEntryAdapter(entry, fallback=True)
        adapter.set_date(date.today())
        return adapter
