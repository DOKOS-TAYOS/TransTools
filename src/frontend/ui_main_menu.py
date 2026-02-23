"""Main menu module for TransTools."""

import sys
from tkinter import Tk, Toplevel, ttk
from typing import Callable

from config import UI_STYLE, __version__
from config.theme import configure_ttk_styles, refresh_theme
from i18n import t


def create_main_menu(
    recording_callback: Callable[[], None],
    history_callback: Callable[[], None],
    info_callback: Callable[[], None],
    config_callback: Callable[[], None],
    exit_callback: Callable[[], None],
) -> Tk:
    """Create and display the main menu window.

    Args:
        recording_callback: Called when user selects recording.
        history_callback: Called when user selects history.
        info_callback: Called when user selects info.
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
    rec_btn = ttk.Button(
        main_frame,
        text=t("menu.recording"),
        command=recording_callback,
        width=btn_width,
    )
    hist_btn = ttk.Button(
        main_frame,
        text=t("menu.history"),
        command=history_callback,
        width=btn_width,
    )
    info_btn = ttk.Button(
        main_frame,
        text=t("menu.info"),
        command=info_callback,
        width=btn_width,
    )
    config_btn = ttk.Button(
        main_frame,
        text=t("menu.config"),
        command=config_callback,
        width=btn_width,
    )
    exit_btn = ttk.Button(
        main_frame,
        text=t("menu.exit"),
        command=lambda: show_exit_confirmation(menu),
        style="Danger.TButton",
        width=btn_width,
    )

    pad = UI_STYLE["padding"]
    welcome.grid(column=0, row=0, padx=pad, pady=pad)
    version_label.grid(column=0, row=1, padx=pad, pady=(0, pad))
    rec_btn.grid(column=0, row=2, padx=pad, pady=pad)
    hist_btn.grid(column=0, row=3, padx=pad, pady=pad)
    info_btn.grid(column=0, row=4, padx=pad, pady=pad)
    config_btn.grid(column=0, row=5, padx=pad, pady=pad)
    exit_btn.grid(column=0, row=6, padx=pad, pady=pad)

    main_frame.pack(fill="both", expand=True)
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
    recording_callback: Callable[[], None],
    history_callback: Callable[[], None],
    info_callback: Callable[[], None],
    config_callback: Callable[[], None],
) -> None:
    """Create and run the main menu.

    Args:
        recording_callback: Called when user selects recording.
        history_callback: Called when user selects history.
        info_callback: Called when user selects info.
        config_callback: Called when user selects config.
    """
    menu = create_main_menu(
        recording_callback=recording_callback,
        history_callback=history_callback,
        info_callback=info_callback,
        config_callback=config_callback,
        exit_callback=lambda: show_exit_confirmation(menu),
    )
    import __main__

    __main__.menu = menu
    menu.mainloop()
