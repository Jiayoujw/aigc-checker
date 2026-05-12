from fastapi import APIRouter, HTTPException
from ..models.schemas import DetectRequest
from ..services.detector_compare import detect_compare

router = APIRouter()


@router.post("/detect-compare")
async def detect_compare_endpoint(req: DetectRequest):
    try:
        result = await detect_compare(req.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比检测失败: {str(e)}")
