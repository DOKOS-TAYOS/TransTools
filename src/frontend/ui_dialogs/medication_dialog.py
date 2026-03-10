"""Medication register dialog."""

from __future__ import annotations

from datetime import date
from tkinter import StringVar, Text, Toplevel, messagebox, ttk

from config import UI_STYLE
from core.context import get_app_service
from frontend.date_widgets import create_date_entry
from frontend.input_widgets import create_entry
from frontend.text_widgets import configure_notes_widget
from frontend.window_utils import place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_medication_dialog(parent, app_service=None) -> None:
    """Show medication register dialog.

    Args:
        parent: Parent Tk window.
    """
    app_service = app_service or get_app_service()
    health = app_service.get_health_config()

    dlg = Toplevel(parent)
    dlg.title(t("menu.medication_record"))
    dlg.resizable(width=False, height=False)
    dlg.configure(background=UI_STYLE["bg"])

    hour_var = StringVar(value="")
    dose_var = StringVar(value=health.get("medication_dose") or "")

    frame = ttk.Frame(dlg, padding=UI_STYLE["padding"])
    ttk.Label(frame, text=t("medication.date")).grid(column=0, row=0, sticky="w", pady=3)
    date_entry = create_date_entry(frame, width=14)
    date_entry.set_date(date.today())
    date_entry.grid(column=1, row=0, sticky="w", pady=3)

    ttk.Label(frame, text=t("medication.hour")).grid(column=0, row=1, sticky="w", pady=3)
    create_entry(frame, textvariable=hour_var, width=14).grid(column=1, row=1, sticky="w", pady=3)

    ttk.Label(frame, text=t("medication.dose")).grid(column=0, row=2, sticky="w", pady=3)
    create_entry(frame, textvariable=dose_var, width=22).grid(column=1, row=2, sticky="w", pady=3)

    ttk.Label(frame, text=t("medication.notes")).grid(column=0, row=3, sticky="nw", pady=3)
    notes_text = Text(frame, width=34, height=5)
    configure_notes_widget(notes_text)
    notes_text.grid(column=1, row=3, sticky="w", pady=3)

    status_var = StringVar(value="")
    ttk.Label(frame, textvariable=status_var).grid(
        column=0, row=4, columnspan=2, sticky="w", pady=3
    )

    def _save() -> None:
        try:
            app_service.add_medication_record(
                target_date=date_entry.get_date(),
                taken=True,
                hour=hour_var.get().strip() or None,
                dose=dose_var.get().strip() or None,
                notes=notes_text.get("1.0", "end").strip() or None,
            )
            status_var.set(t("medication.saved"))
        except ValueError:
            messagebox.showerror(t("error.generic"), t("medication.invalid_date"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Medication save failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    ttk.Button(frame, text=t("common.save"), command=_save, width=UI_STYLE["button_width"]).grid(
        column=0, row=5, padx=4, pady=8
    )
    ttk.Button(
        frame, text=t("menu.close"), command=dlg.destroy, width=UI_STYLE["button_width"]
    ).grid(column=1, row=5, padx=4, pady=8)

    frame.pack(fill="both")
    dlg.transient(parent)
    dlg.update_idletasks()
    pad = int(UI_STYLE["padding"])
    target_width = max(520, frame.winfo_reqwidth() + (pad * 4))
    target_height = max(320, frame.winfo_reqheight() + (pad * 2))
    dlg.minsize(target_width, target_height)
    place_window_centered(dlg, width=target_width, height=target_height)
