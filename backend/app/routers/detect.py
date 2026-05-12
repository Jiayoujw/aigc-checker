import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import DetectRequest, DetectResponse
from ..services.aigc_detector import detect_aigc
from ..services.auth_service import get_current_user, require_user
from ..db.database import get_db
from ..db.models import User
from .history import save_history

router = APIRouter()


@router.post("/detect-aigc", response_model=DetectResponse)
async def detect(
    req: DetectRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await detect_aigc(req.text, req.provider)
        if user:
            await save_history(
                user.id, "detect", req.text, json.dumps(result, ensure_ascii=False), db
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AIGC检测失败: {str(e)}")
