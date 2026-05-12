import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

WIDTH, HEIGHT = A4


def build_report(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CNTitle", parent=styles["Title"], fontSize=20, spaceAfter=6 * mm
    )
    heading_style = ParagraphStyle(
        "CNHeading", parent=styles["Heading2"], fontSize=14, spaceAfter=4 * mm
    )
    body_style = ParagraphStyle(
        "CNBody", parent=styles["Normal"], fontSize=10, leading=16, spaceAfter=4 * mm
    )

    elements = []

    def add_text(text: str, style=body_style):
        elements.append(Paragraph(text, style))

    # Title
    add_text("降AIGC · 文本分析报告", title_style)
    add_text(f'检测类型: {data.get("type", "AIGC检测")} | 检测时间: {data.get("time", "")}')
    elements.append(Spacer(1, 6 * mm))

    # Score
    add_text(f'AI生成概率: {data.get("score", "N/A")}%', heading_style)
    add_text(f'分析: {data.get("analysis", "")}')
    elements.append(Spacer(1, 4 * mm))

    # Suspicious segments
    segments = data.get("suspicious_segments", [])
    if segments:
        add_text("可疑段落标注:", heading_style)
        for i, seg in enumerate(segments[:5]):
            add_text(f'{i + 1}. [AI概率 {seg.get("score", "?")}%] {seg.get("text", "")}')
            add_text(f'   判定理由: {seg.get("reason", "")}')
        elements.append(Spacer(1, 4 * mm))

    # Plagiarism
    if data.get("similarity_score") is not None:
        add_text(f'重复率: {data.get("similarity_score", "N/A")}%', heading_style)
        add_text(f'详情: {data.get("details", "")}')
        elements.append(Spacer(1, 4 * mm))

    # Rewrite
    if data.get("rewritten_text"):
        add_text("改写后文本:", heading_style)
        add_text(data["rewritten_text"])
        add_text(f'改写说明: {data.get("changes_summary", "")}')
        elements.append(Spacer(1, 4 * mm))

    # Footer
    elements.append(Spacer(1, 10 * mm))
    add_text("— 本报告由 降AIGC平台 自动生成 —", ParagraphStyle(
        "Footer", parent=body_style, fontSize=8, alignment=TA_CENTER, textColor=HexColor("#999")
    ))

    doc.build(elements)
    buf.seek(0)
    return buf.read()
