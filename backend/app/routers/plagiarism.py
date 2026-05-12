from fastapi import APIRouter, HTTPException
from ..models.schemas import PlagiarismRequest, PlagiarismResponse
from ..services.plagiarism_checker import check_plagiarism

router = APIRouter()


@router.post("/check-plagiarism", response_model=PlagiarismResponse)
async def plagiarism_check(req: PlagiarismRequest):
    try:
        result = await check_plagiarism(req.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查重检测失败: {str(e)}")
