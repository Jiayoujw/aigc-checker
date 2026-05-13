from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any

from ..services.report_generator import build_report

router = APIRouter()


class ExportRequest(BaseModel):
    type: str = "detect"
    score: float = 0
    level: str = "medium"
    confidence: str = "medium"
    analysis: str = ""
    suspicious_segments: list[dict] = []
    statistical_analysis: dict | None = None
    fused_result: dict | None = None
    paragraphs: list[dict] | None = None
    paragraph_count: int = 0
    score_distribution: dict | None = None
    mixed_content: bool = False
    char_count: int = 0
    detection_time_ms: float = 0
    mode: str = "general"
    provider: str = "auto"
    # Rewrite fields
    rewritten_text: str = ""
    changes_summary: str = ""


@router.post("/export-report")
async def export_report(req: ExportRequest):
    try:
        from datetime import datetime

        data = req.model_dump()
        data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Map common fields for report generator
        if req.fused_result and not data.get("combined_score"):
            data["combined_score"] = req.fused_result.get("combined_score", req.score)
        pdf_bytes = build_report(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="aigc-report-{datetime.now().strftime("%Y%m%d-%H%M%S")}.pdf"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
