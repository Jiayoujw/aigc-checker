from fastapi import APIRouter, HTTPException
from ..models.schemas import RewriteRequest, RewriteResponse
from ..services.rewriter import rewrite_text

router = APIRouter()


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite(req: RewriteRequest):
    try:
        result = await rewrite_text(req.text, req.provider)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"改写失败: {str(e)}")
