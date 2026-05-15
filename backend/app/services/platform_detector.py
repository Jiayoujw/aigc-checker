"""
Unified 3-Platform AIGC Detection Comparison.

Runs CNKI, Weipu, and Wanfang detection simultaneously and produces:
  - Per-platform scores with dimension/signal breakdown
  - Cross-platform consensus analysis
  - Unified rewrite recommendations (targeting all 3 platforms)
  - Platform-specific strategy guide

The three platforms detect the same underlying statistical fingerprints
but with different weights, thresholds, and granularity:
  - CNKI: paragraph-level, prefers precision (avoids false positives)
  - Weipu: sentence-level, prefers recall (avoids false negatives) — strictest
  - Wanfang: content-focused, emphasizes innovation/lack of substance
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Literal

from .cnki_feature_scanner import scan_cnki_features, CNKIFeatureReport
from .weipu_feature_scanner import scan_weipu_features, WeipuFeatureReport
from .wanfang_feature_scanner import scan_wanfang_features, WanfangFeatureReport


@dataclass
class PlatformResult:
    platform: str
    platform_label: str
    score: float
    level: str
    high_risk_items: list[str]
    suggestions: list[str]
    detection_time_ms: float


@dataclass
class CrossPlatformReport:
    platforms: list[PlatformResult]
    consensus_score: float  # weighted average
    score_range: tuple[float, float]  # (min, max) across platforms
    agreement_level: str  # "high" / "medium" / "low"
    strictest_platform: str
    most_lenient_platform: str
    unified_level: str
    unified_rewrite_suggestions: list[str]
    strategy_guide: str
    total_time_ms: float


async def detect_all_platforms(
    text: str,
    mode: str = "general",
    discipline: str | None = None,
    include_weipu: bool = True,
    include_wanfang: bool = True,
) -> CrossPlatformReport:
    """
    Run AIGC detection across CNKI + Weipu + Wanfang in parallel.
    Produces a comprehensive cross-platform comparison report.
    """
    t0 = time.time()

    async def run_cnki():
        t = time.time()
        report = scan_cnki_features(text, mode=mode, discipline=discipline)
        return PlatformResult(
            platform="cnki",
            platform_label="知网",
            score=report.overall_cnki_score,
            level=report.level,
            high_risk_items=report.high_risk_dimensions,
            suggestions=report.rewrite_suggestions,
            detection_time_ms=round((time.time() - t) * 1000),
        )

    async def run_weipu():
        t = time.time()
        report = scan_weipu_features(text, mode=mode, discipline=discipline)
        return PlatformResult(
            platform="weipu",
            platform_label="维普",
            score=report.overall_weipu_score,
            level=report.level,
            high_risk_items=report.high_risk_signals,
            suggestions=report.rewrite_suggestions,
            detection_time_ms=round((time.time() - t) * 1000),
        )

    async def run_wanfang():
        t = time.time()
        report = scan_wanfang_features(text, mode=mode, discipline=discipline)
        return PlatformResult(
            platform="wanfang",
            platform_label="万方",
            score=report.overall_wanfang_score,
            level=report.level,
            high_risk_items=report.high_risk_categories,
            suggestions=report.rewrite_suggestions,
            detection_time_ms=round((time.time() - t) * 1000),
        )

    # Run all in parallel
    tasks = [run_cnki()]
    if include_weipu:
        tasks.append(run_weipu())
    if include_wanfang:
        tasks.append(run_wanfang())

    results: list[PlatformResult] = await asyncio.gather(*tasks)

    # Compute cross-platform statistics
    scores = [r.score for r in results]
    consensus = round(sum(scores) / len(scores), 1) if scores else 0
    score_range = (min(scores), max(scores)) if scores else (0, 0)

    # Agreement level
    score_diff = score_range[1] - score_range[0]
    if score_diff < 12:
        agreement = "high"
    elif score_diff < 25:
        agreement = "medium"
    else:
        agreement = "low"

    # Strictest and most lenient
    sorted_platforms = sorted(results, key=lambda r: r.score)
    strictest = sorted_platforms[-1].platform_label  # highest score = strictest
    most_lenient = sorted_platforms[0].platform_label

    # Unified level
    if consensus >= 70:
        unified_level = "high"
    elif consensus >= 30:
        unified_level = "medium"
    else:
        unified_level = "low"

    # Unified rewrite suggestions (deduplicated across platforms)
    all_suggestions = []
    seen = set()
    for r in results:
        for s in r.suggestions:
            key = s[:30]
            if key not in seen:
                all_suggestions.append(s)
                seen.add(key)

    # Strategy guide
    strategy_guide = _build_strategy_guide(results)

    return CrossPlatformReport(
        platforms=results,
        consensus_score=consensus,
        score_range=score_range,
        agreement_level=agreement,
        strictest_platform=strictest,
        most_lenient_platform=most_lenient,
        unified_level=unified_level,
        unified_rewrite_suggestions=all_suggestions[:10],
        strategy_guide=strategy_guide,
        total_time_ms=round((time.time() - t0) * 1000),
    )


def _build_strategy_guide(results: list[PlatformResult]) -> str:
    """Build platform-specific strategy guidance based on results."""
    parts = []

    for r in results:
        if r.level == "high" or r.score >= 70:
            if r.platform == "cnki":
                parts.append(
                    "【知网策略】重点提升全文整体人类写作感。打散连续AI段落，"
                    "利用致谢、研究展望等自写部分拉低总分。减少全文模板化表达，"
                    "增加个性化观点。"
                )
            elif r.platform == "weipu":
                parts.append(
                    "【维普策略】需逐段甚至逐句检查，不能有任何一段'放水'。"
                    "重点打破连续3句以上的相似句式，制造短-长-短交替节奏。"
                    "在适当位置加入口语化表达和个人感受。特别注意维普检测范围"
                    "含表格和脚注内容。"
                )
            elif r.platform == "wanfang":
                parts.append(
                    "【万方策略】重点提升内容创新性。增加独特分析视角，"
                    "避免纯罗列已有知识。加入深层剖析('究其原因''这意味着')。"
                    "增加个人主观判断和评价，减少浅层的事实陈述。"
                )

    if not parts:
        parts.append("当前文本在各平台检测均为低风险，无需特殊处理。")

    return "\n\n".join(parts)
