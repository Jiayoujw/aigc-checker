"""
Public Accuracy Dashboard Service.

Transparency = Trust. SpeedAI's biggest weakness is the lack of publicly
verifiable accuracy data. We turn this into our advantage by publishing:
  - Real-time MAE (Mean Absolute Error) per platform
  - Total calibration samples collected
  - Prediction error distribution
  - Trending accuracy over time (improving or degrading?)

This builds user confidence: "Their CNKI prediction error is only 8.3% —
that's better than SpeedAI's claimed 10%."
"""

from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import AccuracyMetric, CalibrationRecord


async def get_dashboard_data(db: AsyncSession) -> dict:
    """Get public accuracy dashboard data for all platforms."""
    result = await db.execute(select(AccuracyMetric))
    metrics = result.scalars().all()

    platforms = {}
    for m in metrics:
        platforms[m.platform] = {
            "platform": m.platform,
            "platform_label": _platform_label(m.platform),
            "total_samples": m.total_calibration_samples,
            "mean_absolute_error": m.mean_absolute_error,
            "rmse": m.rmse,
            "correlation": m.correlation_coefficient,
            "within_10_percent_rate": m.within_10_percent_rate,
            "recent_mae_30d": m.recent_mae_30d,
            "last_calibrated_at": m.last_calibrated_at.isoformat() if m.last_calibrated_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }

    # Overall stats
    total_samples = sum(m.total_calibration_samples for m in metrics)

    # Compute overall MAE
    result2 = await db.execute(
        select(func.avg(func.abs(CalibrationRecord.prediction_error)))
    )
    overall_mae = result2.scalar() or 0

    return {
        "platforms": platforms,
        "overall": {
            "total_calibration_samples": total_samples,
            "overall_mae": round(overall_mae, 2),
        },
        "comparison_to_speedai": {
            "speedai_claimed_mae": 10.0,
            "our_mae": round(overall_mae, 2),
            "we_are_better": overall_mae < 10.0 if total_samples >= 50 else None,
            "note": "SpeedAI claims <10% error rate vs CNKI. We publicly verify ours in real-time." if total_samples < 50 else (
                f"Based on {total_samples} real user submissions, our MAE is {overall_mae:.1f}% — "
                f"{'BETTER than' if overall_mae < 10.0 else 'comparable to' if overall_mae < 12.0 else 'behind'} SpeedAI's claimed 10%."
            ),
        },
    }


async def get_error_distribution(platform: str, db: AsyncSession) -> dict:
    """Get error distribution for a specific platform."""
    result = await db.execute(
        select(
            CalibrationRecord.prediction_error,
            CalibrationRecord.created_at,
        )
        .where(CalibrationRecord.platform == platform)
        .order_by(CalibrationRecord.created_at.desc())
        .limit(200)
    )
    records = result.all()

    if not records:
        return {"platform": platform, "error_distribution": {}, "trend": []}

    errors = [r[0] for r in records]

    # Distribution buckets
    buckets = {
        "within_5": sum(1 for e in errors if abs(e) <= 5),
        "within_5_to_10": sum(1 for e in errors if 5 < abs(e) <= 10),
        "within_10_to_15": sum(1 for e in errors if 10 < abs(e) <= 15),
        "within_15_to_20": sum(1 for e in errors if 15 < abs(e) <= 20),
        "over_20": sum(1 for e in errors if abs(e) > 20),
    }

    # Trend: group by week
    trend = []
    if len(records) >= 10:
        weekly_data = {}
        for error, ts in records:
            week_key = ts.strftime("%Y-W%W") if ts else "unknown"
            if week_key not in weekly_data:
                weekly_data[week_key] = []
            weekly_data[week_key].append(abs(error))

        trend = [
            {"week": wk, "mae": round(sum(errs) / len(errs), 2), "samples": len(errs)}
            for wk, errs in sorted(weekly_data.items())[-12:]
        ]

    return {
        "platform": platform,
        "platform_label": _platform_label(platform),
        "total_samples": len(errors),
        "error_distribution": buckets,
        "trend": trend,
    }


def _platform_label(platform: str) -> str:
    return {"cnki": "知网", "weipu": "维普", "wanfang": "万方"}.get(platform, platform)
