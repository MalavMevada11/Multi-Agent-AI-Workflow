import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.config.settings import REPORTS_DIR
from app.schema.state import ReportArtifact, ChartArtifact


def build_pdf_report(
    report: ReportArtifact,
    charts: List[ChartArtifact],
    department: str = "Enterprise",
    output_filename: Optional[str] = None
) -> str:
    """
    Compiles a polished, publication-ready PDF report using ReportLab.
    Includes executive summaries, policy audit tables, KPI matrices, and embedded charts.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"BI_Report_{department.lower()}_{timestamp}.pdf"

    pdf_path = REPORTS_DIR / output_filename
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph(report.title, title_style))
    gen_time = datetime.now().strftime("%B %d, %Y - %H:%M:%S")
    story.append(
        Paragraph(
            f"<b>Department:</b> {department.upper()} &nbsp;|&nbsp; <b>Workflow:</b> Automated Multi-Agent BI & Policy Engine &nbsp;|&nbsp; <b>Date:</b> {gen_time}",
            subtitle_style
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

    # 2. Executive Summary
    story.append(Paragraph("1. Executive Summary", h2_style))
    story.append(Paragraph(report.executive_summary, body_style))
    story.append(Spacer(1, 10))

    # 3. KPI Highlights Matrix
    if report.kpi_cards:
        story.append(Paragraph("2. Key Performance Indicators", h2_style))
        kpi_table_data = [["Metric", "Value", "Status / Trend"]]
        for card in report.kpi_cards:
            kpi_table_data.append([
                card.get("title", ""),
                card.get("value", ""),
                card.get("note", "Normal")
            ])

        kpi_table = Table(kpi_table_data, colWidths=[200, 150, 180])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white])
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 15))

    # 4. Embedded Visualizations
    if charts:
        story.append(Paragraph("3. Visual Business Intelligence", h2_style))
        for chart in charts:
            if Path(chart.file_path).exists():
                story.append(Paragraph(f"<b>Figure:</b> {chart.title}", body_style))
                story.append(Image(chart.file_path, width=480, height=240))
                story.append(Paragraph(f"<i>Takeaway: {chart.key_takeaway}</i>", body_style))
                story.append(Spacer(1, 12))

    # 5. Strategic Recommendations
    if report.recommendations:
        story.append(Paragraph("4. Strategic & Policy Recommendations", h2_style))
        for idx, rec in enumerate(report.recommendations, 1):
            story.append(Paragraph(f"<b>{idx}.</b> {rec}", body_style))
        story.append(Spacer(1, 15))

    # Build PDF document
    doc.build(story)
    return str(pdf_path)
