"""Unified data view dialog with calendar, charts and exports."""

from __future__ import annotations

import gc
from datetime import date, datetime
from pathlib import Path
from tkinter import Toplevel, filedialog, messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import UI_STYLE
from core.context import get_app_service
from core.exporters import export_to_csv, export_to_excel, export_to_pdf, export_to_png
from frontend.date_widgets import create_date_entry
from frontend.input_widgets import create_combobox
from frontend.window_utils import place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_data_view_dialog(parent) -> None:
    """Show unified data dialog with calendar, weekly chart and export.

    Args:
        parent: Parent Tk window.
    """
    app_service = get_app_service()
    dlg = Toplevel(parent)
    dlg.title(t("menu.view_data"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    fig: Figure | None = None
    canvas = None

    def _on_close() -> None:
        nonlocal canvas, fig
        if canvas is not None:
            try:
                canvas.get_tk_widget().destroy()
            except Exception:
                pass
        if fig is not None:
            try:
                plt.close(fig)
            except Exception:
                pass
        plt.close("all")
        gc.collect()
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)

    notebook = ttk.Notebook(dlg)
    notebook.pack(
        fill="both",
        expand=True,
        padx=UI_STYLE["padding"],
        pady=UI_STYLE["padding"],
    )

    calendar_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    chart_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    export_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])

    notebook.add(calendar_tab, text=t("data.tab_calendar"))
    notebook.add(chart_tab, text=t("data.tab_weekly"))
    notebook.add(export_tab, text=t("data.tab_export"))

    _build_calendar_tab(calendar_tab, app_service)

    weekly = pd.DataFrame(app_service.get_weekly_voice_summary())
    fig = Figure(figsize=(8.4, 4.8), dpi=100)
    ax = fig.add_subplot(111)
    if weekly.empty:
        ax.text(0.5, 0.5, t("data.no_weekly"), ha="center", va="center")
        ax.set_axis_off()
    else:
        weekly = weekly.sort_values("week_start")
        ax.plot(weekly["week_start"], weekly["pitch_mean_hz"], marker="o", color="#2c5f7a")
        ax.set_xlabel(t("data.week_start"))
        ax.set_ylabel(t("data.pitch_weekly"))
        ax.set_title(t("data.weekly_chart_title"))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(alpha=0.25)
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=chart_tab)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    _build_export_tab(export_tab, app_service)

    ttk.Button(dlg, text=t("menu.close"), command=_on_close).pack(pady=8)
    dlg.transient(parent)
    dlg.minsize(760, 560)
    place_window_centered(dlg, width=980, height=700)


def _build_calendar_tab(parent, app_service) -> None:
    """Build calendar and per-day non-sensitive summary tab."""
    left = ttk.Frame(parent)
    right = ttk.Frame(parent)
    left.pack(side="left", fill="y", padx=(0, 8))
    right.pack(side="left", fill="both", expand=True)

    details = ttk.Treeview(
        right,
        columns=("k", "v"),
        show="headings",
        height=16,
    )
    details.heading("k", text=t("data.summary_field"))
    details.heading("v", text=t("data.summary_value"))
    details.column("k", width=200, anchor="w")
    details.column("v", width=420, anchor="w")
    details.pack(fill="both", expand=True)

    def _render_day(day: date) -> None:
        summary = app_service.get_daily_summary(day)
        for item in details.get_children():
            details.delete(item)
        details.insert("", "end", values=(t("data.date"), summary["date"]))
        details.insert(
            "",
            "end",
            values=(t("data.voice_samples"), summary["voice_samples"]),
        )
        details.insert(
            "",
            "end",
            values=(t("data.voice_energy"), f"{summary['voice_energy_avg']:.3f}"),
        )
        details.insert(
            "",
            "end",
            values=(t("data.mood_happy"), f"{summary['voice_mood_happy_avg']:.3f}"),
        )
        details.insert(
            "",
            "end",
            values=(t("data.mood_sad"), f"{summary['voice_mood_sad_avg']:.3f}"),
        )
        details.insert(
            "",
            "end",
            values=(t("data.mood_angry"), f"{summary['voice_mood_angry_avg']:.3f}"),
        )
        details.insert(
            "",
            "end",
            values=(t("data.medication_entries"), len(summary["medication"])),
        )
        details.insert("", "end", values=(t("data.visit_entries"), len(summary["visits"])))
        details.insert(
            "",
            "end",
            values=(t("data.event_entries"), len(summary["other_events"])),
        )
        details.insert("", "end", values=(t("data.habit_entries"), len(summary["habits"])))

    try:
        from tkcalendar import Calendar

        cal = Calendar(
            left,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            locale="es_ES",
            font=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
            headersfont=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
        )
        cal.pack(fill="x")

        tags = app_service.build_calendar_dates_with_activity()
        for day_key, kinds in tags.items():
            parsed = datetime.strptime(day_key, "%Y-%m-%d").date()
            tag_name = "activity"
            cal.calevent_create(parsed, ", ".join(sorted(kinds)), tag_name)
            cal.tag_config(tag_name, background="#d8ecf8", foreground="#0f3a56")

        def _on_pick(_event=None) -> None:
            _render_day(cal.selection_get())

        cal.bind("<<CalendarSelected>>", _on_pick)
        _render_day(cal.selection_get())
    except Exception:
        # Fallback without tkcalendar month view.
        ttk.Label(left, text=t("data.calendar_fallback")).pack(anchor="w")
        entry = create_date_entry(left, width=14)
        entry.set_date(date.today())
        entry.grid(pady=4)
        ttk.Button(
            left,
            text=t("data.load_day"),
            command=lambda: _render_day(entry.get_date()),
        ).grid(pady=4)
        _render_day(date.today())


def _build_export_tab(parent, app_service) -> None:
    """Build export controls tab."""
    ttk.Label(
        parent,
        text=t("data.export_desc"),
        wraplength=520,
        justify="left",
    ).pack(anchor="w", pady=4)
    fmt = create_combobox(
        parent,
        state="readonly",
        values=["csv", "xlsx", "pdf", "png"],
        width=12,
    )
    fmt.set("csv")
    fmt.pack(anchor="w", pady=6)

    status = ttk.Label(parent, text="")
    status.pack(anchor="w", pady=6)

    def _run_export() -> None:
        selected = fmt.get().strip().lower()
        if selected not in {"csv", "xlsx", "pdf", "png"}:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=f".{selected}",
            filetypes=[(selected.upper(), f"*.{selected}")],
        )
        if not path:
            return
        dest = Path(path)
        frames = app_service.to_export_frames()
        profile = app_service.get_profile()
        try:
            if selected == "csv":
                export_to_csv(frames, dest)
            elif selected == "xlsx":
                export_to_excel(frames, dest)
            elif selected == "pdf":
                export_to_pdf(frames, dest, profile_name=profile.get("first_name"))
            else:
                export_to_png(frames, dest)
            status.configure(text=t("data.export_ok", path=str(dest)))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Export failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    ttk.Button(parent, text=t("data.export_button"), command=_run_export).pack(anchor="w", pady=8)
