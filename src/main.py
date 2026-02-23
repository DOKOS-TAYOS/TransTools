#!/usr/bin/env python
"""TransTools - Voice tracking application for transition follow-up."""

import sys
from pathlib import Path

# Add src to path (must be before other imports)
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from config import __version__, initialize_and_validate_config  # noqa: E402
from config.env import get_env_from_schema  # noqa: E402
from i18n import initialize_i18n, t  # noqa: E402
from utils import get_logger, setup_logging  # noqa: E402

initialize_and_validate_config()
initialize_i18n()

setup_logging(
    log_level=get_env_from_schema("LOG_LEVEL"),
    log_file=get_env_from_schema("LOG_FILE"),
    log_console=get_env_from_schema("LOG_CONSOLE"),
)
logger = get_logger(__name__)


def _get_menu_window():
    """Get the main menu window from __main__.

    Returns:
        The menu Tk window if set in __main__, else None.
    """
    import __main__

    return getattr(__main__, "menu", None)


def _recording_callback() -> None:
    """Open recording dialog when user selects recording from menu."""
    from frontend.ui_dialogs.recording_dialog import show_recording_dialog

    menu = _get_menu_window()
    if menu:
        show_recording_dialog(menu)


def _history_callback() -> None:
    """Open history dialog when user selects history from menu."""
    from frontend.ui_dialogs.history_dialog import show_history_dialog

    menu = _get_menu_window()
    if menu:
        show_history_dialog(menu)


def _info_callback() -> None:
    """Open info dialog when user selects info from menu."""
    from frontend.ui_dialogs.info_dialog import show_info_dialog

    menu = _get_menu_window()
    if menu:
        show_info_dialog(menu)


def _config_callback() -> None:
    """Open config dialog. Restarts app if user saves changes."""
    from frontend.ui_dialogs.config_dialog import show_config_dialog

    menu = _get_menu_window()
    if menu and show_config_dialog(menu):
        menu.destroy()
        import os

        os.execv(sys.executable, [sys.executable] + sys.argv)


def main() -> None:
    """Main entry point for TransTools application.

    Initializes config, i18n, logging, and starts the main menu.
    """
    log_file = get_env_from_schema("LOG_FILE")
    logger.info("=" * 60)
    logger.info("TransTools starting — v%s", __version__)
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = Path.cwd() / log_path
        logger.info("Log file: %s", log_path.resolve())
    logger.info("=" * 60)

    try:
        from frontend import start_main_menu

        start_main_menu(
            recording_callback=_recording_callback,
            history_callback=_history_callback,
            info_callback=_info_callback,
            config_callback=_config_callback,
        )
        logger.info("TransTools closed")
    except Exception as e:
        logger.critical("Unexpected error: %s", e, exc_info=True)
        from tkinter import messagebox

        messagebox.showerror(t("error.generic"), str(e))
        raise


if __name__ == "__main__":
    main()
