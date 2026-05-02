"""Reusable widgets for information-style dialogs."""

from __future__ import annotations

from tkinter import Canvas, Frame, Label, Misc, ttk
from typing import Any

from config import UI_STYLE
from config.theme import get_surface_palette


def create_collapsible_section(
    parent: ttk.Frame,
    title: str,
    content: str,
    wraplength: int = 780,
    initially_expanded: bool = True,
) -> ttk.Frame:
    """Create a collapsible section with title and body content."""
    outer = ttk.Frame(parent)
    pad = int(UI_STYLE["padding"])
    palette = get_surface_palette()

    header_frame = Frame(
        outer,
        bg=palette.section_header_bg,
        highlightthickness=0,
        cursor="hand2",
    )
    header_frame.pack(fill="x", pady=(pad, 0))

    toggle_label = Label(
        header_frame,
        text=f"v  {title}" if initially_expanded else f">  {title}",
        cursor="hand2",
        bg=palette.section_header_bg,
        fg=palette.section_header_fg,
        font=(UI_STYLE["font_family"], UI_STYLE["font_size"], "bold"),
        padx=pad,
        pady=8,
    )
    toggle_label.pack(anchor="w")

    content_frame = ttk.Frame(outer, style="Card.TFrame", padding=pad)
    content_label = ttk.Label(
        content_frame,
        text=content,
        wraplength=wraplength,
        justify="left",
        style="Card.TLabel",
    )
    content_label.pack(anchor="w", fill="x")

    def _sync_wraplength(event: Any | None = None) -> None:
        """Expand text to the available content width."""
        available_width = content_frame.winfo_width() or outer.winfo_width()
        if available_width <= 1 and event is not None:
            available_width = int(getattr(event, "width", 0))
        dynamic_wrap = max(wraplength, available_width - (pad * 2))
        content_label.configure(wraplength=dynamic_wrap)

    content_frame.bind("<Configure>", _sync_wraplength)
    outer.bind("<Configure>", _sync_wraplength)

    if initially_expanded:
        content_frame.pack(fill="x")

    def _toggle() -> None:
        if content_frame.winfo_ismapped():
            content_frame.pack_forget()
            toggle_label.config(text=f">  {title}")
        else:
            content_frame.pack(fill="x")
            toggle_label.config(text=f"v  {title}")

    toggle_label.bind("<Button-1>", lambda _e: _toggle())
    header_frame.bind("<Button-1>", lambda _e: _toggle())
    return outer


def create_scrollable_content(
    parent: Misc,
    background: str,
) -> tuple[ttk.Frame, Canvas, ttk.Frame]:
    """Create a vertical scrollable area and return (container, canvas, inner_frame)."""
    container = ttk.Frame(parent)
    canvas = Canvas(
        container,
        highlightthickness=0,
        background=background,
    )
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    inner_frame = ttk.Frame(canvas)
    inner_frame.bind(
        "<Configure>",
        lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas_window = canvas.create_window(0, 0, window=inner_frame, anchor="nw")

    def _on_canvas_configure(event: Any) -> None:
        canvas.itemconfig(canvas_window, width=int(event.width))

    def _on_mousewheel(event: Any) -> None:
        if getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            canvas.yview_scroll(1, "units")
        elif getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            canvas.yview_scroll(-1, "units")

    canvas.bind("<Configure>", _on_canvas_configure)
    parent.bind("<MouseWheel>", _on_mousewheel)
    parent.bind("<Button-4>", _on_mousewheel)
    parent.bind("<Button-5>", _on_mousewheel)

    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    return container, canvas, inner_frame
