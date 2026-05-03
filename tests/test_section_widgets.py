"""Tests for reusable scroll helpers in information dialogs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from frontend.ui_dialogs.section_widgets import install_vertical_mousewheel_scrolling


class _FakeBindRoot:
    """Capture global mousewheel bindings for a scrollable region."""

    def __init__(self) -> None:
        self.bound_all: dict[str, Callable[..., Any]] = {}

    def bind_all(self, sequence: str, handler: Callable[..., Any], add: str | None = None) -> None:
        """Record a global event binding."""
        del add
        self.bound_all[sequence] = handler


class _FakeWidget:
    """Small widget stand-in with Tk-like ancestry through ``master``."""

    def __init__(self, master: "_FakeWidget | None" = None) -> None:
        self.master = master


class _FakeEvent:
    """Small event object with Tk-like wheel attributes."""

    def __init__(
        self,
        *,
        widget: _FakeWidget,
        delta: int = 0,
        num: int | None = None,
    ) -> None:
        self.widget = widget
        self.delta = delta
        self.num = num


def test_install_vertical_mousewheel_scrolling_only_handles_descendants() -> None:
    """Scrollable panels should react when the wheel event comes from inside them."""
    root = _FakeBindRoot()
    scroll_region = _FakeWidget()
    child_widget = _FakeWidget(master=scroll_region)
    outside_widget = _FakeWidget()
    scroll_units: list[int] = []

    install_vertical_mousewheel_scrolling(
        bind_root=root,
        scroll_region=scroll_region,
        scroll_command=lambda units: scroll_units.append(units),
    )

    assert tuple(root.bound_all) == ("<MouseWheel>", "<Button-4>", "<Button-5>")

    handled = root.bound_all["<MouseWheel>"](_FakeEvent(widget=child_widget, delta=120))
    ignored = root.bound_all["<MouseWheel>"](_FakeEvent(widget=outside_widget, delta=-120))
    linux_handled = root.bound_all["<Button-5>"](_FakeEvent(widget=child_widget, num=5))

    assert handled == "break"
    assert ignored is None
    assert linux_handled == "break"
    assert scroll_units == [-1, 1]
