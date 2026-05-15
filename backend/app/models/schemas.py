from pydantic import BaseModel, Field
from typing import Literal


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    provider: Literal["deepseek", "openai", "auto"] = "auto"
    mode: Literal["general", "academic", "resume", "social_media"] = "general"


class StatisticalAnalysis(BaseModel):
    score: float
    perplexity: float
    burstiness: float
    template_hits: int
    lexical_diversity: float
    sentence_count: int
    avg_sentence_len: float
    sentence_len_std: float
    details: list[str]


class FusedResult(BaseModel):
    combined_score: float
    llm_score: float
    statistical_score: float
    confidence: str
    level: str


class DetectResponse(BaseModel):
    score: float
    level: Literal["low", "medium", "high"]
    suspicious_segments: list[dict]
    analysis: str
    statistical_analysis: StatisticalAnalysis | None = None
    fused_result: FusedResult | None = None
    detection_time_ms: float | None = None


class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    provider: Literal["deepseek", "openai", "auto"] = "auto"
    intensity: Literal["light", "medium", "deep"] = "medium"
    preserve_terms: bool = False


class RewriteResponse(BaseModel):
    rewritten_text: str
    changes_summary: str
    new_aigc_score: float


# ---- New CNKI-specific models ----

class CNKIDetectRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    mode: Literal["general", "academic", "resume", "social_media"] = "general"
    discipline: str | None = None
    provider: Literal["deepseek", "openai", "auto"] = "auto"


class DimensionScore(BaseModel):
    score: float
    detail: str


class DimensionBreakdown(BaseModel):
    sentence_structure: DimensionScore
    paragraph_similarity: DimensionScore
    information_density: DimensionScore
    connectors: DimensionScore
    terminology: DimensionScore
    citations: DimensionScore
    data_specificity: DimensionScore
    logical_coherence: DimensionScore


class CNKIDetectResponse(BaseModel):
    cnki_score: float
    level: Literal["low", "medium", "high"]
    confidence: float
    method: str
    dimension_breakdown: DimensionBreakdown
    high_risk_dimensions: list[str]
    rewrite_suggestions: list[str]


class RewriteV2Request(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    provider: Literal["deepseek", "openai", "auto"] = "auto"
    intensity: Literal["light", "medium", "deep"] = "medium"
    mode: str = "general"
    target_score: float = 25.0
    max_rounds: int = Field(default=3, ge=1, le=5)


class RewriteV2Response(BaseModel):
    rewritten_text: str
    original_score: float
    new_score: float
    rounds: int
    score_improvement: float
    changes_summary: str
    triggered_dimensions: list[str]
    dimension_scores_before: dict
    dimension_scores_after: dict


# ---- Credit / Quota models ----

class CreditStats(BaseModel):
    daily_detect_used: int
    daily_detect_total: int = 5
    daily_rewrite_used: int
    daily_rewrite_total: int = 2
    purchased_credits: int
    total_detections: int
    total_rewrites: int
    registration_bonus_claimed: bool


class QuotaInfo(BaseModel):
    can_detect: bool
    can_rewrite: bool
    daily_free_remaining: int
    daily_free_total: int
    purchased_credits: int


class DetectQuota(BaseModel):
    can_detect: bool
    daily_free_remaining: int
    daily_free_total: int
    purchased_credits: int


class RewriteQuota(BaseModel):
    can_rewrite: bool
    daily_free_remaining: int
    daily_free_total: int
    purchased_credits: int


class QuotaResponse(BaseModel):
    detect: DetectQuota
    rewrite: RewriteQuota


# ---- Calibration / Feedback models ----

class FeedbackRequest(BaseModel):
    platform: str = Field(..., pattern="^(cnki|weipu|wanfang)$")
    our_predicted_score: float = Field(..., ge=0, le=100)
    real_score: float = Field(..., ge=0, le=100)
    input_text: str = Field(..., min_length=50, max_length=5000)
    mode: str = Field(default="general")


class FeedbackResponse(BaseModel):
    success: bool
    credits_earned: int
    prediction_error: float
    total_samples: int
    message: str


class CalibrationStatsResponse(BaseModel):
    total_samples: int
    platforms: dict[str, dict]


class AccuracyPlatformInfo(BaseModel):
    platform: str
    platform_label: str
    total_samples: int
    mean_absolute_error: float
    rmse: float
    correlation: float
    within_10_percent_rate: float
    recent_mae_30d: float
    last_calibrated_at: str | None
    updated_at: str | None


class AccuracyDashboardResponse(BaseModel):
    platforms: dict[str, AccuracyPlatformInfo]
    overall: dict
    comparison_to_speedai: dict


class ErrorDistributionResponse(BaseModel):
    platform: str
    platform_label: str
    total_samples: int
    error_distribution: dict[str, int]
    trend: list[dict]


# ---- Report Parse / Rewrite models ----

class ReportParseRequest(BaseModel):
    report_text: str = Field(..., min_length=50, max_length=20000)
    platform_hint: str = Field(default="auto", pattern="^(auto|cnki|weipu|wanfang)$")


class FlaggedSectionInfo(BaseModel):
    text: str
    score: float
    risk_level: str


class ReportParseResponse(BaseModel):
    platform: str
    overall_score: float | None
    overall_level: str | None
    flagged_sections: list[FlaggedSectionInfo]
    flagged_count: int
    parse_confidence: float


class ReportRewriteRequest(BaseModel):
    original_text: str = Field(..., min_length=50, max_length=50000)
    report_text: str = Field(..., min_length=50, max_length=20000)
    provider: str = Field(default="auto")
    intensity: str = Field(default="medium", pattern="^(light|medium|deep)$")
    platform_hint: str = Field(default="auto")


class SectionRewriteInfo(BaseModel):
    original_text: str
    rewritten_text: str
    original_score: float
    new_score: float
    improvement: float


class ReportRewriteResponse(BaseModel):
    rewritten_full_text: str
    sections_rewritten: int
    sections_preserved: int
    section_results: list[SectionRewriteInfo]
    original_overall_score: float | None
    estimated_new_score: float
    changes_summary: str
