"""
Professional AIGC Detection Report — 对标知网/维普报告格式.

Report structure:
1. 报告信息区 — 标题、检测时间、方法说明
2. 综合评分区 — AIGC概率仪表盘、置信度、等级
3. 多维特征分析 — 困惑度、句式突发度、词汇多样性、模板匹配
4. 段落级分析 — 逐段评分表 + 高亮标记
5. 可疑内容标注 — 具体段落、原因
6. 检测结论 — 综合判定 + 建议
7. 方法论说明 — 检测技术说明 + 免责声明
"""

import io
import math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import (
    HexColor, Color, black, white, grey,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable,
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas


WIDTH, HEIGHT = A4  # 210 x 297 mm

# Brand colors
BLUE_DARK = HexColor("#1a56db")
BLUE_MID = HexColor("#3b82f6")
BLUE_LIGHT = HexColor("#eff6ff")
RED_DARK = HexColor("#dc2626")
RED_LIGHT = HexColor("#fef2f2")
ORANGE_MID = HexColor("#f59e0b")
ORANGE_LIGHT = HexColor("#fffbeb")
GREEN_DARK = HexColor("#059669")
GREEN_LIGHT = HexColor("#ecfdf5")
GRAY_900 = HexColor("#111827")
GRAY_600 = HexColor("#4b5563")
GRAY_400 = HexColor("#9ca3af")
GRAY_200 = HexColor("#e5e7eb")
GRAY_50 = HexColor("#f9fafb")


class ScoreGaugeFlowable(Flowable):
    """Circular score gauge drawn directly in the PDF."""

    def __init__(self, score: float, width: float = 100, height: float = 100):
        Flowable.__init__(self)
        self.score = max(0, min(100, score))
        self.width = width
        self.height = height
        self._canvas_width = width
        self._canvas_height = height

    def draw(self):
        c = self.canv
        cx = self._canvas_width / 2
        cy = self._canvas_height / 2 + 10
        r = 38

        # Background arc
        c.setStrokeColor(GRAY_200)
        c.setLineWidth(8)
        c.setFillColor(white)
        c.circle(cx, cy, r, fill=0, stroke=1)

        # Score arc (0-180 degrees: left to right)
        angle = (self.score / 100) * 180
        if self.score < 30:
            color = GREEN_DARK
        elif self.score < 70:
            color = ORANGE_MID
        else:
            color = RED_DARK

        c.setStrokeColor(color)
        c.setLineWidth(8)
        c.arc(cx - r, cy - r, cx + r, cy + r, 180, 180 - angle)

        # Score text
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(cx, cy + 5, f"{self.score:.0f}")
        c.setFont("Helvetica", 9)
        c.setFillColor(GRAY_600)
        c.drawCentredString(cx, cy - 15, "AIGC 概率")

        # Level label below
        if self.score < 30:
            level = "低风险"
            lvl_color = GREEN_DARK
        elif self.score < 70:
            level = "中风险"
            lvl_color = ORANGE_MID
        else:
            level = "高风险"
            lvl_color = RED_DARK

        c.setFillColor(lvl_color)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(cx, cy - r - 12, level)


class ColorBar(Flowable):
    """Horizontal colored bar for feature scores."""

    def __init__(self, score: float, label: str, width: float = 200):
        Flowable.__init__(self)
        self.score = max(0, min(100, score))
        self.label = label
        self.width = width
        self.height = 16
        self._canvas_width = width
        self._canvas_height = 16

    def draw(self):
        c = self.canv
        bar_width = self._canvas_width - 60
        bar_x = 60
        bar_y = 2
        bar_height = 10

        # Label
        c.setFillColor(GRAY_600)
        c.setFont("Helvetica", 7)
        c.drawString(0, bar_y + 1, self.label)

        # Background
        c.setFillColor(GRAY_200)
        c.roundRect(bar_x, bar_y, bar_width, bar_height, 5, fill=1, stroke=0)

        # Fill
        filled = bar_width * (self.score / 100)
        if self.score < 30:
            color = GREEN_DARK
        elif self.score < 70:
            color = ORANGE_MID
        else:
            color = RED_DARK
        c.setFillColor(color)
        if filled > 5:
            c.roundRect(bar_x, bar_y, filled, bar_height, 5, fill=1, stroke=0)

        # Score text
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(bar_x + bar_width + 4, bar_y + 1, f"{self.score:.0f}")


def _build_styles() -> dict:
    """Create professional report styles."""
    return {
        "report_title": ParagraphStyle(
            "ReportTitle", fontSize=22, leading=28, textColor=GRAY_900,
            spaceAfter=2 * mm, alignment=TA_CENTER,
        ),
        "report_subtitle": ParagraphStyle(
            "ReportSubtitle", fontSize=9, leading=14, textColor=GRAY_400,
            spaceAfter=8 * mm, alignment=TA_CENTER,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle", fontSize=13, leading=18, textColor=GRAY_900,
            spaceBefore=8 * mm, spaceAfter=4 * mm,
            borderPadding=(0, 0, 2, 0),
        ),
        "subsection_title": ParagraphStyle(
            "SubsectionTitle", fontSize=10, leading=14, textColor=GRAY_600,
            spaceBefore=4 * mm, spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "ReportBody", fontSize=8.5, leading=14, textColor=GRAY_900,
            spaceAfter=2 * mm, alignment=TA_JUSTIFY,
        ),
        "body_small": ParagraphStyle(
            "ReportBodySmall", fontSize=7.5, leading=12, textColor=GRAY_600,
            spaceAfter=1 * mm,
        ),
        "highlight_red": ParagraphStyle(
            "HighlightRed", fontSize=8.5, leading=14, textColor=RED_DARK,
            backColor=RED_LIGHT, spaceAfter=2 * mm,
        ),
        "highlight_orange": ParagraphStyle(
            "HighlightOrange", fontSize=8.5, leading=14, textColor=HexColor("#92400e"),
            backColor=ORANGE_LIGHT, spaceAfter=2 * mm,
        ),
        "highlight_green": ParagraphStyle(
            "HighlightGreen", fontSize=8.5, leading=14, textColor=GREEN_DARK,
            backColor=GREEN_LIGHT, spaceAfter=2 * mm,
        ),
        "footer": ParagraphStyle(
            "Footer", fontSize=7, leading=10, textColor=GRAY_400,
            alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer", fontSize=6.5, leading=10, textColor=GRAY_400,
            spaceBefore=4 * mm,
        ),
    }


def _level_label(score: float) -> str:
    if score < 30:
        return "低"
    elif score < 70:
        return "中"
    return "高"


def _level_color(score: float) -> HexColor:
    if score < 30:
        return GREEN_DARK
    elif score < 70:
        return ORANGE_MID
    return RED_DARK


def build_aigc_report(data: dict) -> bytes:
    """
    Generate professional AIGC detection report matching 维普/知网 format.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="AIGC检测报告",
        author="降AIGC检测平台",
    )
    styles = _build_styles()
    elements = []
    S = styles

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ============================================================
    # 1. REPORT HEADER
    # ============================================================
    elements.append(HRFlowable(width="100%", thickness=2, color=BLUE_DARK, spaceAfter=4 * mm))
    elements.append(Paragraph("AIGC 内容检测报告", S["report_title"]))
    elements.append(Paragraph(
        f"报告编号: AIGC-{datetime.now().strftime('%Y%m%d%H%M%S')}  |  "
        f"生成时间: {now}  |  "
        f"检测引擎: {data.get('provider', 'DeepSeek').upper()}",
        S["report_subtitle"],
    ))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_200, spaceAfter=4 * mm))

    # ============================================================
    # 2. OVERALL SCORE — gauge + level + confidence
    # ============================================================
    score = data.get("combined_score") or data.get("score", 0)
    confidence = data.get("confidence", "medium")
    level = data.get("level", "medium")

    gauge_table = Table([
        [
            ScoreGaugeFlowable(float(score), 90, 90),
            [
                Paragraph(f"<b>检测等级:</b> {_level_label(float(score))}风险 ({'AI生成概率较高' if float(score) >= 50 else 'AI生成概率较低'})", S["body"]),
                Paragraph(f"<b>置信度:</b> {confidence.upper() if confidence else 'MEDIUM'}", S["body"]),
                Paragraph(f"<b>检测模式:</b> {data.get('mode', 'general')}", S["body"]),
                Paragraph(f"<b>文本长度:</b> {data.get('char_count', 0)} 字符 / {data.get('paragraph_count', 1)} 段落", S["body"]),
                Paragraph(f"<b>检测耗时:</b> {data.get('detection_time_ms', 'N/A')}ms", S["body_small"]),
            ],
        ]
    ], colWidths=[110, 350])
    gauge_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(gauge_table)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_200, spaceBefore=4 * mm, spaceAfter=6 * mm))

    # ============================================================
    # 3. MULTI-DIMENSIONAL FEATURE ANALYSIS
    # ============================================================
    stat = data.get("statistical_analysis") or {}
    elements.append(Paragraph("2. 多维特征分析", S["section_title"]))

    if stat:
        features = [
            ("困惑度 (Perplexity)", stat.get("perplexity", 0),
             "文本可预测性。值越高越可能为AI生成"),
            ("句式突发度 (Burstiness)", stat.get("burstiness", 0),
             "句长变化程度。越均匀越可能为AI生成"),
            ("词汇多样性 (Lexical Diversity)", stat.get("lexical_diversity", 0),
             "用词重复度。多样性越低越可能为AI生成"),
            ("模板匹配度 (Template Hits)", min(100, (stat.get("template_hits", 0) or 0) * 12),
             f"匹配到 {stat.get('template_hits', 0)} 处AI常见表达模式"),
        ]

        feat_data = []
        for name, val, desc in features:
            v = float(val)
            feat_data.append([
                Paragraph(f"<b>{name}</b>", S["body_small"]),
                ColorBar(v, "", 140),
                Paragraph(desc, S["body_small"]),
            ])

        feat_table = Table(feat_data, colWidths=[110, 160, 190])
        feat_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(feat_table)

        # Stat details
        if stat.get("details"):
            elements.append(Paragraph("特征详情:", S["subsection_title"]))
            for detail in stat["details"][:5]:
                elements.append(Paragraph(f"  • {detail}", S["body_small"]))

    # ============================================================
    # 4. PARAGRAPH-LEVEL ANALYSIS
    # ============================================================
    paragraphs = data.get("paragraphs") or []
    if paragraphs and len(paragraphs) > 1:
        elements.append(Paragraph("3. 段落级分析", S["section_title"]))

        # Score distribution overview
        dist = data.get("score_distribution", {})
        elements.append(Paragraph(
            f"共检测 <b>{len(paragraphs)}</b> 个段落: "
            f"<font color='#059669'>低风险 {dist.get('low', 0)}</font> / "
            f"<font color='#f59e0b'>中风险 {dist.get('medium', 0)}</font> / "
            f"<font color='#dc2626'>高风险 {dist.get('high', 0)}</font>"
            + ("  ⚠ 检测到混合内容（部分AI生成）" if data.get("mixed_content") else ""),
            S["body"],
        ))

        # Paragraph table header
        para_rows = [[
            Paragraph("<b>#</b>", S["body_small"]),
            Paragraph("<b>段落内容预览</b>", S["body_small"]),
            Paragraph("<b>统计分</b>", S["body_small"]),
            Paragraph("<b>LLM分</b>", S["body_small"]),
            Paragraph("<b>综合</b>", S["body_small"]),
            Paragraph("<b>等级</b>", S["body_small"]),
        ]]

        for p in paragraphs[:30]:
            ps = float(p.get("fused_score", 0))
            preview = (p.get("text", "") or "")[:80]
            if len(p.get("text", "") or "") > 80:
                preview += "..."

            lvl = p.get("level", "low")
            if lvl == "high":
                lvl_color = RED_DARK
                lvl_bg = RED_LIGHT
            elif lvl == "medium":
                lvl_color = ORANGE_MID
                lvl_bg = ORANGE_LIGHT
            else:
                lvl_color = GREEN_DARK
                lvl_bg = GREEN_LIGHT

            para_rows.append([
                Paragraph(str(p.get("index", 0) + 1), S["body_small"]),
                Paragraph(preview, S["body_small"]),
                Paragraph(f"{p.get('stat_score', 0):.0f}", S["body_small"]),
                Paragraph(f"{p.get('llm_score', 0):.0f}" if p.get("llm_score") is not None else "—", S["body_small"]),
                Paragraph(f"<b>{ps:.0f}</b>", S["body_small"]),
                Paragraph(f"<font color='{lvl_color}'>{lvl}</font>", S["body_small"]),
            ])

        para_table = Table(para_rows, colWidths=[20, 245, 38, 38, 38, 38])
        para_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("BACKGROUND", (0, 0), (-1, 0), GRAY_50),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, GRAY_400),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, GRAY_200),
        ]))
        elements.append(para_table)

    # ============================================================
    # 5. SUSPICIOUS SEGMENTS
    # ============================================================
    segments = data.get("suspicious_segments") or []
    llm_analysis = data.get("analysis", "")

    if segments or llm_analysis:
        elements.append(Paragraph("4. 可疑内容标注", S["section_title"]))

        if llm_analysis:
            elements.append(Paragraph(f"<b>综合分析:</b> {llm_analysis}", S["body"]))

        for i, seg in enumerate(segments[:8]):
            seg_score = float(seg.get("score", 0))
            if seg_score >= 70:
                style = S["highlight_red"]
            elif seg_score >= 40:
                style = S["highlight_orange"]
            else:
                style = S["highlight_green"]

            elements.append(Paragraph(
                f"<b>#{i + 1}</b> [AIGC概率: {seg_score:.0f}%] "
                f"{seg.get('text', '')[:200]}",
                style,
            ))
            if seg.get("reason"):
                elements.append(Paragraph(
                    f"    判定依据: {seg['reason'][:150]}", S["body_small"]
                ))

    # ============================================================
    # 6. FUSION VERDICT
    # ============================================================
    fused = data.get("fused_result") or {}
    if fused:
        elements.append(Paragraph("5. 综合判定", S["section_title"]))

        verdict_rows = [
            ["检测维度", "评分", "说明"],
            ["LLM语义检测", f"{fused.get('llm_score', 0):.0f}%", "基于大语言模型的语义级AI痕迹识别"],
            ["统计分析", f"{fused.get('statistical_score', 0):.0f}%", "基于困惑度、句式、词汇等多维统计特征"],
            ["融合判定", f"<b>{fused.get('combined_score', 0):.0f}%</b>",
             f"置信度: {fused.get('confidence', 'medium').upper()}"],
        ]

        verdict_table = Table(verdict_rows, colWidths=[120, 100, 240])
        verdict_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, 0), GRAY_50),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, GRAY_400),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, GRAY_200),
        ]))
        elements.append(verdict_table)

        # Recommendation
        final_score = fused.get("combined_score", score)
        if float(final_score) >= 70:
            recommendation = (
                "<b>建议:</b> 该文本AI生成概率较高，建议进行人工复核。"
                "重点关注标注的高风险段落，确认是否存在过度依赖AI辅助写作的情况。"
            )
        elif float(final_score) >= 30:
            recommendation = (
                "<b>建议:</b> 该文本存在部分AI参与痕迹，建议对中高风险段落进行审查。"
                "可能为人工写作后经AI润色，或部分段落由AI生成。"
            )
        else:
            recommendation = (
                "<b>建议:</b> 该文本AI生成概率较低，整体呈现自然的人类写作特征。"
                "检测结果仅供参考，不排除经过深度人工修改的AI文本。"
            )
        elements.append(Paragraph(recommendation, S["body"]))

    # ============================================================
    # 7. METHODOLOGY + DISCLAIMER
    # ============================================================
    elements.append(Spacer(1, 12 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_200, spaceAfter=4 * mm))
    elements.append(Paragraph("检测方法说明", S["subsection_title"]))
    elements.append(Paragraph(
        "本报告采用多维度AIGC检测技术，结合以下方法进行综合判定:"
        "<br/>• <b>大语言模型语义分析:</b> 基于LLM的语义级AI痕迹识别，分析文本的逻辑结构、表达风格和模板化程度"
        "<br/>• <b>统计特征分析:</b> 基于N-gram困惑度、句式突发度(Burstiness)、词汇多样性(TTR)等统计指标"
        "<br/>• <b>模板模式匹配:</b> 检测常见AI生成文本的高频表达模式和过渡词使用"
        "<br/>• <b>加权融合判定:</b> LLM语义检测(60%) + 统计分析(40%)，加权综合得出最终评分",
        S["disclaimer"],
    ))
    elements.append(Paragraph(
        "<b>免责声明:</b> 本检测结果由自动化系统生成，仅供辅助参考，不构成对文本原创性的最终判定。"
        "检测准确率受文本类型、长度、语言风格等因素影响。对于重要的学术或商业决策，"
        "建议结合人工审查进行综合判断。检测结果不应作为任何形式的处罚或学术不端认定的唯一依据。",
        S["disclaimer"],
    ))

    # Footer
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.3, color=GRAY_200, spaceAfter=2 * mm))
    elements.append(Paragraph(
        f"降AIGC检测平台 · 报告自动生成于 {now} · 版本 2.0",
        S["footer"],
    ))

    doc.build(elements)
    buf.seek(0)
    return buf.read()


def build_report(data: dict) -> bytes:
    """Backward-compatible wrapper."""
    return build_aigc_report(data)
