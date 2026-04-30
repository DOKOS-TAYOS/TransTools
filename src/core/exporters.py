"""Export utilities for reports and datasets."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def export_to_csv(frames: dict[str, pd.DataFrame], destination: Path) -> None:
    """Export daily summary dataset to CSV."""
    try:
        target = frames.get("resumen_diario", pd.DataFrame())
        target.to_csv(destination, index=False)
    except Exception as exc:
        logger.exception("CSV export failed: %s", exc)
        raise DataStoreError(f"No se pudo exportar CSV: {exc}") from exc


def export_to_excel(frames: dict[str, pd.DataFrame], destination: Path) -> None:
    """Export full report data to Excel workbook."""
    try:
        with pd.ExcelWriter(destination, engine="openpyxl") as writer:
            for sheet_name, frame in frames.items():
                frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    except Exception as exc:
        logger.exception("Excel export failed: %s", exc)
        raise DataStoreError(f"No se pudo exportar Excel: {exc}") from exc


def export_to_png(frames: dict[str, pd.DataFrame], destination: Path) -> None:
    """Export weekly voice trend chart as PNG."""
    weekly = frames.get("voz_semanal", pd.DataFrame()).copy()
    fig: Figure | None = None
    try:
        fig, ax = plt.subplots(figsize=(10, 5), dpi=120)
        if weekly.empty:
            ax.text(0.5, 0.5, t("export.png.no_data"), ha="center", va="center")
            ax.set_axis_off()
        else:
            weekly = weekly.sort_values("week_start")
            ax.plot(weekly["week_start"], weekly["pitch_mean_hz"], marker="o", color="#2c5f7a")
            ax.set_title(t("export.png.title"))
            ax.set_xlabel(t("export.png.xlabel"))
            ax.set_ylabel(t("export.png.ylabel"))
            ax.tick_params(axis="x", rotation=45)
            ax.grid(alpha=0.2)
        fig.tight_layout()
        fig.savefig(destination, format="png")
    except Exception as exc:
        logger.exception("PNG export failed: %s", exc)
        raise DataStoreError(f"No se pudo exportar PNG: {exc}") from exc
    finally:
        if fig is not None:
            plt.close(fig)


def export_to_pdf(
    frames: dict[str, pd.DataFrame],
    destination: Path,
    profile_name: str | None = None,
) -> None:
    """Export a compact weekly PDF report."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as exc:
        raise DataStoreError("La libreria reportlab es necesaria para exportar PDF.") from exc

    weekly = frames.get("voz_semanal", pd.DataFrame())
    medication = frames.get("medicacion", pd.DataFrame())
    visits = frames.get("visitas", pd.DataFrame())

    try:
        doc = SimpleDocTemplate(str(destination), pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.HexColor("#1f3d52"),
            spaceAfter=14,
        )
        story: list[Any] = []

        who = profile_name.strip() if profile_name else t("export.pdf.default_user")
        story.append(Paragraph(t("export.pdf.title", name=who), title_style))
        story.append(Spacer(1, 12))

        story.append(Paragraph(t("export.pdf.section_voice"), styles["Heading3"]))
        story.extend(_table_or_empty_message(weekly, max_rows=8, section="voice"))
        story.append(Spacer(1, 10))

        story.append(Paragraph(t("export.pdf.section_medication"), styles["Heading3"]))
        story.extend(_table_or_empty_message(medication, max_rows=10, section="medication"))
        story.append(Spacer(1, 10))

        story.append(Paragraph(t("export.pdf.section_visits"), styles["Heading3"]))
        story.extend(_table_or_empty_message(visits, max_rows=10, section="visits"))

        story.append(Spacer(1, 14))
        story.append(Paragraph(t("export.pdf.section_chart"), styles["Heading3"]))
        chart_img = _build_tone_chart_image(weekly)
        if chart_img is not None:
            from reportlab.platypus import Image as RlImage

            story.append(RlImage(chart_img, width=450, height=240))
        else:
            story.append(Paragraph(t("export.table.no_data"), styles["Italic"]))

        doc.build(story)
    except Exception as exc:
        logger.exception("PDF export failed: %s", exc)
        raise DataStoreError(f"No se pudo exportar PDF: {exc}") from exc


def _build_tone_chart_image(weekly: pd.DataFrame) -> BytesIO | None:
    """Build tone evolution chart as PNG bytes for PDF embedding."""
    if weekly.empty:
        return None
    weekly = weekly.sort_values("week_start").copy()
    fig: Figure | None = None
    try:
        fig, ax = plt.subplots(figsize=(6, 3.2), dpi=100)
        ax.plot(weekly["week_start"], weekly["pitch_mean_hz"], marker="o", color="#2c5f7a")
        ax.set_title(t("export.png.title"))
        ax.set_xlabel(t("export.png.xlabel"))
        ax.set_ylabel(t("export.png.ylabel"))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(alpha=0.2)
        fig.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=100)
        buf.seek(0)
        return buf
    finally:
        if fig is not None:
            plt.close(fig)


def _prepare_pdf_table(frame: pd.DataFrame, section: str) -> pd.DataFrame:
    """Prepare dataframe for PDF: drop cols, rename, round, replace nan."""
    df = frame.copy()
    drop_cols = {"id", "created_at", "taken", "completed"}
    for c in drop_cols:
        if c in df.columns:
            df = df.drop(columns=[c])

    if section == "voice":
        rename = {
            "week_start": "Semana",
            "samples": "N",
            "pitch_mean_hz": "Pitch (Hz)",
            "pitch_min_hz": "Min",
            "pitch_max_hz": "Max",
            "pitch_std_hz": "σ",
            "energy_rms": "Energía",
            "mood_happy": "Feliz",
            "mood_sad": "Triste",
            "mood_angry": "Enfado",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        for col in df.select_dtypes(include=["number"]).columns:
            df[col] = df[col].round(1)
    elif section == "medication":
        rename = {"date": "Fecha", "hour": "Hora", "dose": "Dosis", "notes": "Notas"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    elif section == "visits":
        rename = {
            "date": "Fecha",
            "visit_type": "Tipo",
            "next_visit_date": "Próx.",
            "notes": "Notas",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    df = df.fillna("Ninguna")
    return df


def _table_or_empty_message(
    frame: pd.DataFrame, max_rows: int, section: str = "generic"
) -> list[Any]:
    """Build reportlab elements for a dataframe section."""
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    if frame.empty:
        return [Paragraph(t("export.table.no_data"), styles["Italic"])]

    subset = _prepare_pdf_table(frame.head(max_rows), section)
    cols = list(subset.columns)
    data = [cols] + subset.astype(str).values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9f0f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f3d52")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [table]
