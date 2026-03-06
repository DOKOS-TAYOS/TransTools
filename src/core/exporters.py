"""Export utilities for reports and datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def export_to_csv(frames: dict[str, pd.DataFrame], destination: Path) -> None:
    """Export daily summary dataset to CSV.

    Args:
        frames: Export frames from app service.
        destination: Output CSV path.
    """
    try:
        target = frames.get("resumen_diario", pd.DataFrame())
        target.to_csv(destination, index=False)
    except Exception as exc:
        logger.exception("CSV export failed: %s", exc)
        raise DataStoreError(f"No se pudo exportar CSV: {exc}") from exc


def export_to_excel(frames: dict[str, pd.DataFrame], destination: Path) -> None:
    """Export full report data to Excel workbook.

    Args:
        frames: Export frames from app service.
        destination: Output XLSX path.
    """
    try:
        with pd.ExcelWriter(destination, engine="openpyxl") as writer:
            for sheet_name, frame in frames.items():
                frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    except Exception as exc:
        logger.exception("Excel export failed: %s", exc)
        raise DataStoreError(f"No se pudo exportar Excel: {exc}") from exc


def export_to_png(frames: dict[str, pd.DataFrame], destination: Path) -> None:
    """Export weekly voice trend chart as PNG.

    Args:
        frames: Export frames from app service.
        destination: Output PNG path.
    """
    weekly = frames.get("voz_semanal", pd.DataFrame()).copy()
    fig: Figure | None = None
    try:
        fig, ax = plt.subplots(figsize=(10, 5), dpi=120)
        if weekly.empty:
            ax.text(0.5, 0.5, "Sin datos semanales de voz", ha="center", va="center")
            ax.set_axis_off()
        else:
            weekly = weekly.sort_values("week_start")
            ax.plot(weekly["week_start"], weekly["pitch_mean_hz"], marker="o", color="#2c5f7a")
            ax.set_title("Tendencia semanal de tono de voz")
            ax.set_xlabel("Semana")
            ax.set_ylabel("Pitch medio semanal (Hz)")
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
    """Export a compact weekly PDF report.

    Args:
        frames: Export frames from app service.
        destination: Output PDF path.
        profile_name: Optional first name for title.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as exc:
        raise DataStoreError(
            "La librería reportlab es necesaria para exportar PDF."
        ) from exc

    weekly = frames.get("voz_semanal", pd.DataFrame())
    medication = frames.get("medicacion", pd.DataFrame())
    visits = frames.get("visitas", pd.DataFrame())
    habits = frames.get("habitos", pd.DataFrame())

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

        who = profile_name.strip() if profile_name else "Usuario"
        story.append(Paragraph(f"Informe semanal TransTools - {who}", title_style))
        story.append(Paragraph("Resumen generado localmente (modo offline).", styles["Normal"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("1) Voz (agregado semanal)", styles["Heading3"]))
        story.extend(_table_or_empty_message(weekly, max_rows=8))
        story.append(Spacer(1, 10))

        story.append(Paragraph("2) Medicación (últimos registros)", styles["Heading3"]))
        story.extend(_table_or_empty_message(medication, max_rows=10))
        story.append(Spacer(1, 10))

        story.append(Paragraph("3) Visitas médicas/psicología", styles["Heading3"]))
        story.extend(_table_or_empty_message(visits, max_rows=10))
        story.append(Spacer(1, 10))

        story.append(Paragraph("4) Checklist de hábitos", styles["Heading3"]))
        story.extend(_table_or_empty_message(habits, max_rows=10))

        doc.build(story)
    except Exception as exc:
        logger.exception("PDF export failed: %s", exc)
        raise DataStoreError(f"No se pudo exportar PDF: {exc}") from exc


def _table_or_empty_message(frame: pd.DataFrame, max_rows: int) -> list[Any]:
    """Build reportlab elements for a dataframe section.

    Args:
        frame: Dataframe to convert.
        max_rows: Maximum number of rows shown in PDF.

    Returns:
        List of reportlab flowables.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    if frame.empty:
        return [Paragraph("Sin datos disponibles.", styles["Italic"])]

    subset = frame.head(max_rows).copy()
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
