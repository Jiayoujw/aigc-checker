import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
import enum


class RecordType(str, enum.Enum):
    detect = "detect"
    rewrite = "rewrite"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    records: Mapped[list["HistoryRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class HistoryRecord(Base):
    __tablename__ = "history_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    record_type: Mapped[RecordType] = mapped_column(SAEnum(RecordType))
    input_text: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="records")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50))  # deepseek / openai
    key: Mapped[str] = mapped_column(String(255))
    label: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---- SpeedAI-level features: credits, calibration, accuracy ----

class UserCredit(Base):
    """Credit/points system for free tier + paid usage."""
    __tablename__ = "user_credits"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, index=True
    )
    # Free daily credits reset at midnight
    daily_detect_used: Mapped[int] = mapped_column(default=0)
    daily_rewrite_used: Mapped[int] = mapped_column(default=0)
    daily_limit_detect: Mapped[int] = mapped_column(default=5)
    daily_limit_rewrite: Mapped[int] = mapped_column(default=2)
    # Purchased credits (1 credit = 1 detection or 1 rewrite)
    purchased_credits: Mapped[int] = mapped_column(default=0)
    # Total usage stats
    total_detections: Mapped[int] = mapped_column(default=0)
    total_rewrites: Mapped[int] = mapped_column(default=0)
    # Registration bonus claimed
    registration_bonus_claimed: Mapped[bool] = mapped_column(default=False)
    # Last daily reset timestamp
    last_daily_reset: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CalibrationRecord(Base):
    """User-submitted real platform scores for model calibration."""
    __tablename__ = "calibration_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    platform: Mapped[str] = mapped_column(String(20))  # cnki / weipu / wanfang
    # Our prediction before user feedback
    our_predicted_score: Mapped[float] = mapped_column()
    # User-submitted real score from the platform
    real_score: Mapped[float] = mapped_column()
    # Error: our_predicted - real (positive = we overestimated)
    prediction_error: Mapped[float] = mapped_column()
    # The text that was analyzed (truncated to 5000 chars)
    input_text: Mapped[str] = mapped_column(Text)
    input_text_length: Mapped[int] = mapped_column()
    # Detection mode used
    mode: Mapped[str] = mapped_column(String(20), default="general")
    # Whether this record has been used for recalibration
    used_for_calibration: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AccuracyMetric(Base):
    """Aggregated accuracy metrics for public dashboard."""
    __tablename__ = "accuracy_metrics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    platform: Mapped[str] = mapped_column(String(20), unique=True)
    # Core metrics
    total_calibration_samples: Mapped[int] = mapped_column(default=0)
    mean_absolute_error: Mapped[float] = mapped_column(default=0.0)
    rmse: Mapped[float] = mapped_column(default=0.0)
    correlation_coefficient: Mapped[float] = mapped_column(default=0.0)
    # Percentage of predictions within ±10% of real score
    within_10_percent_rate: Mapped[float] = mapped_column(default=0.0)
    # Last 30 days MAE (rolling window)
    recent_mae_30d: Mapped[float] = mapped_column(default=0.0)
    # Last calibration timestamp
    last_calibrated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
