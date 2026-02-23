"""Configuration dialog for TransTools."""

from pathlib import Path
from tkinter import BooleanVar, IntVar, StringVar, Toplevel, messagebox, ttk

from config import UI_STYLE, get_current_env_values, write_env_file
from config.env import get_env_from_schema
from config.theme import configure_ttk_styles
from i18n import t


def _add_row(frame: ttk.Frame, row: int, label: str, widget: ttk.Widget) -> None:
    """Add a labeled row to the config frame.

    Args:
        frame: Parent ttk.Frame.
        row: Grid row index.
        label: Label text.
        widget: Widget to place in column 1.
    """
    ttk.Label(frame, text=label).grid(column=0, row=row, sticky="w", pady=2)
    widget.grid(column=1, row=row, padx=4, pady=2, sticky="w")


def show_config_dialog(parent) -> bool:
    """Show config dialog.

    Args:
        parent: Parent Tk window.

    Returns:
        True if user saved and app should restart, False otherwise.
    """
    dlg = Toplevel(parent)
    dlg.title(t("menu.config"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])
    configure_ttk_styles(parent)

    result = {"saved": False}
    notebook = ttk.Notebook(dlg)

    # --- General tab ---
    gen_frame = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    row = 0

    lang_var = StringVar(value=get_env_from_schema("LANGUAGE"))
    _add_row(
        gen_frame,
        row,
        "LANGUAGE:",
        ttk.Combobox(
            gen_frame,
            textvariable=lang_var,
            values=("es", "en"),
            width=10,
            state="readonly",
        ),
    )
    row += 1

    out_var = StringVar(value=get_env_from_schema("FILE_OUTPUT_DIR"))
    out_entry = ttk.Entry(gen_frame, textvariable=out_var, width=25)
    _add_row(gen_frame, row, "FILE_OUTPUT_DIR:", out_entry)
    row += 1

    save_audio_var = BooleanVar(value=get_env_from_schema("SAVE_AUDIO"))
    _add_row(
        gen_frame,
        row,
        "SAVE_AUDIO:",
        ttk.Checkbutton(gen_frame, variable=save_audio_var, text=""),
    )
    row += 1

    dur_var = IntVar(value=get_env_from_schema("RECORD_DURATION_SEC"))
    _add_row(
        gen_frame,
        row,
        "RECORD_DURATION_SEC:",
        ttk.Spinbox(gen_frame, from_=5, to=60, textvariable=dur_var, width=8),
    )
    row += 1

    log_var = StringVar(value=get_env_from_schema("LOG_LEVEL"))
    _add_row(
        gen_frame,
        row,
        "LOG_LEVEL:",
        ttk.Combobox(
            gen_frame,
            textvariable=log_var,
            values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            width=10,
            state="readonly",
        ),
    )
    row += 1

    log_console_var = BooleanVar(value=get_env_from_schema("LOG_CONSOLE"))
    _add_row(
        gen_frame,
        row,
        "LOG_CONSOLE:",
        ttk.Checkbutton(gen_frame, variable=log_console_var, text=""),
    )
    row += 1

    notebook.add(gen_frame, text=t("config.tab_general"))

    # --- UI tab ---
    ui_frame = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    row = 0

    ui_bg_var = StringVar(value=get_env_from_schema("UI_BACKGROUND"))
    _add_row(ui_frame, row, "UI_BACKGROUND:", ttk.Entry(ui_frame, textvariable=ui_bg_var, width=15))
    row += 1

    ui_fg_var = StringVar(value=get_env_from_schema("UI_FOREGROUND"))
    _add_row(ui_frame, row, "UI_FOREGROUND:", ttk.Entry(ui_frame, textvariable=ui_fg_var, width=15))
    row += 1

    ui_btn_bg_var = StringVar(value=get_env_from_schema("UI_BUTTON_BG"))
    _add_row(
        ui_frame, row, "UI_BUTTON_BG:", ttk.Entry(ui_frame, textvariable=ui_btn_bg_var, width=15)
    )
    row += 1

    ui_btn_fg_var = StringVar(value=get_env_from_schema("UI_BUTTON_FG"))
    _add_row(
        ui_frame, row, "UI_BUTTON_FG:", ttk.Entry(ui_frame, textvariable=ui_btn_fg_var, width=15)
    )
    row += 1

    ui_btn_cancel_var = StringVar(value=get_env_from_schema("UI_BUTTON_FG_CANCEL"))
    _add_row(
        ui_frame,
        row,
        "UI_BUTTON_FG_CANCEL:",
        ttk.Entry(ui_frame, textvariable=ui_btn_cancel_var, width=15),
    )
    row += 1

    ui_btn_accent_var = StringVar(value=get_env_from_schema("UI_BUTTON_FG_ACCENT2"))
    _add_row(
        ui_frame,
        row,
        "UI_BUTTON_FG_ACCENT2:",
        ttk.Entry(ui_frame, textvariable=ui_btn_accent_var, width=15),
    )
    row += 1

    ui_font_family_var = StringVar(value=get_env_from_schema("UI_FONT_FAMILY"))
    _add_row(
        ui_frame,
        row,
        "UI_FONT_FAMILY:",
        ttk.Entry(ui_frame, textvariable=ui_font_family_var, width=20),
    )
    row += 1

    ui_font_size_var = IntVar(value=get_env_from_schema("UI_FONT_SIZE"))
    _add_row(
        ui_frame,
        row,
        "UI_FONT_SIZE:",
        ttk.Spinbox(ui_frame, from_=8, to=72, textvariable=ui_font_size_var, width=6),
    )
    row += 1

    ui_padding_var = IntVar(value=get_env_from_schema("UI_PADDING"))
    _add_row(
        ui_frame,
        row,
        "UI_PADDING:",
        ttk.Spinbox(ui_frame, from_=2, to=30, textvariable=ui_padding_var, width=6),
    )
    row += 1

    ui_btn_width_var = IntVar(value=get_env_from_schema("UI_BUTTON_WIDTH"))
    _add_row(
        ui_frame,
        row,
        "UI_BUTTON_WIDTH:",
        ttk.Spinbox(ui_frame, from_=5, to=50, textvariable=ui_btn_width_var, width=6),
    )
    row += 1

    ui_btn_width_wide_var = IntVar(value=get_env_from_schema("UI_BUTTON_WIDTH_WIDE"))
    _add_row(
        ui_frame,
        row,
        "UI_BUTTON_WIDTH_WIDE:",
        ttk.Spinbox(ui_frame, from_=10, to=50, textvariable=ui_btn_width_wide_var, width=6),
    )
    row += 1

    notebook.add(ui_frame, text=t("config.tab_ui"))

    def save() -> None:
        values = get_current_env_values()
        values["LANGUAGE"] = lang_var.get().strip() or "es"
        values["FILE_OUTPUT_DIR"] = out_var.get().strip() or "output"
        values["SAVE_AUDIO"] = "true" if save_audio_var.get() else "false"
        values["LOG_CONSOLE"] = "true" if log_console_var.get() else "false"
        try:
            values["RECORD_DURATION_SEC"] = str(max(5, min(60, dur_var.get())))
        except Exception:
            values["RECORD_DURATION_SEC"] = "10"
        values["LOG_LEVEL"] = log_var.get().strip().upper() or "INFO"

        values["UI_BACKGROUND"] = ui_bg_var.get().strip() or "#181818"
        values["UI_FOREGROUND"] = ui_fg_var.get().strip() or "#CCCCCC"
        values["UI_BUTTON_BG"] = ui_btn_bg_var.get().strip() or "#1F1F1F"
        values["UI_BUTTON_FG"] = ui_btn_fg_var.get().strip() or "lime green"
        values["UI_BUTTON_FG_CANCEL"] = ui_btn_cancel_var.get().strip() or "red2"
        values["UI_BUTTON_FG_ACCENT2"] = ui_btn_accent_var.get().strip() or "yellow"
        values["UI_FONT_FAMILY"] = ui_font_family_var.get().strip() or "Bahnschrift"
        try:
            values["UI_FONT_SIZE"] = str(max(8, min(72, ui_font_size_var.get())))
        except Exception:
            values["UI_FONT_SIZE"] = "18"
        try:
            values["UI_PADDING"] = str(max(2, min(30, ui_padding_var.get())))
        except Exception:
            values["UI_PADDING"] = "8"
        try:
            values["UI_BUTTON_WIDTH"] = str(max(5, min(50, ui_btn_width_var.get())))
        except Exception:
            values["UI_BUTTON_WIDTH"] = "12"
        try:
            values["UI_BUTTON_WIDTH_WIDE"] = str(max(10, min(50, ui_btn_width_wide_var.get())))
        except Exception:
            values["UI_BUTTON_WIDTH_WIDE"] = "20"

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

    notebook.pack(fill="both", expand=True, padx=UI_STYLE["padding"], pady=UI_STYLE["padding"])
    btn_frame.pack(pady=UI_STYLE["padding"])

    def _on_close() -> None:
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    dlg.grab_set()
    parent.wait_window(dlg)
    return result["saved"]
