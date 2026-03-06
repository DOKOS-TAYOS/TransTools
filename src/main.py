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
from core.context import get_app_service  # noqa: E402
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


def _voice_study_callback() -> None:
    """Open voice study (recording) dialog when user selects it from menu."""
    from frontend.ui_dialogs.recording_dialog import show_recording_dialog

    menu = _get_menu_window()
    if menu:
        show_recording_dialog(menu)


def _medication_callback() -> None:
    """Open medication register dialog."""
    from frontend.ui_dialogs.medication_dialog import show_medication_dialog

    menu = _get_menu_window()
    if menu:
        show_medication_dialog(menu)


def _other_records_callback() -> None:
    """Open dialog for visits and other events."""
    from frontend.ui_dialogs.other_records_dialog import show_other_records_dialog

    menu = _get_menu_window()
    if menu:
        show_other_records_dialog(menu)


def _habits_callback() -> None:
    """Open adaptive habits dialog."""
    from frontend.ui_dialogs.habits_dialog import show_habits_dialog

    menu = _get_menu_window()
    if menu:
        show_habits_dialog(menu)


def _contacts_callback() -> None:
    """Open contacts/resources dialog."""
    from frontend.ui_dialogs.contacts_dialog import show_contacts_dialog

    menu = _get_menu_window()
    if menu:
        show_contacts_dialog(menu)


def _app_info_callback() -> None:
    """Open application information dialog."""
    from frontend.ui_dialogs.app_info_dialog import show_app_info_dialog

    menu = _get_menu_window()
    if menu:
        show_app_info_dialog(menu)


def _view_data_callback() -> None:
    """Open unified data view dialog."""
    from frontend.ui_dialogs.data_view_dialog import show_data_view_dialog

    menu = _get_menu_window()
    if menu:
        show_data_view_dialog(menu)


def _config_callback() -> None:
    """Open config dialog. Restarts app if user saves changes."""
    from frontend.ui_dialogs.config_dialog import show_config_dialog

    menu = _get_menu_window()
    if menu and show_config_dialog(menu, app_service=get_app_service()):
        menu.destroy()
        import os

        os.execv(sys.executable, [sys.executable] + sys.argv)


def _startup_callback(menu_window) -> None:
    """Run startup flows after main menu creation."""
    from tkinter import messagebox

    from frontend.ui_dialogs.onboarding_dialog import show_onboarding_dialog

    app_service = get_app_service()

    if app_service.needs_onboarding():
        completed = show_onboarding_dialog(menu_window)
        if not completed:
            messagebox.showwarning(t("error.generic"), t("onboarding.required"))
            menu_window.destroy()
            return

    alerts = app_service.get_due_alerts()
    if alerts:
        messagebox.showwarning(
            t("reminders.title"),
            "\n\n".join(f"- {line}" for line in alerts),
        )


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
            voice_study_callback=_voice_study_callback,
            medication_callback=_medication_callback,
            other_records_callback=_other_records_callback,
            habits_callback=_habits_callback,
            contacts_callback=_contacts_callback,
            app_info_callback=_app_info_callback,
            view_data_callback=_view_data_callback,
            config_callback=_config_callback,
            startup_callback=_startup_callback,
        )
        logger.info("TransTools closed")
    except Exception as e:
        logger.critical("Unexpected error: %s", e, exc_info=True)
        from tkinter import messagebox

        messagebox.showerror(t("error.generic"), str(e))
        raise


if __name__ == "__main__":
    main()
