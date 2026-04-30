"""Recording dialog - record, analyze and register voice."""

from __future__ import annotations

import time
from datetime import date, datetime
from threading import Thread
from tkinter import BooleanVar, IntVar, StringVar, Toplevel, messagebox, ttk
from typing import Any, Protocol

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

RECORDING_SYMBOL = "\u25cf"  # ● (black circle, typical recording indicator)

logger = get_logger(__name__)


class SupportsGetDate(Protocol):
    """Protocol for widgets exposing a selected date."""

    def get_date(self) -> date: ...


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


def _collect_record_form_state(
    target_date_entry: SupportsGetDate,
    mood_happy: int,
    mood_sad: int,
    mood_angry: int,
    should_save_audio: bool,
) -> tuple[date, dict[str, float], bool]:
    """Collect the recording form state from the visible controls."""
    return (
        target_date_entry.get_date(),
        _build_self_mood_payload(mood_happy, mood_sad, mood_angry),
        should_save_audio,
    )


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
    save_audio_default = bool(get_env_from_schema("SAVE_AUDIO"))
    save_audio_var = BooleanVar(value=save_audio_default)

    mood_happy_var = IntVar(value=3)
    mood_sad_var = IntVar(value=2)
    mood_angry_var = IntVar(value=1)

    main_frame = ttk.Frame(dlg, padding=UI_STYLE["padding"])

    # --- Ready view: options + record button ---
    ready_frame = ttk.Frame(main_frame)
    status_var = StringVar(value=t("recording.ready"))
    ttk.Label(ready_frame, textvariable=status_var, wraplength=560).grid(
        column=0, row=0, columnspan=2, pady=4
    )

    ttk.Checkbutton(
        ready_frame,
        text=t("recording.save_audio_now"),
        variable=save_audio_var,
    ).grid(column=0, row=1, columnspan=2, sticky="w", pady=4)

    ttk.Label(ready_frame, text=t("recording.for_date")).grid(column=0, row=2, sticky="w", pady=2)
    target_date_entry = create_date_entry(ready_frame, width=14)
    target_date_entry.set_date(date.today())
    target_date_entry.grid(column=1, row=2, sticky="w", pady=2)

    ttk.Label(ready_frame, text=t("recording.self_mood_title")).grid(
        column=0, row=3, columnspan=2, sticky="w"
    )
    ttk.Label(ready_frame, text=t("recording.self_happy")).grid(column=0, row=4, sticky="w", pady=2)
    create_spinbox(ready_frame, from_=0, to=5, width=5, textvariable=mood_happy_var).grid(
        column=1, row=4, sticky="w"
    )
    ttk.Label(ready_frame, text=t("recording.self_sad")).grid(column=0, row=5, sticky="w", pady=2)
    create_spinbox(ready_frame, from_=0, to=5, width=5, textvariable=mood_sad_var).grid(
        column=1, row=5, sticky="w"
    )
    ttk.Label(ready_frame, text=t("recording.self_angry")).grid(column=0, row=6, sticky="w", pady=2)
    create_spinbox(ready_frame, from_=0, to=5, width=5, textvariable=mood_angry_var).grid(
        column=1, row=6, sticky="w"
    )

    record_btn = ttk.Button(
        ready_frame,
        text=t("recording.record"),
        width=UI_STYLE["button_width"],
    )
    record_btn.grid(column=0, row=7, padx=4, pady=8)
    close_btn = ttk.Button(
        ready_frame, text=t("menu.close"), command=dlg.destroy, width=UI_STYLE["button_width"]
    )
    close_btn.grid(column=1, row=7, padx=4, pady=8)

    # --- Recording view: only "Grabando" + symbol ---
    recording_frame = ttk.Frame(main_frame)
    recording_label = ttk.Label(
        recording_frame,
        text=f"{RECORDING_SYMBOL}  {t('recording.recording')}",
        font=(UI_STYLE["font_family"], 14),
    )
    recording_label.pack(pady=16, padx=16)

    recording_timer_active: dict[str, bool] = {"value": False}

    # --- Completed view: message + path (if saved) + exit button ---
    completed_frame = ttk.Frame(main_frame)
    completed_label = ttk.Label(
        completed_frame,
        text=t("recording.completed"),
        font=(UI_STYLE["font_family"], 14),
    )
    completed_label.pack(pady=(16, 8))
    path_label = ttk.Label(completed_frame, text="", wraplength=520)
    exit_btn = ttk.Button(
        completed_frame,
        text=t("menu.close"),
        command=dlg.destroy,
        width=UI_STYLE["button_width"],
    )

    pad = int(UI_STYLE["padding"])

    def _resize_to_frame(frame: ttk.Frame) -> None:
        def _do() -> None:
            dlg.update_idletasks()
            if not dlg.winfo_exists():
                return
            w = max(280, frame.winfo_reqwidth() + pad * 4)
            h = max(120, frame.winfo_reqheight() + pad * 2)
            dlg.geometry(f"{w}x{h}")

        dlg.after_idle(_do)

    def _show_ready() -> None:
        recording_frame.pack_forget()
        completed_frame.pack_forget()
        ready_frame.pack(fill="both")
        _resize_to_frame(ready_frame)

    def _show_recording(msg: str) -> None:
        ready_frame.pack_forget()
        completed_frame.pack_forget()
        recording_label.configure(text=f"{RECORDING_SYMBOL}  {msg}")
        recording_frame.pack(fill="both")
        _resize_to_frame(recording_frame)

    def _update_recording_timer(start_time: float, total_sec: int) -> None:
        if not recording_timer_active["value"] or not dlg.winfo_exists():
            return
        elapsed = int(time.time() - start_time)
        elapsed = min(elapsed, total_sec)
        txt = t("recording.progress", current=str(elapsed), total=str(total_sec))
        recording_label.configure(text=f"{RECORDING_SYMBOL}  {t('recording.recording')}  {txt}")
        if elapsed < total_sec and recording_timer_active["value"]:
            dlg.after(1000, _update_recording_timer, start_time, total_sec)

    def _show_completed(audio_path: str | None = None) -> None:
        ready_frame.pack_forget()
        recording_frame.pack_forget()
        if audio_path:
            path_label.configure(text=t("recording.audio_saved_at", path=audio_path))
            path_label.pack(pady=(0, 12))
        else:
            path_label.pack_forget()
        exit_btn.pack(pady=8)
        completed_frame.pack(fill="both")
        _resize_to_frame(completed_frame)

    is_busy = {"value": False}

    def _set_busy(value: bool) -> None:
        is_busy["value"] = value
        btn_state = "disabled" if value else "normal"
        record_btn.configure(state=btn_state)
        close_btn.configure(state=btn_state)

    def _finish_record(
        kind: str, payload: Any, target_date: date, audio_path: str | None = None
    ) -> None:
        if not dlg.winfo_exists():
            return
        _set_busy(False)

        if kind == "ok":
            _show_completed(audio_path=audio_path)
            return

        recording_timer_active["value"] = False
        _show_ready()
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

                def _to_analyzing() -> None:
                    recording_timer_active["value"] = False
                    _show_recording(t("recording.analyzing"))

                dlg.after(0, _to_analyzing)
            result: VoiceAnalysisResult = analyze_audio(audio, sr)
            audio_path = _save_audio(audio, sr, enabled=should_save_audio)
            app_service.add_voice_record(
                target_date=target_date,
                analysis=result,
                mood_self=mood_self,
                audio_saved_path=audio_path or None,
            )
            if dlg.winfo_exists():
                dlg.after(0, lambda p=audio_path: _finish_record("ok", None, target_date, p))
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
        recording_timer_active["value"] = True
        total_sec = int(get_env_from_schema("RECORD_DURATION_SEC"))
        start_time = time.time()

        _show_recording(t("recording.recording"))
        status_var.set(t("recording.ready"))
        _set_busy(True)

        dlg.after(0, _update_recording_timer, start_time, total_sec)

        target_date, mood_self, should_save_audio = _collect_record_form_state(
            target_date_entry=target_date_entry,
            mood_happy=mood_happy_var.get(),
            mood_sad=mood_sad_var.get(),
            mood_angry=mood_angry_var.get(),
            should_save_audio=bool(save_audio_var.get()),
        )
        worker = Thread(
            target=_run_record_worker,
            args=(target_date, mood_self, should_save_audio),
            daemon=True,
        )
        worker.start()

    record_btn.configure(command=do_record)

    _show_ready()
    main_frame.pack(fill="both")

    def _on_close() -> None:
        if is_busy["value"]:
            return
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    dlg.update_idletasks()
    target_width = max(400, ready_frame.winfo_reqwidth() + (pad * 4))
    target_height = max(320, ready_frame.winfo_reqheight() + (pad * 2))
    dlg.minsize(target_width, target_height)
    place_window_centered(dlg, width=target_width, height=target_height)
