"""Credit/Points system router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.credit_service import (
    get_user_stats,
    check_detect_quota,
    check_rewrite_quota,
    add_credits,
)
from ..services.auth_service import get_current_user
from ..db.database import get_db
from ..db.models import User

router = APIRouter()


@router.get("/credits/stats")
async def credits_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user credit/usage statistics."""
    try:
        stats = await get_user_stats(user.id, db)
        quota = await check_detect_quota(user.id, db)
        return {**stats, "daily_detect_total": quota["daily_free_total"]}
    except Exception as e:
        return {"error": str(e)}


@router.get("/credits/quota")
async def credits_quota(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check user's current quota for both detection and rewrite."""
    detect_quota = await check_detect_quota(user.id, db)
    rewrite_quota = await check_rewrite_quota(user.id, db)
    return {
        "detect": detect_quota,
        "rewrite": rewrite_quota,
    }


@router.post("/credits/add")
async def credits_add(
    amount: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add credits (purchase simulation / admin bonus)."""
    if amount <= 0 or amount > 1000:
        return {"success": False, "reason": "invalid_amount"}
    return await add_credits(user.id, amount, db)
