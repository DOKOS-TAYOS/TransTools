"""History dialog - calendar view and charts."""

import gc
from pathlib import Path

import matplotlib

matplotlib.use("TkAgg")
from tkinter import Toplevel, filedialog, messagebox, ttk

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import UI_STYLE
from frontend.window_utils import place_window_centered
from i18n import t
from loader import export_csv, load_records
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_history_dialog(parent) -> None:
    """Show history dialog with calendar and charts.

    Args:
        parent: Parent Tk window. X closes and returns to main menu.
    """
    dlg = Toplevel(parent)
    dlg.title(t("history.title"))
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

    try:
        df = load_records()
    except DataStoreError as e:
        messagebox.showerror(t("error.generic"), str(e))
        dlg.destroy()
        return

    if df.empty or len(df) == 0:
        ttk.Label(dlg, text=t("history.no_data")).pack(padx=20, pady=20)
        ttk.Button(dlg, text=t("menu.close"), command=_on_close).pack(pady=10)
        dlg.transient(parent)
        place_window_centered(dlg, width=400, height=150)
        return

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Notebook with tabs: Table, Pitch chart, Export
    notebook = ttk.Notebook(dlg)
    notebook.pack(fill="both", expand=True, padx=UI_STYLE["padding"], pady=UI_STYLE["padding"])

    # Tab 1: Table view
    _col_keys = {
        "date": "history.date",
        "sample": "history.sample",
        "pitch_mean_hz": "history.pitch_mean_hz",
        "pitch_std_hz": "history.col_pitch_std_hz",
        "pitch_min_hz": "history.col_pitch_min_hz",
        "pitch_max_hz": "history.col_pitch_max_hz",
        "energy_rms": "history.col_energy_rms",
        "mood_happy": "history.mood_happy",
        "mood_sad": "history.mood_sad",
        "mood_angry": "history.mood_angry",
    }
    table_frame = ttk.Frame(notebook)
    cols = list(df.columns)
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
    for c in cols:
        tree.heading(c, text=t(_col_keys.get(c, c)))
        tree.column(c, width=100)
    scroll = ttk.Scrollbar(table_frame)
    tree.configure(yscrollcommand=scroll.set)
    scroll.configure(command=tree.yview)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    for _, row in df.iterrows():
        tree.insert("", "end", values=[str(row[c])[:50] for c in cols])
    notebook.add(table_frame, text=t("history.tab_table"))

    # Tab 2: Pitch chart
    chart_frame = ttk.Frame(notebook)
    fig = Figure(figsize=(8, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(df["date"], df["pitch_mean_hz"], "o-", markersize=4)
    ax.set_xlabel(t("history.date"))
    ax.set_ylabel(t("history.pitch_mean_hz"))
    ax.set_title(t("history.chart_title"))
    fig.autofmt_xdate()
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    notebook.add(chart_frame, text=t("history.tab_chart"))

    # Tab 3: Export
    export_frame = ttk.Frame(notebook)
    ttk.Label(export_frame, text=t("history.export_label")).pack(pady=8)

    def do_export() -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if path:
            try:
                export_csv(Path(path))
                messagebox.showinfo(t("history.export_title"), t("history.exported_to", path=path))
            except DataStoreError as e:
                messagebox.showerror(t("error.generic"), str(e))

    ttk.Button(export_frame, text=t("history.export_csv"), command=do_export).pack(pady=8)
    notebook.add(export_frame, text=t("history.tab_export"))

    ttk.Button(dlg, text=t("menu.close"), command=_on_close).pack(pady=8)
    dlg.transient(parent)
    dlg.minsize(600, 450)
    place_window_centered(dlg, width=800, height=550)
