"""Calibration & Accuracy Dashboard router."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.calibration_service import submit_feedback, get_calibration_stats
from ..services.accuracy_service import get_dashboard_data, get_error_distribution
from ..services.auth_service import get_current_user
from ..db.database import get_db
from ..db.models import User

router = APIRouter()


class FeedbackRequest(BaseModel):
    platform: str = Field(..., pattern="^(cnki|weipu|wanfang)$")
    our_predicted_score: float = Field(..., ge=0, le=100)
    real_score: float = Field(..., ge=0, le=100)
    input_text: str = Field(..., min_length=50, max_length=5000)
    mode: str = Field(default="general")


@router.post("/calibration/feedback")
async def submit_calibration_feedback(
    req: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a real platform AIGC score for model calibration.

    This is THE critical endpoint. Every user submission improves our
    detection accuracy. Users get +1 credit for each feedback.
    """
    try:
        result = await submit_feedback(
            user_id=user.id,
            platform=req.platform,
            our_predicted_score=req.our_predicted_score,
            real_score=req.real_score,
            input_text=req.input_text,
            mode=req.mode,
            db=db,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {str(e)}")


@router.get("/calibration/stats")
async def calibration_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get global calibration statistics (no auth required)."""
    return await get_calibration_stats(db)


# ---- Public Accuracy Dashboard (no auth required — builds trust) ----

@router.get("/accuracy/dashboard")
async def accuracy_dashboard(
    db: AsyncSession = Depends(get_db),
):
    """
    Public accuracy dashboard.
    Shows real-time MAE, total calibration samples, and SpeedAI comparison.
    No authentication required — transparency builds trust.
    """
    return await get_dashboard_data(db)


@router.get("/accuracy/error-distribution/{platform}")
async def error_distribution(
    platform: str,
    db: AsyncSession = Depends(get_db),
):
    """Get error distribution for a specific platform."""
    return await get_error_distribution(platform, db)
