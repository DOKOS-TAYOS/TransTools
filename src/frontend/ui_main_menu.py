"""Main menu module for TransTools."""

import sys
from tkinter import Tk, Toplevel, ttk
from typing import Callable

from config import UI_STYLE, __version__
from config.theme import configure_ttk_styles, refresh_theme
from frontend.window_utils import place_window_centered
from i18n import t


def create_main_menu(
    voice_study_callback: Callable[[], None],
    medication_callback: Callable[[], None],
    other_records_callback: Callable[[], None],
    habits_callback: Callable[[], None],
    contacts_callback: Callable[[], None],
    app_info_callback: Callable[[], None],
    view_data_callback: Callable[[], None],
    config_callback: Callable[[], None],
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

    welcome = ttk.Label(main_frame, text=t("menu.welcome"), wraplength=380)
    version_label = ttk.Label(main_frame, text=f"v{__version__}")

    btn_width = UI_STYLE["button_width_wide"]
    btn_width_small = UI_STYLE["button_width"]

    voice_study_btn = ttk.Button(
        main_frame,
        text=t("menu.voice_record"),
        command=voice_study_callback,
        width=btn_width,
    )
    medication_btn = ttk.Button(
        main_frame,
        text=t("menu.medication_record"),
        command=medication_callback,
        width=btn_width,
    )
    other_records_btn = ttk.Button(
        main_frame,
        text=t("menu.other_records"),
        command=other_records_callback,
        width=btn_width,
    )
    habits_btn = ttk.Button(
        main_frame,
        text=t("menu.habits"),
        command=habits_callback,
        width=btn_width,
    )
    contacts_btn = ttk.Button(
        main_frame,
        text=t("menu.info_contacts"),
        command=contacts_callback,
        width=btn_width,
    )
    app_info_btn = ttk.Button(
        main_frame,
        text=t("menu.app_info"),
        command=app_info_callback,
        width=btn_width,
    )
    view_data_btn = ttk.Button(
        main_frame,
        text=t("menu.view_data"),
        command=view_data_callback,
        width=btn_width,
    )
    config_btn = ttk.Button(
        main_frame,
        text=t("menu.config"),
        command=config_callback,
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
    welcome.grid(column=0, row=0, columnspan=2, padx=pad, pady=pad)
    version_label.grid(column=0, row=1, columnspan=2, padx=pad, pady=(0, pad))
    voice_study_btn.grid(column=0, row=2, padx=pad, pady=pad)
    medication_btn.grid(column=1, row=2, padx=pad, pady=pad)
    other_records_btn.grid(column=0, row=3, padx=pad, pady=pad)
    habits_btn.grid(column=1, row=3, padx=pad, pady=pad)
    contacts_btn.grid(column=0, row=4, padx=pad, pady=pad)
    app_info_btn.grid(column=1, row=4, padx=pad, pady=pad)
    view_data_btn.grid(column=0, row=5, padx=pad, pady=pad)
    config_btn.grid(column=0, row=6, padx=pad, pady=pad)
    exit_btn.grid(column=1, row=6, padx=pad, pady=pad)

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
    voice_study_callback: Callable[[], None],
    medication_callback: Callable[[], None],
    other_records_callback: Callable[[], None],
    habits_callback: Callable[[], None],
    contacts_callback: Callable[[], None],
    app_info_callback: Callable[[], None],
    view_data_callback: Callable[[], None],
    config_callback: Callable[[], None],
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
    import __main__

    __main__.menu = menu
    if startup_callback:
        startup_callback(menu)
    menu.mainloop()
