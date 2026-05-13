"""
Paragraph-level AIGC detection engine.

This is the core innovation that brings detection quality closer to 知网/维普:
- Splits text into paragraphs, analyzes each independently
- Produces per-paragraph scores + aggregate
- Identifies mixed AI/human content (partial generation)
- Enables heatmap visualization

Architecture:
  Paragraph → [Statistical Check] → [LLM Check if needed] → Score
  Aggregate → Weighted fusion → Confidence → Final verdict
"""

import re
import asyncio
from dataclasses import dataclass, field
from typing import Literal

from .statistical_detector import analyze_statistical, StatisticalResult
from .aigc_detector import detect_aigc


@dataclass
class ParagraphResult:
    index: int
    text: str
    char_count: int
    stat_score: float
    llm_score: float | None  # None if paragraph too short for LLM
    fused_score: float
    level: str  # low/medium/high
    stat_details: list[str] = field(default_factory=list)


@dataclass
class ParagraphReport:
    paragraphs: list[ParagraphResult]
    overall_score: float
    overall_level: str
    confidence: str  # high/medium/low
    score_distribution: dict  # {low: N, medium: N, high: N}
    mixed_content: bool  # True if both AI and human paragraphs detected
    total_chars: int
    paragraph_count: int
    detection_time_ms: float


def _split_paragraphs(text: str) -> list[str]:
    """Split text into meaningful paragraphs for analysis."""
    raw = re.split(r'\n\s*\n', text)
    result = []
    for p in raw:
        p = p.strip()
        if len(p) >= 30:
            # Further split very long paragraphs (over 1000 chars)
            if len(p) > 1000:
                sentences = re.split(r'(?<=[。！？])', p)
                chunk = ""
                for s in sentences:
                    if len(chunk) + len(s) > 800 and len(chunk) >= 30:
                        result.append(chunk.strip())
                        chunk = s
                    else:
                        chunk += s
                if len(chunk.strip()) >= 30:
                    result.append(chunk.strip())
            else:
                result.append(p)
        elif len(p) > 0:
            # Short paragraph — merge with next if possible
            result.append(p)

    return result


async def _analyze_paragraph(
    text: str,
    index: int,
    provider: str,
    mode: str,
    llm_threshold: int = 200,
) -> ParagraphResult:
    """Analyze a single paragraph: always run statistical, optionally run LLM."""
    stat: StatisticalResult = analyze_statistical(text)

    llm_score = None
    if len(text) >= llm_threshold:
        try:
            llm_result = await detect_aigc(text, provider, mode)
            llm_score = llm_result["score"]
        except Exception:
            llm_score = None

    # Fuse scores
    if llm_score is not None:
        fused = round(stat.score * 0.4 + llm_score * 0.6, 1)
    else:
        fused = stat.score

    if fused < 30:
        level = "low"
    elif fused < 70:
        level = "medium"
    else:
        level = "high"

    return ParagraphResult(
        index=index,
        text=text,
        char_count=len(text),
        stat_score=stat.score,
        llm_score=llm_score,
        fused_score=fused,
        level=level,
        stat_details=stat.details,
    )


async def analyze_paragraphs(
    text: str,
    provider: Literal["deepseek", "openai", "auto"] = "auto",
    mode: str = "general",
    max_concurrent: int = 3,
) -> ParagraphReport:
    """
    Full paragraph-level analysis pipeline.

    For short text (< 300 chars): single-pass detection.
    For long text: split into paragraphs, analyze each, aggregate.
    """
    import time
    t0 = time.time()

    paragraphs = _split_paragraphs(text)

    if not paragraphs:
        return ParagraphReport(
            paragraphs=[],
            overall_score=0,
            overall_level="low",
            confidence="low",
            score_distribution={"low": 0, "medium": 0, "high": 0},
            mixed_content=False,
            total_chars=len(text),
            paragraph_count=0,
            detection_time_ms=0,
        )

    # For very short single paragraph, just do one analysis
    if len(paragraphs) == 1 and len(paragraphs[0]) < 300:
        result = await _analyze_paragraph(paragraphs[0], 0, provider, mode)
        level_dist = {"low": 0, "medium": 0, "high": 0}
        level_dist[result.level] = 1
        return ParagraphReport(
            paragraphs=[result],
            overall_score=result.fused_score,
            overall_level=result.level,
            confidence="medium" if result.llm_score is not None else "low",
            score_distribution=level_dist,
            mixed_content=False,
            total_chars=len(text),
            paragraph_count=1,
            detection_time_ms=round((time.time() - t0) * 1000),
        )

    # Process paragraphs with concurrency limit
    sem = asyncio.Semaphore(max_concurrent)

    async def _bounded_analyze(text: str, index: int) -> ParagraphResult:
        async with sem:
            return await _analyze_paragraph(text, index, provider, mode)

    tasks = [_bounded_analyze(p, i) for i, p in enumerate(paragraphs)]
    results = await asyncio.gather(*tasks)

    # Aggregate
    total_chars = sum(r.char_count for r in results)
    if total_chars == 0:
        weighted_score = 0.0
    else:
        weighted_score = sum(r.fused_score * r.char_count for r in results) / total_chars

    weighted_score = round(weighted_score, 1)

    # Level distribution
    level_dist = {"low": 0, "medium": 0, "high": 0}
    for r in results:
        level_dist[r.level] += 1

    # Mixed content detection
    has_high = level_dist["high"] > 0
    has_low = level_dist["low"] > 0
    mixed = has_high and has_low

    # Overall level
    if weighted_score < 30:
        overall_level = "low"
    elif weighted_score < 70:
        overall_level = "medium"
    else:
        overall_level = "high"

    # Confidence based on agreement
    scores = [r.fused_score for r in results]
    if len(scores) >= 2:
        score_variance = sum((s - weighted_score) ** 2 for s in scores) / len(scores)
        if score_variance < 100:
            confidence = "high"
        elif score_variance < 400:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = "medium"

    return ParagraphReport(
        paragraphs=results,
        overall_score=weighted_score,
        overall_level=overall_level,
        confidence=confidence,
        score_distribution=level_dist,
        mixed_content=mixed,
        total_chars=total_chars,
        paragraph_count=len(results),
        detection_time_ms=round((time.time() - t0) * 1000),
    )
