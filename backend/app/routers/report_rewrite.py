"""Report upload + targeted rewrite router (SpeedAI "精准降AI")."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.report_parser import parse_report
from ..services.rewriter_v3 import rewrite_from_report
from ..services.credit_service import consume_rewrite, check_rewrite_quota
from ..services.auth_service import get_current_user
from ..db.database import get_db
from ..db.models import User
from .history import save_history

router = APIRouter()


class ReportParseRequest(BaseModel):
    report_text: str = Field(..., min_length=50, max_length=20000)
    platform_hint: str = Field(default="auto", pattern="^(auto|cnki|weipu|wanfang)$")


class ReportRewriteRequest(BaseModel):
    original_text: str = Field(..., min_length=50, max_length=50000)
    report_text: str = Field(..., min_length=50, max_length=20000)
    provider: str = Field(default="auto")
    intensity: str = Field(default="medium", pattern="^(light|medium|deep)$")
    platform_hint: str = Field(default="auto")


@router.post("/report/parse")
async def parse_detection_report(
    req: ReportParseRequest,
    user: User | None = Depends(get_current_user),
):
    """
    Parse an official CNKI/Weipu/Wanfang AIGC detection report.
    Extracts overall score, flagged sections, and metadata.
    No credits consumed — this is a utility endpoint.
    """
    try:
        report = parse_report(req.report_text, req.platform_hint)
        return {
            "platform": report.platform,
            "overall_score": report.overall_score,
            "overall_level": report.overall_level,
            "flagged_sections": [
                {
                    "text": s.text[:300],
                    "score": s.score,
                    "risk_level": s.risk_level,
                }
                for s in report.flagged_sections
            ],
            "flagged_count": len(report.flagged_sections),
            "parse_confidence": report.parse_confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告解析失败: {str(e)}")


@router.post("/rewrite-from-report")
async def rewrite_from_detection_report(
    req: ReportRewriteRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SpeedAI-style "精准降AI": upload original text + official detection report →
    extract flagged sections → rewrite only those sections → reassemble.

    This is more efficient than full-text rewrite and preserves the user's
    original writing in non-flagged sections.
    """
    # Check quota
    if user:
        quota = await check_rewrite_quota(user.id, db)
        if not quota["can_rewrite"]:
            raise HTTPException(
                status_code=402,
                detail=f"额度不足。每日免费剩余{quota['daily_free_remaining']}次，购买积分剩余{quota['purchased_credits']}分",
            )

    try:
        result = await rewrite_from_report(
            original_text=req.original_text,
            report_text=req.report_text,
            provider=req.provider,
            intensity=req.intensity,
            platform_hint=req.platform_hint,
        )

        response = {
            "rewritten_full_text": result.rewritten_full_text,
            "sections_rewritten": result.sections_rewritten,
            "sections_preserved": result.sections_preserved,
            "section_results": [
                {
                    "original_text": sr.original_text[:200] + ("..." if len(sr.original_text) > 200 else ""),
                    "rewritten_text": sr.rewritten_text[:200] + ("..." if len(sr.rewritten_text) > 200 else ""),
                    "original_score": sr.original_score,
                    "new_score": sr.new_score,
                    "improvement": sr.improvement,
                }
                for sr in result.section_results
            ],
            "original_overall_score": result.original_overall_score,
            "estimated_new_score": result.estimated_new_score,
            "changes_summary": result.changes_summary,
        }

        # Consume credit
        if user:
            await consume_rewrite(user.id, db)
            await save_history(
                user.id, "rewrite", req.original_text,
                json.dumps(response, ensure_ascii=False), db,
            )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告改写失败: {str(e)}")
