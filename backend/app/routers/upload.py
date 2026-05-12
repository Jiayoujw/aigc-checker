from fastapi import APIRouter, UploadFile, HTTPException

from ..services.file_parser import parse_file

router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".docx", ".pdf"}


@router.post("/upload")
async def upload_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未指定文件名")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持 .txt, .docx, .pdf",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

    try:
        text = await parse_file(file.filename, content)
        return {"text": text, "filename": file.filename, "length": len(text)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
