import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import RewriteRequest, RewriteResponse
from ..services.rewriter import rewrite_text
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
        result = await rewrite_text(req.text, req.provider)
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
