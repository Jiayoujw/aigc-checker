"""
Multi-dimensional AIGC detection using statistical features.

This complements the LLM-based detector with offline, reproducible metrics:
1. Perplexity estimation via n-gram model
2. Burstiness (sentence structure variance)
3. Template phrase detection
4. Lexical diversity (TTR, hapax ratio)
5. Sentence length distribution

Inspired by GLTR (Gehrmann et al.) and DetectGPT principles.
"""

import re
import math
from collections import Counter
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# AI-typical patterns — transition phrases, template expressions
# ---------------------------------------------------------------------------
AI_TEMPLATE_PATTERNS = [
    # Overused transitions
    "首先.*其次.*最后",
    "总而言之",
    "综上所述",
    "与此同时",
    "此外",
    "值得注意的是",
    "不可否认",
    # Template conclusions
    "在未来的发展中",
    "随着.*的不断发展",
    "具有重要的.*意义",
    "发挥着.*重要作用",
    "为.*做出了.*贡献",
    # Overly balanced structure markers
    "不仅.*而且",
    "一方面.*另一方面",
    "既.*又",
    # AI hedging patterns
    "需要指出的是",
    "从某种程度上说",
    "在一定程度上",
    "相对而言",
    "大体上来说",
]

# Common AI-generated bigrams/trigrams in Chinese text
AI_COMMON_NGRAMS = {
    "越来越重要", "革命性的变化", "海量数据", "有意义的模式",
    "不断提升", "持续优化", "深入分析", "广泛应用",
    "智能化", "数字化", "赋能", "闭环", "抓手", "对齐",
    "不可忽视", "不可或缺", "至关重要",
}


@dataclass
class StatisticalResult:
    score: float  # 0-100 AIGC probability
    perplexity: float
    burstiness: float
    template_hits: int
    lexical_diversity: float
    sentence_count: int
    avg_sentence_len: float
    sentence_len_std: float
    details: list[str] = field(default_factory=list)


def _split_sentences(text: str) -> list[str]:
    """Split Chinese text into sentences."""
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 3]


def _tokenize_chinese(text: str) -> list[str]:
    """Character-level tokenization for Chinese text."""
    tokens = []
    for char in text:
        if '一' <= char <= '鿿':
            tokens.append(char)
        elif char.isalnum():
            tokens.append(char.lower())
    return tokens


def _estimate_perplexity(text: str) -> float:
    """
    Estimate text perplexity using character-level trigram model.
    Lower perplexity → more predictable → more likely AI-generated.
    Returns log-perplexity normalized to 0-100 scale.
    """
    tokens = _tokenize_chinese(text)
    if len(tokens) < 10:
        return 50.0  # neutral for very short text

    # Build trigram frequencies
    trigrams = []
    for i in range(len(tokens) - 2):
        trigrams.append(tuple(tokens[i:i+3]))

    trigram_count = Counter(trigrams)
    bigram_count = Counter()
    for i in range(len(tokens) - 1):
        bigram_count[tuple(tokens[i:i+2])] += 1

    # Compute cross-entropy
    total_log_prob = 0.0
    n = 0
    for i in range(len(tokens) - 2):
        bigram = tuple(tokens[i:i+2])
        trigram = tuple(tokens[i:i+3])
        bigram_freq = bigram_count.get(bigram, 0)
        trigram_freq = trigram_count.get(trigram, 0)

        # Laplace smoothing
        prob = (trigram_freq + 1) / (bigram_freq + len(trigram_count) + 1)
        total_log_prob += -math.log2(prob)
        n += 1

    if n == 0:
        return 50.0

    avg_perplexity = 2 ** (total_log_prob / n)

    # Normalize: typical AI text has perplexity 2-15, human 15-80+
    # Map to 0-100 scale (higher = more AI-like)
    if avg_perplexity < 2:
        score = 95.0
    elif avg_perplexity > 80:
        score = 5.0
    else:
        score = max(0, min(100, 95 - math.log2(avg_perplexity) * 15))

    return round(score, 1)


def _compute_burstiness(sentences: list[str]) -> float:
    """
    Burstiness = variance of sentence lengths.
    AI text tends to have very uniform sentence lengths (low burstiness).
    Human text has natural variation (high burstiness).
    Returns 0-100 (higher = more AI-like, more uniform).
    """
    if len(sentences) < 3:
        return 50.0

    lengths = [len(s) for s in sentences]
    mean_len = sum(lengths) / len(lengths)

    if mean_len == 0:
        return 50.0

    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    std = math.sqrt(variance)
    cv = std / mean_len  # coefficient of variation

    # CV < 0.3 → very uniform → high AI probability
    # CV > 1.0 → very varied → more human-like
    if cv < 0.2:
        return 85.0
    elif cv < 0.4:
        return 70.0
    elif cv < 0.6:
        return 40.0
    elif cv < 0.8:
        return 20.0
    else:
        return 5.0


def _detect_template_phrases(text: str) -> tuple[int, list[str]]:
    """Count AI template phrase occurrences."""
    hits = 0
    found = []
    for pattern in AI_TEMPLATE_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            hits += len(matches)
            found.append(f"{pattern}: {len(matches)}次")

    for ngram in AI_COMMON_NGRAMS:
        count = text.count(ngram)
        if count > 0:
            hits += count
            if count >= 2:
                found.append(f"'{ngram}': {count}次")

    return hits, found


def _lexical_diversity(text: str) -> float:
    """
    Type-Token Ratio (TTR) for character bigrams.
    Lower diversity → more repetitive → more AI-like.
    Returns 0-100 (higher = more AI-like, less diverse).
    """
    tokens = _tokenize_chinese(text)
    if len(tokens) < 20:
        return 50.0

    bigrams = [tuple(tokens[i:i+2]) for i in range(len(tokens) - 1)]
    types = len(set(bigrams))
    tokens_count = len(bigrams)

    if tokens_count == 0:
        return 50.0

    ttr = types / tokens_count

    # TTR < 0.3 → very repetitive → AI-like
    if ttr > 0.7:
        return 10.0
    elif ttr > 0.5:
        return 25.0
    elif ttr > 0.35:
        return 45.0
    elif ttr > 0.25:
        return 65.0
    else:
        return 85.0


def _sentence_stats(sentences: list[str]) -> tuple[int, float, float]:
    """Returns (count, mean_length, std_length)."""
    if not sentences:
        return 0, 0, 0
    lengths = [len(s) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    return len(sentences), mean_len, math.sqrt(variance)


def analyze_statistical(text: str) -> StatisticalResult:
    """
    Run full multi-dimensional statistical analysis.
    This is an offline, fast complement to the LLM-based detector.
    """
    sentences = _split_sentences(text)
    sent_count, avg_len, len_std = _sentence_stats(sentences)

    perplexity = _estimate_perplexity(text)
    burstiness = _compute_burstiness(sentences)
    template_hits, template_details = _detect_template_phrases(text)
    lex_div = _lexical_diversity(text)

    # Weighted ensemble score
    weights = {
        "perplexity": 0.30,
        "burstiness": 0.20,
        "template": 0.25,
        "lexical": 0.15,
        "sentence": 0.10,
    }

    # Sentence uniformity score (from avg_len and std)
    if sent_count >= 3 and avg_len > 0:
        cv = len_std / avg_len
        if cv < 0.3:
            sent_score = 80.0
        elif cv < 0.5:
            sent_score = 50.0
        else:
            sent_score = 15.0
    else:
        sent_score = 50.0

    template_score = min(100, template_hits * 12)

    score = (
        weights["perplexity"] * perplexity
        + weights["burstiness"] * burstiness
        + weights["template"] * template_score
        + weights["lexical"] * lex_div
        + weights["sentence"] * sent_score
    )

    # Build diagnostic details
    details = []
    if perplexity > 60:
        details.append(f"困惑度偏低({perplexity:.0f})，文本可预测性高")
    if burstiness > 60:
        details.append(f"句式均匀度偏高({burstiness:.0f})，缺少自然变化")
    if template_hits > 0:
        details.extend(template_details[:5])
    if lex_div > 60:
        details.append(f"词汇多样性偏低({lex_div:.0f})，存在重复用词模式")

    return StatisticalResult(
        score=round(min(100, score), 1),
        perplexity=perplexity,
        burstiness=burstiness,
        template_hits=template_hits,
        lexical_diversity=lex_div,
        sentence_count=sent_count,
        avg_sentence_len=round(avg_len, 1),
        sentence_len_std=round(len_std, 1),
        details=details,
    )


def fuse_scores(llm_score: float, stat_score: float) -> dict:
    """
    Combine LLM-based detection with statistical analysis for a
    more robust final verdict. Uses weighted average with confidence.
    """
    combined = round(llm_score * 0.55 + stat_score * 0.45, 1)

    # Confidence: if both agree, confidence is high
    diff = abs(llm_score - stat_score)
    if diff < 15:
        confidence = "high"
    elif diff < 30:
        confidence = "medium"
    else:
        confidence = "low"

    if combined < 30:
        level = "low"
    elif combined < 70:
        level = "medium"
    else:
        level = "high"

    return {
        "combined_score": combined,
        "llm_score": llm_score,
        "statistical_score": stat_score,
        "confidence": confidence,
        "level": level,
    }
