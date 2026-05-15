"""
Calibration Service — User Feedback Loop for Model Accuracy.

This is THE critical service that transforms our detection from "theoretically correct"
to "actually reliable." Every time a user submits a real CNKI/Weipu/Wanfang score,
we:
  1. Record the (predicted, real) pair
  2. Recompute accuracy metrics
  3. Make the data available for model retraining

Over time, with enough samples, we can:
  - Auto-adjust dimension weights to minimize prediction error
  - Publish a real-time accuracy dashboard (transparency = trust)
  - Identify which features most correlate with actual platform scores
"""

import math
from datetime import datetime, timedelta
from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import CalibrationRecord, AccuracyMetric


async def submit_feedback(
    user_id: str,
    platform: str,  # cnki / weipu / wanfang
    our_predicted_score: float,
    real_score: float,
    input_text: str,
    mode: str,
    db: AsyncSession,
) -> dict:
    """
    User submits a real platform AIGC score for calibration.

    This is the core feedback loop:
      User detects text → gets our prediction → goes to real platform →
      comes back with real score → we learn from the gap.
    """
    error = our_predicted_score - real_score

    record = CalibrationRecord(
        user_id=user_id,
        platform=platform,
        our_predicted_score=round(our_predicted_score, 1),
        real_score=round(real_score, 1),
        prediction_error=round(error, 1),
        input_text=input_text[:5000],
        input_text_length=len(input_text),
        mode=mode,
    )
    db.add(record)
    await db.flush()

    # Recompute accuracy metrics
    await recompute_accuracy(platform, db)

    # Reward user for feedback
    from .credit_service import add_credits
    await add_credits(user_id, 1, db)  # +1 credit per feedback

    return {
        "success": True,
        "prediction_error": round(error, 1),
        "overestimated": error > 0,
        "message": (
            f"感谢反馈！我们的预测{'偏高' if error > 0 else '偏低'}{abs(error):.0f}分。"
            "已奖励1个积分。"
        ),
    }


async def recompute_accuracy(platform: str, db: AsyncSession):
    """
    Recompute accuracy metrics from all calibration records for a platform.
    Updates the AccuracyMetric table.
    """
    # Get all calibration records for this platform
    result = await db.execute(
        select(CalibrationRecord)
        .where(
            and_(
                CalibrationRecord.platform == platform,
                CalibrationRecord.used_for_calibration == True,
            )
        )
    )
    records = result.scalars().all()

    # Also include recent un-used records
    result2 = await db.execute(
        select(CalibrationRecord)
        .where(
            and_(
                CalibrationRecord.platform == platform,
                CalibrationRecord.used_for_calibration == False,
            )
        )
    )
    new_records = result2.scalars().all()

    all_records = list(records) + list(new_records)
    n = len(all_records)

    if n == 0:
        return

    errors = [r.prediction_error for r in all_records]
    predicted = [r.our_predicted_score for r in all_records]
    real = [r.real_score for r in all_records]

    # Mean Absolute Error
    mae = sum(abs(e) for e in errors) / n

    # Root Mean Square Error
    rmse = math.sqrt(sum(e ** 2 for e in errors) / n)

    # Pearson correlation
    mean_pred = sum(predicted) / n
    mean_real = sum(real) / n
    cov = sum((p - mean_pred) * (r - mean_real) for p, r in zip(predicted, real)) / n
    std_pred = math.sqrt(sum((p - mean_pred) ** 2 for p in predicted) / n)
    std_real = math.sqrt(sum((r - mean_real) ** 2 for r in real) / n)
    if std_pred > 0 and std_real > 0:
        correlation = cov / (std_pred * std_real)
    else:
        correlation = 0

    # Within ±10% rate
    within_10 = sum(1 for e in errors if abs(e) <= 10) / n

    # Recent 30-day MAE
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_errors = [
        r.prediction_error for r in all_records
        if r.created_at.replace(tzinfo=None) >= thirty_days_ago
    ]
    recent_mae = sum(abs(e) for e in recent_errors) / len(recent_errors) if recent_errors else mae

    # Upsert accuracy metric
    existing = await db.execute(
        select(AccuracyMetric).where(AccuracyMetric.platform == platform)
    )
    metric = existing.scalar_one_or_none()

    if metric is None:
        metric = AccuracyMetric(platform=platform)
        db.add(metric)

    metric.total_calibration_samples = n
    metric.mean_absolute_error = round(mae, 2)
    metric.rmse = round(rmse, 2)
    metric.correlation_coefficient = round(correlation, 4)
    metric.within_10_percent_rate = round(within_10, 4)
    metric.recent_mae_30d = round(recent_mae, 2)
    metric.last_calibrated_at = datetime.utcnow()

    # Mark new records as used
    for r in new_records:
        r.used_for_calibration = True

    await db.flush()


async def get_calibration_stats(db: AsyncSession) -> dict:
    """Get global calibration statistics."""
    result = await db.execute(
        select(
            func.count(CalibrationRecord.id).label("total"),
            func.avg(func.abs(CalibrationRecord.prediction_error)).label("mae"),
        )
    )
    row = result.one()
    return {
        "total_feedback_submissions": row.total or 0,
        "overall_mae": round(row.mae or 0, 2),
    }
