"""Configuration dialog for TransTools."""

from pathlib import Path
from tkinter import BooleanVar, Canvas, IntVar, StringVar, TclError, Toplevel, messagebox, ttk
from typing import Any

from config import UI_STYLE, get_current_env_values, write_env_file
from config.env import get_env_from_schema
from config.theme import configure_ttk_styles, refresh_theme
from frontend.window_utils import place_window_centered
from i18n import t


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


def _bounded_int_value(var: IntVar, minimum: int, maximum: int, default: int) -> str:
    """Read an IntVar safely and clamp it into the supported bounds."""
    try:
        return str(max(minimum, min(maximum, var.get())))
    except (TclError, ValueError):
        return str(default)


def show_config_dialog(parent, app_service: Any | None = None) -> bool:
    """Show config dialog.

    Args:
        parent: Parent Tk window.
        app_service: Optional AppService instance to persist profile/health data.

    Returns:
        True if user saved and app should restart, False otherwise.
    """
    dlg = Toplevel(parent)
    dlg.title(t("menu.config"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])
    refresh_theme()
    configure_ttk_styles(parent)
    _font = (UI_STYLE["font_family"], UI_STYLE["font_size"])

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
        ttk.Combobox(
            gen_frame,
            textvariable=lang_var,
            values=("es", "en"),
            width=10,
            state="readonly",
            font=_font,
        ),
    )

    out_var = StringVar(value=get_env_from_schema("FILE_OUTPUT_DIR"))
    out_entry = ttk.Entry(gen_frame, textvariable=out_var, width=30, font=_font)
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
        ttk.Spinbox(
            gen_frame,
            from_=5,
            to=60,
            textvariable=dur_var,
            width=8,
            font=_font,
        ),
    )

    log_var = StringVar(value=get_env_from_schema("LOG_LEVEL"))
    row = _add_param_row(
        gen_frame,
        row,
        "config.general.log_level",
        "config.general.log_level_desc",
        ttk.Combobox(
            gen_frame,
            textvariable=log_var,
            values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            width=10,
            state="readonly",
            font=_font,
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

    notebook.add(gen_frame, text=t("config.tab_general"))

    # --- UI tab ---
    ui_frame = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    row = 0

    ui_bg_var = StringVar(value=get_env_from_schema("UI_BACKGROUND"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.bg",
        "config.ui.bg_desc",
        ttk.Entry(ui_frame, textvariable=ui_bg_var, width=18, font=_font),
    )

    ui_fg_var = StringVar(value=get_env_from_schema("UI_FOREGROUND"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.fg",
        "config.ui.fg_desc",
        ttk.Entry(ui_frame, textvariable=ui_fg_var, width=18, font=_font),
    )

    ui_btn_bg_var = StringVar(value=get_env_from_schema("UI_BUTTON_BG"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.btn_bg",
        "config.ui.btn_bg_desc",
        ttk.Entry(ui_frame, textvariable=ui_btn_bg_var, width=18, font=_font),
    )

    ui_btn_fg_var = StringVar(value=get_env_from_schema("UI_BUTTON_FG"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.btn_fg",
        "config.ui.btn_fg_desc",
        ttk.Entry(ui_frame, textvariable=ui_btn_fg_var, width=18, font=_font),
    )

    ui_btn_cancel_var = StringVar(value=get_env_from_schema("UI_BUTTON_FG_CANCEL"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.btn_fg_cancel",
        "config.ui.btn_fg_cancel_desc",
        ttk.Entry(ui_frame, textvariable=ui_btn_cancel_var, width=18, font=_font),
    )

    ui_btn_accent_var = StringVar(value=get_env_from_schema("UI_BUTTON_FG_ACCENT2"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.btn_fg_accent",
        "config.ui.btn_fg_accent_desc",
        ttk.Entry(ui_frame, textvariable=ui_btn_accent_var, width=18, font=_font),
    )

    ui_font_family_var = StringVar(value=get_env_from_schema("UI_FONT_FAMILY"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.font_family",
        "config.ui.font_family_desc",
        ttk.Entry(ui_frame, textvariable=ui_font_family_var, width=22, font=_font),
    )

    ui_font_size_var = IntVar(value=get_env_from_schema("UI_FONT_SIZE"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.font_size",
        "config.ui.font_size_desc",
        ttk.Spinbox(
            ui_frame,
            from_=8,
            to=72,
            textvariable=ui_font_size_var,
            width=6,
            font=_font,
        ),
    )

    ui_padding_var = IntVar(value=get_env_from_schema("UI_PADDING"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.padding",
        "config.ui.padding_desc",
        ttk.Spinbox(
            ui_frame,
            from_=2,
            to=30,
            textvariable=ui_padding_var,
            width=6,
            font=_font,
        ),
    )

    ui_btn_width_var = IntVar(value=get_env_from_schema("UI_BUTTON_WIDTH"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.btn_width",
        "config.ui.btn_width_desc",
        ttk.Spinbox(
            ui_frame,
            from_=5,
            to=50,
            textvariable=ui_btn_width_var,
            width=6,
            font=_font,
        ),
    )

    ui_btn_width_wide_var = IntVar(value=get_env_from_schema("UI_BUTTON_WIDTH_WIDE"))
    row = _add_param_row(
        ui_frame,
        row,
        "config.ui.btn_width_wide",
        "config.ui.btn_width_wide_desc",
        ttk.Spinbox(
            ui_frame,
            from_=10,
            to=50,
            textvariable=ui_btn_width_wide_var,
            width=6,
            font=_font,
        ),
    )

    notebook.add(ui_frame, text=t("config.tab_ui"))

    def save() -> None:
        values = get_current_env_values()
        values["LANGUAGE"] = lang_var.get().strip() or "es"
        values["FILE_OUTPUT_DIR"] = out_var.get().strip() or "output"
        values["SAVE_AUDIO"] = "true" if save_audio_var.get() else "false"
        values["LOG_CONSOLE"] = "true" if log_console_var.get() else "false"
        values["RECORD_DURATION_SEC"] = _bounded_int_value(
            dur_var,
            minimum=5,
            maximum=60,
            default=10,
        )
        values["LOG_LEVEL"] = log_var.get().strip().upper() or "INFO"

        values["UI_BACKGROUND"] = ui_bg_var.get().strip() or "#181818"
        values["UI_FOREGROUND"] = ui_fg_var.get().strip() or "#CCCCCC"
        values["UI_BUTTON_BG"] = ui_btn_bg_var.get().strip() or "#1F1F1F"
        values["UI_BUTTON_FG"] = ui_btn_fg_var.get().strip() or "lime green"
        values["UI_BUTTON_FG_CANCEL"] = ui_btn_cancel_var.get().strip() or "red2"
        values["UI_BUTTON_FG_ACCENT2"] = ui_btn_accent_var.get().strip() or "yellow"
        values["UI_FONT_FAMILY"] = ui_font_family_var.get().strip() or "Bahnschrift"
        values["UI_FONT_SIZE"] = _bounded_int_value(
            ui_font_size_var,
            minimum=8,
            maximum=72,
            default=18,
        )
        values["UI_PADDING"] = _bounded_int_value(ui_padding_var, minimum=2, maximum=30, default=8)
        values["UI_BUTTON_WIDTH"] = _bounded_int_value(
            ui_btn_width_var,
            minimum=5,
            maximum=50,
            default=12,
        )
        values["UI_BUTTON_WIDTH_WIDE"] = _bounded_int_value(
            ui_btn_width_wide_var,
            minimum=10,
            maximum=50,
            default=20,
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
