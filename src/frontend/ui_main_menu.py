"""Main menu module for TransTools."""

import sys
from pathlib import Path
from tkinter import Tk, Toplevel, ttk
from typing import Callable

from PIL import Image, ImageTk

from config import UI_STYLE, __version__
from config.theme import configure_ttk_styles, refresh_theme
from frontend.window_utils import place_window_centered
from i18n import t


def _load_menu_logo() -> ImageTk.PhotoImage | None:
    """Load the main menu logo image if available."""
    logo_path = Path(__file__).resolve().parents[2] / "images" / "TransTools_logo.png"
    if not logo_path.exists():
        return None

    try:
        image = Image.open(logo_path)
    except Exception:
        return None

    max_width = 560
    max_height = 235
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def create_main_menu(
    voice_study_callback: Callable[[Tk], None],
    medication_callback: Callable[[Tk], None],
    other_records_callback: Callable[[Tk], None],
    habits_callback: Callable[[Tk], None],
    contacts_callback: Callable[[Tk], None],
    app_info_callback: Callable[[Tk], None],
    view_data_callback: Callable[[Tk], None],
    config_callback: Callable[[Tk], None],
    exit_callback: Callable[[], None],
) -> Tk:
    """Create and display the main menu window.

    Args:
        voice_study_callback: Called when user selects voice study.
        medication_callback: Called when user selects medication register.
        other_records_callback: Called when user selects other records.
        habits_callback: Called when user selects habit checklist.
        contacts_callback: Called when user selects support contacts.
        app_info_callback: Called when user selects application info.
        view_data_callback: Called when user selects unified data view.
        config_callback: Called when user selects config.
        exit_callback: Called when user selects exit.

    Returns:
        The main menu Tk window.
    """
    refresh_theme()
    menu = Tk()
    menu.title(f"{t('menu.title')} — v{__version__}")
    menu.configure(background=UI_STYLE["bg"])
    menu.resizable(width=False, height=False)
    menu.protocol("WM_DELETE_WINDOW", lambda: show_exit_confirmation(menu))
    configure_ttk_styles(menu)

    main_frame = ttk.Frame(menu, padding=UI_STYLE["padding"])
    logo_image = _load_menu_logo()
    if logo_image is not None:
        menu._logo_image = logo_image  # type: ignore[attr-defined]

    logo_label = None
    if logo_image is not None:
        logo_label = ttk.Label(main_frame, image=logo_image)
    welcome = ttk.Label(main_frame, text=t("menu.welcome"), wraplength=460, justify="center")
    version_label = ttk.Label(main_frame, text=f"v{__version__}")

    btn_width = max(UI_STYLE["button_width_wide"], 24)
    btn_width_small = max(UI_STYLE["button_width"], 18)

    voice_study_btn = ttk.Button(
        main_frame,
        text=t("menu.voice_record"),
        command=lambda: voice_study_callback(menu),
        width=btn_width,
    )
    medication_btn = ttk.Button(
        main_frame,
        text=t("menu.medication_record"),
        command=lambda: medication_callback(menu),
        width=btn_width,
    )
    other_records_btn = ttk.Button(
        main_frame,
        text=t("menu.other_records"),
        command=lambda: other_records_callback(menu),
        width=btn_width,
    )
    habits_btn = ttk.Button(
        main_frame,
        text=t("menu.habits"),
        command=lambda: habits_callback(menu),
        width=btn_width,
    )
    contacts_btn = ttk.Button(
        main_frame,
        text=t("menu.info_contacts"),
        command=lambda: contacts_callback(menu),
        width=btn_width,
    )
    app_info_btn = ttk.Button(
        main_frame,
        text=t("menu.app_info"),
        command=lambda: app_info_callback(menu),
        width=btn_width,
    )
    view_data_btn = ttk.Button(
        main_frame,
        text=t("menu.view_data"),
        command=lambda: view_data_callback(menu),
        width=btn_width,
    )
    config_btn = ttk.Button(
        main_frame,
        text=t("menu.config"),
        command=lambda: config_callback(menu),
        width=btn_width_small,
    )
    exit_btn = ttk.Button(
        main_frame,
        text=t("menu.exit"),
        command=exit_callback,
        style="Danger.TButton",
        width=btn_width_small,
    )

    pad = UI_STYLE["padding"]
    current_row = 0
    if logo_label is not None:
        logo_label.grid(column=0, row=current_row, columnspan=2, padx=pad, pady=(pad, 8))
        current_row += 1
    welcome.grid(column=0, row=current_row, columnspan=2, padx=pad, pady=(0, pad))
    current_row += 1
    version_label.grid(column=0, row=current_row, columnspan=2, padx=pad, pady=(0, pad))
    current_row += 1
    voice_study_btn.grid(column=0, row=current_row, padx=pad, pady=pad)
    medication_btn.grid(column=1, row=current_row, padx=pad, pady=pad)
    current_row += 1
    other_records_btn.grid(column=0, row=current_row, padx=pad, pady=pad)
    habits_btn.grid(column=1, row=current_row, padx=pad, pady=pad)
    current_row += 1
    contacts_btn.grid(column=0, row=current_row, padx=pad, pady=pad)
    app_info_btn.grid(column=1, row=current_row, padx=pad, pady=pad)
    current_row += 1
    view_data_btn.grid(column=0, row=current_row, padx=pad, pady=pad)
    current_row += 1
    config_btn.grid(column=0, row=current_row, padx=pad, pady=pad)
    exit_btn.grid(column=1, row=current_row, padx=pad, pady=pad)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.pack(fill="both", expand=True)
    place_window_centered(menu)
    return menu


def show_exit_confirmation(parent_menu: Tk) -> None:
    """Show exit confirmation dialog.

    Args:
        parent_menu: Main menu Tk window.
    """
    exit_dlg = Toplevel(parent_menu)
    exit_dlg.title(t("menu.exit_title"))
    exit_dlg.resizable(width=False, height=False)
    exit_dlg.configure(background=UI_STYLE["bg"])

    msg = ttk.Label(exit_dlg, text=t("menu.exit_confirm"))
    yes_btn = ttk.Button(
        exit_dlg,
        text=t("menu.yes"),
        command=lambda: _close_application(parent_menu),
        style="Danger.TButton",
        width=UI_STYLE["button_width"],
    )
    no_btn = ttk.Button(
        exit_dlg,
        text=t("menu.no"),
        command=exit_dlg.destroy,
        style="Accent.TButton",
        width=UI_STYLE["button_width"],
    )

    pad = UI_STYLE["padding"]
    msg.pack(padx=pad, pady=pad)
    yes_btn.pack(side="left", padx=pad, pady=pad)
    no_btn.pack(side="right", padx=pad, pady=pad)

    exit_dlg.protocol("WM_DELETE_WINDOW", exit_dlg.destroy)
    place_window_centered(exit_dlg)
    exit_dlg.transient(parent_menu)
    exit_dlg.grab_set()
    parent_menu.wait_window(exit_dlg)


def _close_application(menu: Tk) -> None:
    """Close the application.

    Args:
        menu: Main menu Tk window to destroy.
    """
    menu.destroy()
    sys.exit()


def start_main_menu(
    voice_study_callback: Callable[[Tk], None],
    medication_callback: Callable[[Tk], None],
    other_records_callback: Callable[[Tk], None],
    habits_callback: Callable[[Tk], None],
    contacts_callback: Callable[[Tk], None],
    app_info_callback: Callable[[Tk], None],
    view_data_callback: Callable[[Tk], None],
    config_callback: Callable[[Tk], None],
    startup_callback: Callable[[Tk], None] | None = None,
) -> None:
    """Create and run the main menu.

    Args:
        voice_study_callback: Called when user selects voice study.
        medication_callback: Called when user selects medication register.
        other_records_callback: Called when user selects other records.
        habits_callback: Called when user selects habits.
        contacts_callback: Called when user selects contacts.
        app_info_callback: Called when user selects application info.
        view_data_callback: Called when user selects data view.
        config_callback: Called when user selects config.
        startup_callback: Optional callback executed after menu creation.
    """
    menu = create_main_menu(
        voice_study_callback=voice_study_callback,
        medication_callback=medication_callback,
        other_records_callback=other_records_callback,
        habits_callback=habits_callback,
        contacts_callback=contacts_callback,
        app_info_callback=app_info_callback,
        view_data_callback=view_data_callback,
        config_callback=config_callback,
        exit_callback=lambda: show_exit_confirmation(menu),
    )
    if startup_callback:
        startup_callback(menu)
    menu.mainloop()
