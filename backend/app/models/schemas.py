from pydantic import BaseModel, Field
from typing import Literal


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=5000)
    provider: Literal["deepseek", "openai", "auto"] = "auto"
    mode: Literal["general", "academic", "resume", "social_media"] = "general"


class DetectResponse(BaseModel):
    score: float
    level: Literal["low", "medium", "high"]
    suspicious_segments: list[dict]
    analysis: str


class PlagiarismRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=5000)


class PlagiarismResponse(BaseModel):
    similarity_score: float
    similar_sources: list[dict]
    details: str


class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=5000)
    provider: Literal["deepseek", "openai", "auto"] = "auto"
    intensity: Literal["light", "medium", "deep"] = "medium"
    preserve_terms: bool = False


class RewriteResponse(BaseModel):
    rewritten_text: str
    changes_summary: str
    new_aigc_score: float
