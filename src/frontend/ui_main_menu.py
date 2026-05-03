"""Main menu module for TransTools."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, Toplevel, ttk
from typing import Callable, TypedDict

from PIL import Image, ImageTk

from config import UI_STYLE, __version__
from config.theme import get_surface_palette, prepare_ttk_window
from frontend.ui_dialogs.section_widgets import create_scrollable_content
from frontend.window_utils import place_window_centered
from i18n import t


class MenuActionSpec(TypedDict):
    """Button metadata for a landing-page action."""

    action_key: str
    label_key: str
    style: str


class MenuSectionSpec(TypedDict):
    """Section metadata for a group of landing-page actions."""

    title_key: str
    description_key: str
    columns: int
    items: tuple[MenuActionSpec, ...]


def _load_menu_logo() -> ImageTk.PhotoImage | None:
    """Load the main menu logo image if available."""
    logo_path = Path(__file__).resolve().parents[2] / "images" / "TransTools_logo.png"
    if not logo_path.exists():
        return None

    try:
        image = Image.open(logo_path)
    except Exception:
        return None

    max_width = 280
    max_height = 125
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def get_summary_toggle_label(is_expanded: bool) -> str:
    """Return the label used to show or hide the quick summary."""
    key = "companion.menu_summary_hide" if is_expanded else "companion.menu_summary_show"
    return t(key)


def build_menu_sections() -> tuple[MenuSectionSpec, ...]:
    """Return the premium landing-page sections shown on the main menu."""
    return (
        {
            "title_key": "menu.section_capture",
            "description_key": "menu.section_capture_desc",
            "columns": 2,
            "items": (
                {
                    "action_key": "voice_study",
                    "label_key": "menu.voice_record",
                    "style": "MenuCard.TButton",
                },
                {
                    "action_key": "medication",
                    "label_key": "menu.medication_record",
                    "style": "MenuCard.TButton",
                },
                {
                    "action_key": "other_records",
                    "label_key": "menu.other_records",
                    "style": "MenuCard.TButton",
                },
                {
                    "action_key": "habits",
                    "label_key": "menu.habits",
                    "style": "MenuCard.TButton",
                },
            ),
        },
        {
            "title_key": "menu.section_support",
            "description_key": "menu.section_support_desc",
            "columns": 1,
            "items": (
                {
                    "action_key": "companion",
                    "label_key": "menu.companion",
                    "style": "MenuCard.TButton",
                },
                {
                    "action_key": "view_data",
                    "label_key": "menu.view_data",
                    "style": "MenuCard.TButton",
                },
                {
                    "action_key": "contacts",
                    "label_key": "menu.info_contacts",
                    "style": "MenuCard.TButton",
                },
                {
                    "action_key": "app_info",
                    "label_key": "menu.app_info",
                    "style": "MenuCard.TButton",
                },
            ),
        },
        {
            "title_key": "menu.section_settings",
            "description_key": "menu.section_settings_desc",
            "columns": 2,
            "items": (
                {
                    "action_key": "config",
                    "label_key": "menu.config",
                    "style": "Utility.TButton",
                },
                {
                    "action_key": "exit",
                    "label_key": "menu.exit",
                    "style": "Danger.TButton",
                },
            ),
        },
    )


def _create_section_card(
    parent: ttk.Frame,
    *,
    title: str,
    description: str,
    columns: int,
    items: tuple[MenuActionSpec, ...],
    callbacks: dict[str, Callable[[], None]],
) -> ttk.Frame:
    """Create a reusable card with a section heading and action buttons."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=14)
    header = ttk.Label(card, text=title, style="CardTitle.TLabel")
    body = ttk.Label(
        card,
        text=description,
        style="CardMuted.TLabel",
        justify="left",
        wraplength=420 if columns == 1 else 340,
    )

    header.grid(column=0, row=0, columnspan=columns, sticky="w")
    body.grid(column=0, row=1, columnspan=columns, sticky="ew", pady=(6, 12))

    for column in range(columns):
        card.columnconfigure(column, weight=1)

    for index, item in enumerate(items):
        row = (index // columns) + 2
        column = index % columns
        ttk.Button(
            card,
            text=t(item["label_key"]),
            command=callbacks[item["action_key"]],
            style=item["style"],
        ).grid(column=column, row=row, padx=4, pady=4, sticky="ew")

    return card


def create_main_menu(
    voice_study_callback: Callable[[Tk], None],
    medication_callback: Callable[[Tk], None],
    other_records_callback: Callable[[Tk], None],
    habits_callback: Callable[[Tk], None],
    companion_callback: Callable[[Tk], None],
    contacts_callback: Callable[[Tk], None],
    app_info_callback: Callable[[Tk], None],
    view_data_callback: Callable[[Tk], None],
    config_callback: Callable[[Tk], None],
    dashboard_summary_provider: Callable[[], str] | None,
    exit_callback: Callable[[], None],
) -> Tk:
    """Create and display the main menu window."""
    menu = Tk()
    prepare_ttk_window(menu)
    palette = get_surface_palette()

    menu.title(f"{t('menu.title')} - v{__version__}")
    menu.configure(background=UI_STYLE["bg"])
    menu.resizable(width=False, height=True)
    menu.protocol("WM_DELETE_WINDOW", lambda: show_exit_confirmation(menu))
    menu.columnconfigure(0, weight=1)
    menu.rowconfigure(0, weight=1)

    pad = int(UI_STYLE["padding"])
    scroll_container, _canvas, main_frame = create_scrollable_content(menu, UI_STYLE["bg"])
    scroll_container.grid(column=0, row=0, sticky="nsew")
    main_frame.configure(style="App.TFrame", padding=max(10, pad * 2))
    main_frame.columnconfigure(0, weight=5)
    main_frame.columnconfigure(1, weight=6)

    logo_image = _load_menu_logo()
    if logo_image is not None:
        menu._logo_image = logo_image  # type: ignore[attr-defined]

    hero_frame = tk.Frame(
        main_frame,
        bg=palette.hero_bg,
        highlightthickness=1,
        highlightbackground=palette.panel_border,
        padx=18,
        pady=16,
    )
    hero_frame.grid(column=0, row=0, columnspan=2, sticky="ew", pady=(0, pad + 6))
    hero_frame.grid_columnconfigure(0, weight=1)

    current_hero_row = 0
    if logo_image is not None:
        logo_label = tk.Label(hero_frame, image=logo_image, bg=palette.hero_bg, bd=0)
        logo_label.grid(column=0, row=current_hero_row, sticky="n", pady=(0, 8))
        current_hero_row += 1

    if logo_image is None:
        ttk.Label(hero_frame, text=t("menu.title"), style="HeroTitle.TLabel").grid(
            column=0,
            row=current_hero_row,
            sticky="n",
        )
        current_hero_row += 1

    ttk.Label(
        hero_frame,
        text=t("menu.welcome"),
        style="HeroSubtitle.TLabel",
        justify="center",
        wraplength=720,
    ).grid(column=0, row=current_hero_row, sticky="ew", pady=(6, 8))
    current_hero_row += 1

    ttk.Label(hero_frame, text=f"v{__version__}", style="HeroMeta.TLabel").grid(
        column=0,
        row=current_hero_row,
        sticky="n",
    )

    callbacks: dict[str, Callable[[], None]] = {
        "voice_study": lambda: voice_study_callback(menu),
        "medication": lambda: medication_callback(menu),
        "other_records": lambda: other_records_callback(menu),
        "habits": lambda: habits_callback(menu),
        "companion": lambda: companion_callback(menu),
        "contacts": lambda: contacts_callback(menu),
        "app_info": lambda: app_info_callback(menu),
        "view_data": lambda: view_data_callback(menu),
        "config": lambda: config_callback(menu),
        "exit": exit_callback,
    }

    if dashboard_summary_provider is not None:
        summary_card = ttk.Frame(main_frame, style="Card.TFrame", padding=18)
        summary_card.grid(column=0, row=1, columnspan=2, sticky="ew", pady=(0, pad + 2))
        summary_card.columnconfigure(0, weight=1)
        summary_card.columnconfigure(1, weight=0)

        dashboard_summary_var = StringVar(value="")
        dashboard_summary_expanded_var = BooleanVar(value=False)
        dashboard_summary_toggle_var = StringVar(value=get_summary_toggle_label(False))

        ttk.Label(
            summary_card,
            text=t("companion.menu_summary_title"),
            style="CardTitle.TLabel",
        ).grid(column=0, row=0, sticky="w")

        summary_text = ttk.Label(
            summary_card,
            textvariable=dashboard_summary_var,
            style="SummaryBody.TLabel",
            justify="left",
            wraplength=760,
        )
        summary_toggle_btn = ttk.Button(
            summary_card,
            textvariable=dashboard_summary_toggle_var,
            style="SummaryToggle.TButton",
        )
        summary_toggle_btn.grid(column=1, row=0, sticky="e")

        def _apply_summary_visibility() -> None:
            is_expanded = bool(dashboard_summary_expanded_var.get())
            dashboard_summary_toggle_var.set(get_summary_toggle_label(is_expanded))
            if is_expanded:
                summary_text.grid(column=0, row=1, columnspan=2, sticky="ew", pady=(10, 0))
            else:
                summary_text.grid_forget()

        def _refresh_summary() -> None:
            try:
                dashboard_summary_var.set(dashboard_summary_provider())
            except Exception:
                dashboard_summary_var.set(t("companion.menu_summary_unavailable"))

        def _toggle_summary() -> None:
            dashboard_summary_expanded_var.set(not bool(dashboard_summary_expanded_var.get()))
            if dashboard_summary_expanded_var.get():
                _refresh_summary()
            _apply_summary_visibility()

        summary_toggle_btn.configure(command=_toggle_summary)
        menu.bind("<FocusIn>", lambda _event: _refresh_summary())
        _refresh_summary()
        _apply_summary_visibility()

    sections = build_menu_sections()
    section_positions = (
        (0, 2, 1),
        (1, 2, 1),
        (0, 3, 2),
    )
    for section, (column, row, span) in zip(sections, section_positions, strict=True):
        section_card = _create_section_card(
            main_frame,
            title=t(section["title_key"]),
            description=t(section["description_key"]),
            columns=section["columns"],
            items=section["items"],
            callbacks=callbacks,
        )
        section_card.grid(
            column=column,
            row=row,
            columnspan=span,
            sticky="nsew",
            padx=(0, pad // 2 if column == 0 and span == 1 else 0),
            pady=(0, pad),
        )
        if column == 1:
            section_card.grid_configure(padx=(pad // 2, 0))

    ttk.Frame(main_frame, style="App.TFrame", height=6).grid(column=0, row=4, columnspan=2)
    menu.minsize(900, 620)
    place_window_centered(menu, width=980, height=760)
    return menu


def show_exit_confirmation(parent_menu: Tk) -> None:
    """Show exit confirmation dialog."""
    exit_dlg = Toplevel(parent_menu)
    prepare_ttk_window(exit_dlg)
    exit_dlg.title(t("menu.exit_title"))
    exit_dlg.resizable(width=False, height=False)
    exit_dlg.configure(background=UI_STYLE["bg"])

    body = ttk.Frame(exit_dlg, style="Card.TFrame", padding=20)
    body.pack(fill="both", expand=True, padx=18, pady=18)
    body.columnconfigure(0, weight=1)
    body.columnconfigure(1, weight=1)

    ttk.Label(body, text=t("menu.exit_confirm"), style="CardTitle.TLabel", justify="center").grid(
        column=0,
        row=0,
        columnspan=2,
        pady=(0, 16),
    )
    ttk.Button(
        body,
        text=t("menu.yes"),
        command=lambda: _close_application(parent_menu),
        style="Danger.TButton",
        width=max(12, int(UI_STYLE["button_width"])),
    ).grid(column=0, row=1, padx=6, sticky="ew")
    ttk.Button(
        body,
        text=t("menu.no"),
        command=exit_dlg.destroy,
        style="Utility.TButton",
        width=max(12, int(UI_STYLE["button_width"])),
    ).grid(column=1, row=1, padx=6, sticky="ew")

    exit_dlg.protocol("WM_DELETE_WINDOW", exit_dlg.destroy)
    place_window_centered(exit_dlg, width=420, height=200)
    exit_dlg.transient(parent_menu)
    exit_dlg.grab_set()
    parent_menu.wait_window(exit_dlg)


def _close_application(menu: Tk) -> None:
    """Close the application."""
    menu.destroy()
    sys.exit()


def start_main_menu(
    voice_study_callback: Callable[[Tk], None],
    medication_callback: Callable[[Tk], None],
    other_records_callback: Callable[[Tk], None],
    habits_callback: Callable[[Tk], None],
    companion_callback: Callable[[Tk], None],
    contacts_callback: Callable[[Tk], None],
    app_info_callback: Callable[[Tk], None],
    view_data_callback: Callable[[Tk], None],
    config_callback: Callable[[Tk], None],
    dashboard_summary_provider: Callable[[], str] | None = None,
    startup_callback: Callable[[Tk], None] | None = None,
) -> None:
    """Create and run the main menu."""
    menu = create_main_menu(
        voice_study_callback=voice_study_callback,
        medication_callback=medication_callback,
        other_records_callback=other_records_callback,
        habits_callback=habits_callback,
        companion_callback=companion_callback,
        contacts_callback=contacts_callback,
        app_info_callback=app_info_callback,
        view_data_callback=view_data_callback,
        config_callback=config_callback,
        dashboard_summary_provider=dashboard_summary_provider,
        exit_callback=lambda: show_exit_confirmation(menu),
    )
    if startup_callback:
        startup_callback(menu)
    menu.mainloop()
