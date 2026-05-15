"""
Wanfang (万方) AIGC Detection Feature Scanner.

万方 uses deep learning (Transformer/BERT) + multi-dimensional feature engineering.
Key characteristics:
  - Character frequency analysis: each AI char is contextually "optimal"
  - Word co-occurrence probability: AI collocations are too "perfect"
  - Sentence vector comparison: finds optimal AI/human classification threshold
  - Perplexity: AI logic is too perfect → low perplexity
  - Innovation density: AI lacks unique perspective depth
  - 1:1 training sample ratio (human:AI balanced)
  - Thresholds: >85% 显著疑似 (red), 50-85% 一般疑似 (yellow), <50% 排除疑似

Distinct from CNKI/Weipu:
  - More emphasis on "innovation density" (独创性)
  - Character-level optimality analysis
  - Less strict on connectors, more strict on content substance
  - Image AIGC detection capability (unique among three)
"""

import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Wanfang-specific analysis categories
# ---------------------------------------------------------------------------

# Category A: Language features (语言特征)
WANFANG_CONNECTORS = [
    "因此", "所以", "然而", "但是", "而且", "此外", "另外",
    "首先", "其次", "最后", "总之", "综上所述",
    "值得注意的是", "不可忽视的是", "需要强调的是",
    "与此同时", "另一方面", "相比之下", "相对而言",
    "正因为", "由于", "基于", "鉴于",
]

# Category B: Content features (内容特征)
# Innovation markers — human writing has these, AI doesn't
INNOVATION_MARKERS = [
    r'(我|笔者|作者|本研究|本文).{1,20}(首次|率先|创新|提出|尝试|探索)',
    r'(与.*不同).{1,30}(我们|本研究)',
    r'(现有|传统|以往).{1,20}(不足|局限|缺陷|问题)',
    r'(需要|值得|有待).{1,20}(进一步|深入|更加)',
    r'(然而|但是|不过).{1,20}(实际上|事实上|恰恰相反)',
    r'(独特|特殊|特别).{1,10}(之处|在于|的是)',
]

# Category C: Computational features (计算特征)
HIGH_PROB_CHARS = set(
    "的是在了一不有和人这中大上为个可以到说们就来也地对多以要下现从而过时能会"
    "由只很都还也就更已经再又第次个种些点之以其及并"
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class LanguageFeatureResult:
    connector_density: float  # per 1000 chars
    sentence_pattern_variety: float  # 0-1, higher = more variety
    expression_flexibility: float  # 0-1, higher = more flexible
    score: float
    detail: str


@dataclass
class ContentFeatureResult:
    innovation_score: float  # 0-1, higher = more innovative (human)
    logic_depth_score: float  # 0-1, higher = deeper analysis (human)
    subjectivity_score: float  # 0-1, higher = more subjective (human)
    score: float
    detail: str


@dataclass
class ComputationalFeatureResult:
    char_optimality: float  # 0-1, higher = more optimal/AI-like
    collocation_perfection: float  # 0-1, higher = more perfect/AI-like
    perplexity_score: float  # 0-100
    score: float
    detail: str


@dataclass
class WanfangFeatureReport:
    language: LanguageFeatureResult
    content: ContentFeatureResult
    computational: ComputationalFeatureResult
    overall_wanfang_score: float
    level: str  # "excluded" / "suspected" / "significant"
    level_label: str  # "排除疑似" / "一般疑似" / "显著疑似"
    high_risk_categories: list[str]
    rewrite_suggestions: list[str]


# ============================================================================
# Category A: Language Feature Analysis
# ============================================================================
def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 2]


def analyze_language_features(text: str) -> LanguageFeatureResult:
    """Analyze language-level features: connectors, sentence patterns, expression style."""
    connectors_found = []
    for conn in WANFANG_CONNECTORS:
        connectors_found.extend(re.findall(re.escape(conn), text))

    text_len = len(text)
    connector_density = (len(connectors_found) / text_len * 1000) if text_len > 0 else 0

    # Sentence pattern variety
    sentences = _split_sentences(text)
    if len(sentences) >= 3:
        # Measure by sentence length distribution entropy
        lengths = [len(s) for s in sentences]
        len_counter = Counter([round(l / 5) * 5 for l in lengths])  # bin by 5 chars
        total = len(lengths)
        entropy = 0.0
        for count in len_counter.values():
            p = count / total
            entropy -= p * math.log2(p)
        max_entropy = math.log2(len(len_counter)) if len_counter else 1
        pattern_variety = entropy / max_entropy if max_entropy > 0 else 0.5
    else:
        pattern_variety = 0.5

    # Expression flexibility: check for varied sentence starters
    if len(sentences) >= 3:
        starters = [s[:2] if len(s) >= 2 else s for s in sentences]
        unique_starters = len(set(starters))
        flexibility = unique_starters / len(sentences)
    else:
        flexibility = 0.5

    # Scoring
    score = 30.0
    if connector_density > 10:
        score += 30
    elif connector_density > 7:
        score += 20
    elif connector_density > 4:
        score += 5
    else:
        score -= 10

    if pattern_variety < 0.4:
        score += 15
    if flexibility < 0.3:
        score += 15
    elif flexibility > 0.6:
        score -= 10

    score = min(100, max(0, score))

    detail = f"连接词密度{connector_density:.1f}/千字，句式多样性{pattern_variety:.2f}，起首变化{flexibility:.2f}"

    return LanguageFeatureResult(
        connector_density=round(connector_density, 1),
        sentence_pattern_variety=round(pattern_variety, 3),
        expression_flexibility=round(flexibility, 3),
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Category B: Content Feature Analysis (万方独有重点)
# ============================================================================
def analyze_content_features(text: str) -> ContentFeatureResult:
    """
    Wanfang's unique focus: content substance.
    - Innovation density: does the text have unique perspectives?
    - Logic depth: does it deeply analyze or just list points?
    - Subjectivity: does it show personal judgment or just report facts?
    """
    # Innovation markers
    innovation_hits = 0
    for pattern in INNOVATION_MARKERS:
        matches = re.findall(pattern, text)
        innovation_hits += len(matches)

    text_len = max(1, len(text))
    innovation_density = innovation_hits / (text_len / 1000)  # per 1000 chars

    # Logic depth: AI tends to list points without deep analysis
    listing_patterns = [
        r'(第[一二三四五六七八九十\d]+[点条])',
        r'(\d+[\.、)）])',
        r'(首先.*其次.*(再次|最后))',
        r'(一方面.*另一方面)',
    ]
    listing_count = 0
    for pattern in listing_patterns:
        listing_count += len(re.findall(pattern, text))
    listing_density = listing_count / (text_len / 1000)

    # Deep analysis markers
    depth_markers = [
        r'(具体.*来说|具体.*而言)',
        r'(以.*为例|比如|例如)',
        r'(这意味着|这暗示|这反映|这揭示)',
        r'(究其.*原因|其.*根源|根本.*在于)',
        r'(值得.*思考|需要.*反思|值得.*关注)',
    ]
    depth_hits = 0
    for pattern in depth_markers:
        depth_hits += len(re.findall(pattern, text))
    depth_density = depth_hits / (text_len / 1000)

    # Subjectivity: personal judgment markers
    subjectivity_markers = [
        r'(我|笔者|作者).{1,10}(认为|觉得|看来|发现|注意到)',
        r'(令人|值得|让人).{1,10}(的[是])?',
        r'(出乎|意料|意外|惊喜|遗憾|可惜)',
        r'(独特|新颖|创新|突破|开创)',
    ]
    subjectivity_hits = 0
    for pattern in subjectivity_markers:
        subjectivity_hits += len(re.findall(pattern, text))
    subjectivity_density = subjectivity_hits / (text_len / 1000)

    # Scoring: Wanfang wants HIGH innovation, HIGH depth, HIGH subjectivity
    innovation_score = min(1.0, innovation_density / 2.0)  # normalize
    logic_depth_score = min(1.0, depth_density / 1.5)

    # Listing without depth = AI signal
    if listing_density > 1.5 and depth_density < 0.3:
        logic_depth_score = max(0, logic_depth_score - 0.3)

    subjectivity_score = min(1.0, subjectivity_density / 1.5)

    # Aggregate: LOW scores = AI-like
    composite = (innovation_score + logic_depth_score + subjectivity_score) / 3

    # Convert to 0-100 (higher = more AI-like, inverted)
    score = round((1 - composite) * 100, 1)

    detail_parts = []
    if innovation_density < 0.3:
        detail_parts.append(f"创新密度极低({innovation_density:.2f}/千字)")
    if logic_depth_score < 0.3:
        detail_parts.append(f"分析深度不足({depth_density:.1f}/千字深度标记)")
    if subjectivity_score < 0.3:
        detail_parts.append(f"缺乏主观判断({subjectivity_density:.1f}/千字)")
    if listing_density > 1.5 and depth_density < 0.3:
        detail_parts.append("罗列式结构明显，缺乏深层剖析")

    detail = "；".join(detail_parts) if detail_parts else "内容特征基本正常"

    return ContentFeatureResult(
        innovation_score=round(innovation_score, 3),
        logic_depth_score=round(logic_depth_score, 3),
        subjectivity_score=round(subjectivity_score, 3),
        score=score,
        detail=detail,
    )


# ============================================================================
# Category C: Computational Feature Analysis
# ============================================================================
def analyze_computational_features(text: str) -> ComputationalFeatureResult:
    """
    Wanfang's computational features:
    1. Character optimality: each AI char is the "optimal" pick in context
    2. Collocation perfection: AI word pairs are too "perfect"
    3. Perplexity: too-perfect logic → low perplexity
    """
    text_len = len(text)
    if text_len < 50:
        return ComputationalFeatureResult(
            char_optimality=0.5, collocation_perfection=0.5, perplexity_score=50.0,
            score=50.0, detail="文本过短",
        )

    # 1. Character optimality: ratio of high-probability chars
    high_prob_count = sum(1 for c in text if c in HIGH_PROB_CHARS)
    char_optimality = high_prob_count / text_len if text_len > 0 else 0

    # 2. Collocation perfection: bigram probability smoothness
    chars = [c for c in text if '一' <= c <= '鿿' or c.isalnum()]
    if len(chars) >= 20:
        bigrams = [tuple(chars[i:i+2]) for i in range(len(chars) - 1)]
        bigram_counter = Counter(bigrams)

        # Calculate diversity
        types = len(bigram_counter)
        tokens = len(bigrams)
        ttr = types / tokens if tokens > 0 else 0

        # AI text has higher TTR (more evenly distributed bigrams)
        # Human text has lower TTR (some bigrams repeat more naturally)
        if ttr > 0.8:
            collocation_perfection = 0.85  # too diverse = AI
        elif ttr > 0.6:
            collocation_perfection = 0.55
        elif ttr > 0.4:
            collocation_perfection = 0.30
        else:
            collocation_perfection = 0.10
    else:
        collocation_perfection = 0.5

    # 3. Perplexity estimation (simplified)
    if len(chars) >= 10:
        # Measure character-level predictability
        char_counter = Counter(chars)
        total_chars = len(chars)
        entropy = 0.0
        for count in char_counter.values():
            p = count / total_chars
            entropy -= p * math.log2(p)

        # Lower entropy = more predictable = more AI-like
        max_entropy = math.log2(len(char_counter)) if char_counter else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.5

        perplexity_score = round((1 - normalized_entropy) * 100, 1)
    else:
        perplexity_score = 50.0

    # Composite computational score
    score = (
        0.35 * (char_optimality * 100)
        + 0.35 * (collocation_perfection * 100)
        + 0.30 * perplexity_score
    )

    detail = (
        f"字符最优度{char_optimality:.2f}，搭配完美度{collocation_perfection:.2f}，"
        f"困惑度{perplexity_score:.0f}"
    )

    return ComputationalFeatureResult(
        char_optimality=round(char_optimality, 3),
        collocation_perfection=round(collocation_perfection, 3),
        perplexity_score=perplexity_score,
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Complete Wanfang Scan
# ============================================================================
def scan_wanfang_features(
    text: str,
    mode: str = "general",
    discipline: str | None = None,
) -> WanfangFeatureReport:
    """Run full Wanfang multi-category AIGC detection."""

    lang = analyze_language_features(text)
    content = analyze_content_features(text)
    comp = analyze_computational_features(text)

    # Weighted fusion — Wanfang weights content features higher than CNKI/Weipu
    weights = {
        "language": 0.30,
        "content": 0.40,  # Wanfang emphasizes content substance
        "computational": 0.30,
    }

    if mode == "academic":
        weights = {"language": 0.20, "content": 0.50, "computational": 0.30}

    overall = (
        weights["language"] * lang.score
        + weights["content"] * content.score
        + weights["computational"] * comp.score
    )
    overall = round(overall, 1)

    # Wanfang thresholds
    if overall >= 85:
        level = "significant"
        level_label = "显著疑似"
    elif overall >= 50:
        level = "suspected"
        level_label = "一般疑似"
    else:
        level = "excluded"
        level_label = "排除疑似"

    # High-risk categories
    high_risk = []
    if lang.score > 60:
        high_risk.append("语言特征异常（连接词过多/句式单一）")
    if content.score > 60:
        high_risk.append("内容特征异常（创新度低/分析浅层/缺乏主观性）")
    if comp.score > 60:
        high_risk.append("计算特征异常（字符最优度过高/搭配过于完美）")

    # Rewrite suggestions
    suggestions = []
    if lang.score > 60:
        suggestions.append(
            f"语言特征异常：减少连接词({lang.connector_density:.1f}/千字)，"
            f"增加句式多样性(当前{lang.sentence_pattern_variety:.2f})"
        )
    if content.score > 60:
        parts = []
        if content.innovation_score < 0.3:
            parts.append("增加创新性观点和独特视角，避免纯罗列已知知识")
        if content.logic_depth_score < 0.3:
            parts.append("加入深层分析('究其原因''这意味着')代替浅层罗列")
        if content.subjectivity_score < 0.3:
            parts.append("增加主观判断和评价('我认为''值得关注的是')")
        if parts:
            suggestions.append("内容特征异常：" + "；".join(parts))
    if comp.score > 60:
        suggestions.append(
            f"计算特征异常：字符选择过于'最优'(最优度{comp.char_optimality:.2f})，"
            "尝试加入非最优但更自然的表达方式"
        )

    return WanfangFeatureReport(
        language=lang,
        content=content,
        computational=comp,
        overall_wanfang_score=overall,
        level=level,
        level_label=level_label,
        high_risk_categories=high_risk,
        rewrite_suggestions=suggestions,
    )
