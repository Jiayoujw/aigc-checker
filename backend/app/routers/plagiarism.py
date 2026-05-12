import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import PlagiarismRequest, PlagiarismResponse
from ..services.plagiarism_checker import check_plagiarism
from ..services.auth_service import get_current_user
from ..db.database import get_db
from ..db.models import User
from .history import save_history

router = APIRouter()


@router.post("/check-plagiarism", response_model=PlagiarismResponse)
async def plagiarism_check(
    req: PlagiarismRequest,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await check_plagiarism(req.text)
        if user:
            await save_history(
                user.id,
                "plagiarism",
                req.text,
                json.dumps(result, ensure_ascii=False),
                db,
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查重检测失败: {str(e)}")
