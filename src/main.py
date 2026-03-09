#!/usr/bin/env python
"""TransTools - Voice tracking application for transition follow-up."""

import os
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


def _voice_study_callback(menu, app_service) -> None:
    """Open voice study (recording) dialog when user selects it from menu."""
    from frontend.ui_dialogs.recording_dialog import show_recording_dialog

    show_recording_dialog(menu, app_service=app_service)


def _medication_callback(menu, app_service) -> None:
    """Open medication register dialog."""
    from frontend.ui_dialogs.medication_dialog import show_medication_dialog

    show_medication_dialog(menu, app_service=app_service)


def _other_records_callback(menu, app_service) -> None:
    """Open dialog for visits and other events."""
    from frontend.ui_dialogs.other_records_dialog import show_other_records_dialog

    show_other_records_dialog(menu, app_service=app_service)


def _habits_callback(menu, app_service) -> None:
    """Open adaptive habits dialog."""
    from frontend.ui_dialogs.habits_dialog import show_habits_dialog

    show_habits_dialog(menu, app_service=app_service)


def _contacts_callback(menu, app_service) -> None:
    """Open contacts/resources dialog."""
    from frontend.ui_dialogs.contacts_dialog import show_contacts_dialog

    show_contacts_dialog(menu, app_service=app_service)


def _app_info_callback(menu, _app_service) -> None:
    """Open application information dialog."""
    from frontend.ui_dialogs.app_info_dialog import show_app_info_dialog

    show_app_info_dialog(menu)


def _view_data_callback(menu, app_service) -> None:
    """Open unified data view dialog."""
    from frontend.ui_dialogs.data_view_dialog import show_data_view_dialog

    show_data_view_dialog(menu, app_service=app_service)


def _config_callback(menu, app_service) -> None:
    """Open config dialog. Restarts app if user saves changes."""
    from frontend.ui_dialogs.config_dialog import show_config_dialog

    if show_config_dialog(menu, app_service=app_service):
        menu.destroy()
        os.execv(sys.executable, [sys.executable] + sys.argv)


def _startup_callback(menu_window, app_service) -> None:
    """Run startup flows after main menu creation."""
    from tkinter import messagebox

    from frontend.ui_dialogs.onboarding_dialog import show_onboarding_dialog

    if app_service.needs_onboarding():
        completed = show_onboarding_dialog(menu_window, app_service=app_service)
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

        app_service = get_app_service()
        start_main_menu(
            voice_study_callback=lambda menu: _voice_study_callback(menu, app_service),
            medication_callback=lambda menu: _medication_callback(menu, app_service),
            other_records_callback=lambda menu: _other_records_callback(menu, app_service),
            habits_callback=lambda menu: _habits_callback(menu, app_service),
            contacts_callback=lambda menu: _contacts_callback(menu, app_service),
            app_info_callback=lambda menu: _app_info_callback(menu, app_service),
            view_data_callback=lambda menu: _view_data_callback(menu, app_service),
            config_callback=lambda menu: _config_callback(menu, app_service),
            startup_callback=lambda menu: _startup_callback(menu, app_service),
        )
        logger.info("TransTools closed")
    except Exception as e:
        logger.critical("Unexpected error: %s", e, exc_info=True)
        try:
            from tkinter import messagebox

            messagebox.showerror(t("error.generic"), str(e))
        except Exception:
            print(f"[TransTools] Fatal error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
