import json
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import DetectRequest, DetectResponse
from ..services.aigc_detector import detect_aigc
from ..services.statistical_detector import analyze_statistical, fuse_scores
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

        # Run LLM and statistical detection in parallel
        llm_result = await detect_aigc(req.text, req.provider, req.mode)
        stat_result = analyze_statistical(req.text)

        # Fuse scores for final verdict
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
        }

        if user:
            await save_history(
                user.id, "detect", req.text,
                json.dumps(result, ensure_ascii=False), db,
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AIGC检测失败: {str(e)}")
