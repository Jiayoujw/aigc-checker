import json
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import DetectRequest, CNKIDetectRequest
from ..services.aigc_detector import detect_aigc
from ..services.statistical_detector import analyze_statistical, fuse_scores
from ..services.paragraph_detector import analyze_paragraphs
from ..services.cnki_classifier import predict_cnki_score
from ..services.info_diff_detector import detect_by_info_diff
from ..services.weipu_feature_scanner import scan_weipu_features
from ..services.wanfang_feature_scanner import scan_wanfang_features
from ..services.platform_detector import detect_all_platforms
from ..services.auth_service import get_current_user
from ..db.database import get_db
from ..db.models import User
from .history import save_history

router = APIRouter()


@router.post("/detect-aigc")
async def detect(
    req: DetectRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        t0 = time.time()

        text_len = len(req.text)

        # For long texts (> 500 chars, multiple paragraphs), use paragraph-level analysis
        # For short texts, use the original single-pass approach
        if text_len > 500 and req.text.count('\n\n') >= 1:
            report = await analyze_paragraphs(req.text, req.provider, req.mode)

            # Build comprehensive response
            result = {
                "score": report.overall_score,
                "level": report.overall_level,
                "confidence": report.confidence,
                "mixed_content": report.mixed_content,
                "paragraph_count": report.paragraph_count,
                "score_distribution": report.score_distribution,
                "paragraphs": [
                    {
                        "index": p.index,
                        "text": p.text,
                        "char_count": p.char_count,
                        "stat_score": p.stat_score,
                        "llm_score": p.llm_score,
                        "fused_score": p.fused_score,
                        "level": p.level,
                        "stat_details": p.stat_details,
                    }
                    for p in report.paragraphs
                ],
                "suspicious_segments": [
                    {
                        "text": p.text[:200] + ("..." if len(p.text) > 200 else ""),
                        "score": p.fused_score,
                        "reason": "; ".join(p.stat_details[:2]) if p.stat_details else "多维分析检测到AI特征",
                    }
                    for p in report.paragraphs if p.fused_score >= 50
                ][:5],
                "analysis": (
                    f"段落级深度分析完成。共检测{report.paragraph_count}个段落，"
                    f"综合AIGC概率{report.overall_score:.0f}%（{report.overall_level}风险）。"
                    + (f"检测到混合内容：文本中同时存在AI生成和人工写作特征。" if report.mixed_content else "")
                ),
                "detection_time_ms": report.detection_time_ms,
                "provider": req.provider,
                "mode": req.mode,
            }
        else:
            # Short text: single-pass LLM + statistical fusion
            llm_result = await detect_aigc(req.text, req.provider, req.mode)
            stat_result = analyze_statistical(req.text)
            fused = fuse_scores(llm_result["score"], stat_result.score)

            result = {
                **llm_result,
                "statistical_analysis": {
                    "score": stat_result.score,
                    "perplexity": stat_result.perplexity,
                    "burstiness": stat_result.burstiness,
                    "template_hits": stat_result.template_hits,
                    "lexical_diversity": stat_result.lexical_diversity,
                    "sentence_count": stat_result.sentence_count,
                    "avg_sentence_len": stat_result.avg_sentence_len,
                    "sentence_len_std": stat_result.sentence_len_std,
                    "details": stat_result.details,
                },
                "fused_result": fused,
                "detection_time_ms": round((time.time() - t0) * 1000),
                "provider": req.provider,
                "mode": req.mode,
            }

        if user:
            await save_history(
                user.id, "detect", req.text,
                json.dumps(result, ensure_ascii=False), db,
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AIGC检测失败: {str(e)}")


@router.post("/detect-cnki")
async def detect_cnki(
    req: CNKIDetectRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    CNKI-style AIGC detection using 8-dimension feature scanner.
    Predicts what CNKI's AIGC detection score would be for this text.
    """
    try:
        t0 = time.time()
        result = predict_cnki_score(req.text, mode=req.mode, discipline=req.discipline)

        result["detection_time_ms"] = round((time.time() - t0) * 1000)

        if user:
            await save_history(
                user.id, "detect", req.text,
                json.dumps(result, ensure_ascii=False), db,
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CNKI检测失败: {str(e)}")


@router.post("/detect-info-diff")
async def detect_info_diff(
    req: CNKIDetectRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Information-difference AIGC detection (CNKI patent CN119357388A method).
    Generates rewritten variants and measures info change.
    """
    try:
        t0 = time.time()
        report = await detect_by_info_diff(
            req.text,
            provider=req.provider,
            discipline=req.discipline or "general",
        )

        result = {
            "info_diff_score": report.normalized_score,
            "level": report.level,
            "confidence": report.confidence,
            "info_diff": report.info_diff,
            "original_info": report.original_info,
            "variant_infos": report.variant_infos,
            "mean_variant_composite": report.mean_variant_composite,
            "detail": report.detail,
            "detection_time_ms": round((time.time() - t0) * 1000),
        }

        if user:
            await save_history(
                user.id, "detect", req.text,
                json.dumps(result, ensure_ascii=False), db,
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"信息量差值检测失败: {str(e)}")


@router.post("/detect-weipu")
async def detect_weipu(
    req: CNKIDetectRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Weipu-style AIGC detection using 9-signal sentence-level scanner.
    维普使用句子级微观扫描(150-200字窗口)，检测粒度比知网更细，标准更严格。
    """
    try:
        t0 = time.time()
        report = scan_weipu_features(req.text, mode=req.mode, discipline=req.discipline)

        result = {
            "weipu_score": report.overall_weipu_score,
            "level": report.level,
            "signals": [
                {
                    "signal_id": s.signal_id,
                    "name": s.name,
                    "severity": s.severity,
                    "score": s.score,
                    "detail": s.detail,
                }
                for s in report.signals
            ],
            "sentence_analysis": {
                "count": report.sentence_analysis.sentence_count,
                "mean_len": report.sentence_analysis.mean_len,
                "length_cv": report.sentence_analysis.length_cv,
                "consecutive_similar": report.sentence_analysis.consecutive_similar_count,
                "long_sentence_ratio": report.sentence_analysis.long_sentence_ratio,
                "adj_diff_cv": report.sentence_analysis.adj_diff_cv,
                "detail": report.sentence_analysis.detail,
            },
            "high_risk_signals": report.high_risk_signals,
            "rewrite_suggestions": report.rewrite_suggestions,
            "detection_time_ms": round((time.time() - t0) * 1000),
        }

        if user:
            await save_history(
                user.id, "detect", req.text,
                json.dumps(result, ensure_ascii=False), db,
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"维普检测失败: {str(e)}")


@router.post("/detect-wanfang")
async def detect_wanfang(
    req: CNKIDetectRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Wanfang-style AIGC detection focusing on content substance and innovation.
    万方侧重内容创新性分析，关注语言+内容+计算三大特征类别。
    """
    try:
        t0 = time.time()
        report = scan_wanfang_features(req.text, mode=req.mode, discipline=req.discipline)

        result = {
            "wanfang_score": report.overall_wanfang_score,
            "level": report.level,
            "level_label": report.level_label,
            "language_features": {
                "connector_density": report.language.connector_density,
                "sentence_pattern_variety": report.language.sentence_pattern_variety,
                "expression_flexibility": report.language.expression_flexibility,
                "score": report.language.score,
                "detail": report.language.detail,
            },
            "content_features": {
                "innovation_score": report.content.innovation_score,
                "logic_depth_score": report.content.logic_depth_score,
                "subjectivity_score": report.content.subjectivity_score,
                "score": report.content.score,
                "detail": report.content.detail,
            },
            "computational_features": {
                "char_optimality": report.computational.char_optimality,
                "collocation_perfection": report.computational.collocation_perfection,
                "perplexity_score": report.computational.perplexity_score,
                "score": report.computational.score,
                "detail": report.computational.detail,
            },
            "high_risk_categories": report.high_risk_categories,
            "rewrite_suggestions": report.rewrite_suggestions,
            "detection_time_ms": round((time.time() - t0) * 1000),
        }

        if user:
            await save_history(
                user.id, "detect", req.text,
                json.dumps(result, ensure_ascii=False), db,
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"万方检测失败: {str(e)}")


@router.post("/detect-all-platforms")
async def detect_all_platforms_endpoint(
    req: CNKIDetectRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cross-platform AIGC detection: CNKI + Weipu + Wanfang comparison.
    Runs all three platform detectors in parallel and produces a comparison report.
    """
    try:
        t0 = time.time()
        report = await detect_all_platforms(
            req.text,
            mode=req.mode,
            discipline=req.discipline,
        )

        result = {
            "platforms": [
                {
                    "platform": p.platform,
                    "platform_label": p.platform_label,
                    "score": p.score,
                    "level": p.level,
                    "high_risk_items": p.high_risk_items,
                    "suggestions": p.suggestions,
                    "detection_time_ms": p.detection_time_ms,
                }
                for p in report.platforms
            ],
            "consensus_score": report.consensus_score,
            "score_range": list(report.score_range),
            "agreement_level": report.agreement_level,
            "strictest_platform": report.strictest_platform,
            "most_lenient_platform": report.most_lenient_platform,
            "unified_level": report.unified_level,
            "unified_suggestions": report.unified_rewrite_suggestions,
            "strategy_guide": report.strategy_guide,
            "total_time_ms": report.total_time_ms,
        }

        if user:
            await save_history(
                user.id, "detect", req.text,
                json.dumps(result, ensure_ascii=False), db,
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"多平台检测失败: {str(e)}")
