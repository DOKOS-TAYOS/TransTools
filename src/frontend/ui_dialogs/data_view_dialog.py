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
from frontend.date_widgets import create_date_entry, get_calendar_locale
from frontend.input_widgets import create_combobox
from frontend.window_utils import place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_data_view_dialog(parent, app_service=None) -> None:
    """Show unified data dialog with calendar, weekly chart and export.

    Args:
        parent: Parent Tk window.
    """
    app_service = app_service or get_app_service()
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

    notebook.add(calendar_tab, text=t("data.tab_calendar"))
    notebook.add(chart_tab, text=t("data.tab_weekly"))

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

    ttk.Button(dlg, text=t("menu.close"), command=_on_close).pack(pady=8)
    dlg.transient(parent)
    dlg.minsize(760, 700)
    place_window_centered(dlg, width=980, height=860)


def _build_calendar_tab(parent, app_service) -> None:
    """Build calendar and per-day non-sensitive summary tab."""
    left = ttk.Frame(parent)
    right = ttk.Frame(parent)
    left.pack(side="left", fill="y", padx=(0, 8))
    right.pack(side="left", fill="both", expand=True)
    right.update_idletasks()

    details = ttk.Treeview(
        right,
        columns=("k", "v"),
        show="headings",
        height=16,
    )
    details.heading("k", text=t("data.summary_field"))
    details.heading("v", text=t("data.summary_value"))
    details.column("k", width=240, minwidth=200, stretch=False, anchor="w")
    details.column("v", width=220, minwidth=160, stretch=False, anchor="w")
    details.pack(fill="both", expand=True)

    def _fit_detail_columns(event=None) -> None:
        """Fit treeview columns inside the visible table width."""
        available_width = details.winfo_width()
        if available_width <= 1 and event is not None:
            available_width = getattr(event, "width", 0)
        if available_width <= 1:
            return

        field_width = min(260, max(190, int(available_width * 0.45)))
        value_width = max(150, available_width - field_width - 6)
        details.column("k", width=field_width)
        details.column("v", width=value_width)

    details.bind("<Configure>", _fit_detail_columns)

    def _render_day(day: date) -> None:
        summary = app_service.get_daily_summary(day)
        for item in details.get_children():
            details.delete(item)
        empty = t("data.no_value")

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
        for i, med in enumerate(summary["medication"], 1):
            dose_val = (med.get("dose") or "").strip() or empty
            hour_val = (med.get("hour") or "").strip() or empty
            notes_val = (med.get("notes") or "").strip() or empty
            med_label = t("data.medication_item", n=str(i))
            details.insert(
                "",
                "end",
                values=(f"  {med_label} ({t('data.medication_dose')})", dose_val),
            )
            if hour_val != empty:
                details.insert(
                    "",
                    "end",
                    values=(f"  {med_label} ({t('data.medication_hour')})", hour_val),
                )
            if notes_val != empty:
                details.insert(
                    "",
                    "end",
                    values=(f"  {med_label} ({t('data.medication_notes')})", notes_val),
                )
        details.insert("", "end", values=(t("data.visit_entries"), len(summary["visits"])))
        for i, v in enumerate(summary["visits"], 1):
            vtype = (
                t("data.visit_type_medical")
                if v.get("visit_type") == "medical"
                else t("data.visit_type_psychology")
            )
            notes_val = (v.get("notes") or "").strip() or empty
            visit_label = t("data.visit_item", n=str(i))
            details.insert("", "end", values=(f"  {visit_label}", vtype))
            if notes_val != empty:
                details.insert(
                    "",
                    "end",
                    values=(f"  {visit_label} ({t('data.visit_notes')})", notes_val),
                )
        details.insert(
            "",
            "end",
            values=(t("data.event_entries"), len(summary["other_events"])),
        )
        for i, ev in enumerate(summary["other_events"], 1):
            notes_val = (ev.get("notes") or "").strip() or empty
            cat = (ev.get("category") or "general").strip()
            event_label = t("data.event_item", n=str(i))
            details.insert("", "end", values=(f"  {event_label}", cat))
            if notes_val != empty:
                details.insert(
                    "",
                    "end",
                    values=(f"  {event_label} ({t('data.event_notes')})", notes_val),
                )
        details.insert("", "end", values=(t("data.habit_entries"), len(summary["habits"])))

    try:
        from tkcalendar import Calendar

        cal = Calendar(
            left,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            locale=get_calendar_locale(),
            font=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
            headersfont=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
        )
        cal.pack(fill="x")

        activity_label = {
            "voice": t("data.activity_voice"),
            "medication": t("data.activity_medication"),
            "visit": t("data.activity_visit"),
            "event": t("data.activity_event"),
            "habit": t("data.activity_habit"),
        }
        tags = app_service.build_calendar_dates_with_activity()
        for day_key, kinds in tags.items():
            try:
                parsed = datetime.strptime(day_key, "%Y-%m-%d").date()
            except ValueError:
                continue
            tag_name = "activity"
            labels = [activity_label.get(kind, kind) for kind in sorted(kinds)]
            cal.calevent_create(parsed, ", ".join(labels), tag_name)
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

    _build_export_controls(left, app_service)


def _build_export_controls(parent, app_service) -> None:
    """Build export controls below the calendar area."""
    export_frame = ttk.Frame(parent, padding=UI_STYLE["padding"])
    export_frame.pack(fill="x", pady=(12, 0))

    ttk.Label(
        export_frame,
        text=t("data.tab_export"),
    ).pack(anchor="w")

    description_label = ttk.Label(
        export_frame,
        text=t("data.export_desc"),
        wraplength=240,
        justify="left",
    )
    description_label.pack(fill="x", anchor="w", pady=(4, 4))
    controls_row = ttk.Frame(export_frame)
    controls_row.pack(fill="x", pady=6)
    fmt = create_combobox(
        controls_row,
        state="readonly",
        values=["csv", "xlsx", "pdf", "png"],
        width=12,
    )
    fmt.set("csv")
    fmt.pack(side="left")

    status = ttk.Label(export_frame, text="", wraplength=240, justify="left")
    status.pack(fill="x", anchor="w", pady=6)

    def _sync_export_wrap(event=None) -> None:
        """Expand export text to the available width."""
        available_width = export_frame.winfo_width()
        if available_width <= 1 and event is not None:
            available_width = getattr(event, "width", 0)
        wraplength = max(220, available_width - (UI_STYLE["padding"] * 2))
        description_label.configure(wraplength=wraplength)
        status.configure(wraplength=wraplength)

    export_frame.bind("<Configure>", _sync_export_wrap)

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

    ttk.Button(controls_row, text=t("data.export_button"), command=_run_export).pack(
        side="left",
        padx=(8, 0),
    )
