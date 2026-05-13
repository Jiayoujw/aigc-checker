"""
User API Key management — 企业级功能.
Users can bring their own DeepSeek/OpenAI API keys for detection.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..db.models import User, ApiKey
from ..services.auth_service import require_user, get_current_user

router = APIRouter()


class ApiKeyCreate(BaseModel):
    provider: str = Field(..., pattern="^(deepseek|openai)$")
    key: str = Field(..., min_length=10, max_length=255)
    label: str = Field(default="", max_length=100)


class ApiKeyResponse(BaseModel):
    id: str
    provider: str
    key_prefix: str
    label: str
    created_at: str


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_keys(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            provider=k.provider,
            key_prefix=f"{k.key[:8]}...{k.key[-4:]}",
            label=k.label or "",
            created_at=k.created_at.isoformat() if k.created_at else "",
        )
        for k in keys
    ]


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_key(
    req: ApiKeyCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    # Check existing keys count (limit to 10 per user)
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id)
    )
    if len(result.scalars().all()) >= 10:
        raise HTTPException(status_code=400, detail="最多保存10个API Key")

    key = ApiKey(
        user_id=user.id,
        provider=req.provider,
        key=req.key,
        label=req.label or "",
    )
    db.add(key)
    await db.commit()
    return {"ok": True, "id": key.id}


@router.delete("/api-keys/{key_id}")
async def delete_key(
    key_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    await db.commit()
    return {"ok": True}
