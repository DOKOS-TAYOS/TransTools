"""Information dialog for TransTools."""

from tkinter import Canvas, Frame, Label, Toplevel, ttk

from config import UI_STYLE, __version__
from frontend.window_utils import place_window_centered
from i18n import t

# Accent color for collapsible section headers (visible on light and dark themes)
_SECTION_HEADER_BG = "#2c5f7a"
_SECTION_HEADER_FG = "#ffffff"


def _create_collapsible_section(
    parent: ttk.Frame,
    title: str,
    content: str,
    wraplength: int = 620,
    initially_expanded: bool = True,
) -> ttk.Frame:
    """Create a collapsible section with title and content.

    Args:
        parent: Parent frame.
        title: Section header text.
        content: Section body text.
        wraplength: Max width for text wrapping.
        initially_expanded: Whether section starts expanded.

    Returns:
        The outer frame containing the section.
    """
    outer = ttk.Frame(parent)
    pad = UI_STYLE["padding"]

    header_frame = Frame(
        outer,
        bg=_SECTION_HEADER_BG,
        highlightthickness=0,
        cursor="hand2",
    )
    header_frame.pack(fill="x", pady=(pad, 0))

    toggle_label = Label(
        header_frame,
        text=f"▼  {title}" if initially_expanded else f"▶  {title}",
        cursor="hand2",
        bg=_SECTION_HEADER_BG,
        fg=_SECTION_HEADER_FG,
        font=(UI_STYLE["font_family"], UI_STYLE["font_size"], "bold"),
        padx=pad,
        pady=6,
    )
    toggle_label.pack(anchor="w")

    content_frame = ttk.Frame(outer)
    content_label = ttk.Label(
        content_frame,
        text=content,
        wraplength=wraplength,
        justify="left",
    )
    content_label.pack(anchor="w", padx=(pad, 0), pady=(4, pad))

    if initially_expanded:
        content_frame.pack(fill="x")
    else:
        content_frame.pack_forget()

    def _toggle() -> None:
        if content_frame.winfo_ismapped():
            content_frame.pack_forget()
            toggle_label.config(text=f"▶ {title}")
        else:
            content_frame.pack(fill="x")
            toggle_label.config(text=f"▼ {title}")

    toggle_label.bind("<Button-1>", lambda e: _toggle())
    header_frame.bind("<Button-1>", lambda e: _toggle())

    return outer


def show_info_dialog(parent) -> None:
    """Show information dialog.

    Args:
        parent: Parent Tk window. Closing with X returns to main menu.
    """
    dlg = Toplevel(parent)
    dlg.title(t("menu.info"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    pad = UI_STYLE["padding"]
    wraplength = 620

    scroll_container = ttk.Frame(dlg)
    canvas = Canvas(
        scroll_container,
        highlightthickness=0,
        background=UI_STYLE["bg"],
    )
    scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
    inner_frame = ttk.Frame(canvas)
    inner_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas_window = canvas.create_window(0, 0, window=inner_frame, anchor="nw")

    def _on_canvas_configure(event) -> None:
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event) -> None:
        if getattr(event, "num", None) == 5 or getattr(event, "delta", 0) == -120:
            canvas.yview_scroll(1, "units")
        elif getattr(event, "num", None) == 4 or getattr(event, "delta", 0) == 120:
            canvas.yview_scroll(-1, "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", _on_mousewheel)
    canvas.bind_all("<Button-5>", _on_mousewheel)

    # Sections
    _create_collapsible_section(
        inner_frame,
        t("info.section_about"),
        t("info.content"),
        wraplength=wraplength,
        initially_expanded=True,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    _create_collapsible_section(
        inner_frame,
        t("info.section_features"),
        t("info.features_content"),
        wraplength=wraplength,
        initially_expanded=True,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    _create_collapsible_section(
        inner_frame,
        t("info.section_privacy"),
        t("info.privacy_content"),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    _create_collapsible_section(
        inner_frame,
        t("info.section_disclaimer"),
        t("info.disclaimer_content"),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    _create_collapsible_section(
        inner_frame,
        t("info.section_version"),
        t("info.version_content", version=__version__),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_container.pack(fill="both", expand=True, padx=pad, pady=pad)

    close_btn = ttk.Button(dlg, text=t("menu.close"), command=dlg.destroy)
    close_btn.pack(pady=pad)

    def _unbind_mousewheel() -> None:
        try:
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        except Exception:
            pass

    dlg.bind("<Destroy>", lambda e: _unbind_mousewheel())

    def _on_close() -> None:
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    dlg.minsize(520, 420)
    place_window_centered(dlg, width=1020, height=680)
