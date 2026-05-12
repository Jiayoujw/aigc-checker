from fastapi import APIRouter, HTTPException
from ..models.schemas import DetectRequest, DetectResponse
from ..services.aigc_detector import detect_aigc

router = APIRouter()


@router.post("/detect-aigc", response_model=DetectResponse)
async def detect(req: DetectRequest):
    try:
        result = await detect_aigc(req.text, req.provider)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AIGC检测失败: {str(e)}")
