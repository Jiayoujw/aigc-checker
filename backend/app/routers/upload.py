import asyncio
import os
import tempfile
import time
import uuid
from fastapi import APIRouter, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..services.file_parser import parse_file

router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".docx", ".pdf"}

# In-memory progress store (use Redis in production)
_progress_store: dict[str, dict] = {}


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

    task_id = str(uuid.uuid4())
    t0 = time.time()

    # Stream to temp file — handles arbitrary file sizes without memory pressure.
    # SpooledTemporaryFile keeps data in memory up to 50MB, then spills to disk.
    suffix = ext if ext != ".pdf" else ".pdf"
    tmp = tempfile.SpooledTemporaryFile(
        max_size=50 * 1024 * 1024, suffix=suffix
    )
    total_read = 0
    chunk_size = 2 * 1024 * 1024  # 2MB chunks for fast throughput

    _progress_store[task_id] = {"stage": "upload", "progress": 0, "ts": time.time()}

    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_read += len(chunk)
            tmp.write(chunk)
            # Progress tracks upload phase only (0-50), parsing gets 50-100
            pct = min(49, total_read // (50 * 1024 * 1024) * 49) if total_read < 50 * 1024 * 1024 else 49
            _progress_store[task_id] = {"stage": "upload", "progress": pct, "size_mb": round(total_read / (1024 * 1024), 1), "ts": time.time()}
    except Exception:
        tmp.close()
        raise HTTPException(status_code=500, detail="文件上传中断")

    _progress_store[task_id] = {"stage": "parsing", "progress": 50, "ts": time.time()}

    def on_progress(pct: int):
        _progress_store[task_id] = {"stage": "parsing", "progress": 50 + pct // 2, "ts": time.time()}

    try:
        # For PDFs, parse from file path (PyMuPDF supports streaming from disk).
        # For other formats, read back into memory (they're small by nature).
        if ext == ".pdf":
            tmp_path = tmp.name if hasattr(tmp, 'name') else None
            if tmp_path and os.path.exists(tmp_path):
                text = await parse_file(file.filename, None, on_progress=on_progress, file_path=tmp_path)
            else:
                tmp.seek(0)
                content = tmp.read()
                text = await parse_file(file.filename, content, on_progress=on_progress)
        else:
            tmp.seek(0)
            content = tmp.read()
            text = await parse_file(file.filename, content, on_progress=on_progress)

        elapsed = time.time() - t0
        _progress_store[task_id] = {"stage": "done", "progress": 100, "ts": time.time()}

        return {
            "text": text,
            "filename": file.filename,
            "length": len(text),
            "task_id": task_id,
            "size_mb": round(total_read / (1024 * 1024), 1),
            "parse_time_ms": round(elapsed * 1000),
        }
    except Exception as e:
        _progress_store[task_id] = {"stage": "error", "progress": 0, "ts": time.time()}
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
    finally:
        tmp.close()


@router.get("/upload/progress/{task_id}")
async def upload_progress(task_id: str, request: Request):
    """SSE endpoint for real-time upload + parse progress."""

    async def event_stream():
        while True:
            if await request.is_disconnected():
                break

            info = _progress_store.get(task_id, {"stage": "unknown", "progress": 0})
            import json
            yield f"data: {json.dumps(info)}\n\n"

            if info["stage"] in ("done", "error"):
                await asyncio.sleep(1)
                break

            await asyncio.sleep(0.3)

        _progress_store.pop(task_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
