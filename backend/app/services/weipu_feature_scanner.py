"""
Weipu (维普) AIGC Detection Feature Scanner — 9 Detection Signals.

维普 4.0 (2026) uses sentence-level micro-scanning with 150-200 char windows.
Key differences from CNKI:
  - Sentence-level granularity (CNKI is paragraph-level)
  - Stricter thresholds (prefers recall over precision — more false positives)
  - Continuous sentence pattern detection (3 consecutive similar = trigger)
  - Adjacent sentence length difference analysis (new in v4.0)
  - Term stacking density threshold: 7/100 chars (CNKI: 6/100)
  - Table, footnote, endnote content included in detection scope
  - Semantic coherence sensitivity: "too smooth" = AI signal
  - Long sentence (>30 chars) special scrutiny
  - Reverse detection: identifies mechanical rewriting patterns

Reference signals (9 dimensions):
  1. Template phrase co-occurrence (模板词组共现) — HIGH
  2. Sentence pattern uniformity (句式过于工整) — HIGH
  3. Style distribution uniformity (AI风格分布均匀) — HIGH
  4. Training data matching (训练数据匹配) — HIGH
  5. Cross-paragraph semantic perfection (跨段语义关联过完美) — MEDIUM
  6. Terminology normalization (学术术语规范化无变化) — MEDIUM
  7. Lack of colloquial supplements (缺少口语化补充) — MEDIUM
  8. Length uniformity (长度均匀无节奏) — LOW
  9. Citation format perfection (引用格式过于规整) — LOW
"""

import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Weipu-specific patterns
# ---------------------------------------------------------------------------

# Signal 1: Template phrase co-occurrence (维普 special focus)
WEIPU_TEMPLATE_PHRASES = [
    # High-trigger compound templates
    "随着.*的.*发展",
    "在当前.*背景下",
    "值得注意的是",
    "综上所述",
    "基于以上.*分析",
    "通过.*可以看出",
    # AI递进句式 (维普重点标记)
    "首先.*其次.*最后",
    "一方面.*另一方面",
    "不仅.*而且.*还",
    "既.*又.*同时",
    # AI总结句式
    "具有重要的.*意义",
    "发挥着.*重要作用",
    "为.*做出了.*贡献",
    "在.*方面具有.*优势",
    # 维普v4.0新增
    "需要.*指出.*的是",
    "从.*角度.*来看",
    "在.*过程.*中",
    "通过.*方式.*实现",
    "以.*为.*基础",
]

# Signal 1b: Co-occurrence pairs (two phrases within 100 chars)
COOCCURRENCE_PAIRS = [
    ("首先", "其次"),
    ("此外", "同时"),
    ("综上所述", "分析"),
    ("随着", "发展"),
    ("通过", "实现"),
    ("基于", "提出"),
    ("针对", "进行"),
]

# Signal 2: Sentence pattern markers
SENTENCE_PATTERNS = [
    # Subject-predicate-object rigid structure
    (r'^.{1,5}(通过|基于|利用|采用|针对).{1,10}(进行|开展|实现|完成|达到)', "方式-动作固定结构"),
    # Modifier stacking
    (r'(的.{2,8}){3,}', "定语堆叠"),
    # Parallel structure
    (r'^.{2,6}(、.{2,6}){2,}[，。]', "并列结构"),
]

# Signal 5: Cross-paragraph semantic connectors
SEMANTIC_CONNECTORS = [
    "基于以上", "综上所述", "如前所述", "由上可知",
    "进一步地", "此外", "另外", "与此相对",
    "正因为如此", "所以", "因此", "故而",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class WeipuSignalResult:
    signal_id: int
    name: str
    severity: str  # high/medium/low
    score: float  # 0-100
    detail: str
    raw_data: dict = field(default_factory=dict)


@dataclass
class SentenceLevelAnalysis:
    """维普核心：句子级分析"""
    sentence_count: int
    mean_len: float
    std_len: float
    length_cv: float
    # Adjacent sentence length difference (v4.0 new)
    adjacent_diffs: list[float]
    mean_adjacent_diff: float
    adj_diff_cv: float
    # Continuous similar sentence detection
    consecutive_similar_count: int
    # Long sentence ratio (>30 chars)
    long_sentence_ratio: float
    # Score
    score: float
    detail: str


@dataclass
class WeipuFeatureReport:
    """Complete 9-signal Weipu analysis."""
    signals: list[WeipuSignalResult]
    sentence_analysis: SentenceLevelAnalysis
    overall_weipu_score: float  # 0-100 predicted Weipu AIGC probability
    level: str  # low/medium/high
    high_risk_signals: list[str]
    rewrite_suggestions: list[str]


# ============================================================================
# Sentence-level analysis (维普核心)
# ============================================================================
def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 2]


def _split_weipu_windows(text: str, window_size: int = 180) -> list[str]:
    """
    Weipu scans in 150-200 char overlapping windows.
    This mimics their micro-scanning approach.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return [text] if len(text) >= 30 else []

    windows = []
    current = ""
    for s in sentences:
        if len(current) + len(s) <= window_size:
            current += s + "。"
        else:
            if len(current) >= 30:
                windows.append(current)
            current = s + "。"
    if len(current) >= 30:
        windows.append(current)

    return windows


def analyze_sentence_level(text: str) -> SentenceLevelAnalysis:
    """
    Weipu's core: sentence-level micro-analysis.
    Analyzes each sentence and its relationship to neighbors.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return SentenceLevelAnalysis(
            sentence_count=len(sentences), mean_len=0, std_len=0, length_cv=0,
            adjacent_diffs=[], mean_adjacent_diff=0, adj_diff_cv=0,
            consecutive_similar_count=0, long_sentence_ratio=0,
            score=50.0, detail="文本过短，无法进行句子级分析",
        )

    lengths = [len(s) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    std_len = math.sqrt(variance)
    length_cv = std_len / mean_len if mean_len > 0 else 0

    # Adjacent sentence length differences (v4.0 new)
    adjacent_diffs = []
    for i in range(len(lengths) - 1):
        diff = abs(lengths[i] - lengths[i+1])
        adjacent_diffs.append(diff)

    mean_adjacent_diff = sum(adjacent_diffs) / len(adjacent_diffs) if adjacent_diffs else 0
    adj_variance = sum((d - mean_adjacent_diff) ** 2 for d in adjacent_diffs) / len(adjacent_diffs) if adjacent_diffs else 0
    adj_diff_cv = math.sqrt(adj_variance) / mean_adjacent_diff if mean_adjacent_diff > 0 else 0

    # Continuous similar sentence detection (3+ consecutive sentences with similar length)
    consecutive_similar = 0
    current_streak = 1
    for i in range(1, len(lengths)):
        if abs(lengths[i] - lengths[i-1]) <= 3:  # within 3 chars = similar
            current_streak += 1
        else:
            if current_streak >= 3:
                consecutive_similar += 1
            current_streak = 1
    if current_streak >= 3:
        consecutive_similar += 1

    # Long sentence ratio
    long_count = sum(1 for l in lengths if l > 30)
    long_ratio = long_count / len(lengths)

    # Scoring: Weipu is stricter than CNKI
    score = 50.0
    detail_parts = []

    # CV scoring (tighter thresholds than CNKI)
    if length_cv < 0.20:
        score += 30
        detail_parts.append(f"句长CV极低({length_cv:.2f})，强烈AI特征")
    elif length_cv < 0.30:
        score += 20
        detail_parts.append(f"句长CV偏低({length_cv:.2f})，较强AI特征")
    elif length_cv < 0.45:
        score += 5
        detail_parts.append(f"句长CV中等({length_cv:.2f})")
    else:
        score -= 10
        detail_parts.append(f"句长CV自然({length_cv:.2f})")

    # Adjacent diff uniformity (low variation = AI)
    if adj_diff_cv < 0.5:
        score += 15
        detail_parts.append(f"相邻句长差异过于均匀(cv={adj_diff_cv:.2f})")
    elif adj_diff_cv > 1.0:
        score -= 5

    # Consecutive similar sentences (Weipu: 3 = trigger)
    if consecutive_similar >= 2:
        score += 15
        detail_parts.append(f"检测到{consecutive_similar}组连续相似句式")
    elif consecutive_similar >= 1:
        score += 8

    # Long sentence ratio (Weipu scrutinizes long sentences harder)
    if long_ratio > 0.5 and length_cv < 0.35:
        score += 10
        detail_parts.append(f"长句比例高({long_ratio:.0%})且句长均匀")

    score = min(100, max(0, score))
    detail = "；".join(detail_parts) if detail_parts else "句子级特征正常"

    return SentenceLevelAnalysis(
        sentence_count=len(sentences),
        mean_len=round(mean_len, 1),
        std_len=round(std_len, 1),
        length_cv=round(length_cv, 3),
        adjacent_diffs=[round(d, 1) for d in adjacent_diffs[:20]],
        mean_adjacent_diff=round(mean_adjacent_diff, 1),
        adj_diff_cv=round(adj_diff_cv, 3),
        consecutive_similar_count=consecutive_similar,
        long_sentence_ratio=round(long_ratio, 3),
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# 9 Individual Signal Detectors
# ============================================================================

def signal1_template_cooccurrence(text: str) -> WeipuSignalResult:
    """Signal 1: Template phrase co-occurrence (HIGH severity)."""
    found_phrases = []
    positions = []

    for pattern in WEIPU_TEMPLATE_PHRASES:
        for match in re.finditer(pattern, text):
            found_phrases.append(match.group())
            positions.append(match.start())

    # Check co-occurrence pairs
    cooccur_count = 0
    for a, b in COOCCURRENCE_PAIRS:
        a_positions = [m.start() for m in re.finditer(re.escape(a), text)]
        b_positions = [m.start() for m in re.finditer(re.escape(b), text)]
        for ap in a_positions:
            for bp in b_positions:
                if 0 < abs(bp - ap) < 100:
                    cooccur_count += 1

    total_hits = len(found_phrases) + cooccur_count * 2  # co-occurrence weighted higher

    if total_hits >= 15:
        score = 90.0
        detail = f"检测到{len(found_phrases)}个模板词组+{cooccur_count}对共现组合，密集模板化，极强AI特征"
    elif total_hits >= 10:
        score = 70.0
        detail = f"模板词组较多({len(found_phrases)}个+{cooccur_count}对共现)，强AI特征"
    elif total_hits >= 5:
        score = 45.0
        detail = f"存在{len(found_phrases)}个模板词组"
    else:
        score = 15.0
        detail = "模板词组使用正常"

    return WeipuSignalResult(
        signal_id=1, name="模板词组共现", severity="high",
        score=round(score, 1), detail=detail,
        raw_data={"found_phrases": found_phrases[:15], "cooccurrence_pairs": cooccur_count},
    )


def signal2_sentence_uniformity(text: str, sent_analysis: SentenceLevelAnalysis) -> WeipuSignalResult:
    """Signal 2: Sentence pattern uniformity (HIGH severity)."""
    sentences = _split_sentences(text)
    pattern_hits = 0
    pattern_details = []

    for pattern, label in SENTENCE_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            pattern_hits += len(matches)
            pattern_details.append(f"{label}: {len(matches)}处")

    # Combine with sentence analysis
    cv = sent_analysis.length_cv
    consecutive = sent_analysis.consecutive_similar_count

    score = 30.0
    if cv < 0.2 and consecutive >= 2:
        score = 92.0
    elif cv < 0.3 and consecutive >= 1:
        score = 75.0
    elif cv < 0.35:
        score = 55.0
    elif cv < 0.5:
        score = 30.0
    else:
        score = 10.0

    if pattern_hits >= 3:
        score = min(100, score + 15)

    detail = f"句长CV={cv:.2f}，连续相似{consecutive}组" + (f"，固定句式{pattern_hits}处" if pattern_hits else "")

    return WeipuSignalResult(
        signal_id=2, name="句式过于工整", severity="high",
        score=round(score, 1), detail=detail,
        raw_data={"cv": cv, "consecutive_similar": consecutive, "pattern_hits": pattern_hits},
    )


def signal3_style_uniformity(text: str) -> WeipuSignalResult:
    """Signal 3: Style distribution uniformity (HIGH severity).
    Weipu checks if every paragraph maintains identical tone/style."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) >= 30]

    if len(paragraphs) < 2:
        return WeipuSignalResult(
            signal_id=3, name="AI风格分布均匀", severity="high",
            score=40.0, detail="段落数不足，无法分析风格一致性",
        )

    # Style fingerprints: measure sentence count, avg length, connector ratio per paragraph
    fingerprints = []
    for p in paragraphs:
        sents = _split_sentences(p)
        if not sents:
            continue
        avg_len = sum(len(s) for s in sents) / len(sents)
        connector_count = sum(1 for pattern in WEIPU_TEMPLATE_PHRASES[:6]
                            for _ in re.finditer(pattern.replace(".*", ""), p))
        connector_ratio = connector_count / len(sents) if sents else 0
        fingerprints.append((len(sents), round(avg_len), round(connector_ratio, 2)))

    if len(fingerprints) < 2:
        return WeipuSignalResult(
            signal_id=3, name="AI风格分布均匀", severity="high",
            score=40.0, detail="段落数不足",
        )

    # Calculate consistency (lower variance = more AI-like)
    sent_counts = [f[0] for f in fingerprints]
    avg_lens = [f[1] for f in fingerprints]
    connector_ratios = [f[2] for f in fingerprints]

    cv_sents = math.sqrt(sum((s - sum(sent_counts)/len(sent_counts))**2 for s in sent_counts) / len(sent_counts)) / (sum(sent_counts)/len(sent_counts)) if sum(sent_counts)/len(sent_counts) > 0 else 0
    cv_lens = math.sqrt(sum((l - sum(avg_lens)/len(avg_lens))**2 for l in avg_lens) / len(avg_lens)) / (sum(avg_lens)/len(avg_lens)) if sum(avg_lens)/len(avg_lens) > 0 else 0

    if cv_sents < 0.3 and cv_lens < 0.2:
        score = 85.0
        detail = f"段落风格高度一致(句子数cv={cv_sents:.2f}, 句长cv={cv_lens:.2f})，极强AI特征"
    elif cv_sents < 0.5 and cv_lens < 0.3:
        score = 60.0
        detail = f"段落风格较一致，存在AI特征"
    elif cv_sents < 0.7:
        score = 30.0
        detail = "段落风格有一定变化"
    else:
        score = 10.0
        detail = "段落风格变化自然"

    return WeipuSignalResult(
        signal_id=3, name="AI风格分布均匀", severity="high",
        score=round(score, 1), detail=detail,
    )


def signal4_training_data_match(text: str) -> WeipuSignalResult:
    """Signal 4: Training data matching (HIGH severity).
    Weipu checks against known LLM output patterns from GPT/DeepSeek/Kimi/etc."""
    # Known LLM fingerprint patterns that Weipu's training data includes
    LLM_FINGERPRINTS = [
        # DeepSeek patterns
        r'从某种意义.*来说',
        r'需要.*注意.*的是',
        r'值得.*深思.*的是',
        # GPT patterns
        r'It is (worth|important|necessary) (noting|to note|mentioning)',
        r'In (conclusion|summary|other words)',
        r'Furthermore.*Moreover',
        # Kimi patterns
        r'换.*角度.*来看',
        r'如果.*深入.*思考',
        r'换个.*思路.*来看',
        # General LLM patterns
        r'(不是.*而是).{5,30}(更不是.*而是)',
        r'(既要.*又要).{5,30}(既不能.*也不能)',
    ]

    total_matches = 0
    matched_patterns = []
    for pattern in LLM_FINGERPRINTS:
        matches = re.findall(pattern, text)
        if matches:
            total_matches += len(matches)
            matched_patterns.append(pattern[:30])

    text_len = len(text)
    density = total_matches / max(1, text_len) * 1000

    if density > 0.5:
        score = 80.0
        detail = f"匹配到{total_matches}处已知LLM指纹特征(密度{density:.2f}/千字)，强AI特征"
    elif density > 0.2:
        score = 55.0
        detail = f"部分匹配LLM指纹特征({total_matches}处)"
    elif total_matches > 0:
        score = 30.0
        detail = f"少量LLM指纹匹配({total_matches}处)"
    else:
        score = 10.0
        detail = "未匹配到已知LLM指纹"

    return WeipuSignalResult(
        signal_id=4, name="训练数据匹配", severity="high",
        score=round(score, 1), detail=detail,
        raw_data={"match_count": total_matches, "density": round(density, 3)},
    )


def signal5_cross_paragraph_perfection(text: str) -> WeipuSignalResult:
    """Signal 5: Cross-paragraph semantic perfection (MEDIUM severity).
    Weipu flags paragraphs that transition TOO smoothly."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) >= 30]

    if len(paragraphs) < 2:
        return WeipuSignalResult(
            signal_id=5, name="跨段语义关联过完美", severity="medium",
            score=30.0, detail="段落数不足",
        )

    # Count paragraphs that start with explicit semantic connectors
    transition_count = 0
    for i, p in enumerate(paragraphs[1:], 1):
        first_sentence = _split_sentences(p)
        if first_sentence:
            first = first_sentence[0]
            for conn in SEMANTIC_CONNECTORS:
                if conn in first:
                    transition_count += 1
                    break

    transition_ratio = transition_count / (len(paragraphs) - 1)

    if transition_ratio > 0.8:
        score = 80.0
        detail = f"段落衔接过于完美({transition_count}/{len(paragraphs)-1}段有显式过渡)，AI特征"
    elif transition_ratio > 0.5:
        score = 55.0
        detail = f"段落衔接较规整({transition_count}/{len(paragraphs)-1}段)"
    elif transition_ratio > 0.3:
        score = 30.0
        detail = "段落过渡基本自然"
    else:
        score = 8.0
        detail = "段落过渡自然多变"

    return WeipuSignalResult(
        signal_id=5, name="跨段语义关联过完美", severity="medium",
        score=round(score, 1), detail=detail,
    )


def signal6_terminology_normalization(text: str) -> WeipuSignalResult:
    """Signal 6: Terminology normalization without variation (MEDIUM severity).
    Weipu: 7 terms per 100 chars triggers "term stacking density" alert."""
    # Reuse the DISCIPLINE_TERMS from CNKI scanner; simplified here
    COMMON_TERMS = [
        "人工智能", "机器学习", "深度学习", "数据分析", "神经网络",
        "算法", "模型", "系统", "技术", "方法", "策略", "机制",
        "结构化", "模块化", "数字化", "智能化", "信息化",
        "优化", "创新", "突破", "改进", "完善", "提升",
        "实验", "研究", "分析", "验证", "评估", "检测",
    ]

    term_positions = []
    for term in COMMON_TERMS:
        for match in re.finditer(re.escape(term), text):
            term_positions.append((match.start(), term))

    text_len = len(text)
    term_density = (len(term_positions) / text_len * 100) if text_len > 0 else 0

    # Check if terms are always used in their "standard" form (no colloquial variants)
    colloquial_variants = {
        "利用": r'用(?!.*方法|.*技术)',
        "实施": r'(做|干)(?!.*实验)',
        "开展": r'(做|搞)(?!.*研究)',
        "进行": r'(做|干)(?!.*分析)',
    }

    has_colloquial = False
    for _formal, pattern in colloquial_variants.items():
        if re.search(pattern, text):
            has_colloquial = True
            break

    # Weipu threshold: 7 terms/100 chars
    if term_density > 10:
        score = 85.0
        detail = f"术语堆叠密度极高({term_density:.1f}/百字)，超过维普阈值(7/百字)"
    elif term_density > 7:
        score = 65.0
        detail = f"术语密度偏高({term_density:.1f}/百字)，超过维普阈值"
    elif term_density > 4:
        score = 35.0
        detail = f"术语密度正常({term_density:.1f}/百字)"
    else:
        score = 12.0
        detail = "术语使用正常"

    if not has_colloquial and term_density > 3:
        score = min(100, score + 10)
        detail += "，且无口语化变体"

    return WeipuSignalResult(
        signal_id=6, name="学术术语规范化无变化", severity="medium",
        score=round(score, 1), detail=detail,
        raw_data={"term_density": round(term_density, 1), "has_colloquial": has_colloquial},
    )


def signal7_lack_of_colloquial(text: str) -> WeipuSignalResult:
    """Signal 7: Lack of colloquial supplements (MEDIUM severity).
    Weipu: 100% rigorous expression, no personal-feeling language = AI signal."""
    # Personal/colloquial expression markers
    COLLOQUIAL_MARKERS = [
        r'(我|笔者|作者)(个人|自己)?(认为|觉得|感觉|看来)',
        r'(说句|坦白|老实|说实在)[话说]?',
        r'换[个句]话说',
        r'有意思的是',
        r'不得不[承认说]',
        r'说实话',
        r'其实',
        r'说白了',
        r'打个比方',
        r'举个例[子说]',
        r'值得一[提试]',
    ]

    colloquial_count = 0
    for pattern in COLLOQUIAL_MARKERS:
        matches = re.findall(pattern, text)
        colloquial_count += len(matches)

    text_len = len(text)
    density = colloquial_count / max(1, text_len) * 1000

    if colloquial_count == 0 and text_len > 500:
        score = 82.0
        detail = "全文无任何个人感受或口语化表达，100%严谨书面语，强AI特征"
    elif colloquial_count == 0:
        score = 55.0
        detail = "缺少口语化补充，但文本较短"
    elif density < 0.5:
        score = 50.0
        detail = f"口语化表达极少({colloquial_count}处)，仍偏AI风格"
    elif density < 1.5:
        score = 25.0
        detail = f"有一定口语化表达({colloquial_count}处)"
    else:
        score = 8.0
        detail = f"口语化表达自然({colloquial_count}处)"

    return WeipuSignalResult(
        signal_id=7, name="缺少口语化补充", severity="medium",
        score=round(score, 1), detail=detail,
    )


def signal8_length_uniformity(sent_analysis: SentenceLevelAnalysis) -> WeipuSignalResult:
    """Signal 8: Length uniformity without rhythm (LOW severity)."""
    cv = sent_analysis.length_cv
    adj_cv = sent_analysis.adj_diff_cv

    if cv < 0.2 and adj_cv < 0.5:
        score = 85.0
        detail = f"句长和节奏高度均匀(cv={cv:.2f}, adj_cv={adj_cv:.2f})，无自然节奏"
    elif cv < 0.3:
        score = 55.0
        detail = f"长度较均匀(cv={cv:.2f})，缺乏节奏变化"
    elif cv < 0.45:
        score = 30.0
        detail = "长度有一定变化"
    else:
        score = 8.0
        detail = "长度变化自然，有节奏感"

    return WeipuSignalResult(
        signal_id=8, name="长度均匀无节奏", severity="low",
        score=round(score, 1), detail=detail,
    )


def signal9_citation_perfection(text: str) -> WeipuSignalResult:
    """Signal 9: Citation format perfection (LOW severity).
    Every citation is in standard [Author, Year] format = AI signal."""
    standard_citation_pattern = r'\[[A-Za-z一-鿿]+\s*[,，]\s*\d{4}\]'
    standard_citations = re.findall(standard_citation_pattern, text)

    # Check for variation in citation styles
    has_varied = bool(re.search(r'[\(（]\d{4}[\)）]', text))  # (2024) style
    has_narrative = bool(re.search(r'[A-Za-z一-鿿]+\s*[\(（]\d{4}[\)）].{2,20}(提出|认为|发现|指出)', text))

    n_standard = len(standard_citations)

    if n_standard >= 5 and not has_varied:
        score = 75.0
        detail = f"{n_standard}处引用全为[作者, 年份]标准格式，无引用风格变化，AI特征"
    elif n_standard >= 3 and not (has_varied or has_narrative):
        score = 50.0
        detail = f"引用格式较单一({n_standard}处标准格式)"
    elif n_standard > 0 and (has_varied or has_narrative):
        score = 18.0
        detail = "引用风格有变化"
    elif n_standard == 0:
        score = 20.0
        detail = "无格式化引用（可能不适用）"
    else:
        score = 30.0
        detail = "引用格式基本正常"

    return WeipuSignalResult(
        signal_id=9, name="引用格式过于规整", severity="low",
        score=round(score, 1), detail=detail,
        raw_data={"standard_citations": n_standard, "has_varied": has_varied, "has_narrative": has_narrative},
    )


# ============================================================================
# Complete Weipu Scan
# ============================================================================
def scan_weipu_features(
    text: str,
    mode: str = "general",
    discipline: str | None = None,
) -> WeipuFeatureReport:
    """Run all 9 Weipu detection signals and produce aggregated report."""

    # Core sentence-level analysis
    sent_analysis = analyze_sentence_level(text)

    # Run all 9 signals
    s1 = signal1_template_cooccurrence(text)
    s2 = signal2_sentence_uniformity(text, sent_analysis)
    s3 = signal3_style_uniformity(text)
    s4 = signal4_training_data_match(text)
    s5 = signal5_cross_paragraph_perfection(text)
    s6 = signal6_terminology_normalization(text)
    s7 = signal7_lack_of_colloquial(text)
    s8 = signal8_length_uniformity(sent_analysis)
    s9 = signal9_citation_perfection(text)

    signals = [s1, s2, s3, s4, s5, s6, s7, s8, s9]

    # Weighted aggregation — Weipu weights HIGH severity signals more
    weights = [0.18, 0.18, 0.14, 0.14, 0.10, 0.08, 0.08, 0.05, 0.05]

    if mode == "academic":
        # Academic mode: increase terminology and citation weight
        weights = [0.16, 0.16, 0.12, 0.12, 0.10, 0.10, 0.09, 0.05, 0.10]

    overall = sum(w * s.score for w, s in zip(weights, signals))
    overall = round(overall, 1)

    if overall < 30:
        level = "low"
    elif overall < 70:
        level = "medium"
    else:
        level = "high"

    # High-risk signals (score > 60)
    high_risk = [s.name for s in signals if s.score > 60]

    # Rewrite suggestions
    suggestions = []
    if s1.score > 60:
        suggestions.append(f"模板词组共现过多：需删除60%以上'随着XX发展''值得注意的是'等模板短语，打破固定搭配")
    if s2.score > 60:
        suggestions.append(f"句式过于工整(CV={sent_analysis.length_cv:.2f})：需打破3句以上连续相似句式，随机改变句子长度和结构")
    if s3.score > 60:
        suggestions.append("全文风格过于一致：不同段落应采用不同的表达风格，有的严谨有的轻松")
    if s4.score > 60:
        suggestions.append("检测到LLM指纹特征：需改变深层表达逻辑，避免'从某种意义来说''值得注意的是'等LLM常用表达")
    if s5.score > 60:
        suggestions.append("段落衔接过于完美：删除40-60%的显式过渡词，让部分段落直接开始")
    if s6.score > 60:
        suggestions.append("术语堆叠密度过高：适当位置用口语化表达替代术语（'利用'→'用'，'开展'→'做'）")
    if s7.score > 60:
        suggestions.append("缺少个人感受：加入'我个人认为''有意思的是''说实话'等主观表达")
    if s8.score > 60:
        suggestions.append("节奏过于均匀：制造'短-长-短'交替节奏，增加句长变化")
    if s9.score > 60:
        suggestions.append("引用格式过于规整：混合使用叙述式引用([Author] (Year) 提出...)和括号式引用")

    return WeipuFeatureReport(
        signals=signals,
        sentence_analysis=sent_analysis,
        overall_weipu_score=overall,
        level=level,
        high_risk_signals=high_risk,
        rewrite_suggestions=suggestions,
    )
