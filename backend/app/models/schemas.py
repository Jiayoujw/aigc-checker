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


class PlagiarismRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)


class PlagiarismResponse(BaseModel):
    similarity_score: float
    similar_sources: list[dict]
    details: str


class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    provider: Literal["deepseek", "openai", "auto"] = "auto"
    intensity: Literal["light", "medium", "deep"] = "medium"
    preserve_terms: bool = False


class RewriteResponse(BaseModel):
    rewritten_text: str
    changes_summary: str
    new_aigc_score: float
