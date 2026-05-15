"""
CNKI / Weipu / Wanfang Report Parser.

Parses official AIGC detection reports to extract:
  - Overall AIGC score
  - Flagged/high-risk sections with text content
  - Per-section scores and risk levels
  - Detection metadata (date, version, etc.)

Supports:
  - PDF reports (CNKI, Weipu, Wanfang all output PDF)
  - HTML reports (some platforms provide web-based reports)
  - Plain text copy-paste from reports

This enables the "精准降AI" feature: upload report → auto-extract flagged
sections → rewrite only those sections → preserve everything else.
"""

import re
from dataclasses import dataclass, field


@dataclass
class FlaggedSection:
    """A section flagged by the official detection platform."""
    text: str
    score: float  # 0-100 AIGC probability assigned by the platform
    risk_level: str  # "high" / "medium" / "low"
    label: str = ""  # Optional label (e.g., "段落3", "第2章")
    page: int | None = None


@dataclass
class ParsedReport:
    """Structured data extracted from an official AIGC detection report."""
    platform: str  # "cnki" / "weipu" / "wanfang" / "unknown"
    overall_score: float | None  # Overall AIGC score (0-100)
    overall_level: str | None  # "low" / "medium" / "high"
    flagged_sections: list[FlaggedSection]
    raw_metadata: dict
    parse_confidence: float  # 0-1, how confident we are in the parsing


def parse_report(text: str, platform_hint: str = "auto") -> ParsedReport:
    """
    Parse a copy-pasted or OCR-extracted report text.

    Users can:
    1. Copy-paste text from a PDF report
    2. Copy-paste from the web version
    3. Upload a screenshot → OCR → paste text (future)

    Args:
        text: Raw text extracted from the report
        platform_hint: "cnki", "weipu", "wanfang", or "auto" for auto-detection
    """
    platform = _detect_platform(text, platform_hint)

    if platform == "cnki":
        return _parse_cnki_report(text)
    elif platform == "weipu":
        return _parse_weipu_report(text)
    elif platform == "wanfang":
        return _parse_wanfang_report(text)
    else:
        return _parse_generic_report(text)


def _detect_platform(text: str, hint: str) -> str:
    """Auto-detect which platform generated this report."""
    if hint != "auto":
        return hint

    text_lower = text.lower()
    if any(kw in text for kw in ["知网", "cnki", "中国知网", "aigc-check"]):
        return "cnki"
    if any(kw in text for kw in ["维普", "weipu", "vip", "vpcs", "泛语"]):
        return "weipu"
    if any(kw in text for kw in ["万方", "wanfang", "文察"]):
        return "wanfang"
    return "unknown"


def _parse_cnki_report(text: str) -> ParsedReport:
    """Parse a CNKI AIGC detection report."""
    flagged = []
    metadata = {}

    # Try to extract overall score
    # CNKI reports typically show: "AIGC检测结果: XX%" or similar
    score_patterns = [
        r'AIGC.*?(?:概率|得分|检测结果|综合判定).*?(\d{1,3})\s*[%％]',
        r'(?:AI|人工智能).*?(?:概率|比例|得分).*?(\d{1,3})\s*[%％]',
        r'(?:综合|总体|全文).*?(?:AI|AIGC).*?(\d{1,3})\s*[%％]',
        r'疑似.*?AI.*?(\d{1,3})\s*[%％]',
        r'(\d{1,3})\s*[%％].*?(?:AI|AIGC)',
    ]

    overall_score = None
    for pattern in score_patterns:
        match = re.search(pattern, text)
        if match:
            overall_score = float(match.group(1))
            metadata["score_source"] = pattern
            break

    # Extract flagged paragraphs
    # CNKI typically marks sections with scores
    # Look for patterns like: paragraph text followed by score
    section_patterns = [
        # "段落N: XX分" format
        r'(?:段落|第\s*\d+\s*段|片段)\s*\d*\s*[:：]\s*(\d{1,3})\s*[分%％].*?\n(.*?)(?=\n(?:段落|第\s*\d+\s*段|$))',
        # Score at end of paragraph
        r'(.{50,300}?)\s*[\[(（]\s*AI.*?(\d{1,3})\s*[%％分]\s*[\]）)]',
        # Highlighted text with risk level
        r'(?:高风险|中风险|低风险|疑似AI)[:：]?\s*(.{30,300}?)\s*(?:AI.*?)?(\d{1,3})\s*[%％]',
    ]

    for pattern in section_patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            score_val = None
            text_val = None
            groups = match.groups()
            if len(groups) >= 2:
                try:
                    score_val = float(groups[-1]) if groups[-1].strip().isdigit() else float(groups[-2]) if groups[-2].strip().isdigit() else None
                except (ValueError, IndexError):
                    continue
                text_val = groups[0] if groups[0].strip() else groups[1] if len(groups) > 1 else ""
            if score_val and text_val and len(text_val.strip()) > 10:
                level = "high" if score_val >= 70 else ("medium" if score_val >= 30 else "low")
                flagged.append(FlaggedSection(
                    text=text_val.strip()[:500],
                    score=score_val,
                    risk_level=level,
                ))

    # Determine level
    if overall_score:
        level = "high" if overall_score >= 70 else ("medium" if overall_score >= 30 else "low")
    else:
        level = None

    confidence = 0.7 if overall_score and flagged else (0.4 if overall_score else 0.2)

    return ParsedReport(
        platform="cnki",
        overall_score=overall_score,
        overall_level=level,
        flagged_sections=flagged[:20],
        raw_metadata=metadata,
        parse_confidence=confidence,
    )


def _parse_weipu_report(text: str) -> ParsedReport:
    """Parse a Weipu AIGC detection report."""
    flagged = []
    metadata = {}

    score_patterns = [
        r'(?:AIGC|AI).*?(?:检测|判定).*?结果.*?(\d{1,3})\s*[%％]',
        r'(?:综合|总体).*?(?:AIGC|AI).*?(\d{1,3})\s*[%％]',
        r'AI.*?率.*?(\d{1,3})\s*[%％]',
        r'(\d{1,3})\s*[%％].*?(?:AIGC|AI率)',
    ]

    overall_score = None
    for pattern in score_patterns:
        match = re.search(pattern, text)
        if match:
            overall_score = float(match.group(1))
            metadata["score_source"] = pattern
            break

    # Weipu marks sentence-level flagged content
    section_patterns = [
        r'(?:高风险|重点标记|疑似AI|句子\d+)[:：]\s*(.{20,300}?)\s*(?:AI.*?)?(\d{1,3})\s*[%％分]',
        r'(.{30,300}?)\s*[\[(（]\s*(?:AI|AIGC).*?(\d{1,3})\s*[%％分]\s*[\]）)]',
    ]

    for pattern in section_patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            groups = match.groups()
            if len(groups) >= 2:
                try:
                    score_val = float(groups[-1]) if groups[-1].strip().isdigit() else None
                except ValueError:
                    continue
                text_val = groups[0].strip() if groups[0].strip() else ""
                if score_val and len(text_val) > 10:
                    level = "high" if score_val >= 70 else ("medium" if score_val >= 30 else "low")
                    flagged.append(FlaggedSection(
                        text=text_val[:500],
                        score=float(score_val),
                        risk_level=level,
                    ))

    level = "high" if (overall_score and overall_score >= 70) else ("medium" if (overall_score and overall_score >= 30) else "low") if overall_score else None
    confidence = 0.65 if overall_score else 0.3

    return ParsedReport(
        platform="weipu",
        overall_score=overall_score,
        overall_level=level,
        flagged_sections=flagged[:20],
        raw_metadata=metadata,
        parse_confidence=confidence,
    )


def _parse_wanfang_report(text: str) -> ParsedReport:
    """Parse a Wanfang AIGC detection report."""
    flagged = []
    metadata = {}

    score_patterns = [
        r'(?:AIGC|AI).*?(?:检测|判定).*?(\d{1,3})\s*[%％]',
        r'(?:疑似|AI).*?比例.*?(\d{1,3})\s*[%％]',
        r'AI.*?可能性.*?(\d{1,3})\s*[%％]',
    ]

    overall_score = None
    for pattern in score_patterns:
        match = re.search(pattern, text)
        if match:
            overall_score = float(match.group(1))
            break

    # Wanfang uses color-coded highlighting: red (>85%), yellow (50-85%)
    section_patterns = [
        r'(?:显著疑似|一般疑似|红色|黄色|高亮).*?[:：]\s*(.{30,300}?)\s*(?:AI.*?)?(\d{1,3})\s*[%％]',
        r'(.{30,300}?)\s*[\[(（]\s*(?:疑似).*?(\d{1,3})\s*[%％]\s*[\]）)]',
    ]

    for pattern in section_patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            groups = match.groups()
            if len(groups) >= 2:
                try:
                    score_val = float(groups[-1]) if groups[-1].strip().isdigit() else None
                except ValueError:
                    continue
                text_val = groups[0].strip() if groups[0].strip() else ""
                if score_val and len(text_val) > 10:
                    level = "high" if score_val >= 85 else ("medium" if score_val >= 50 else "low")
                    flagged.append(FlaggedSection(
                        text=text_val[:500],
                        score=float(score_val),
                        risk_level=level,
                    ))

    level = "high" if (overall_score and overall_score >= 85) else ("medium" if (overall_score and overall_score >= 50) else "low") if overall_score else None
    confidence = 0.6 if overall_score else 0.3

    return ParsedReport(
        platform="wanfang",
        overall_score=overall_score,
        overall_level=level,
        flagged_sections=flagged[:20],
        raw_metadata=metadata,
        parse_confidence=confidence,
    )


def _parse_generic_report(text: str) -> ParsedReport:
    """Fallback parser: try to extract any score and flagged sections."""
    flagged = []
    overall_score = None

    # Look for any percentage near AIGC/AI keywords
    score_matches = re.findall(r'(\d{1,3})\s*[%％]', text)
    if score_matches:
        scores = [int(s) for s in score_matches if 0 <= int(s) <= 100]
        if scores:
            overall_score = float(max(scores))  # Usually the highest is the overall

    return ParsedReport(
        platform="unknown",
        overall_score=overall_score,
        overall_level=None,
        flagged_sections=flagged,
        raw_metadata={},
        parse_confidence=0.3 if overall_score else 0.1,
    )
