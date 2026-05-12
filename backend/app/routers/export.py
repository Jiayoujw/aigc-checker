from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any

from ..services.report_generator import build_report

router = APIRouter()


class ExportRequest(BaseModel):
    type: str = "detect"
    score: float = 0
    analysis: str = ""
    suspicious_segments: list[dict] = []
    similarity_score: float | None = None
    details: str = ""
    rewritten_text: str = ""
    changes_summary: str = ""


@router.post("/export-report")
async def export_report(req: ExportRequest):
    try:
        from datetime import datetime

        data = req.model_dump()
        data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
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
