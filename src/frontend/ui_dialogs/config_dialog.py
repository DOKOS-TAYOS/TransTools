"""Configuration dialog for TransTools."""

from __future__ import annotations

from pathlib import Path
from tkinter import BooleanVar, Canvas, IntVar, StringVar, TclError, Tk, Toplevel, messagebox, ttk
from typing import Any, cast

from config import UI_STYLE, get_current_env_values, write_env_file
from config.env import get_env_from_schema
from config.theme import prepare_ttk_window
from frontend.input_widgets import create_combobox, create_entry, create_spinbox
from frontend.window_utils import place_window_centered
from i18n import t

LEGACY_VISUAL_ENV_KEYS: tuple[str, ...] = (
    "UI_BACKGROUND",
    "UI_FOREGROUND",
    "UI_BUTTON_BG",
    "UI_BUTTON_FG",
    "UI_BUTTON_FG_CANCEL",
    "UI_BUTTON_FG_ACCENT2",
    "UI_FONT_FAMILY",
    "UI_PADDING",
    "UI_BUTTON_WIDTH",
    "UI_BUTTON_WIDTH_WIDE",
)


def _add_param_row(
    frame: ttk.Frame,
    row: int,
    title_key: str,
    desc_key: str,
    widget: ttk.Widget,
) -> int:
    """Add a config parameter row with title and description.

    Args:
        frame: Parent ttk.Frame.
        row: Grid row index.
        title_key: i18n key for the parameter title.
        desc_key: i18n key for the parameter description.
        widget: Widget to place in column 1.

    Returns:
        Next row index (row + 2).
    """
    pad = UI_STYLE["padding"]
    ttk.Label(frame, text=t(title_key)).grid(column=0, row=row, sticky="w", pady=(pad, 0))
    widget.grid(column=1, row=row, padx=pad, pady=(pad, 0), sticky="w")
    desc = ttk.Label(frame, text=t(desc_key), wraplength=640, style="Small.TLabel")
    desc.grid(column=0, row=row + 1, columnspan=2, sticky="w", padx=(0, pad), pady=(2, pad))
    return row + 2


def _bounded_int(raw_value: object, minimum: int, maximum: int, default: int) -> str:
    """Clamp a Tk-backed or plain integer-like value into the supported bounds."""
    try:
        if hasattr(raw_value, "get"):
            raw_value = cast(Any, raw_value).get()
        return str(max(minimum, min(maximum, int(cast(Any, raw_value)))))
    except (TclError, TypeError, ValueError, OverflowError):
        return str(default)


def get_theme_mode_choices() -> tuple[tuple[str, str], ...]:
    """Return the supported theme-mode values and their translation keys."""
    return (
        ("dark", "config.ui.theme_mode_dark"),
        ("light", "config.ui.theme_mode_light"),
    )


def _normalize_theme_mode(raw_value: str) -> str:
    """Normalize theme mode to one of the supported persistent values."""
    theme_mode = str(raw_value).strip().lower()
    return theme_mode if theme_mode in {"dark", "light"} else "dark"


def build_config_values_to_save(
    current_values: dict[str, str],
    *,
    language: str,
    output_dir: str,
    save_audio: bool,
    record_duration_sec: object,
    log_level: str,
    log_console: bool,
    ui_theme_mode: str,
    ui_font_size: object,
) -> dict[str, str]:
    """Build the persisted settings payload for the simplified config dialog."""
    values = dict(current_values)
    values["LANGUAGE"] = language.strip() or "es"
    values["FILE_OUTPUT_DIR"] = output_dir.strip() or "output"
    values["SAVE_AUDIO"] = "true" if save_audio else "false"
    values["LOG_CONSOLE"] = "true" if log_console else "false"
    values["RECORD_DURATION_SEC"] = _bounded_int(
        record_duration_sec,
        minimum=5,
        maximum=60,
        default=10,
    )
    values["LOG_LEVEL"] = log_level.strip().upper() or "INFO"
    values["UI_THEME_MODE"] = _normalize_theme_mode(ui_theme_mode)
    values["UI_FONT_SIZE"] = _bounded_int(ui_font_size, minimum=8, maximum=72, default=16)

    for legacy_key in LEGACY_VISUAL_ENV_KEYS:
        values.pop(legacy_key, None)

    return values


def show_config_dialog(parent: Tk | Toplevel) -> bool:
    """Show config dialog.

    Args:
        parent: Parent Tk window.

    Returns:
        True if user saved and app should restart, False otherwise.
    """
    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    dlg.title(t("menu.config"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    result = {"saved": False}
    pad = UI_STYLE["padding"]

    scroll_container = ttk.Frame(dlg)
    canvas = Canvas(
        scroll_container,
        highlightthickness=0,
        background=UI_STYLE["bg"],
    )
    scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
    inner_frame = ttk.Frame(canvas)
    inner_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas_window = canvas.create_window(0, 0, window=inner_frame, anchor="nw")

    def _on_canvas_configure(event) -> None:
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event) -> None:
        if getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            canvas.yview_scroll(1, "units")
        elif getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            canvas.yview_scroll(-1, "units")

    dlg.bind("<MouseWheel>", _on_mousewheel)
    dlg.bind("<Button-4>", _on_mousewheel)
    dlg.bind("<Button-5>", _on_mousewheel)

    notebook = ttk.Notebook(inner_frame)

    # --- General settings tab ---
    gen_frame = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    row = 0

    lang_var = StringVar(value=get_env_from_schema("LANGUAGE"))
    row = _add_param_row(
        gen_frame,
        row,
        "config.general.language",
        "config.general.language_desc",
        create_combobox(
            gen_frame,
            textvariable=lang_var,
            values=("es", "en"),
            width=10,
            state="readonly",
        ),
    )

    out_var = StringVar(value=get_env_from_schema("FILE_OUTPUT_DIR"))
    out_entry = create_entry(gen_frame, textvariable=out_var, width=30)
    row = _add_param_row(
        gen_frame, row, "config.general.output_dir", "config.general.output_dir_desc", out_entry
    )

    save_audio_var = BooleanVar(value=get_env_from_schema("SAVE_AUDIO"))
    row = _add_param_row(
        gen_frame,
        row,
        "config.general.save_audio",
        "config.general.save_audio_desc",
        ttk.Checkbutton(gen_frame, variable=save_audio_var, text=""),
    )

    dur_var = IntVar(value=get_env_from_schema("RECORD_DURATION_SEC"))
    row = _add_param_row(
        gen_frame,
        row,
        "config.general.record_duration",
        "config.general.record_duration_desc",
        create_spinbox(
            gen_frame,
            from_=5,
            to=60,
            textvariable=dur_var,
            width=8,
        ),
    )

    log_var = StringVar(value=get_env_from_schema("LOG_LEVEL"))
    row = _add_param_row(
        gen_frame,
        row,
        "config.general.log_level",
        "config.general.log_level_desc",
        create_combobox(
            gen_frame,
            textvariable=log_var,
            values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            width=10,
            state="readonly",
        ),
    )

    log_console_var = BooleanVar(value=get_env_from_schema("LOG_CONSOLE"))
    row = _add_param_row(
        gen_frame,
        row,
        "config.general.log_console",
        "config.general.log_console_desc",
        ttk.Checkbutton(gen_frame, variable=log_console_var, text=""),
    )

    theme_mode_choices = get_theme_mode_choices()
    theme_mode_labels = {value: t(label_key) for value, label_key in theme_mode_choices}
    theme_mode_by_label = {label: value for value, label in theme_mode_labels.items()}
    ui_theme_mode_var = StringVar(
        value=theme_mode_labels[_normalize_theme_mode(str(get_env_from_schema("UI_THEME_MODE")))]
    )
    row = _add_param_row(
        gen_frame,
        row,
        "config.ui.theme_mode",
        "config.ui.theme_mode_desc",
        create_combobox(
            gen_frame,
            textvariable=ui_theme_mode_var,
            values=tuple(theme_mode_by_label),
            width=18,
            state="readonly",
        ),
    )

    ui_font_size_var = IntVar(value=get_env_from_schema("UI_FONT_SIZE"))
    row = _add_param_row(
        gen_frame,
        row,
        "config.ui.font_size",
        "config.ui.font_size_desc",
        create_spinbox(
            gen_frame,
            from_=8,
            to=72,
            textvariable=ui_font_size_var,
            width=6,
        ),
    )

    notebook.add(gen_frame, text=t("config.tab_general"))

    def save() -> None:
        values = build_config_values_to_save(
            get_current_env_values(),
            language=lang_var.get(),
            output_dir=out_var.get(),
            save_audio=save_audio_var.get(),
            record_duration_sec=dur_var,
            log_level=log_var.get(),
            log_console=log_console_var.get(),
            ui_theme_mode=theme_mode_by_label.get(
                ui_theme_mode_var.get().strip(),
                str(get_env_from_schema("UI_THEME_MODE")),
            ),
            ui_font_size=ui_font_size_var,
        )

        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        write_env_file(env_path, values)

        result["saved"] = True
        messagebox.showinfo(t("menu.config"), t("config.saved_message"))
        dlg.destroy()

    def cancel() -> None:
        dlg.destroy()

    btn_frame = ttk.Frame(dlg)
    ttk.Button(btn_frame, text=t("config.save"), command=save).pack(side="left", padx=4)
    ttk.Button(btn_frame, text=t("config.cancel"), command=cancel).pack(side="left", padx=4)

    canvas.configure(yscrollcommand=scrollbar.set)
    notebook.pack(fill="both", expand=True, padx=pad, pady=pad)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_container.pack(fill="both", expand=True, padx=pad, pady=pad)
    btn_frame.pack(pady=pad)

    dlg.update_idletasks()
    req_w = inner_frame.winfo_reqwidth() + 30
    req_h = inner_frame.winfo_reqheight() + 100
    max_h = int(dlg.winfo_screenheight() * 0.7)
    w = max(400, req_w)
    h = min(max(300, req_h), max_h)
    place_window_centered(dlg, width=w, height=h)

    def _on_close() -> None:
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    dlg.grab_set()
    parent.wait_window(dlg)
    return result["saved"]
