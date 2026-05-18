"""PDF report generation, branded for Mubarak Bin Mohammed Charter School.

Follows the Charter Schools Visual Identity Guidelines:
  - Navy (#04045C) anchors every page.
  - Teal (#00B3BC) is the single accent (no second accent color used).
  - Gopher is the English typeface — registered from assets/fonts/.
  - The school logo (white) sits on a navy header bar at the top.
  - Backgrounds never use black.
"""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

import branding

# --- Brand colors as ReportLab objects -------------------------------
BRAND = colors.HexColor(branding.NAVY)
ACCENT = colors.HexColor(branding.TEAL)
SOFT_BG = colors.HexColor(branding.SOFT_BG)
MUTED = colors.HexColor(branding.MUTED)


# --- Register Gopher fonts (with safe Helvetica fallback) -----------
def _register_fonts() -> tuple[str, str]:
    """Register Gopher OTF files; return (body_font, bold_font) names."""
    fonts_dir = branding.FONTS
    registered: dict[str, str] = {}
    candidates = {
        "Gopher": fonts_dir / "Gopher-Regular.ttf",
        "Gopher-Medium": fonts_dir / "Gopher-Medium.ttf",
        "Gopher-Bold": fonts_dir / "Gopher-Bold.ttf",
        "Gopher-Black": fonts_dir / "Gopher-Black.ttf",
    }
    for name, path in candidates.items():
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            registered[name] = name
        except Exception:  # noqa: BLE001 — bad font is non-fatal
            continue

    body = registered.get("Gopher", "Helvetica")
    bold = registered.get("Gopher-Bold", "Helvetica-Bold")
    return body, bold


BODY_FONT, BOLD_FONT = _register_fonts()


# --- Styles ----------------------------------------------------------
def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName=BOLD_FONT,
            fontSize=18,
            textColor=BRAND,
            spaceAfter=4,
            leading=22,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=BOLD_FONT,
            fontSize=12,
            textColor=BRAND,
            spaceBefore=14,
            spaceAfter=4,
            leading=16,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=10,
            textColor=BRAND,
            leading=14,
        ),
        "subtle": ParagraphStyle(
            "subtle",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=9,
            textColor=MUTED,
            leading=12,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=8,
            textColor=MUTED,
            leading=11,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=10,
            textColor=BRAND,
            leading=14,
            leftIndent=14,
            bulletIndent=2,
        ),
    }


# --- Header / footer drawn on every page -----------------------------
def _draw_header_footer(canvas, doc):
    """Navy header bar with white logo + small footer with school name."""
    canvas.saveState()
    page_w, page_h = letter

    # Navy header bar
    canvas.setFillColor(BRAND)
    canvas.rect(0, page_h - 0.6 * inch, page_w, 0.6 * inch, fill=1, stroke=0)

    # Logo on the left of the bar (white-on-transparent PNG)
    if branding.LOGO_WHITE.exists():
        try:
            from reportlab.lib.utils import ImageReader

            logo = ImageReader(str(branding.LOGO_WHITE))
            iw, ih = logo.getSize()
            target_h = 0.32 * inch
            target_w = iw * (target_h / ih)
            canvas.drawImage(
                logo,
                0.5 * inch,
                page_h - 0.6 * inch + (0.6 * inch - target_h) / 2,
                width=target_w,
                height=target_h,
                mask="auto",
            )
        except Exception:  # noqa: BLE001
            pass

    # Right-aligned app name in white
    canvas.setFillColor(colors.white)
    canvas.setFont(BOLD_FONT, 10)
    canvas.drawRightString(
        page_w - 0.5 * inch,
        page_h - 0.38 * inch,
        branding.APP_NAME,
    )

    # Thin teal accent line just below the bar
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(2)
    canvas.line(0, page_h - 0.6 * inch - 1, page_w, page_h - 0.6 * inch - 1)

    # Footer
    canvas.setFillColor(MUTED)
    canvas.setFont(BODY_FONT, 7)
    canvas.drawString(
        0.5 * inch,
        0.35 * inch,
        f"{branding.SCHOOL_NAME_EN} — Confidential coaching draft",
    )
    canvas.drawRightString(
        page_w - 0.5 * inch,
        0.35 * inch,
        f"Page {doc.page}",
    )
    canvas.restoreState()


# --- Helpers ---------------------------------------------------------
def _meta_table(lesson: dict[str, Any]) -> Table:
    rows = [
        ["Teacher", lesson.get("teacher_name") or "—"],
        ["Grade", lesson.get("grade") or "—"],
        ["Subject", lesson.get("subject") or "—"],
        ["Topic", lesson.get("topic") or "—"],
        ["Date", lesson.get("lesson_date") or "—"],
        ["Duration", f"{lesson.get('duration_minutes') or '—'} min"],
    ]
    t = Table(rows, colWidths=[1.2 * inch, 4.8 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), SOFT_BG),
                ("FONTNAME", (0, 0), (0, -1), BOLD_FONT),
                ("FONTNAME", (1, 0), (1, -1), BODY_FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -1), BRAND),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), BOLD_FONT),
            ("FONTNAME", (0, 1), (-1, -1), BODY_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), BRAND),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


# --- Main ------------------------------------------------------------
def generate_pdf(lesson: dict[str, Any], report: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=0.95 * inch,   # leave room for navy header bar
        bottomMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        title=f"Coaching Report — {lesson.get('teacher_name', '')}",
        author=branding.SCHOOL_NAME_EN,
    )
    s = _styles()
    story: list[Any] = []

    story.append(Paragraph("Coaching Report", s["h1"]))
    story.append(Paragraph(branding.SCHOOL_NAME_EN, s["subtle"]))
    story.append(Spacer(1, 8))
    story.append(_meta_table(lesson))

    story.append(Paragraph("Lesson Summary", s["h2"]))
    story.append(Paragraph(report.get("summary", "—"), s["body"]))

    tt = report.get("talk_time", {})
    story.append(Paragraph("Talk-Time Breakdown", s["h2"]))
    tt_rows = [
        ["Speaker", "Words", "% of total", "Turns"],
        ["Teacher", str(tt.get("teacher_words", 0)),
         f"{tt.get('teacher_percentage', 0)}%", str(tt.get("teacher_turns", 0))],
        ["Students", str(tt.get("student_words", 0)),
         f"{tt.get('student_percentage', 0)}%", str(tt.get("student_turns", 0))],
    ]
    t = Table(tt_rows, colWidths=[1.5 * inch, 1.2 * inch, 1.5 * inch, 1.5 * inch])
    t.setStyle(_table_style())
    story.append(t)
    if tt.get("notes"):
        story.append(Spacer(1, 6))
        story.append(Paragraph(tt["notes"], s["body"]))

    story.append(Paragraph("Questioning Analysis", s["h2"]))
    questions = report.get("questions", [])
    if questions:
        rows = [["#", "Question", "DOK", "Why"]]
        for i, q in enumerate(questions, 1):
            rows.append(
                [
                    str(i),
                    Paragraph(q.get("text", ""), s["body"]),
                    str(q.get("dok_level", "—")),
                    Paragraph(q.get("rationale", ""), s["body"]),
                ]
            )
        t = Table(rows, colWidths=[0.3 * inch, 2.6 * inch, 0.5 * inch, 2.6 * inch], repeatRows=1)
        t.setStyle(_table_style())
        story.append(t)
    else:
        story.append(Paragraph("No teacher questions identified.", s["body"]))

    story.append(Paragraph("DOK Distribution", s["h2"]))
    dok = report.get("dok_distribution", {})
    dok_desc = {
        "1": "Recall / identify",
        "2": "Explain / compare / summarize",
        "3": "Justify / reason / use evidence",
        "4": "Extended investigation / transfer",
    }
    rows = [["Level", "Count", "Description"]]
    for level in ("1", "2", "3", "4"):
        rows.append([f"DOK {level}", str(dok.get(level, 0)), dok_desc[level]])
    t = Table(rows, colWidths=[0.9 * inch, 0.7 * inch, 4.4 * inch])
    t.setStyle(_table_style())
    story.append(t)

    story.append(Paragraph("Checking for Understanding", s["h2"]))
    cfus = report.get("cfu_moments", [])
    if cfus:
        for cfu in cfus:
            story.append(
                Paragraph(
                    f"<b>{cfu.get('type', 'CFU')}</b> — {cfu.get('description', '')}",
                    s["body"],
                )
            )
            if cfu.get("effectiveness"):
                story.append(Paragraph(f"<i>{cfu['effectiveness']}</i>", s["body"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph(
            "No deliberate CFU structures identified in this lesson.", s["body"]))

    story.append(Paragraph("Glows", s["h2"]))
    for g in report.get("glows", []) or ["—"]:
        story.append(Paragraph(g, s["bullet"], bulletText="•"))

    story.append(Paragraph("Grows", s["h2"]))
    for g in report.get("grows", []) or ["—"]:
        story.append(Paragraph(g, s["bullet"], bulletText="•"))

    story.append(Paragraph("Suggested Next Steps", s["h2"]))
    for n in report.get("next_steps", []) or ["—"]:
        story.append(Paragraph(n, s["bullet"], bulletText="•"))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Disclaimer", s["h2"]))
    story.append(Paragraph(report.get("disclaimer", ""), s["small"]))

    doc.build(
        story,
        onFirstPage=_draw_header_footer,
        onLaterPages=_draw_header_footer,
    )
    buf.seek(0)
    return buf.read()
