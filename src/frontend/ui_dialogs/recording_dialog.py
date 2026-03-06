"""Recording dialog - record, analyze and register voice."""

from __future__ import annotations

from datetime import date, datetime
from tkinter import BooleanVar, IntVar, StringVar, Toplevel, messagebox, ttk

from audio import VoiceAnalysisResult, analyze_audio, record_audio
from config import UI_STYLE, get_audio_dir
from config.env import get_env_from_schema
from core.context import get_app_service
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


def show_recording_dialog(parent) -> None:
    """Show recording dialog. Record -> Analyze -> Save.

    Args:
        parent: Parent Tk window. X closes and returns to main menu.
    """
    dlg = Toplevel(parent)
    dlg.title(t("menu.voice_record"))
    dlg.resizable(width=False, height=False)
    dlg.configure(background=UI_STYLE["bg"])

    app_service = get_app_service()
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

    ttk.Label(frame, text=selected_date_label.get()).grid(column=0, row=2, sticky="w", pady=4)
    date_entry = create_date_entry(frame, width=14)
    date_entry.set_date(date.today())
    date_entry.grid(column=1, row=2, sticky="w", pady=4)

    ttk.Checkbutton(
        frame,
        text=t("recording.save_audio_now"),
        variable=save_audio_var,
    ).grid(column=0, row=3, columnspan=2, sticky="w", pady=4)

    ttk.Label(frame, text=t("recording.self_mood_title")).grid(
        column=0,
        row=4,
        columnspan=2,
        sticky="w",
    )
    ttk.Label(frame, text=t("recording.self_happy")).grid(column=0, row=5, sticky="w", pady=2)
    create_spinbox(frame, from_=0, to=5, width=5, textvariable=mood_happy_var).grid(
        column=1,
        row=5,
        sticky="w",
    )
    ttk.Label(frame, text=t("recording.self_sad")).grid(column=0, row=6, sticky="w", pady=2)
    create_spinbox(frame, from_=0, to=5, width=5, textvariable=mood_sad_var).grid(
        column=1,
        row=6,
        sticky="w",
    )
    ttk.Label(frame, text=t("recording.self_angry")).grid(column=0, row=7, sticky="w", pady=2)
    create_spinbox(frame, from_=0, to=5, width=5, textvariable=mood_angry_var).grid(
        column=1,
        row=7,
        sticky="w",
    )

    def do_record() -> None:
        status_var.set(t("recording.recording"))
        result_var.set("")
        dlg.update()
        try:
            target_date = date_entry.get_date()
            audio, sr = record_audio()
            status_var.set(t("recording.analyzing"))
            dlg.update()
            result: VoiceAnalysisResult = analyze_audio(audio, sr)
            audio_path = _save_audio(audio, sr, enabled=bool(save_audio_var.get()))
            app_service.add_voice_record(
                target_date=target_date,
                analysis=result,
                mood_self=_build_self_mood_payload(
                    mood_happy_var.get(),
                    mood_sad_var.get(),
                    mood_angry_var.get(),
                ),
                audio_saved_path=audio_path or None,
            )
            now = datetime.now()
            result_var.set(
                t(
                    "recording.result",
                    datetime=now.strftime("%Y-%m-%d %H:%M"),
                    date=target_date.isoformat(),
                )
            )
            status_var.set(t("recording.saved_ok"))
        except RecordingError as e:
            messagebox.showerror(t("recording.error_recording"), str(e))
            status_var.set(t("recording.error_recording_msg"))
        except AnalysisError as e:
            messagebox.showerror(t("recording.error_analysis"), str(e))
            status_var.set(t("recording.error_analysis_msg"))
        except ValueError:
            messagebox.showerror(t("recording.error_date"), t("recording.error_date_msg"))
            status_var.set(t("recording.error_date_msg"))
        except DataStoreError as e:
            messagebox.showerror(t("recording.error_save"), str(e))
            status_var.set(t("recording.error_save_msg"))
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            messagebox.showerror(t("error.generic"), str(e))
            status_var.set(t("recording.error_unexpected"))

    ttk.Button(
        frame,
        text=t("recording.record"),
        command=do_record,
        width=UI_STYLE["button_width"],
    ).grid(column=0, row=8, padx=4, pady=8)
    ttk.Button(
        frame, text=t("menu.close"), command=dlg.destroy, width=UI_STYLE["button_width"]
    ).grid(column=1, row=8, padx=4, pady=8)

    frame.pack(fill="both", expand=True)

    def _on_close() -> None:
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    place_window_centered(dlg, width=470, height=360)
