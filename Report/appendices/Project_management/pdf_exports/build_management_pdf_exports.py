#!/usr/bin/env python3
"""Generate marker-readable PDF companions for management appendices.

The source management files remain the editable evidence. These PDFs are
fixed-layout companion exports for cases where a marker should not need to
open Word or Excel to inspect the main tables.
"""

from __future__ import annotations

import csv
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_MANAGEMENT_DIR = SCRIPT_DIR.parent
REPORT_DIR = PROJECT_MANAGEMENT_DIR.parents[1]
REPO_ROOT = REPORT_DIR.parent

DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "ExportTitle",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        spaceAfter=6,
    )
    subtitle = ParagraphStyle(
        "ExportSubtitle",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=8,
    )
    heading = ParagraphStyle(
        "ExportHeading",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        spaceBefore=8,
        spaceAfter=5,
    )
    body = ParagraphStyle(
        "ExportBody",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        spaceAfter=5,
    )
    cell = ParagraphStyle(
        "ExportCell",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=6.6,
        leading=7.6,
        wordWrap="CJK",
    )
    header = ParagraphStyle(
        "ExportHeaderCell",
        parent=cell,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    return {
        "title": title,
        "subtitle": subtitle,
        "heading": heading,
        "body": body,
        "cell": cell,
        "header": header,
    }


STYLES = _styles()


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def paragraph(text: object, style: ParagraphStyle | None = None) -> Paragraph:
    style = style or STYLES["cell"]
    value = "" if text is None else str(text)
    value = escape(value).replace("\n", "<br/>")
    return Paragraph(value, style)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(doc.leftMargin, 10 * mm, "B-BOT management appendix companion export")
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(path: Path, title: str, story: list, pagesize=landscape(A4)) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=pagesize,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=16 * mm,
    )
    story = [
        Paragraph(title, STYLES["title"]),
        Paragraph(
            "Generated companion PDF for marker-readable appendix review. "
            "The editable source files remain the authoritative Office/Markdown evidence.",
            STYLES["subtitle"],
        ),
    ] + story
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def make_table(
    rows: list[list[object]],
    col_widths: list[float],
    header_rows: int = 1,
    font_size: float = 6.6,
    leading: float = 7.6,
) -> Table:
    cell_style = ParagraphStyle(
        f"ExportCell{font_size}",
        parent=STYLES["cell"],
        fontSize=font_size,
        leading=leading,
    )
    header_style = ParagraphStyle(
        f"ExportHeader{font_size}",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    converted: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        style = header_style if row_index < header_rows else cell_style
        converted.append([paragraph(value, style) for value in row])

    table = Table(converted, colWidths=col_widths, repeatRows=header_rows, splitByRow=True)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#23405f")),
                ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#777777")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
            ]
        )
    )
    return table


def docx_tables(path: Path) -> list[list[list[str]]]:
    with zipfile.ZipFile(path) as docx:
        root = ET.fromstring(docx.read("word/document.xml"))

    tables: list[list[list[str]]] = []
    for table in root.findall(".//w:tbl", DOCX_NS):
        rows: list[list[str]] = []
        for tr in table.findall("w:tr", DOCX_NS):
            row: list[str] = []
            for tc in tr.findall("w:tc", DOCX_NS):
                text = " ".join(t.text or "" for t in tc.findall(".//w:t", DOCX_NS))
                row.append(" ".join(text.split()))
            rows.append(row)
        tables.append(rows)
    return tables


def level_from_marks(values: list[str]) -> str:
    labels = ["Low", "Medium", "High"]
    for label, value in zip(labels, values):
        if value.strip().upper() == "X":
            return label
    return ""


def simplify_risk_table(rows: list[list[str]], first_heading: str) -> list[list[str]]:
    simplified = [[first_heading, "Severity", "Potential", "Score", "Mitigation / control measures"]]
    for row in rows[2:]:
        if len(row) < 9 or not row[0].strip():
            continue
        simplified.append(
            [
                row[0],
                level_from_marks(row[1:4]),
                level_from_marks(row[4:7]),
                row[7],
                row[8],
            ]
        )
    return simplified


def markdown_tables(path: Path) -> dict[str, list[list[str]]]:
    current_heading = ""
    tables: dict[str, list[list[str]]] = {}
    active_rows: list[list[str]] | None = None
    lines = path.read_text(encoding="utf-8").splitlines()

    for line in lines:
        if line.startswith("## "):
            if active_rows is not None and current_heading:
                tables[current_heading] = active_rows
            current_heading = line.lstrip("#").strip()
            active_rows = None
            continue
        if line.startswith("|") and current_heading:
            cells = [cell.strip() for cell in next(csv.reader([line.strip().strip("|")], delimiter="|"))]
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            if active_rows is None:
                active_rows = []
            active_rows.append(cells)
            continue
        if active_rows is not None and line.strip() == "":
            tables[current_heading] = active_rows
            active_rows = None

    if active_rows is not None and current_heading:
        tables[current_heading] = active_rows
    return tables


def build_project_plan_pdf() -> Path:
    planning_md = REPORT_DIR / "planning" / "Project_Management_Gantt_and_Weekly_Log.md"
    tables = markdown_tables(planning_md)
    out = SCRIPT_DIR / "Appendix_B_Project_Plan_Gantt_companion.pdf"

    source_rows = [
        ["Evidence item", "Location"],
        ["Filled planning spreadsheet", rel(PROJECT_MANAGEMENT_DIR / "Appendix_B_Project_Plan_Gantt" / "Project Planning Template - B-BOT filled.xlsx")],
        ["Reconstructed Gantt and weekly log source", rel(planning_md)],
        ["Rendered Gantt PDF", rel(REPORT_DIR / "figures" / "project_management_gantt.pdf")],
        ["Rendered Gantt PNG", rel(REPORT_DIR / "figures" / "project_management_gantt.png")],
    ]
    phase_rows = [
        ["Phase", "Approximate period", "Evidence / output"],
        ["Planning and management", "Oct 2025 and Apr 2026", "Proposal, objectives, risk/H&S records, reconstructed final schedule and appendix planning."],
        ["Mechanical and electrical build", "Oct 2025 - Mar 2026", "3D modelling, print iteration, PCB/wiring work, harness construction, motor soldering and integration cleanup."],
        ["Embedded firmware and control", "Nov 2025 - Feb 2026", "ESP32 PlatformIO firmware, CAN motor feedback, IMU processing, PID/LQR/VMC balance and safety states."],
        ["Host software, ROS 2 and vision", "Feb 2026 - Apr 2026", "Host architecture decision, micro-ROS camera bring-up, MediaPipe bridge and supervisory TCP command safety."],
        ["Testing, data and report", "Mar 2026 - Apr 2026", "Experiment matrix, measured/provisional data policy, generated figures, LaTeX report and appendix integration."],
    ]

    story: list = [
        Paragraph("Source Evidence", STYLES["heading"]),
        make_table(source_rows, [70 * mm, 190 * mm], font_size=7.2, leading=8.2),
        Spacer(1, 5 * mm),
        Paragraph("Rendered Gantt Preview", STYLES["heading"]),
    ]

    gantt_png = REPORT_DIR / "figures" / "project_management_gantt.png"
    if gantt_png.exists():
        try:
            image = Image(str(gantt_png))
            max_width = 260 * mm
            max_height = 135 * mm
            scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
            image.drawWidth = image.imageWidth * scale
            image.drawHeight = image.imageHeight * scale
            story.append(image)
        except Exception as exc:  # pragma: no cover - depends on local image backend.
            story.append(Paragraph(f"Gantt image could not be embedded by ReportLab: {exc}", STYLES["body"]))
    else:
        story.append(Paragraph("Rendered Gantt image is not present; use the PDF/PNG paths above.", STYLES["body"]))

    story += [
        Spacer(1, 4 * mm),
        Paragraph("Phase Summary", STYLES["heading"]),
        make_table(phase_rows, [45 * mm, 45 * mm, 170 * mm], font_size=7.0, leading=8.2),
    ]

    reduced = tables.get("B.1 Project Management Narrative")
    if reduced:
        story += [
            Spacer(1, 4 * mm),
            Paragraph("Reduced-Development Periods", STYLES["heading"]),
            make_table(reduced, [60 * mm, 70 * mm, 130 * mm], font_size=7.0, leading=8.2),
        ]

    weekly = tables.get("B.3 Weekly Activity Log")
    if weekly:
        story += [
            PageBreak(),
            Paragraph("Weekly Activity Log", STYLES["heading"]),
            make_table(weekly, [14 * mm, 32 * mm, 43 * mm, 119 * mm, 52 * mm], font_size=5.8, leading=6.7),
        ]

    deviations = tables.get("B.4 Key Schedule Deviations and Responses")
    if deviations:
        story += [
            PageBreak(),
            Paragraph("Key Schedule Deviations and Responses", STYLES["heading"]),
            make_table(deviations, [65 * mm, 65 * mm, 75 * mm, 55 * mm], font_size=6.6, leading=7.8),
        ]

    build_pdf(out, "Appendix B: Project Plan, Gantt Chart and Weekly Activity Log", story)
    return out


def build_project_risk_pdf() -> Path:
    source = PROJECT_MANAGEMENT_DIR / "Appendix_C_Project_Risk_Register" / "Project Risk Register - B-BOT filled.docx"
    tables = docx_tables(source)
    out = SCRIPT_DIR / "Appendix_C_Project_Risk_Register_companion.pdf"
    risk_rows = simplify_risk_table(tables[1], "Project delivery risk")
    story = [
        Paragraph("Source Evidence", STYLES["heading"]),
        make_table([["Evidence item", "Location"], ["Filled Word register", rel(source)]], [60 * mm, 200 * mm], font_size=7.2),
        Spacer(1, 5 * mm),
        Paragraph("Project-Delivery Risk Register", STYLES["heading"]),
        make_table(risk_rows, [82 * mm, 25 * mm, 25 * mm, 18 * mm, 110 * mm], font_size=6.4, leading=7.4),
    ]
    build_pdf(out, "Appendix C: Project Risk Register", story)
    return out


def build_cpd_pdf() -> Path:
    source = PROJECT_MANAGEMENT_DIR / "Appendix_D_CPD_Log" / "CPD Log - B-BOT filled.docx"
    tables = docx_tables(source)
    out = SCRIPT_DIR / "Appendix_D_CPD_Log_companion.pdf"
    current = tables[0]
    planned = tables[1]
    total_hours = sum(int(row[3]) for row in current[1:] if len(row) > 3 and row[3].isdigit())
    story = [
        Paragraph("Source Evidence", STYLES["heading"]),
        make_table([["Evidence item", "Location"], ["Filled Word CPD log", rel(source)]], [60 * mm, 200 * mm], font_size=7.2),
        Spacer(1, 4 * mm),
        Paragraph(f"Current and Recent CPD Activity ({total_hours} recorded hours)", STYLES["heading"]),
        make_table(current, [54 * mm, 140 * mm, 39 * mm, 25 * mm], font_size=6.2, leading=7.4),
        Spacer(1, 5 * mm),
        Paragraph("Planned and Future CPD Activity", STYLES["heading"]),
        make_table(planned, [49 * mm, 112 * mm, 70 * mm, 29 * mm], font_size=6.0, leading=7.2),
    ]
    build_pdf(out, "Appendix D: Continuing Professional Development Log", story)
    return out


def build_health_safety_pdf() -> Path:
    source = PROJECT_MANAGEMENT_DIR / "Appendix_E_Health_and_Safety" / "H&S Risk Register - B-BOT filled.docx"
    tables = docx_tables(source)
    out = SCRIPT_DIR / "Appendix_E_Health_and_Safety_companion.pdf"
    info = tables[0]
    risk_rows = simplify_risk_table(tables[1], "Health and safety hazard")
    story = [
        Paragraph("Source Evidence", STYLES["heading"]),
        make_table([["Evidence item", "Location"], ["Filled Word H&S risk assessment", rel(source)]], [60 * mm, 200 * mm], font_size=7.2),
        Spacer(1, 4 * mm),
        Paragraph("Document Details", STYLES["heading"]),
        make_table(info, [45 * mm, 70 * mm, 45 * mm, 50 * mm, 25 * mm, 25 * mm], font_size=7.0, leading=8.0),
        Spacer(1, 5 * mm),
        Paragraph("Health and Safety Risk Assessment", STYLES["heading"]),
        make_table(risk_rows, [82 * mm, 25 * mm, 25 * mm, 18 * mm, 110 * mm], font_size=6.4, leading=7.4),
    ]
    build_pdf(out, "Appendix E: Health and Safety Risk Assessment", story)
    return out


def main() -> int:
    outputs = [
        build_project_plan_pdf(),
        build_project_risk_pdf(),
        build_cpd_pdf(),
        build_health_safety_pdf(),
    ]
    for output in outputs:
        print(rel(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
