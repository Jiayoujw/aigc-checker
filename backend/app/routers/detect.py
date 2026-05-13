import json
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import DetectRequest
from ..services.aigc_detector import detect_aigc
from ..services.statistical_detector import analyze_statistical, fuse_scores
from ..services.paragraph_detector import analyze_paragraphs
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
