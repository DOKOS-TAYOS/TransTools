"""Recording dialog - record, analyze, save."""

from datetime import datetime
from tkinter import Toplevel, messagebox, ttk

from audio import analyze_audio, record_audio
from config import UI_STYLE, get_audio_dir
from config.env import get_env_from_schema
from frontend.window_utils import place_window_centered
from i18n import t
from loader import append_record
from utils import AnalysisError, DataStoreError, RecordingError, get_logger

logger = get_logger(__name__)


def _save_audio(audio_data, sample_rate: int) -> str:
    """Save audio to output/audio/ if SAVE_AUDIO is True.

    Args:
        audio_data: Float32 audio array.
        sample_rate: Sample rate in Hz.

    Returns:
        Path to saved file, or empty string if skipped.
    """
    if not get_env_from_schema("SAVE_AUDIO"):
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
    return str(path)


def show_recording_dialog(parent) -> None:
    """Show recording dialog. Record -> Analyze -> Save.

    Args:
        parent: Parent Tk window. X closes and returns to main menu.
    """
    dlg = Toplevel(parent)
    dlg.title(t("menu.recording"))
    dlg.resizable(width=False, height=False)
    dlg.configure(background=UI_STYLE["bg"])

    status_var = __import__("tkinter").StringVar(value=t("recording.ready"))
    result_var = __import__("tkinter").StringVar(value="")

    frame = ttk.Frame(dlg, padding=UI_STYLE["padding"])
    ttk.Label(frame, textvariable=status_var, wraplength=360).grid(
        column=0, row=0, columnspan=2, pady=4
    )
    ttk.Label(frame, textvariable=result_var, wraplength=360).grid(
        column=0, row=1, columnspan=2, pady=4
    )

    def do_record() -> None:
        status_var.set(t("recording.recording"))
        result_var.set("")
        dlg.update()
        try:
            audio, sr = record_audio()
            status_var.set(t("recording.analyzing"))
            dlg.update()
            result = analyze_audio(audio, sr)
            audio_path = _save_audio(audio, sr)
            now = datetime.now()
            append_record(
                date=now,
                pitch_mean_hz=result.pitch_mean_hz,
                pitch_std_hz=result.pitch_std_hz,
                pitch_min_hz=result.pitch_min_hz,
                pitch_max_hz=result.pitch_max_hz,
                energy_rms=result.energy_rms,
                mood_score=result.mood_score,
                audio_path=audio_path,
            )
            result_var.set(
                t(
                    "recording.result",
                    hz=f"{result.pitch_mean_hz:.1f}",
                    datetime=now.strftime("%Y-%m-%d %H:%M"),
                )
            )
            status_var.set(t("recording.saved_ok"))
        except RecordingError as e:
            messagebox.showerror(t("recording.error_recording"), str(e))
            status_var.set(t("recording.error_recording_msg"))
        except AnalysisError as e:
            messagebox.showerror(t("recording.error_analysis"), str(e))
            status_var.set(t("recording.error_analysis_msg"))
        except DataStoreError as e:
            messagebox.showerror(t("recording.error_save"), str(e))
            status_var.set(t("recording.error_save_msg"))
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            messagebox.showerror(t("error.generic"), str(e))
            status_var.set(t("recording.error_unexpected"))

    ttk.Button(frame, text=t("recording.record"), command=do_record, width=UI_STYLE["button_width"]).grid(
        column=0, row=2, padx=4, pady=8
    )
    ttk.Button(
        frame, text=t("menu.close"), command=dlg.destroy, width=UI_STYLE["button_width"]
    ).grid(column=1, row=2, padx=4, pady=8)

    frame.pack(fill="both", expand=True)

    def _on_close() -> None:
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)
    dlg.transient(parent)
    place_window_centered(dlg, preserve_size=True)
