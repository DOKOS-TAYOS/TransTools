"""Information dialog for TransTools."""

from tkinter import Toplevel, ttk

from config import UI_STYLE
from frontend.window_utils import place_window_centered
from i18n import t


def show_info_dialog(parent) -> None:
    """Show information dialog.

    Args:
        parent: Parent Tk window. Closing with X returns to main menu.
    """
    dlg = Toplevel(parent)
    dlg.title(t("menu.info"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    text = ttk.Label(
        dlg,
        text=t("info.content"),
        wraplength=400,
    )
    close_btn = ttk.Button(dlg, text=t("menu.close"), command=dlg.destroy)

    pad = UI_STYLE["padding"]
    text.pack(padx=pad, pady=pad)
    close_btn.pack(pady=pad)

    def _on_close() -> None:
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    place_window_centered(dlg, preserve_size=True)
