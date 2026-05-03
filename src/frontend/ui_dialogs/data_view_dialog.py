"""Unified data view dialog with calendar, charts and exports."""

from __future__ import annotations

import gc
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import IntVar, StringVar, Toplevel, filedialog, messagebox, ttk
from typing import Any

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import UI_STYLE
from config.theme import prepare_ttk_window
from core.context import get_app_service
from core.exporters import export_to_csv, export_to_excel, export_to_pdf, export_to_png
from frontend.date_widgets import DateEntryAdapter, create_date_entry, get_calendar_locale
from frontend.input_widgets import create_combobox
from frontend.window_utils import (
    TreeColumnSpec,
    apply_tree_column_specs,
    place_window_centered,
)
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def get_process_tab_table_rows() -> dict[str, int]:
    """Return the grid rows used by the stacked process tables."""
    return {
        "roadmap": 2,
        "appointments": 4,
    }


def build_process_roadmap_tree_specs() -> tuple[TreeColumnSpec, ...]:
    """Return explicit roadmap table widths for the process tab."""
    return (
        TreeColumnSpec("category", width=220, minwidth=200, anchor="w", stretch=False),
        TreeColumnSpec("title", width=560, minwidth=420, anchor="w", stretch=True),
        TreeColumnSpec("target", width=150, minwidth=140, anchor="w", stretch=False),
        TreeColumnSpec("completed", width=120, minwidth=120, anchor="center", stretch=False),
    )


def build_process_appointments_tree_specs() -> tuple[TreeColumnSpec, ...]:
    """Return explicit appointments table widths for the process tab."""
    return (
        TreeColumnSpec("date", width=160, minwidth=150, anchor="w", stretch=False),
        TreeColumnSpec("type", width=220, minwidth=200, anchor="w", stretch=False),
        TreeColumnSpec("title", width=500, minwidth=380, anchor="w", stretch=True),
        TreeColumnSpec("done", width=120, minwidth=120, anchor="center", stretch=False),
    )


def _create_scrolled_tree_frame(
    parent: ttk.Frame,
    title: str,
    columns: tuple[str, ...],
    headings: dict[str, str],
    specs: tuple[TreeColumnSpec, ...],
    height: int,
) -> ttk.Treeview:
    """Create a labeled treeview with vertical and horizontal scrollbars."""
    ttk.Label(parent, text=title).grid(column=0, row=0, sticky="w", pady=(0, 6))

    tree_frame = ttk.Frame(parent)
    tree_frame.grid(column=0, row=1, sticky="nsew")
    tree_frame.columnconfigure(0, weight=1)
    tree_frame.rowconfigure(0, weight=1)

    tree = ttk.Treeview(
        tree_frame,
        columns=columns,
        show="headings",
        height=height,
    )
    for column_name in columns:
        tree.heading(column_name, text=headings[column_name])
    apply_tree_column_specs(tree, specs)
    tree.grid(column=0, row=0, sticky="nsew")

    yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    yscroll.grid(column=1, row=0, sticky="ns")
    xscroll.grid(column=0, row=1, sticky="ew")
    return tree


def show_data_view_dialog(parent, app_service=None) -> None:
    """Show unified data dialog with calendar, weekly chart and export.

    Args:
        parent: Parent Tk window.
    """
    app_service = app_service or get_app_service()
    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    dlg.title(t("menu.view_data"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])
    dlg.minsize(1100, 700)
    dlg.transient(parent)
    place_window_centered(dlg, width=1280, height=860)

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

    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(side="bottom", fill="x", padx=UI_STYLE["padding"], pady=(0, UI_STYLE["padding"]))
    ttk.Button(btn_frame, text=t("menu.close"), command=_on_close).pack(side="right")

    notebook = ttk.Notebook(dlg)
    notebook.pack(
        fill="both",
        expand=True,
        padx=UI_STYLE["padding"],
        pady=UI_STYLE["padding"],
    )

    user_tab = ttk.Frame(notebook, padding=6)
    calendar_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    chart_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    process_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    wellbeing_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])

    notebook.add(user_tab, text=t("config.tab_user"))
    notebook.add(calendar_tab, text=t("data.tab_calendar"))
    notebook.add(chart_tab, text=t("data.tab_weekly"))
    notebook.add(process_tab, text=t("companion.tab_process"))
    notebook.add(wellbeing_tab, text=t("companion.tab_wellbeing"))

    _build_user_tab(user_tab, app_service)
    _build_calendar_tab(calendar_tab, app_service)
    _build_process_tab(process_tab, app_service)
    _build_wellbeing_summary_tab(wellbeing_tab, app_service)

    weekly = pd.DataFrame(app_service.get_weekly_voice_summary())
    fig = Figure(figsize=(8.4, 4.8), dpi=100)
    ax = fig.add_subplot(111)
    if weekly.empty:
        ax.text(0.5, 0.5, t("data.no_weekly"), ha="center", va="center")
        ax.set_axis_off()
    else:
        weekly = weekly.sort_values("week_start")
        ax.plot(
            weekly["week_start"],
            weekly["pitch_mean_hz"],
            marker="o",
            color=str(UI_STYLE["chart_line"]),
        )
        ax.set_xlabel(t("data.week_start"))
        ax.set_ylabel(t("data.pitch_weekly"))
        ax.set_title(t("data.weekly_chart_title"))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(alpha=0.25)
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=chart_tab)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def _fix_geometry() -> None:
        dlg.update_idletasks()
        place_window_centered(dlg, width=1280, height=860)

    dlg.after(50, _fix_geometry)


def _parse_optional_iso_date(value: str | None) -> date | None:
    """Parse optional ISO date string."""
    if not value or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _set_optional_date_entry(entry: DateEntryAdapter, value: str | None) -> None:
    """Populate an optional date entry from persisted ISO text."""
    entry.set_optional_date(_parse_optional_iso_date(value))


def _get_optional_date_iso(entry: DateEntryAdapter) -> str | None:
    """Read an optional date entry back into ISO text."""
    selected = entry.get_optional_date()
    return selected.isoformat() if selected is not None else None


def _build_user_tab(parent, app_service) -> None:
    """Build user info tab (profile and health settings)."""
    content = ttk.Frame(parent)
    content.pack(anchor="n", fill="x", expand=False)

    profile = app_service.get_profile()
    health = app_service.get_health_config()
    _font = (UI_STYLE["font_family"], UI_STYLE["font_size"])
    pad = 4

    first_name_var = StringVar(value=profile.get("first_name", ""))
    med_period_var = IntVar(value=health.get("medication_every_days") or 7)
    med_dose_var = StringVar(value=health.get("medication_dose") or "")

    med_next_entry = create_date_entry(content, width=14)
    _set_optional_date_entry(med_next_entry, health.get("next_medication_date"))

    next_medical_entry = create_date_entry(content, width=14)
    _set_optional_date_entry(next_medical_entry, health.get("next_medical_visit_date"))

    next_psych_entry = create_date_entry(content, width=14)
    _set_optional_date_entry(next_psych_entry, health.get("next_psych_visit_date"))

    row = 0

    def _add_row(title_key: str, desc_key: str, widget: Any) -> None:
        nonlocal row
        ttk.Label(content, text=t(title_key)).grid(column=0, row=row, sticky="w", pady=(pad, 0))
        widget.grid(column=1, row=row, padx=pad, pady=(pad, 0), sticky="w")
        ttk.Label(content, text=t(desc_key), wraplength=640, style="Small.TLabel").grid(
            column=0, row=row + 1, columnspan=2, sticky="w", padx=(0, pad), pady=(1, pad)
        )
        row += 2

    _add_row(
        "config.profile.first_name",
        "config.profile.first_name_desc",
        ttk.Entry(content, textvariable=first_name_var, width=30, font=_font),
    )
    _add_row(
        "config.profile.next_medication_date",
        "config.profile.next_medication_date_desc",
        med_next_entry,
    )
    _add_row(
        "config.profile.medication_every_days",
        "config.profile.medication_every_days_desc",
        ttk.Spinbox(content, from_=1, to=60, textvariable=med_period_var, width=8, font=_font),
    )
    _add_row(
        "config.profile.medication_dose",
        "config.profile.medication_dose_desc",
        ttk.Entry(content, textvariable=med_dose_var, width=20, font=_font),
    )
    _add_row(
        "config.profile.next_medical_visit_date",
        "config.profile.next_medical_visit_date_desc",
        next_medical_entry,
    )
    _add_row(
        "config.profile.next_psych_visit_date",
        "config.profile.next_psych_visit_date_desc",
        next_psych_entry,
    )

    status_var = StringVar(value="")
    ttk.Label(content, textvariable=status_var, wraplength=640).grid(
        column=0, row=row, columnspan=2, sticky="w", pady=pad
    )
    row += 1

    def _save_user() -> None:
        try:
            app_service.update_profile_and_health(
                first_name=first_name_var.get().strip(),
                next_medication_date=_get_optional_date_iso(med_next_entry),
                medication_every_days=med_period_var.get(),
                medication_dose=med_dose_var.get().strip() or None,
                next_medical_visit_date=_get_optional_date_iso(next_medical_entry),
                next_psych_visit_date=_get_optional_date_iso(next_psych_entry),
            )
            status_var.set(t("data.user_info_saved"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("User info save failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    btn_frame = ttk.Frame(content)
    btn_frame.grid(column=0, row=row, columnspan=2, pady=pad)
    ttk.Button(btn_frame, text=t("config.save"), command=_save_user).pack(side="left", padx=4)


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
            labels = [activity_label.get(kind) or kind for kind in sorted(kinds)]
            cal.calevent_create(parsed, ", ".join(labels), tag_name)
            cal.tag_config(
                tag_name,
                background=str(UI_STYLE["calendar_activity_bg"]),
                foreground=str(UI_STYLE["calendar_activity_fg"]),
            )

        def _on_pick(_event=None) -> None:
            selected_day = cal.selection_get()
            if selected_day is not None:
                _render_day(selected_day)

        cal.bind("<<CalendarSelected>>", _on_pick)
        initial_day = cal.selection_get()
        if initial_day is not None:
            _render_day(initial_day)
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


EXPORT_OPTIONS = [
    ("csv", "data.export_csv"),
    ("xlsx", "data.export_xlsx"),
    ("pdf", "data.export_pdf"),
    ("png", "data.export_png"),
]


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
        wraplength=380,
        justify="left",
    )
    description_label.pack(fill="x", anchor="w", pady=(4, 4))

    date_row = ttk.Frame(export_frame)
    date_row.pack(fill="x", pady=(4, 0))
    ttk.Label(date_row, text=t("data.export_date_from")).pack(side="left")
    date_from = create_date_entry(date_row, width=12)
    date_from.set_date(date.today() - timedelta(days=30))
    date_from.pack(side="left", padx=(4, 12))
    ttk.Label(date_row, text=t("data.export_date_to")).pack(side="left")
    date_to = create_date_entry(date_row, width=12)
    date_to.set_date(date.today())
    date_to.pack(side="left", padx=(4, 0))

    controls_row = ttk.Frame(export_frame)
    controls_row.pack(fill="x", pady=6)
    display_values = [t(key) for _, key in EXPORT_OPTIONS]
    fmt = create_combobox(
        controls_row,
        state="readonly",
        values=display_values,
        width=22,
    )
    fmt.set(display_values[0])
    fmt.pack(side="left")

    status = ttk.Label(export_frame, text="", wraplength=380, justify="left")
    status.pack(fill="x", anchor="w", pady=6)

    def _sync_export_wrap(event=None) -> None:
        """Expand export text to the available width."""
        available_width = export_frame.winfo_width()
        if available_width <= 1 and event is not None:
            available_width = getattr(event, "width", 0)
        wraplength = max(360, available_width - (UI_STYLE["padding"] * 2))
        description_label.configure(wraplength=wraplength)
        status.configure(wraplength=wraplength)

    export_frame.bind("<Configure>", _sync_export_wrap)

    def _selected_format() -> str | None:
        sel = fmt.get().strip()
        for fmt_key, key in EXPORT_OPTIONS:
            if t(key) == sel:
                return fmt_key
        return None

    def _run_export() -> None:
        selected = _selected_format()
        if selected not in {"csv", "xlsx", "pdf", "png"}:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=f".{selected}",
            filetypes=[(selected.upper(), f"*.{selected}")],
        )
        if not path:
            return
        dest = Path(path)
        date_start = date_from.get_date()
        date_end = date_to.get_date()
        if date_start > date_end:
            messagebox.showwarning(
                t("error.generic"),
                t("data.export_date_range_invalid"),
            )
            return
        frames = app_service.to_export_frames(
            date_from=date_start,
            date_to=date_end,
        )
        profile = app_service.get_profile()
        try:
            if selected == "csv":
                export_to_csv(frames, dest)
            elif selected == "xlsx":
                export_to_excel(frames, dest)
            elif selected == "pdf":
                export_to_pdf(
                    frames,
                    dest,
                    profile_name=profile.get("first_name"),
                )
            else:
                export_to_png(frames, dest)
            status.configure(text=t("data.export_ok"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Export failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    ttk.Button(controls_row, text=t("data.export_button"), command=_run_export).pack(
        side="left",
        padx=(8, 0),
    )


def _build_process_tab(parent: ttk.Frame, app_service: Any) -> None:
    """Show roadmap and appointment progress in the data view."""
    parent.columnconfigure(0, weight=1)
    table_rows = get_process_tab_table_rows()
    parent.rowconfigure(table_rows["roadmap"], weight=1)
    parent.rowconfigure(table_rows["appointments"], weight=1)

    snapshot = app_service.get_dashboard_snapshot()
    intro = ttk.Label(
        parent,
        text=t("companion.process_intro"),
        wraplength=1120,
        justify="left",
    )
    intro.grid(column=0, row=0, sticky="w", pady=(0, 8))

    ttk.Label(
        parent,
        text=t(
            "companion.process_summary",
            stage=t(f"companion.stage.{snapshot.journey_stage}"),
            roadmap=str(snapshot.weekly_completed_steps),
            wellbeing=str(snapshot.weekly_wellbeing_logs),
            voice=str(snapshot.weekly_voice_samples),
        ),
        wraplength=1120,
        justify="left",
    ).grid(column=0, row=1, sticky="w", pady=(0, 10))

    roadmap_section = ttk.Frame(parent)
    roadmap_section.grid(column=0, row=table_rows["roadmap"], sticky="nsew", pady=(0, 10))
    roadmap_section.columnconfigure(0, weight=1)
    roadmap_section.rowconfigure(1, weight=1)
    roadmap_tree = _create_scrolled_tree_frame(
        roadmap_section,
        title=t("companion.roadmap_title"),
        columns=("category", "title", "target", "completed"),
        headings={
            "category": t("companion.roadmap_category"),
            "title": t("companion.roadmap_title_col"),
            "target": t("companion.roadmap_target"),
            "completed": t("companion.roadmap_completed"),
        },
        specs=build_process_roadmap_tree_specs(),
        height=7,
    )

    for item in app_service.list_roadmap_items():
        roadmap_tree.insert(
            "",
            "end",
            values=(
                t(f"companion.category.{item.category}"),
                item.title,
                item.target_date or t("data.no_value"),
                t("menu.yes") if item.completed else t("menu.no"),
            ),
        )

    appointments_section = ttk.Frame(parent)
    appointments_section.grid(column=0, row=table_rows["appointments"], sticky="nsew")
    appointments_section.columnconfigure(0, weight=1)
    appointments_section.rowconfigure(1, weight=1)
    appointments_tree = _create_scrolled_tree_frame(
        appointments_section,
        title=t("companion.upcoming_title"),
        columns=("date", "type", "title", "done"),
        headings={
            "date": t("data.date"),
            "type": t("other.visit_type"),
            "title": t("companion.appointment_title"),
            "done": t("companion.roadmap_completed"),
        },
        specs=build_process_appointments_tree_specs(),
        height=7,
    )

    for prep in app_service.list_appointment_preps():
        appointments_tree.insert(
            "",
            "end",
            values=(
                prep.target_date,
                t(f"companion.appointment_type.{prep.appointment_type}"),
                prep.title,
                t("menu.yes") if prep.is_completed else t("menu.no"),
            ),
        )


def _build_wellbeing_summary_tab(parent: ttk.Frame, app_service: Any) -> None:
    """Show recent wellbeing check-ins in the data view."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(1, weight=1)

    ttk.Label(
        parent,
        text=t("companion.wellbeing_intro"),
        wraplength=920,
        justify="left",
    ).grid(column=0, row=0, sticky="w", pady=(0, 8))

    tree = ttk.Treeview(
        parent,
        columns=("date", "mood", "energy", "sleep", "source", "notes"),
        show="headings",
        height=16,
    )
    tree.heading("date", text=t("data.date"))
    tree.heading("mood", text=t("companion.wellbeing_mood"))
    tree.heading("energy", text=t("companion.wellbeing_energy"))
    tree.heading("sleep", text=t("companion.wellbeing_sleep"))
    tree.heading("source", text=t("companion.wellbeing_source"))
    tree.heading("notes", text=t("other.notes"))
    tree.grid(column=0, row=1, sticky="nsew")

    for item in app_service.list_wellbeing_logs()[:30]:
        tree.insert(
            "",
            "end",
            values=(
                item.target_date,
                item.mood,
                item.energy,
                item.sleep,
                t(f"companion.source.{item.linked_source or 'manual'}"),
                item.notes or item.side_effects or t("data.no_value"),
            ),
        )
