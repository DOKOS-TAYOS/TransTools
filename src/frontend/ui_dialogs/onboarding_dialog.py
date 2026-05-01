"""First-run onboarding wizard."""

from __future__ import annotations

from datetime import date
from tkinter import BooleanVar, IntVar, StringVar, Toplevel, messagebox, ttk

from config import UI_STYLE
from config.theme import prepare_ttk_window
from core.context import get_app_service
from frontend.date_widgets import create_date_entry
from frontend.input_widgets import create_entry, create_spinbox
from frontend.window_utils import place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_onboarding_dialog(parent, app_service=None) -> bool:
    """Show first-run onboarding wizard.

    Args:
        parent: Parent Tk window.

    Returns:
        True when completed successfully.
    """
    app_service = app_service or get_app_service()
    if not app_service.needs_onboarding():
        return True

    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    dlg.title(t("onboarding.title"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])
    dlg.transient(parent)
    dlg.grab_set()

    first_name_var = StringVar(value="")
    dose_var = StringVar(value="")
    period_var = IntVar(value=7)
    status_var = StringVar(value="")

    has_next_med_var = BooleanVar(value=False)
    has_next_medical_var = BooleanVar(value=False)
    has_next_psych_var = BooleanVar(value=False)

    steps: list[ttk.Frame] = []
    step_idx = {"value": 0}

    body = ttk.Frame(dlg, padding=UI_STYLE["padding"])
    body.pack(fill="both", expand=True)
    nav = ttk.Frame(dlg, padding=UI_STYLE["padding"])
    nav.pack(fill="x")

    # Step 1: Welcome/help.
    s1 = ttk.Frame(body)
    ttk.Label(s1, text=t("onboarding.welcome_title")).pack(anchor="w", pady=(0, 6))
    welcome_body_label = ttk.Label(
        s1,
        text=t("onboarding.welcome_body"),
        wraplength=680,
        justify="left",
    )
    welcome_body_label.pack(anchor="w", fill="x")
    ttk.Label(s1, text=t("onboarding.help_title")).pack(anchor="w", pady=(12, 6))
    help_body_label = ttk.Label(
        s1,
        text=t("onboarding.help_body"),
        wraplength=680,
        justify="left",
    )
    help_body_label.pack(anchor="w", fill="x")
    steps.append(s1)

    # Step 2: Profile and optional settings.
    s2 = ttk.Frame(body)
    s2.columnconfigure(1, weight=1)
    ttk.Label(s2, text=t("onboarding.first_name")).grid(column=0, row=0, sticky="w", pady=4)
    first_name_entry = create_entry(s2, textvariable=first_name_var, width=30)
    first_name_entry.grid(column=1, row=0, sticky="w", pady=4)

    ttk.Checkbutton(
        s2,
        text=t("onboarding.next_medication_enable"),
        variable=has_next_med_var,
    ).grid(column=0, row=1, columnspan=2, sticky="w", pady=4)
    medication_frame = ttk.Frame(s2)
    medication_frame.grid(column=0, row=2, columnspan=2, sticky="ew")
    medication_frame.columnconfigure(0, weight=1)
    ttk.Label(medication_frame, text=t("onboarding.next_medication_date")).grid(
        column=0,
        row=0,
        sticky="w",
        pady=2,
    )
    med_date_entry = create_date_entry(medication_frame, width=14)
    med_date_entry.set_date(date.today())
    med_date_entry.grid(column=0, row=1, sticky="w", pady=(0, 4))
    ttk.Label(medication_frame, text=t("onboarding.med_period")).grid(
        column=0,
        row=2,
        sticky="w",
        pady=2,
    )
    create_spinbox(medication_frame, from_=1, to=60, width=8, textvariable=period_var).grid(
        column=0,
        row=3,
        sticky="w",
        pady=(0, 4),
    )
    ttk.Label(medication_frame, text=t("onboarding.med_dose")).grid(
        column=0,
        row=4,
        sticky="w",
        pady=2,
    )
    create_entry(medication_frame, textvariable=dose_var, width=25).grid(
        column=0,
        row=5,
        sticky="w",
        pady=(0, 2),
    )

    ttk.Checkbutton(
        s2,
        text=t("onboarding.next_medical_enable"),
        variable=has_next_medical_var,
    ).grid(column=0, row=3, columnspan=2, sticky="w", pady=4)
    medical_frame = ttk.Frame(s2)
    medical_frame.grid(column=0, row=4, columnspan=2, sticky="ew")
    medical_frame.columnconfigure(0, weight=1)
    ttk.Label(medical_frame, text=t("onboarding.next_medical_date")).grid(
        column=0,
        row=0,
        sticky="w",
        pady=2,
    )
    med_visit_entry = create_date_entry(medical_frame, width=14)
    med_visit_entry.set_date(date.today())
    med_visit_entry.grid(column=0, row=1, sticky="w", pady=(0, 2))

    ttk.Checkbutton(
        s2,
        text=t("onboarding.next_psych_enable"),
        variable=has_next_psych_var,
    ).grid(column=0, row=5, columnspan=2, sticky="w", pady=4)
    psych_frame = ttk.Frame(s2)
    psych_frame.grid(column=0, row=6, columnspan=2, sticky="ew")
    psych_frame.columnconfigure(0, weight=1)
    ttk.Label(psych_frame, text=t("onboarding.next_psych_date")).grid(
        column=0,
        row=0,
        sticky="w",
        pady=2,
    )
    psych_visit_entry = create_date_entry(psych_frame, width=14)
    psych_visit_entry.set_date(date.today())
    psych_visit_entry.grid(column=0, row=1, sticky="w", pady=(0, 2))
    steps.append(s2)

    # Step 3: Confirmation.
    s3 = ttk.Frame(body)
    summary_var = StringVar(value="")
    ttk.Label(s3, text=t("onboarding.summary_title")).pack(anchor="w", pady=(0, 6))
    ttk.Label(s3, textvariable=summary_var, wraplength=680, justify="left").pack(anchor="w")
    ttk.Label(
        s3,
        textvariable=status_var,
        wraplength=680,
        justify="left",
    ).pack(anchor="w", pady=(8, 0))
    steps.append(s3)

    btn_prev = ttk.Button(nav, text=t("onboarding.prev"))
    btn_next = ttk.Button(nav, text=t("onboarding.next"))
    btn_finish = ttk.Button(nav, text=t("onboarding.finish"))
    btn_cancel = ttk.Button(nav, text=t("menu.exit"), style="Danger.TButton")

    btn_prev.pack(side="left", padx=4)
    btn_next.pack(side="left", padx=4)
    btn_finish.pack(side="right", padx=4)
    btn_cancel.pack(side="right", padx=4)

    result = {"done": False}

    def _sync_optional_frames() -> None:
        """Show optional config blocks only when their checkbox is enabled."""
        if has_next_med_var.get():
            medication_frame.grid()
        else:
            medication_frame.grid_remove()
        if has_next_medical_var.get():
            medical_frame.grid()
        else:
            medical_frame.grid_remove()
        if has_next_psych_var.get():
            psych_frame.grid()
        else:
            psych_frame.grid_remove()
        dlg.update_idletasks()

    def _render_step() -> None:
        for idx, step in enumerate(steps):
            if idx == step_idx["value"]:
                step.pack(fill="both", expand=True)
            else:
                step.pack_forget()
        _sync_optional_frames()
        btn_prev.configure(state=("normal" if step_idx["value"] > 0 else "disabled"))
        btn_next.configure(state=("normal" if step_idx["value"] < len(steps) - 1 else "disabled"))
        btn_finish.configure(
            state=("normal" if step_idx["value"] == len(steps) - 1 else "disabled")
        )
        if step_idx["value"] == 1:
            first_name_entry.focus_set()
        if step_idx["value"] == 2:
            summary_var.set(
                _build_summary_text(
                    first_name=first_name_var.get().strip(),
                    has_next_med=has_next_med_var.get(),
                    med_date=med_date_entry.get_date().isoformat(),
                    period=period_var.get(),
                    dose=dose_var.get().strip(),
                    has_next_medical=has_next_medical_var.get(),
                    med_visit=med_visit_entry.get_date().isoformat(),
                    has_next_psych=has_next_psych_var.get(),
                    psych_visit=psych_visit_entry.get_date().isoformat(),
                )
            )

    def _next() -> None:
        if step_idx["value"] < len(steps) - 1:
            step_idx["value"] += 1
            _render_step()

    def _prev() -> None:
        if step_idx["value"] > 0:
            step_idx["value"] -= 1
            _render_step()

    def _finish() -> None:
        name = first_name_var.get().strip()
        if not name:
            messagebox.showwarning(t("error.generic"), t("onboarding.first_name_required"))
            step_idx["value"] = 1
            _render_step()
            return
        try:
            app_service.complete_onboarding(
                first_name=name,
                next_medication_date=(
                    med_date_entry.get_date().isoformat() if has_next_med_var.get() else None
                ),
                medication_every_days=period_var.get(),
                medication_dose=dose_var.get().strip() or None,
                next_medical_visit_date=(
                    med_visit_entry.get_date().isoformat() if has_next_medical_var.get() else None
                ),
                next_psych_visit_date=(
                    psych_visit_entry.get_date().isoformat() if has_next_psych_var.get() else None
                ),
            )
            result["done"] = True
            dlg.destroy()
        except (ValueError, DataStoreError) as exc:
            logger.exception("Onboarding save failed: %s", exc)
            status_var.set(str(exc))
            messagebox.showerror(t("error.generic"), str(exc))

    def _cancel() -> None:
        if messagebox.askyesno(t("onboarding.cancel_title"), t("onboarding.cancel_body")):
            dlg.destroy()

    btn_prev.configure(command=_prev)
    btn_next.configure(command=_next)
    btn_finish.configure(command=_finish)
    btn_cancel.configure(command=_cancel)
    has_next_med_var.trace_add("write", lambda *_args: _sync_optional_frames())
    has_next_medical_var.trace_add("write", lambda *_args: _sync_optional_frames())
    has_next_psych_var.trace_add("write", lambda *_args: _sync_optional_frames())

    dlg.protocol("WM_DELETE_WINDOW", _cancel)
    _render_step()
    dlg.update_idletasks()

    original_med = has_next_med_var.get()
    original_medical = has_next_medical_var.get()
    original_psych = has_next_psych_var.get()

    has_next_med_var.set(True)
    has_next_medical_var.set(True)
    has_next_psych_var.set(True)
    _sync_optional_frames()
    dlg.update_idletasks()

    steps_req_width = max(step.winfo_reqwidth() for step in steps)
    steps_req_height = max(step.winfo_reqheight() for step in steps)

    has_next_med_var.set(original_med)
    has_next_medical_var.set(original_medical)
    has_next_psych_var.set(original_psych)
    _sync_optional_frames()
    dlg.update_idletasks()

    nav_req_width = nav.winfo_reqwidth()
    nav_req_height = nav.winfo_reqheight()
    pad = int(UI_STYLE["padding"])

    target_width = max(
        840,
        steps_req_width + (pad * 8),
        nav_req_width + (pad * 6),
    )
    target_height = max(
        760,
        steps_req_height + nav_req_height + (pad * 10),
    )

    text_wraplength = max(680, target_width - (pad * 10))
    welcome_body_label.configure(wraplength=text_wraplength)
    help_body_label.configure(wraplength=text_wraplength)

    dlg.minsize(target_width, target_height)
    place_window_centered(dlg, width=target_width, height=target_height)
    parent.wait_window(dlg)
    return bool(result["done"])


def _build_summary_text(
    first_name: str,
    has_next_med: bool,
    med_date: str,
    period: int,
    dose: str,
    has_next_medical: bool,
    med_visit: str,
    has_next_psych: bool,
    psych_visit: str,
) -> str:
    """Create onboarding summary string."""
    lines = [
        f"- {t('onboarding.summary_name')}: {first_name or '-'}",
        f"- {t('onboarding.summary_next_med')}: "
        f"{med_date if has_next_med else t('common.not_set')}",
        f"- {t('onboarding.summary_period')}: {period if has_next_med else t('common.not_set')}",
        f"- {t('onboarding.summary_dose')}: {dose or t('common.not_set')}",
        f"- {t('onboarding.summary_next_medical')}: "
        f"{med_visit if has_next_medical else t('common.not_set')}",
        f"- {t('onboarding.summary_next_psych')}: "
        f"{psych_visit if has_next_psych else t('common.not_set')}",
    ]
    return "\n".join(lines)
