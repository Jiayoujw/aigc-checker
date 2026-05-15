import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import RewriteRequest, RewriteResponse, RewriteV2Request, RewriteV2Response
from ..services.rewriter import rewrite_text
from ..services.rewriter_v2 import rewrite_targeted
from ..services.auth_service import get_current_user
from ..db.database import get_db
from ..db.models import User
from .history import save_history

router = APIRouter()


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite(
    req: RewriteRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await rewrite_text(
            req.text, req.provider, req.intensity, req.preserve_terms
        )
        if user:
            await save_history(
                user.id,
                "rewrite",
                req.text,
                json.dumps(result, ensure_ascii=False),
                db,
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"改写失败: {str(e)}")


@router.post("/rewrite-v2", response_model=RewriteV2Response)
async def rewrite_v2(
    req: RewriteV2Request,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Targeted anti-CNKI rewriting with closed-loop refinement.
    1. Scans CNKI features to identify high-risk dimensions
    2. Generates dimension-specific rewrite instructions
    3. Rewrites → re-detects → re-rewrites (up to 3 rounds)
    4. Returns before/after scores with per-dimension breakdown
    """
    try:
        result = await rewrite_targeted(
            text=req.text,
            provider=req.provider,
            intensity=req.intensity,
            target_score=req.target_score,
            max_rounds=req.max_rounds,
            mode=req.mode,
        )

        response = RewriteV2Response(
            rewritten_text=result.rewritten_text,
            original_score=result.original_score,
            new_score=result.new_score,
            rounds=result.rounds,
            score_improvement=result.score_improvement,
            changes_summary=result.changes_summary,
            triggered_dimensions=result.triggered_dimensions,
            dimension_scores_before=result.dimension_scores_before,
            dimension_scores_after=result.dimension_scores_after,
        )

        if user:
            await save_history(
                user.id, "rewrite", req.text,
                json.dumps(response.model_dump(), ensure_ascii=False), db,
            )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"改写失败: {str(e)}")
