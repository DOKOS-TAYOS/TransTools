"""Unified companion dialog for roadmap, appointments and wellbeing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from tkinter import BooleanVar, IntVar, StringVar, Text, Toplevel, messagebox, ttk
from typing import Any, Callable

from config import UI_STYLE
from config.theme import prepare_ttk_window
from core.context import get_app_service
from core.types import AppointmentPrepRecord, DashboardSnapshot, RoadmapItem, WellbeingLog
from frontend.date_widgets import DateEntryAdapter, create_date_entry
from frontend.input_widgets import create_combobox, create_entry, create_spinbox
from frontend.text_widgets import configure_notes_widget
from frontend.ui_dialogs.section_widgets import create_scrollable_content
from frontend.window_utils import (
    TreeColumnSpec,
    apply_tree_column_specs,
    get_scroll_friendly_window_height,
    place_window_centered,
)
from i18n import t
from utils import DataStoreError

_ROADMAP_CATEGORIES = [
    "salud",
    "voz",
    "documentacion",
    "entorno_social",
    "imagen_expresion",
    "cirugias_recuperacion",
    "bienestar",
]
_APPOINTMENT_TYPES = ["medical", "psychology", "general"]
_WELLBEING_SOURCES = ["manual", "medication", "visit"]
COMPANION_DIALOG_HEIGHT = get_scroll_friendly_window_height(840)


@dataclass(frozen=True)
class AppointmentFormTextHeights:
    """Comfortable text widget heights for the appointments form."""

    questions: int
    talking_points: int
    follow_up: int
    outcome: int


def build_appointment_tree_column_specs() -> tuple[TreeColumnSpec, ...]:
    """Return the appointments table widths used by the companion dialog."""
    return (
        TreeColumnSpec("date", width=120, minwidth=112, anchor="w", stretch=False),
        TreeColumnSpec("type", width=148, minwidth=132, anchor="w", stretch=False),
        TreeColumnSpec("title", width=286, minwidth=260, anchor="w", stretch=True),
        TreeColumnSpec("done", width=114, minwidth=110, anchor="center", stretch=False),
    )


def build_appointment_form_text_heights() -> dict[str, int]:
    """Return the editing heights for multiline appointment fields."""
    heights = AppointmentFormTextHeights(
        questions=5,
        talking_points=5,
        follow_up=3,
        outcome=3,
    )
    return {
        "questions": heights.questions,
        "talking_points": heights.talking_points,
        "follow_up": heights.follow_up,
        "outcome": heights.outcome,
    }


def _optional_date_to_iso(entry: DateEntryAdapter) -> str | None:
    """Read an optional date widget as ISO text."""
    selected = entry.get_optional_date()
    return selected.isoformat() if selected is not None else None


def _set_optional_iso_date(entry: DateEntryAdapter, value: str | None) -> None:
    """Populate a date widget from optional ISO text."""
    if not value:
        entry.set_optional_date(None)
        return
    try:
        entry.set_optional_date(date.fromisoformat(value))
    except ValueError:
        entry.set_optional_date(None)


def _category_label(category: str) -> str:
    """Translate roadmap category labels."""
    return t(f"companion.category.{category}")


def _appointment_type_label(appointment_type: str) -> str:
    """Translate appointment type labels."""
    return t(f"companion.appointment_type.{appointment_type}")


def _bool_label(value: bool) -> str:
    """Translate yes/no state for treeviews."""
    return t("menu.yes") if value else t("menu.no")


def _set_text_value(widget: Text, value: str | None) -> None:
    """Replace a Tk text widget content."""
    widget.delete("1.0", "end")
    if value:
        widget.insert("1.0", value)


def _bind_wrap_to_width(
    container: ttk.Frame | ttk.LabelFrame,
    label: ttk.Label,
    padding: int,
    minimum_wraplength: int = 320,
) -> None:
    """Keep long dashboard copy wrapped to the current available width."""

    def _sync_wrap(_event: Any | None = None) -> None:
        available_width = max(container.winfo_width(), container.winfo_reqwidth()) - (padding * 3)
        label.configure(wraplength=max(minimum_wraplength, available_width))

    container.bind("<Configure>", _sync_wrap, add="+")
    _sync_wrap()


def show_companion_dialog(parent: Any, app_service: Any | None = None) -> None:
    """Open the companion dashboard and management dialog."""
    app_service = app_service or get_app_service()

    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    dlg.title(t("menu.companion"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])
    dlg.minsize(1140, 720)
    dlg.transient(parent)

    notebook = ttk.Notebook(dlg)
    notebook.pack(fill="both", expand=True, padx=UI_STYLE["padding"], pady=UI_STYLE["padding"])

    dashboard_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    roadmap_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    appointments_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    wellbeing_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])

    notebook.add(dashboard_tab, text=t("companion.tab_dashboard"))
    notebook.add(roadmap_tab, text=t("companion.tab_roadmap"))
    notebook.add(appointments_tab, text=t("companion.tab_appointments"))
    notebook.add(wellbeing_tab, text=t("companion.tab_wellbeing"))

    refresh_dashboard = _build_dashboard_tab(dashboard_tab, app_service, notebook)
    refresh_roadmap = _build_roadmap_tab(roadmap_tab, app_service, refresh_dashboard)
    refresh_appointments = _build_appointments_tab(
        appointments_tab,
        app_service,
        refresh_dashboard,
    )
    refresh_wellbeing = _build_wellbeing_tab(wellbeing_tab, app_service, refresh_dashboard)

    def _refresh_all() -> None:
        refresh_dashboard()
        refresh_roadmap()
        refresh_appointments()
        refresh_wellbeing()

    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(fill="x", padx=UI_STYLE["padding"], pady=(0, UI_STYLE["padding"]))
    ttk.Button(btn_frame, text=t("companion.refresh"), command=_refresh_all).pack(side="left")
    ttk.Button(btn_frame, text=t("menu.close"), command=dlg.destroy).pack(side="right")

    _refresh_all()
    place_window_centered(dlg, width=1280, height=COMPANION_DIALOG_HEIGHT)


def _build_dashboard_tab(
    parent: ttk.Frame,
    app_service: Any,
    notebook: ttk.Notebook,
) -> Callable[[], None]:
    """Create the action-oriented dashboard tab."""
    pad = int(UI_STYLE["padding"])
    parent.columnconfigure(0, weight=1)
    parent.columnconfigure(1, weight=1)

    stage_var = StringVar(value="transitioning")
    action_var = StringVar(value="")
    weekly_var = StringVar(value="")
    alerts_var = StringVar(value="")
    appointments_var = StringVar(value="")
    roadmap_var = StringVar(value="")

    header = ttk.Label(parent, text=t("companion.dashboard_intro"), wraplength=900, justify="left")
    header.grid(column=0, row=0, columnspan=2, sticky="w", pady=(0, pad))
    _bind_wrap_to_width(parent, header, pad, minimum_wraplength=420)

    stage_frame = ttk.LabelFrame(parent, text=t("companion.stage_title"), padding=pad)
    stage_frame.grid(column=0, row=1, sticky="nsew", padx=(0, pad), pady=(0, pad))
    stage_frame.columnconfigure(0, weight=1)
    ttk.Label(stage_frame, text=t("companion.stage_label")).grid(column=0, row=0, sticky="w")
    stage_combo = create_combobox(
        stage_frame,
        state="readonly",
        values=[
            t("companion.stage.transitioning"),
            t("companion.stage.post_transition"),
        ],
        width=22,
        textvariable=stage_var,
    )
    stage_combo.grid(column=0, row=1, sticky="ew", pady=(6, 0))

    def _save_stage() -> None:
        selected = stage_combo.get().strip()
        new_stage = (
            "post_transition"
            if selected == t("companion.stage.post_transition")
            else "transitioning"
        )
        app_service.update_journey_stage(new_stage)
        _refresh()

    ttk.Button(stage_frame, text=t("common.save"), command=_save_stage).grid(
        column=1, row=1, sticky="w", padx=(pad, 0), pady=(6, 0)
    )

    action_frame = ttk.LabelFrame(parent, text=t("companion.recommended_title"), padding=pad)
    action_frame.grid(column=1, row=1, sticky="nsew", pady=(0, pad))
    action_label = ttk.Label(action_frame, textvariable=action_var, wraplength=460, justify="left")
    action_label.pack(anchor="w", fill="x")
    _bind_wrap_to_width(action_frame, action_label, pad)

    weekly_frame = ttk.LabelFrame(parent, text=t("companion.weekly_title"), padding=pad)
    weekly_frame.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=(0, pad))
    weekly_label = ttk.Label(weekly_frame, textvariable=weekly_var, wraplength=460, justify="left")
    weekly_label.pack(anchor="w", fill="x")
    _bind_wrap_to_width(weekly_frame, weekly_label, pad)

    alerts_frame = ttk.LabelFrame(parent, text=t("companion.pending_title"), padding=pad)
    alerts_frame.grid(column=0, row=3, columnspan=2, sticky="nsew", pady=(0, pad))
    alerts_label = ttk.Label(alerts_frame, textvariable=alerts_var, wraplength=460, justify="left")
    alerts_label.pack(anchor="w", fill="x")
    _bind_wrap_to_width(alerts_frame, alerts_label, pad)

    appointments_frame = ttk.LabelFrame(parent, text=t("companion.upcoming_title"), padding=pad)
    appointments_frame.grid(column=0, row=4, columnspan=2, sticky="nsew", pady=(0, pad))
    appointments_label = ttk.Label(
        appointments_frame,
        textvariable=appointments_var,
        wraplength=460,
        justify="left",
    )
    appointments_label.pack(anchor="w", fill="x")
    _bind_wrap_to_width(appointments_frame, appointments_label, pad)
    ttk.Button(
        appointments_frame,
        text=t("companion.open_appointments"),
        command=lambda: notebook.select(2),
    ).pack(anchor="w", pady=(pad, 0))

    roadmap_frame = ttk.LabelFrame(parent, text=t("companion.roadmap_title"), padding=pad)
    roadmap_frame.grid(column=0, row=5, columnspan=2, sticky="nsew", pady=(0, pad))
    roadmap_label = ttk.Label(
        roadmap_frame,
        textvariable=roadmap_var,
        wraplength=460,
        justify="left",
    )
    roadmap_label.pack(anchor="w", fill="x")
    _bind_wrap_to_width(roadmap_frame, roadmap_label, pad)
    ttk.Button(
        roadmap_frame,
        text=t("companion.open_roadmap"),
        command=lambda: notebook.select(1),
    ).pack(anchor="w", pady=(pad, 0))

    def _format_appointments(snapshot: DashboardSnapshot) -> str:
        if not snapshot.upcoming_appointments:
            return t("companion.none")
        return "\n".join(
            f"- {prep.target_date}: {prep.title} ({_appointment_type_label(prep.appointment_type)})"
            for prep in snapshot.upcoming_appointments
        )

    def _format_roadmap(snapshot: DashboardSnapshot) -> str:
        if not snapshot.open_roadmap_items:
            return t("companion.none")
        return "\n".join(
            f"- {_category_label(item.category)}: {item.title}"
            for item in snapshot.open_roadmap_items
        )

    def _refresh() -> None:
        snapshot = app_service.get_dashboard_snapshot()
        stage_var.set(
            t(f"companion.stage.{snapshot.journey_stage}")
            if snapshot.journey_stage in {"transitioning", "post_transition"}
            else t("companion.stage.transitioning")
        )
        action_var.set(snapshot.recommended_action)
        weekly_var.set(
            t(
                "companion.weekly_summary",
                roadmap=str(snapshot.weekly_completed_steps),
                wellbeing=str(snapshot.weekly_wellbeing_logs),
                voice=str(snapshot.weekly_voice_samples),
            )
        )
        alerts_var.set(
            "\n".join(f"- {line}" for line in snapshot.pending_alerts)
            if snapshot.pending_alerts
            else t("companion.none")
        )
        appointments_var.set(_format_appointments(snapshot))
        roadmap_var.set(_format_roadmap(snapshot))

    return _refresh


def _build_roadmap_tab(
    parent: ttk.Frame,
    app_service: Any,
    refresh_dashboard: Callable[[], None],
) -> Callable[[], None]:
    """Create the roadmap management tab."""
    pad = int(UI_STYLE["padding"])
    parent.columnconfigure(0, weight=3)
    parent.columnconfigure(1, weight=2)
    parent.rowconfigure(0, weight=1)

    tree = ttk.Treeview(
        parent,
        columns=("category", "title", "target", "completed"),
        show="headings",
        height=16,
    )
    tree.heading("category", text=t("companion.roadmap_category"))
    tree.heading("title", text=t("companion.roadmap_title_col"))
    tree.heading("target", text=t("companion.roadmap_target"))
    tree.heading("completed", text=t("companion.roadmap_completed"))
    tree.column("category", width=150, anchor="w")
    tree.column("title", width=270, anchor="w")
    tree.column("target", width=110, anchor="w")
    tree.column("completed", width=90, anchor="center")
    tree.grid(column=0, row=0, sticky="nsew", padx=(0, pad))

    form = ttk.Frame(parent)
    form.grid(column=1, row=0, sticky="nsew")

    current_id = StringVar(value="")
    title_var = StringVar(value="")
    active_var = BooleanVar(value=True)
    hidden_var = BooleanVar(value=False)
    status_var = StringVar(value="")

    ttk.Label(form, text=t("companion.roadmap_category")).grid(column=0, row=0, sticky="w")
    category_combo = create_combobox(
        form,
        state="readonly",
        values=[_category_label(category) for category in _ROADMAP_CATEGORIES],
        width=28,
    )
    category_combo.set(_category_label(_ROADMAP_CATEGORIES[0]))
    category_combo.grid(column=0, row=1, sticky="w", pady=(0, pad))

    ttk.Label(form, text=t("companion.roadmap_title_col")).grid(column=0, row=2, sticky="w")
    create_entry(form, textvariable=title_var, width=32).grid(column=0, row=3, sticky="ew")

    ttk.Label(form, text=t("companion.roadmap_target")).grid(
        column=0,
        row=4,
        sticky="w",
        pady=(pad, 0),
    )
    target_entry = create_date_entry(form, width=14)
    target_entry.set_optional_date(None)
    target_entry.grid(column=0, row=5, sticky="w")

    ttk.Label(form, text=t("companion.roadmap_details")).grid(
        column=0,
        row=6,
        sticky="w",
        pady=(pad, 0),
    )
    details_text = Text(form, width=34, height=6)
    configure_notes_widget(details_text)
    details_text.grid(column=0, row=7, sticky="ew")

    ttk.Checkbutton(form, text=t("companion.roadmap_active"), variable=active_var).grid(
        column=0, row=8, sticky="w", pady=(pad, 0)
    )
    ttk.Checkbutton(form, text=t("companion.roadmap_hidden"), variable=hidden_var).grid(
        column=0, row=9, sticky="w"
    )

    ttk.Label(form, textvariable=status_var, wraplength=360, justify="left").grid(
        column=0, row=10, sticky="w", pady=(pad, 0)
    )

    items_by_id: dict[str, RoadmapItem] = {}

    def _selected_category_key() -> str:
        label = category_combo.get().strip()
        for category in _ROADMAP_CATEGORIES:
            if _category_label(category) == label:
                return category
        return _ROADMAP_CATEGORIES[0]

    def _fill_form(item: RoadmapItem) -> None:
        current_id.set(item.id)
        category_combo.set(_category_label(item.category))
        title_var.set(item.title)
        target_entry.set_optional_date(None)
        _set_optional_iso_date(target_entry, item.target_date)
        _set_text_value(details_text, item.details)
        active_var.set(item.is_active)
        hidden_var.set(item.is_hidden)
        status_var.set("")

    def _clear_form() -> None:
        current_id.set("")
        category_combo.set(_category_label(_ROADMAP_CATEGORIES[0]))
        title_var.set("")
        target_entry.set_optional_date(None)
        _set_text_value(details_text, None)
        active_var.set(True)
        hidden_var.set(False)
        status_var.set("")

    def _on_select(_event=None) -> None:
        selected = tree.focus()
        if not selected:
            return
        item = items_by_id.get(selected)
        if item is not None:
            _fill_form(item)

    def _save() -> None:
        try:
            app_service.save_roadmap_item(
                item_id=current_id.get().strip() or None,
                category=_selected_category_key(),
                title=title_var.get(),
                details=details_text.get("1.0", "end").strip() or None,
                target_date=_optional_date_to_iso(target_entry),
                is_active=bool(active_var.get()),
                is_hidden=bool(hidden_var.get()),
            )
            status_var.set(t("companion.saved"))
            _clear_form()
            _refresh()
            refresh_dashboard()
        except (DataStoreError, ValueError) as exc:
            messagebox.showerror(t("error.generic"), str(exc))

    def _toggle_completed() -> None:
        selected = tree.focus()
        if not selected or selected not in items_by_id:
            status_var.set(t("companion.select_roadmap_item_first"))
            tree.focus_set()
            return
        item = items_by_id[selected]
        app_service.toggle_roadmap_item_completed(item.id, completed=not item.completed)
        status_var.set(t("companion.saved"))
        _refresh()
        refresh_dashboard()

    ttk.Button(form, text=t("companion.new"), command=_clear_form).grid(
        column=0, row=11, sticky="w", pady=(pad, 0)
    )
    ttk.Button(form, text=t("common.save"), command=_save).grid(
        column=0, row=12, sticky="w", pady=(6, 0)
    )
    ttk.Button(
        form,
        text=t("companion.toggle_selected_roadmap_item"),
        command=_toggle_completed,
    ).grid(column=0, row=13, sticky="w", pady=(6, 0))

    tree.bind("<<TreeviewSelect>>", _on_select)

    def _refresh() -> None:
        items = app_service.list_roadmap_items()
        items_by_id.clear()
        for row in tree.get_children():
            tree.delete(row)
        for item in items:
            items_by_id[item.id] = item
            tree.insert(
                "",
                "end",
                iid=item.id,
                values=(
                    _category_label(item.category),
                    item.title,
                    item.target_date or t("data.no_value"),
                    _bool_label(item.completed),
                ),
            )

    return _refresh


def _build_appointments_tab(
    parent: ttk.Frame,
    app_service: Any,
    refresh_dashboard: Callable[[], None],
) -> Callable[[], None]:
    """Create the appointment preparation tab."""
    pad = int(UI_STYLE["padding"])
    parent.columnconfigure(0, weight=3)
    parent.columnconfigure(1, weight=4)
    parent.rowconfigure(0, weight=1)

    tree_frame = ttk.Frame(parent, style="Card.TFrame")
    tree_frame.grid(column=0, row=0, sticky="nsew", padx=(0, pad))
    tree_frame.columnconfigure(0, weight=1)
    tree_frame.rowconfigure(0, weight=1)

    tree = ttk.Treeview(
        tree_frame,
        columns=("date", "type", "title", "done"),
        show="headings",
        height=16,
    )
    tree.heading("date", text=t("data.date"))
    tree.heading("type", text=t("other.visit_type"))
    tree.heading("title", text=t("companion.appointment_title"))
    tree.heading("done", text=t("companion.roadmap_completed"))
    apply_tree_column_specs(tree, build_appointment_tree_column_specs())
    tree.grid(column=0, row=0, sticky="nsew")

    tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)
    tree_scroll.grid(column=1, row=0, sticky="ns")

    form_container, _form_canvas, form = create_scrollable_content(parent, str(UI_STYLE["bg"]))
    form_container.grid(column=1, row=0, sticky="nsew")
    form.configure(style="App.TFrame", padding=(0, 0, pad, 0))
    form.columnconfigure(0, weight=1)

    current_id = StringVar(value="")
    title_var = StringVar(value="")
    status_var = StringVar(value="")
    text_heights = build_appointment_form_text_heights()

    ttk.Label(form, text=t("data.date")).grid(column=0, row=0, sticky="w")
    target_entry = create_date_entry(form, width=14)
    target_entry.set_date(date.today())
    target_entry.grid(column=0, row=1, sticky="w", pady=(0, pad))

    ttk.Label(form, text=t("other.visit_type")).grid(column=0, row=2, sticky="w")
    type_combo = create_combobox(
        form,
        state="readonly",
        values=[_appointment_type_label(kind) for kind in _APPOINTMENT_TYPES],
        width=34,
    )
    type_combo.set(_appointment_type_label("medical"))
    type_combo.grid(column=0, row=3, sticky="ew")

    ttk.Label(form, text=t("companion.appointment_title")).grid(
        column=0,
        row=4,
        sticky="w",
        pady=(pad, 0),
    )
    create_entry(form, textvariable=title_var, width=44).grid(column=0, row=5, sticky="ew")

    ttk.Label(form, text=t("companion.questions")).grid(column=0, row=6, sticky="w", pady=(pad, 0))
    questions_text = Text(form, width=44, height=text_heights["questions"], wrap="word")
    configure_notes_widget(questions_text)
    questions_text.grid(column=0, row=7, sticky="ew")

    ttk.Label(form, text=t("companion.talking_points")).grid(
        column=0,
        row=8,
        sticky="w",
        pady=(pad, 0),
    )
    talking_points_text = Text(form, width=44, height=text_heights["talking_points"], wrap="word")
    configure_notes_widget(talking_points_text)
    talking_points_text.grid(column=0, row=9, sticky="ew")

    ttk.Label(form, text=t("companion.follow_up_step")).grid(
        column=0,
        row=10,
        sticky="w",
        pady=(pad, 0),
    )
    follow_up_text = Text(form, width=44, height=text_heights["follow_up"], wrap="word")
    configure_notes_widget(follow_up_text)
    follow_up_text.grid(column=0, row=11, sticky="ew")

    ttk.Label(form, text=t("companion.outcome_notes")).grid(
        column=0,
        row=12,
        sticky="w",
        pady=(pad, 0),
    )
    outcome_text = Text(form, width=44, height=text_heights["outcome"], wrap="word")
    configure_notes_widget(outcome_text)
    outcome_text.grid(column=0, row=13, sticky="ew")

    ttk.Label(form, textvariable=status_var, wraplength=420, justify="left").grid(
        column=0, row=14, sticky="ew", pady=(pad, 0)
    )

    items_by_id: dict[str, AppointmentPrepRecord] = {}

    def _selected_type() -> str:
        label = type_combo.get().strip()
        for appointment_type in _APPOINTMENT_TYPES:
            if _appointment_type_label(appointment_type) == label:
                return appointment_type
        return "general"

    def _fill_form(item: AppointmentPrepRecord) -> None:
        current_id.set(item.id)
        target_entry.set_date(date.fromisoformat(item.target_date))
        type_combo.set(_appointment_type_label(item.appointment_type))
        title_var.set(item.title)
        _set_text_value(questions_text, item.questions)
        _set_text_value(talking_points_text, item.talking_points)
        _set_text_value(follow_up_text, item.follow_up_step)
        _set_text_value(outcome_text, item.outcome_notes)
        status_var.set("")

    def _clear_form() -> None:
        current_id.set("")
        target_entry.set_date(date.today())
        type_combo.set(_appointment_type_label("medical"))
        title_var.set("")
        _set_text_value(questions_text, None)
        _set_text_value(talking_points_text, None)
        _set_text_value(follow_up_text, None)
        _set_text_value(outcome_text, None)
        status_var.set("")

    def _on_select(_event=None) -> None:
        selected = tree.focus()
        if selected and selected in items_by_id:
            _fill_form(items_by_id[selected])

    def _save() -> None:
        try:
            app_service.save_appointment_prep(
                prep_id=current_id.get().strip() or None,
                target_date=target_entry.get_date().isoformat(),
                appointment_type=_selected_type(),
                title=title_var.get(),
                questions=questions_text.get("1.0", "end").strip() or None,
                talking_points=talking_points_text.get("1.0", "end").strip() or None,
                follow_up_step=follow_up_text.get("1.0", "end").strip() or None,
            )
            status_var.set(t("companion.saved"))
            _clear_form()
            _refresh()
            refresh_dashboard()
        except (DataStoreError, ValueError) as exc:
            messagebox.showerror(t("error.generic"), str(exc))

    def _complete() -> None:
        selected = tree.focus()
        if not selected or selected not in items_by_id:
            status_var.set(t("companion.select_appointment_first"))
            tree.focus_set()
            return
        try:
            app_service.complete_appointment_prep(
                selected,
                outcome_notes=outcome_text.get("1.0", "end").strip() or None,
                follow_up_step=follow_up_text.get("1.0", "end").strip() or None,
            )
            status_var.set(t("companion.saved"))
            _refresh()
            refresh_dashboard()
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))

    action_frame = ttk.Frame(form)
    action_frame.grid(column=0, row=15, sticky="ew", pady=(pad, 0))
    action_frame.columnconfigure(0, weight=1)
    action_frame.columnconfigure(1, weight=1)
    ttk.Button(action_frame, text=t("companion.new"), command=_clear_form).grid(
        column=0, row=0, sticky="ew", padx=(0, 6)
    )
    ttk.Button(action_frame, text=t("common.save"), command=_save).grid(
        column=1, row=0, sticky="ew"
    )
    ttk.Button(
        action_frame,
        text=t("companion.complete_selected_appointment"),
        command=_complete,
    ).grid(column=0, row=1, columnspan=2, sticky="ew", pady=(6, 0))

    tree.bind("<<TreeviewSelect>>", _on_select)

    def _refresh() -> None:
        items = app_service.list_appointment_preps()
        items_by_id.clear()
        for row in tree.get_children():
            tree.delete(row)
        for item in items:
            items_by_id[item.id] = item
            tree.insert(
                "",
                "end",
                iid=item.id,
                values=(
                    item.target_date,
                    _appointment_type_label(item.appointment_type),
                    item.title,
                    _bool_label(item.is_completed),
                ),
            )

    return _refresh


def _build_wellbeing_tab(
    parent: ttk.Frame,
    app_service: Any,
    refresh_dashboard: Callable[[], None],
) -> Callable[[], None]:
    """Create the wellbeing logging tab."""
    pad = int(UI_STYLE["padding"])
    parent.columnconfigure(0, weight=3)
    parent.columnconfigure(1, weight=2)
    parent.rowconfigure(0, weight=1)

    tree = ttk.Treeview(
        parent,
        columns=("date", "mood", "energy", "sleep", "source"),
        show="headings",
        height=16,
    )
    tree.heading("date", text=t("data.date"))
    tree.heading("mood", text=t("companion.wellbeing_mood"))
    tree.heading("energy", text=t("companion.wellbeing_energy"))
    tree.heading("sleep", text=t("companion.wellbeing_sleep"))
    tree.heading("source", text=t("companion.wellbeing_source"))
    tree.column("date", width=110, anchor="w")
    tree.column("mood", width=70, anchor="center")
    tree.column("energy", width=70, anchor="center")
    tree.column("sleep", width=70, anchor="center")
    tree.column("source", width=120, anchor="w")
    tree.grid(column=0, row=0, sticky="nsew", padx=(0, pad))

    form = ttk.Frame(parent)
    form.grid(column=1, row=0, sticky="nsew")

    current_id = StringVar(value="")
    mood_var = IntVar(value=3)
    energy_var = IntVar(value=3)
    sleep_var = IntVar(value=3)
    status_var = StringVar(value="")

    ttk.Label(form, text=t("data.date")).grid(column=0, row=0, sticky="w")
    target_entry = create_date_entry(form, width=14)
    target_entry.set_date(date.today())
    target_entry.grid(column=0, row=1, sticky="w", pady=(0, pad))

    ttk.Label(form, text=t("companion.wellbeing_mood")).grid(column=0, row=2, sticky="w")
    create_spinbox(form, from_=0, to=5, width=6, textvariable=mood_var).grid(
        column=0, row=3, sticky="w"
    )
    ttk.Label(form, text=t("companion.wellbeing_energy")).grid(
        column=0,
        row=4,
        sticky="w",
        pady=(pad, 0),
    )
    create_spinbox(form, from_=0, to=5, width=6, textvariable=energy_var).grid(
        column=0, row=5, sticky="w"
    )
    ttk.Label(form, text=t("companion.wellbeing_sleep")).grid(
        column=0,
        row=6,
        sticky="w",
        pady=(pad, 0),
    )
    create_spinbox(form, from_=0, to=5, width=6, textvariable=sleep_var).grid(
        column=0, row=7, sticky="w"
    )

    ttk.Label(form, text=t("companion.wellbeing_source")).grid(
        column=0,
        row=8,
        sticky="w",
        pady=(pad, 0),
    )
    source_combo = create_combobox(
        form,
        state="readonly",
        values=[t(f"companion.source.{source}") for source in _WELLBEING_SOURCES],
        width=24,
    )
    source_combo.set(t("companion.source.manual"))
    source_combo.grid(column=0, row=9, sticky="w")

    ttk.Label(form, text=t("companion.wellbeing_side_effects")).grid(
        column=0, row=10, sticky="w", pady=(pad, 0)
    )
    side_effects_text = Text(form, width=34, height=4)
    configure_notes_widget(side_effects_text)
    side_effects_text.grid(column=0, row=11, sticky="ew")

    ttk.Label(form, text=t("other.notes")).grid(column=0, row=12, sticky="w", pady=(pad, 0))
    notes_text = Text(form, width=34, height=4)
    configure_notes_widget(notes_text)
    notes_text.grid(column=0, row=13, sticky="ew")

    ttk.Label(form, textvariable=status_var, wraplength=360, justify="left").grid(
        column=0, row=14, sticky="w", pady=(pad, 0)
    )

    items_by_id: dict[str, WellbeingLog] = {}

    def _selected_source() -> str:
        label = source_combo.get().strip()
        for source in _WELLBEING_SOURCES:
            if t(f"companion.source.{source}") == label:
                return source
        return "manual"

    def _fill_form(item: WellbeingLog) -> None:
        current_id.set(item.id)
        target_entry.set_date(date.fromisoformat(item.target_date))
        mood_var.set(item.mood)
        energy_var.set(item.energy)
        sleep_var.set(item.sleep)
        source_combo.set(t(f"companion.source.{item.linked_source or 'manual'}"))
        _set_text_value(side_effects_text, item.side_effects)
        _set_text_value(notes_text, item.notes)

    def _clear_form() -> None:
        current_id.set("")
        target_entry.set_date(date.today())
        mood_var.set(3)
        energy_var.set(3)
        sleep_var.set(3)
        source_combo.set(t("companion.source.manual"))
        _set_text_value(side_effects_text, None)
        _set_text_value(notes_text, None)

    def _save() -> None:
        try:
            app_service.save_wellbeing_log(
                log_id=current_id.get().strip() or None,
                target_date=target_entry.get_date().isoformat(),
                mood=mood_var.get(),
                energy=energy_var.get(),
                sleep=sleep_var.get(),
                side_effects=side_effects_text.get("1.0", "end").strip() or None,
                notes=notes_text.get("1.0", "end").strip() or None,
                linked_source=_selected_source(),
            )
            status_var.set(t("companion.saved"))
            _clear_form()
            _refresh()
            refresh_dashboard()
        except (DataStoreError, ValueError) as exc:
            messagebox.showerror(t("error.generic"), str(exc))

    def _on_select(_event=None) -> None:
        selected = tree.focus()
        if selected and selected in items_by_id:
            _fill_form(items_by_id[selected])

    ttk.Button(form, text=t("companion.new"), command=_clear_form).grid(
        column=0, row=15, sticky="w", pady=(pad, 0)
    )
    ttk.Button(form, text=t("common.save"), command=_save).grid(
        column=0, row=16, sticky="w", pady=(6, 0)
    )

    tree.bind("<<TreeviewSelect>>", _on_select)

    def _refresh() -> None:
        items = app_service.list_wellbeing_logs()
        items_by_id.clear()
        for row in tree.get_children():
            tree.delete(row)
        for item in items:
            items_by_id[item.id] = item
            tree.insert(
                "",
                "end",
                iid=item.id,
                values=(
                    item.target_date,
                    item.mood,
                    item.energy,
                    item.sleep,
                    t(f"companion.source.{item.linked_source or 'manual'}"),
                ),
            )

    return _refresh
