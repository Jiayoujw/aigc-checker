from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db.database import get_db
from ..db.models import HistoryRecord, RecordType
from ..services.auth_service import require_user, get_current_user
from ..db.models import User

router = APIRouter()


@router.get("/history")
async def get_history(
    record_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(HistoryRecord).where(HistoryRecord.user_id == user.id)
    if record_type and record_type in ("detect", "rewrite"):
        query = query.where(HistoryRecord.record_type == RecordType(record_type))

    query = query.order_by(HistoryRecord.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return [
        {
            "id": r.id,
            "type": r.record_type.value,
            "input_text": r.input_text[:200] + ("..." if len(r.input_text) > 200 else ""),
            "result_json": r.result_json,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.delete("/history/{record_id}")
async def delete_history(
    record_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(HistoryRecord).where(
            HistoryRecord.id == record_id, HistoryRecord.user_id == user.id
        )
    )
    await db.commit()
    return {"ok": True}


async def save_history(
    user_id: str,
    record_type: str,
    input_text: str,
    result_json: str,
    db: AsyncSession,
):
    record = HistoryRecord(
        user_id=user_id,
        record_type=RecordType(record_type),
        input_text=input_text,
        result_json=result_json,
    )
    db.add(record)
    await db.commit()
