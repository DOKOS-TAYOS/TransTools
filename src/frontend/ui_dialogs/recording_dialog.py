"""Recording dialog - record, analyze and register voice."""

from __future__ import annotations

from datetime import date, datetime
from threading import Thread
from tkinter import BooleanVar, IntVar, StringVar, Toplevel, messagebox, ttk
from typing import Any

from audio import analyze_audio, record_audio
from config import UI_STYLE, get_audio_dir
from config.env import get_env_from_schema
from core.context import get_app_service
from core.types import VoiceAnalysisResult
from frontend.date_widgets import create_date_entry
from frontend.input_widgets import create_spinbox
from frontend.window_utils import place_window_centered
from i18n import t
from utils import AnalysisError, DataStoreError, RecordingError, get_logger

logger = get_logger(__name__)


def _save_audio(audio_data, sample_rate: int, enabled: bool) -> str:
    """Save audio to output/audio/ when requested.

    Args:
        audio_data: Float32 audio array.
        sample_rate: Sample rate in Hz.
        enabled: Whether this recording should be persisted.

    Returns:
        Path to saved file, or empty string if skipped.
    """
    if not enabled:
        return ""
    try:
        import soundfile as sf
    except ImportError:
        logger.warning("soundfile not installed, skipping audio save")
        return ""
    out_dir = get_audio_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"recording_{ts}.wav"
    sf.write(str(path), audio_data, sample_rate)
    return str(path.resolve())


def _build_self_mood_payload(happy: int, sad: int, angry: int) -> dict[str, float]:
    """Convert 0-5 mood scales to normalized 0..1 values.

    Args:
        happy: Self-perceived happiness in 0..5.
        sad: Self-perceived sadness in 0..5.
        angry: Self-perceived anger in 0..5.

    Returns:
        Mood payload with keys happy/sad/angry.
    """
    return {
        "happy": max(0.0, min(1.0, happy / 5.0)),
        "sad": max(0.0, min(1.0, sad / 5.0)),
        "angry": max(0.0, min(1.0, angry / 5.0)),
    }


def show_recording_dialog(parent, app_service=None) -> None:
    """Show recording dialog. Record -> Analyze -> Save.

    Args:
        parent: Parent Tk window. X closes and returns to main menu.
    """
    dlg = Toplevel(parent)
    dlg.title(t("menu.voice_record"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    app_service = app_service or get_app_service()
    status_var = StringVar(value=t("recording.ready"))
    result_var = StringVar(value="")
    selected_date_label = StringVar(value=t("recording.for_date"))
    save_audio_default = bool(get_env_from_schema("SAVE_AUDIO"))
    save_audio_var = BooleanVar(value=save_audio_default)

    mood_happy_var = IntVar(value=3)
    mood_sad_var = IntVar(value=2)
    mood_angry_var = IntVar(value=1)

    frame = ttk.Frame(dlg, padding=UI_STYLE["padding"])
    ttk.Label(frame, textvariable=status_var, wraplength=420).grid(
        column=0, row=0, columnspan=2, pady=4
    )
    ttk.Label(frame, textvariable=result_var, wraplength=420).grid(
        column=0, row=1, columnspan=2, pady=4
    )

    ttk.Label(frame, text=selected_date_label.get()).grid(
        column=0,
        row=2,
        columnspan=2,
        sticky="w",
        pady=4,
    )
    date_entry = create_date_entry(frame, width=14)
    date_entry.set_date(date.today())
    date_entry.grid(column=0, row=3, columnspan=2, sticky="w", pady=(0, 4))

    ttk.Checkbutton(
        frame,
        text=t("recording.save_audio_now"),
        variable=save_audio_var,
    ).grid(column=0, row=4, columnspan=2, sticky="w", pady=4)

    ttk.Label(frame, text=t("recording.self_mood_title")).grid(
        column=0,
        row=5,
        columnspan=2,
        sticky="w",
    )
    ttk.Label(frame, text=t("recording.self_happy")).grid(column=0, row=6, sticky="w", pady=2)
    create_spinbox(frame, from_=0, to=5, width=5, textvariable=mood_happy_var).grid(
        column=1,
        row=6,
        sticky="w",
    )
    ttk.Label(frame, text=t("recording.self_sad")).grid(column=0, row=7, sticky="w", pady=2)
    create_spinbox(frame, from_=0, to=5, width=5, textvariable=mood_sad_var).grid(
        column=1,
        row=7,
        sticky="w",
    )
    ttk.Label(frame, text=t("recording.self_angry")).grid(column=0, row=8, sticky="w", pady=2)
    create_spinbox(frame, from_=0, to=5, width=5, textvariable=mood_angry_var).grid(
        column=1,
        row=8,
        sticky="w",
    )

    is_busy = {"value": False}

    def _set_busy(value: bool) -> None:
        is_busy["value"] = value
        btn_state = "disabled" if value else "normal"
        record_btn.configure(state=btn_state)
        close_btn.configure(state=btn_state)

    def _finish_record(kind: str, payload: Any, target_date: date) -> None:
        if not dlg.winfo_exists():
            return
        _set_busy(False)

        if kind == "ok":
            now = datetime.now()
            result_var.set(
                t(
                    "recording.result",
                    datetime=now.strftime("%Y-%m-%d %H:%M"),
                    date=target_date.isoformat(),
                )
            )
            status_var.set(t("recording.saved_ok"))
            return

        if kind == "recording":
            messagebox.showerror(t("recording.error_recording"), str(payload))
            status_var.set(t("recording.error_recording_msg"))
            return
        if kind == "analysis":
            messagebox.showerror(t("recording.error_analysis"), str(payload))
            status_var.set(t("recording.error_analysis_msg"))
            return
        if kind == "save":
            messagebox.showerror(t("recording.error_save"), str(payload))
            status_var.set(t("recording.error_save_msg"))
            return

        logger.exception("Unexpected error in record worker: %s", payload)
        messagebox.showerror(t("error.generic"), str(payload))
        status_var.set(t("recording.error_unexpected"))

    def _run_record_worker(
        target_date: date,
        mood_self: dict[str, float],
        should_save_audio: bool,
    ) -> None:
        try:
            audio, sr = record_audio()
            if dlg.winfo_exists():
                dlg.after(0, lambda: status_var.set(t("recording.analyzing")))
            result: VoiceAnalysisResult = analyze_audio(audio, sr)
            audio_path = _save_audio(audio, sr, enabled=should_save_audio)
            app_service.add_voice_record(
                target_date=target_date,
                analysis=result,
                mood_self=mood_self,
                audio_saved_path=audio_path or None,
            )
            if dlg.winfo_exists():
                dlg.after(0, lambda: _finish_record("ok", None, target_date))
        except RecordingError as exc:
            if dlg.winfo_exists():
                dlg.after(0, lambda err=exc: _finish_record("recording", err, target_date))
        except AnalysisError as exc:
            if dlg.winfo_exists():
                dlg.after(0, lambda err=exc: _finish_record("analysis", err, target_date))
        except DataStoreError as exc:
            if dlg.winfo_exists():
                dlg.after(0, lambda err=exc: _finish_record("save", err, target_date))
        except Exception as exc:
            if dlg.winfo_exists():
                dlg.after(0, lambda err=exc: _finish_record("unexpected", err, target_date))

    def do_record() -> None:
        if is_busy["value"]:
            return
        try:
            target_date = date_entry.get_date()
        except ValueError:
            messagebox.showerror(t("recording.error_date"), t("recording.error_date_msg"))
            status_var.set(t("recording.error_date_msg"))
            return

        status_var.set(t("recording.recording"))
        result_var.set("")
        _set_busy(True)

        mood_self = _build_self_mood_payload(
            mood_happy_var.get(),
            mood_sad_var.get(),
            mood_angry_var.get(),
        )
        worker = Thread(
            target=_run_record_worker,
            args=(target_date, mood_self, bool(save_audio_var.get())),
            daemon=True,
        )
        worker.start()

    record_btn = ttk.Button(
        frame,
        text=t("recording.record"),
        command=do_record,
        width=UI_STYLE["button_width"],
    )
    record_btn.grid(column=0, row=9, padx=4, pady=8)
    close_btn = ttk.Button(
        frame, text=t("menu.close"), command=dlg.destroy, width=UI_STYLE["button_width"]
    )
    close_btn.grid(column=1, row=9, padx=4, pady=8)

    frame.pack(fill="both")

    def _on_close() -> None:
        if is_busy["value"]:
            return
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    dlg.update_idletasks()
    pad = int(UI_STYLE["padding"])
    target_width = max(520, frame.winfo_reqwidth() + (pad * 4))
    target_height = max(360, frame.winfo_reqheight() + (pad * 2))
    dlg.minsize(target_width, target_height)
    place_window_centered(dlg, width=target_width, height=target_height)
