"""
Information-Difference AIGC Detection (信息量差值检测).

Based on CNKI patent CN119357388A (2024-09):
  1. Generate N rewritten variants of the input text via LLM
  2. Compute information content of original and each variant
  3. Small info-difference → AI-generated (rewriting doesn't change much)
  4. Large info-difference → human-written (rewriting causes significant fluctuation)
  5. Normalize by discipline-specific prior distribution

This is CNKI's core differentiator — no other detection platform uses this method.
"""

import math
import asyncio
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from .llm_client import LLMClient


# ---------------------------------------------------------------------------
# Information content computation
# ---------------------------------------------------------------------------
def _char_entropy(text: str) -> float:
    """Shannon entropy of character distribution (higher = more diverse)."""
    if not text:
        return 0.0
    counter = Counter(text)
    total = len(text)
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def _ngram_diversity(text: str, n: int = 2) -> float:
    """Type-token ratio for character n-grams."""
    chars = [c for c in text if '一' <= c <= '鿿' or c.isalnum()]
    if len(chars) < n + 5:
        return 0.5
    ngrams = [tuple(chars[i:i+n]) for i in range(len(chars) - n + 1)]
    return len(set(ngrams)) / len(ngrams) if ngrams else 0.5


def _sentence_length_entropy(text: str) -> float:
    """Entropy of sentence length distribution."""
    import re
    sentences = re.split(r'[。！？；\n]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 2]
    if len(sentences) < 3:
        return 0.0
    lengths = [len(s) for s in sentences]
    counter = Counter(lengths)
    total = len(lengths)
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def compute_information_content(text: str) -> dict:
    """
    Compute multi-dimensional information content of a text.
    Returns raw metrics + composite score.
    """
    char_count = len(text)
    char_ent = _char_entropy(text)
    bigram_div = _ngram_diversity(text, 2)
    sent_ent = _sentence_length_entropy(text)

    # Composite info score (roughly 0-10 scale)
    composite = (
        0.25 * math.log2(max(1, char_count))
        + 0.30 * char_ent
        + 0.25 * bigram_div * 10
        + 0.20 * sent_ent
    )

    return {
        "char_count": char_count,
        "char_entropy": round(char_ent, 4),
        "bigram_diversity": round(bigram_div, 4),
        "sentence_entropy": round(sent_ent, 4),
        "composite": round(composite, 4),
    }


# ---------------------------------------------------------------------------
# LLM variant generation prompt
# ---------------------------------------------------------------------------
VARIANT_PROMPT = """你是一个文本改写助手。请对以下文本进行改写，保持原意不变，但用不同的表达方式重新组织语言。改写时：
1. 可以调整句式结构、词汇选择、段落组织
2. 保留核心内容和关键信息
3. 不要改变专业术语
4. 改写后的文本长度应与原文相近

只返回改写后的文本，不要加任何说明。"""


async def _generate_variants(
    text: str,
    provider: str = "auto",
    n_variants: int = 3,
) -> list[str]:
    """Generate N rewritten variants of the text via LLM."""
    client = LLMClient(provider)

    async def _one_variant(temp: float) -> str:
        try:
            response = await client.client.chat.completions.create(
                model=client.model,
                messages=[
                    {"role": "system", "content": VARIANT_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=temp,
                max_tokens=min(len(text) * 2, 16000),
            )
            content = response.choices[0].message.content
            return content if content else text
        except Exception:
            return text  # fallback: use original

    # Generate variants with different temperatures for diversity
    temps = [0.5, 0.7, 0.9][:n_variants]
    tasks = [_one_variant(t) for t in temps]
    variants = await asyncio.gather(*tasks)
    return variants


# ---------------------------------------------------------------------------
# Prior distribution (simulated — in production, this comes from real data)
# ---------------------------------------------------------------------------
# CNKI maintains discipline-specific priors based on their massive academic corpus.
# We simulate these with reasonable defaults that can be calibrated with real data.
DISCIPLINE_PRIORS = {
    "general": {"mean_diff": 0.85, "std_diff": 0.30},
    "cs": {"mean_diff": 0.78, "std_diff": 0.28},
    "medical": {"mean_diff": 0.92, "std_diff": 0.32},
    "engineering": {"mean_diff": 0.80, "std_diff": 0.29},
    "economics": {"mean_diff": 0.88, "std_diff": 0.31},
    "law": {"mean_diff": 0.75, "std_diff": 0.27},
    "humanities": {"mean_diff": 0.95, "std_diff": 0.35},
}


@dataclass
class InfoDiffReport:
    original_info: dict
    variant_infos: list[dict]
    mean_variant_composite: float
    info_diff: float  # absolute difference
    normalized_score: float  # 0-100 CNKI-style AIGC probability
    level: str
    confidence: str
    detail: str


async def detect_by_info_diff(
    text: str,
    provider: str = "auto",
    discipline: str = "general",
    n_variants: int = 3,
) -> InfoDiffReport:
    """
    Full CNKI patent info-difference detection pipeline.

    1. Generate N rewritten variants
    2. Compute information content for each
    3. Calculate difference between original and mean variant
    4. Normalize by discipline prior → AIGC probability
    """
    # Step 1 & 2: Generate variants and compute info
    variants = await _generate_variants(text, provider, n_variants)

    original_info = compute_information_content(text)
    variant_infos = [compute_information_content(v) for v in variants]

    mean_composite = sum(v["composite"] for v in variant_infos) / len(variant_infos) if variant_infos else original_info["composite"]

    # Step 3: Absolute normalized difference
    # Diff = |original - mean_variant| / max(original, mean_variant)
    max_val = max(original_info["composite"], mean_composite)
    if max_val > 0:
        info_diff = abs(original_info["composite"] - mean_composite) / max_val
    else:
        info_diff = 0.0

    # Step 4: Normalize by discipline prior
    prior = DISCIPLINE_PRIORS.get(discipline, DISCIPLINE_PRIORS["general"])
    prior_mean = prior["mean_diff"]
    prior_std = prior["std_diff"]

    # Z-score: how many stds is this diff from the prior mean?
    if prior_std > 0:
        z_score = (info_diff - prior_mean) / prior_std
    else:
        z_score = 0

    # Convert to 0-100 AIGC probability
    # Low info_diff (negative z) → AI text
    # High info_diff (positive z) → human text
    # Sigmoid-like normalization
    if z_score < -2:
        normalized = 90.0
    elif z_score < -1:
        normalized = 75.0
    elif z_score < 0:
        normalized = 55.0
    elif z_score < 1:
        normalized = 30.0
    elif z_score < 2:
        normalized = 12.0
    else:
        normalized = 5.0

    # Confidence based on variant consistency
    variant_composites = [v["composite"] for v in variant_infos]
    if len(variant_composites) >= 2:
        var_variance = sum(
            (c - mean_composite) ** 2 for c in variant_composites
        ) / len(variant_composites)
        if var_variance < 0.01:
            confidence = "high"
        elif var_variance < 0.05:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = "medium"

    # Level
    if normalized < 30:
        level = "low"
    elif normalized < 70:
        level = "medium"
    else:
        level = "high"

    # Detail
    if normalized >= 70:
        detail = (
            f"信息量差值较小({info_diff:.3f})，低于学科先验均值({prior_mean:.2f})，"
            f"改写前后信息量变化不显著，强AI生成特征"
        )
    elif normalized >= 40:
        detail = (
            f"信息量差值中等({info_diff:.3f})，改写前后有一定变化，存在部分AI特征"
        )
    else:
        detail = (
            f"信息量差值较大({info_diff:.3f})，高于学科先验均值({prior_mean:.2f})，"
            f"改写前后信息量波动显著，人写特征"
        )

    return InfoDiffReport(
        original_info=original_info,
        variant_infos=variant_infos,
        mean_variant_composite=round(mean_composite, 4),
        info_diff=round(info_diff, 4),
        normalized_score=round(normalized, 1),
        level=level,
        confidence=confidence,
        detail=detail,
    )
