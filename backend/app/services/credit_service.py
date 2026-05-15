"""
Credit/Points System — Free Tier + Purchased Credits.

SpeedAI model:
  - Registration: 2500 points bonus
  - Daily: 5 free detections (no word limit)
  - Paid: 1.2 元/千字
  - Referral: bonus points for both parties
  - Activity: up to 30,000 bonus points

Our model (competitive):
  - Registration: 10 free credits (1 detect = 1 credit, 1 rewrite = 2 credits)
  - Daily: 5 free detections + 2 free rewrites (reset at midnight)
  - Paid credits: ¥0.8/千字 (beats SpeedAI's 1.2)
  - Referral bonus: +5 credits each
  - Public dashboard accuracy: builds trust
"""

from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import UserCredit


DAILY_FREE_DETECT = 5
DAILY_FREE_REWRITE = 2
REGISTRATION_BONUS = 10
REFERRAL_BONUS = 5
REWRITE_COST = 2  # credits per rewrite
DETECT_COST = 1   # credits per detection


async def get_or_create_credits(user_id: str, db: AsyncSession) -> UserCredit:
    """Get user credit record, creating it if it doesn't exist."""
    result = await db.execute(
        select(UserCredit).where(UserCredit.user_id == user_id)
    )
    credit = result.scalar_one_or_none()

    if credit is None:
        credit = UserCredit(
            user_id=user_id,
            daily_limit_detect=DAILY_FREE_DETECT,
            daily_limit_rewrite=DAILY_FREE_REWRITE,
            purchased_credits=REGISTRATION_BONUS,
            registration_bonus_claimed=True,
            last_daily_reset=datetime.utcnow(),
        )
        db.add(credit)
        await db.flush()

    # Check if daily limits need reset
    await _maybe_reset_daily(credit, db)
    return credit


async def _maybe_reset_daily(credit: UserCredit, db: AsyncSession):
    """Reset daily counters if it's a new day."""
    now = datetime.utcnow()
    last = credit.last_daily_reset

    if last.date() < now.date():
        credit.daily_detect_used = 0
        credit.daily_rewrite_used = 0
        credit.last_daily_reset = now
        await db.flush()


async def check_detect_quota(user_id: str, db: AsyncSession) -> dict:
    """Check if user can perform a detection. Returns quota info."""
    credit = await get_or_create_credits(user_id, db)

    daily_remaining = max(0, credit.daily_limit_detect - credit.daily_detect_used)
    total_available = daily_remaining + credit.purchased_credits

    can_detect = total_available >= DETECT_COST

    return {
        "can_detect": can_detect,
        "daily_free_remaining": daily_remaining,
        "daily_free_total": credit.daily_limit_detect,
        "purchased_credits": credit.purchased_credits,
        "total_available": total_available,
        "total_detections": credit.total_detections,
        "total_rewrites": credit.total_rewrites,
    }


async def check_rewrite_quota(user_id: str, db: AsyncSession) -> dict:
    """Check if user can perform a rewrite."""
    credit = await get_or_create_credits(user_id, db)

    daily_remaining = max(0, credit.daily_limit_rewrite - credit.daily_rewrite_used)
    total_available = daily_remaining + credit.purchased_credits // REWRITE_COST

    can_rewrite = total_available >= 1

    return {
        "can_rewrite": can_rewrite,
        "daily_free_remaining": daily_remaining,
        "daily_free_total": credit.daily_limit_rewrite,
        "purchased_credits": credit.purchased_credits,
        "total_available": total_available,
    }


async def consume_detect(user_id: str, db: AsyncSession) -> dict:
    """Consume 1 credit for a detection. Uses free daily first, then purchased."""
    credit = await get_or_create_credits(user_id, db)

    daily_remaining = max(0, credit.daily_limit_detect - credit.daily_detect_used)

    if daily_remaining > 0:
        credit.daily_detect_used += 1
        source = "daily_free"
    elif credit.purchased_credits >= DETECT_COST:
        credit.purchased_credits -= DETECT_COST
        source = "purchased"
    else:
        return {"success": False, "reason": "insufficient_credits"}

    credit.total_detections += 1
    await db.flush()

    return {
        "success": True,
        "source": source,
        "remaining_daily_free": max(0, credit.daily_limit_detect - credit.daily_detect_used),
        "remaining_purchased": credit.purchased_credits,
    }


async def consume_rewrite(user_id: str, db: AsyncSession) -> dict:
    """Consume credits for a rewrite."""
    credit = await get_or_create_credits(user_id, db)

    daily_remaining = max(0, credit.daily_limit_rewrite - credit.daily_rewrite_used)

    if daily_remaining > 0:
        credit.daily_rewrite_used += 1
        source = "daily_free"
    elif credit.purchased_credits >= REWRITE_COST:
        credit.purchased_credits -= REWRITE_COST
        source = "purchased"
    else:
        return {"success": False, "reason": "insufficient_credits"}

    credit.total_rewrites += 1
    await db.flush()

    return {
        "success": True,
        "source": source,
        "remaining_daily_free": max(0, credit.daily_limit_rewrite - credit.daily_rewrite_used),
        "remaining_purchased": credit.purchased_credits,
    }


async def add_credits(user_id: str, amount: int, db: AsyncSession) -> dict:
    """Add purchased or bonus credits."""
    credit = await get_or_create_credits(user_id, db)
    credit.purchased_credits += amount
    await db.flush()
    return {
        "success": True,
        "added": amount,
        "total_purchased": credit.purchased_credits,
    }


async def get_user_stats(user_id: str, db: AsyncSession) -> dict:
    """Get user usage statistics for dashboard."""
    credit = await get_or_create_credits(user_id, db)
    return {
        "daily_detect_remaining": max(0, credit.daily_limit_detect - credit.daily_detect_used),
        "daily_rewrite_remaining": max(0, credit.daily_limit_rewrite - credit.daily_rewrite_used),
        "purchased_credits": credit.purchased_credits,
        "total_detections": credit.total_detections,
        "total_rewrites": credit.total_rewrites,
    }
