"""
CNKI 8-Dimension Feature Scanner for AIGC Detection.

Models the detection logic from CNKI patents CN117151074A (v1) and CN119357388A (v2):
  1. Sentence structure uniformity (句长分布)
  2. Paragraph structure similarity (段落结构相似度)
  3. Information density (信息密度，每百字实义词)
  4. Connector distribution uniformity (连接词分布均匀性)
  5. Terminology matching score (专业术语匹配度)
  6. Citation quality (引文质量)
  7. Data/case specificity (数据/案例具体性)
  8. Logical coherence (逻辑连贯性)

Reference: 安彤、薛德军等 (2025), 《知识管理论坛》
"""

import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Dimension 4: Connector / transition phrase catalog
# ---------------------------------------------------------------------------
CNKI_CONNECTORS = [
    # High-trigger: very common AI connectors
    "综上所述", "由此可见", "值得注意的是", "不可忽视",
    "具有重要意义", "不言而喻", "综合考虑",
    # Medium-trigger: template transitions
    "首先", "其次", "最后", "此外", "与此同时",
    "另一方面", "从某种程度上说", "在一定程度上",
    "相对而言", "大体上来说", "需要指出的是",
    "在未来的发展中", "随着.*的不断发展",
    "发挥着.*重要作用", "为.*做出了.*贡献",
    "越来越重要", "不可或缺", "至关重要",
    "不仅.*而且", "既.*又",
    # New in CNKI v3.0 (2025-2026): evenly-spaced connectors
    "基于此", "鉴于此", "有鉴于此", "由此观之",
    "总而言之", "总之", "综上", "概而言之",
]

# ---------------------------------------------------------------------------
# Dimension 5: Common academic terminology by discipline (starter set)
# ---------------------------------------------------------------------------
DISCIPLINE_TERMS = {
    "cs": [
        "机器学习", "深度学习", "神经网络", "卷积", "循环神经网络",
        "注意力机制", "Transformer", "BERT", "GPT", "大语言模型",
        "自然语言处理", "计算机视觉", "特征提取", "语义分割",
        "目标检测", "强化学习", "迁移学习", "联邦学习", "知识图谱",
        "表示学习", "自监督学习", "对比学习", "扩散模型",
        "损失函数", "梯度下降", "反向传播", "过拟合", "正则化",
        "残差网络", "生成对抗网络", "变分自编码器", "图神经网络",
    ],
    "medical": [
        "临床", "诊断", "治疗", "预后", "病理", "生理", "药理",
        "影像学", "超声", "CT", "MRI", "核磁共振", "X线",
        "血液", "细胞", "基因", "蛋白", "免疫", "代谢", "内分泌",
        "手术", "术后", "并发症", "适应症", "禁忌症",
        "随机对照", "双盲", "安慰剂", "队列研究", "荟萃分析",
        "发病率", "死亡率", "生存率", "有效率", "不良反应",
        "糖尿病", "高血压", "冠心病", "肿瘤", "脑卒中", "肺炎",
    ],
    "engineering": [
        "有限元", "力学", "应力", "应变", "载荷", "疲劳", "断裂",
        "热传导", "流体", "湍流", "层流", "雷诺数", "CFD",
        "材料", "合金", "复合", "纳米", "腐蚀", "磨损", "润滑",
        "电机", "电路", "电压", "电流", "功率", "频率", "阻抗",
        "控制", "反馈", "PID", "鲁棒", "自适应", "最优控制",
        "信号", "滤波", "采样", "傅里叶", "小波", "频域", "时域",
    ],
    "economics": [
        "GDP", "CPI", "货币政策", "财政政策", "利率", "通货膨胀",
        "供需", "均衡", "边际", "效用", "弹性", "外部性",
        "市场结构", "垄断", "寡头", "博弈", "纳什均衡",
        "回归分析", "面板数据", "工具变量", "内生性", "因果推断",
        "经济增长", "人力资本", "全要素生产率", "索洛模型",
    ],
    "law": [
        "法条", "司法解释", "判例", "管辖权", "诉讼", "仲裁",
        "合同", "侵权", "物权", "债权", "知识产权", "商标", "专利",
        "刑事", "民事", "行政", "宪法", "立法", "司法",
        "当事人", "原告", "被告", "证据", "举证", "质证",
        "法律适用", "法律效力", "法律责任", "法律后果",
    ],
}


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 2]


def _split_paragraphs(text: str) -> list[str]:
    raw = re.split(r'\n\s*\n', text)
    return [p.strip() for p in raw if len(p.strip()) >= 30]


def _content_words(text: str) -> list[str]:
    """Extract content (实义) words: nouns, verbs, adjectives, excluding
    function words, pronouns, conjunctions, and particles."""
    FUNCTION_CHARS = set(
        "的了吗呢吧啊着过把被对从到在"
        "和与或但而虽然而因此因为所以"
        "这个是那个它们你我他她它"
        "只很都也还就更已经再又"
        "一二三四五六七八九十百千万"
        "第次个种些点之以其及并"
    )
    words = []
    # Segment by common delimiters, then filter function chars
    for segment in re.split(r'[，。！？、：；""''（）\s]+', text):
        # Crude: count chars that are NOT function chars
        content_chars = [c for c in segment if c not in FUNCTION_CHARS and '一' <= c <= '鿿']
        if content_chars:
            words.append(''.join(content_chars))
    return words


@dataclass
class SentenceStructureResult:
    sentence_count: int
    mean_len: float
    std_len: float
    cv: float  # coefficient of variation
    distribution_type: str  # "unimodal" (AI-like), "multimodal" (human-like), "insufficient"
    distribution_bins: list[int] = field(default_factory=list)
    score: float = 50.0  # 0-100, higher = more AI-like
    detail: str = ""


@dataclass
class ParagraphSimilarityResult:
    paragraph_count: int
    similarity_scores: list[float] = field(default_factory=list)
    mean_similarity: float = 0.0
    score: float = 50.0
    detail: str = ""


@dataclass
class InformationDensityResult:
    mean_density: float  # content words per 100 chars
    std_density: float
    score: float = 50.0
    detail: str = ""


@dataclass
class ConnectorResult:
    total_connectors: int
    per_1000_chars: float
    positions: list[int]  # char positions of each connector
    uniformity_score: float  # 0-1, 1 = perfectly uniform
    score: float = 50.0
    found_patterns: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class TerminologyResult:
    term_density: float  # terms per 1000 chars
    term_variation: float  # how much the term usage varies across paragraphs
    score: float = 50.0
    detail: str = ""


@dataclass
class CitationResult:
    has_citations: bool
    citation_count: int
    has_specific_refs: bool  # real-looking references vs "有研究表明"
    vague_refs: list[str] = field(default_factory=list)
    score: float = 50.0
    detail: str = ""


@dataclass
class DataSpecificityResult:
    has_numbers: bool
    number_density: float  # numbers per 1000 chars
    has_specific_data: bool  # real statistics vs "大约""很多"
    vague_quantifiers: list[str] = field(default_factory=list)
    score: float = 50.0
    detail: str = ""


@dataclass
class LogicalCoherenceResult:
    paragraph_transitions: int  # count of inter-paragraph logical connections
    transition_quality: float  # 0-1, 1 = every paragraph has explicit transition
    score: float = 50.0
    detail: str = ""


@dataclass
class CNKIFeatureReport:
    """Complete 8-dimension feature analysis."""
    # D1
    sentence_structure: SentenceStructureResult
    # D2
    paragraph_similarity: ParagraphSimilarityResult
    # D3
    information_density: InformationDensityResult
    # D4
    connectors: ConnectorResult
    # D5
    terminology: TerminologyResult
    # D6
    citations: CitationResult
    # D7
    data_specificity: DataSpecificityResult
    # D8
    logical_coherence: LogicalCoherenceResult

    # Aggregated
    overall_cnki_score: float  # 0-100, predicted CNKI AIGC probability
    level: str  # "low" / "medium" / "high"
    high_risk_dimensions: list[str] = field(default_factory=list)
    rewrite_suggestions: list[str] = field(default_factory=list)


# ============================================================================
# Dimension 1: Sentence Structure Analysis
# ============================================================================
def analyze_sentence_structure(text: str) -> SentenceStructureResult:
    """
    CNKI checks if sentence lengths follow a unimodal bell curve (15-25 chars),
    which strongly indicates AI generation. Human writing has multi-modal
    distribution with natural variation.

    The 2026 CNKI v3.0 threshold tightens: CV < 0.35 triggers high suspicion.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return SentenceStructureResult(
            sentence_count=len(sentences), mean_len=0, std_len=0, cv=0,
            distribution_type="insufficient", score=50.0,
            detail="文本过短，无法分析句式结构",
        )

    lengths = [len(s) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    std_len = math.sqrt(variance)
    cv = std_len / mean_len if mean_len > 0 else 0

    # Build histogram bins (5 chars each) to detect unimodal vs multimodal
    bins = [0] * 12  # 0-5, 5-10, ..., 55-60+
    for l in lengths:
        idx = min(l // 5, 11)
        bins[idx] += 1

    # Detect peaks: count bins that are local maxima
    peaks = 0
    for i in range(1, len(bins) - 1):
        if bins[i] > bins[i-1] and bins[i] > bins[i+1] and bins[i] > 0:
            peaks += 1

    if peaks <= 1:
        distribution_type = "unimodal"
    elif peaks >= 3:
        distribution_type = "multimodal"
    else:
        distribution_type = "bimodal"

    # CNKI scoring logic
    # CV < 0.3 → high AI (CNKI v3.0 uses 0.35)
    if cv < 0.25:
        score = 90.0
        detail = f"句长高度均匀(CV={cv:.2f})，呈单峰分布，极强AI特征"
    elif cv < 0.35:
        score = 75.0
        detail = f"句长较均匀(CV={cv:.2f})，分布偏单峰，较强AI特征"
    elif cv < 0.5:
        score = 40.0
        detail = f"句长有一定变化(CV={cv:.2f})，接近自然分布"
    elif cv < 0.7:
        score = 20.0
        detail = f"句长变化自然(CV={cv:.2f})，多峰分布，人写特征"
    else:
        score = 5.0
        detail = f"句长变化丰富(CV={cv:.2f})，典型人写特征"

    # Boost score if unimodal AND CV is low
    if distribution_type == "unimodal" and cv < 0.4:
        score = min(100, score + 10)

    return SentenceStructureResult(
        sentence_count=len(sentences),
        mean_len=round(mean_len, 1),
        std_len=round(std_len, 1),
        cv=round(cv, 3),
        distribution_type=distribution_type,
        distribution_bins=bins,
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Dimension 2: Paragraph Structure Similarity
# ============================================================================
def analyze_paragraph_similarity(text: str) -> ParagraphSimilarityResult:
    """
    CNKI checks whether all paragraphs follow the same "topic-explain-example-
    summary" template. AI-generated text often has paragraph embedding
    similarities of 0.7-0.9, while human writing is 0.2-0.5.

    We approximate embedding similarity using structural fingerprinting:
    - Sentence count per paragraph
    - Lead sentence type (question/statement/quote)
    - Presence of connector words in first/last sentence
    """
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 2:
        return ParagraphSimilarityResult(
            paragraph_count=len(paragraphs),
            similarity_scores=[],
            mean_similarity=0,
            score=30.0,
            detail="段落数不足，无法分析段落相似度",
        )

    # Build structural fingerprint for each paragraph
    def fingerprint(para: str) -> tuple:
        sentences = _split_sentences(para)
        n_sent = len(sentences)

        # Lead sentence characteristics
        first = sentences[0] if sentences else ""
        starts_with_question = first.endswith("？") or first.endswith("?")
        starts_with_connector = any(
            re.match(c.replace(".*", ""), first) for c in CNKI_CONNECTORS[:6]
        )

        # Last sentence characteristics
        last = sentences[-1] if len(sentences) > 1 else ""
        ends_with_summary = any(
            kw in last for kw in ["综上所述", "总之", "因此", "由此可见", "综上"]
        )

        return (n_sent, starts_with_question, starts_with_connector, ends_with_summary)

    fps = [fingerprint(p) for p in paragraphs]

    # Compute pairwise Jaccard-like similarity of fingerprints
    similarities = []
    for i in range(len(fps)):
        for j in range(i + 1, len(fps)):
            match = sum(1 for a, b in zip(fps[i], fps[j]) if a == b)
            sim = match / len(fps[i])
            similarities.append(sim)

    mean_sim = sum(similarities) / len(similarities) if similarities else 0

    # CNKI threshold: > 0.7 = high AI suspicion
    if mean_sim > 0.75:
        score = 85.0
        detail = f"段落结构高度相似({mean_sim:.2f})，呈现模板化特征，极强AI信号"
    elif mean_sim > 0.6:
        score = 65.0
        detail = f"段落结构较相似({mean_sim:.2f})，存在模板化倾向"
    elif mean_sim > 0.4:
        score = 35.0
        detail = f"段落结构有一定差异({mean_sim:.2f})，部分段落自然变化"
    else:
        score = 10.0
        detail = f"段落结构变化自然({mean_sim:.2f})，人写特征"

    return ParagraphSimilarityResult(
        paragraph_count=len(paragraphs),
        similarity_scores=[round(s, 3) for s in similarities[:10]],
        mean_similarity=round(mean_sim, 3),
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Dimension 3: Information Density
# ============================================================================
def analyze_information_density(text: str) -> InformationDensityResult:
    """
    CNKI measures "information density" as content words per 100 characters.
    AI text: 65-75% with almost no variance across paragraphs.
    Human text: 40-80% with natural peaks and valleys.
    """
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        paragraphs = [text]

    densities = []
    for p in paragraphs:
        content = _content_words(p)
        content_chars = sum(len(w) for w in content)
        total_chars = len(re.sub(r'\s', '', p))
        if total_chars > 0:
            density = (content_chars / total_chars) * 100
        else:
            density = 0
        densities.append(density)

    mean_density = sum(densities) / len(densities) if densities else 0
    variance = sum((d - mean_density) ** 2 for d in densities) / len(densities) if len(densities) > 1 else 0
    std_density = math.sqrt(variance)

    # CNKI scoring
    # AI text: mean 65-75%, std < 5 (very stable)
    if 60 <= mean_density <= 80 and std_density < 5:
        score = 85.0
        detail = f"信息密度稳定在{mean_density:.0f}%±{std_density:.1f}%，密度过于均匀，强AI特征"
    elif std_density < 8:
        score = 60.0
        detail = f"信息密度波动较小(std={std_density:.1f})，存在AI特征"
    elif std_density < 15:
        score = 30.0
        detail = f"信息密度有自然波动(std={std_density:.1f})，接近人写"
    else:
        score = 10.0
        detail = f"信息密度波动自然(std={std_density:.1f})，人写特征"

    return InformationDensityResult(
        mean_density=round(mean_density, 1),
        std_density=round(std_density, 1),
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Dimension 4: Connector Distribution Uniformity
# ============================================================================
def analyze_connectors(text: str) -> ConnectorResult:
    """
    CNKI checks not just connector FREQUENCY but POSITIONAL UNIFORMITY.
    AI text: 8-15 connectors per 1000 chars, EVENLY SPACED every 80-120 chars.
    Human text: 2-6 per 1000 chars, clustered, not evenly distributed.

    This is a key differentiator added in CNKI v3.0 (2025).
    """
    # Find all connector positions
    positions = []
    found_patterns = []
    for pattern in CNKI_CONNECTORS:
        for match in re.finditer(pattern, text):
            positions.append(match.start())
            found_patterns.append(f"{pattern}:{match.start()}")

    positions.sort()
    total = len(positions)
    text_len = len(text)
    per_1000 = (total / text_len * 1000) if text_len > 0 else 0

    # Calculate uniformity of connector spacing
    if len(positions) >= 3:
        gaps = [positions[i+1] - positions[i] for i in range(len(positions) - 1)]
        mean_gap = sum(gaps) / len(gaps)
        if mean_gap > 0:
            gap_variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
            gap_std = math.sqrt(gap_variance)
            gap_cv = gap_std / mean_gap
            # Lower CV = more uniform = more AI-like
            uniformity = max(0, 1 - gap_cv)
        else:
            uniformity = 0
    else:
        uniformity = 0

    # CNKI scoring based on BOTH density AND uniformity
    if per_1000 > 12 and uniformity > 0.6:
        score = 92.0
        detail = f"连接词密度极高({per_1000:.1f}/千字)且分布均匀(uniformity={uniformity:.2f})，极强AI特征"
    elif per_1000 > 8 and uniformity > 0.4:
        score = 75.0
        detail = f"连接词密度高({per_1000:.1f}/千字)，分布较均匀，强AI特征"
    elif per_1000 > 8:
        score = 55.0
        detail = f"连接词密度偏高({per_1000:.1f}/千字)，但分布不均"
    elif per_1000 > 4:
        score = 30.0
        detail = f"连接词密度正常({per_1000:.1f}/千字)"
    else:
        score = 10.0
        detail = f"连接词使用较少({per_1000:.1f}/千字)，人写特征"

    return ConnectorResult(
        total_connectors=total,
        per_1000_chars=round(per_1000, 1),
        positions=positions,
        uniformity_score=round(uniformity, 3),
        score=round(score, 1),
        found_patterns=found_patterns[:20],
        detail=detail,
    )


# ============================================================================
# Dimension 5: Terminology Matching Score
# ============================================================================
def analyze_terminology(text: str, discipline: str | None = None) -> TerminologyResult:
    """
    CNKI has discipline-specific terminology databases. AI text tends to use
    terms with perfectly consistent formality — never substituting a formal
    term with colloquial language. Human writers naturally mix in simpler
    alternatives.

    We check:
    1. Term density (AI uses higher density of formal terms)
    2. Term variation across paragraphs (AI is too consistent)
    """
    # Collect all known terms
    all_terms = set()
    for terms in DISCIPLINE_TERMS.values():
        all_terms.update(terms)

    # If discipline specified, weight those terms higher
    primary_terms = set()
    if discipline and discipline in DISCIPLINE_TERMS:
        primary_terms = set(DISCIPLINE_TERMS[discipline])

    # Find term occurrences
    term_positions = []
    for term in all_terms:
        for match in re.finditer(re.escape(term), text):
            term_positions.append((match.start(), term))

    text_len = len(text)
    term_density = (len(term_positions) / text_len * 1000) if text_len > 0 else 0

    # Check variation across paragraphs
    paragraphs = _split_paragraphs(text)
    para_term_counts = []
    for p in paragraphs:
        count = 0
        for term in all_terms:
            count += len(re.findall(re.escape(term), p))
        para_term_counts.append(count)

    if len(para_term_counts) >= 2 and sum(para_term_counts) > 0:
        mean_terms = sum(para_term_counts) / len(para_term_counts)
        variance = sum((c - mean_terms) ** 2 for c in para_term_counts) / len(para_term_counts)
        term_variation = math.sqrt(variance) / mean_terms if mean_terms > 0 else 0
    else:
        term_variation = 0

    # Scoring
    if term_density > 20 and term_variation < 0.3:
        score = 80.0
        detail = f"术语密度高({term_density:.1f}/千字)且使用过于均匀(cv={term_variation:.2f})，强AI特征"
    elif term_density > 20:
        score = 55.0
        detail = f"术语密度偏高({term_density:.1f}/千字)，有一定AI特征"
    elif term_variation < 0.2 and term_density > 5:
        score = 50.0
        detail = "术语使用过于均匀，缺少口语化替代表达"
    else:
        score = 20.0
        detail = f"术语使用自然(密度{term_density:.1f}/千字)"

    return TerminologyResult(
        term_density=round(term_density, 1),
        term_variation=round(term_variation, 3),
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Dimension 6: Citation Quality
# ============================================================================
def analyze_citations(text: str) -> CitationResult:
    """
    CNKI checks citation quality:
    - AI often fabricates citations or uses vague references
    - "有研究表明""据统计""相关研究显示" without specifics = red flag
    - Real citations have author names, years, titles, DOIs
    """
    # Vague reference patterns — strong AI signal
    VAGUE_PATTERNS = [
        r'有研究[表明显]示',
        r'据[统调]查[，,]',
        r'相关研\S{1,3}[表明显]示',
        r'大量研\S{1,3}[表明显]示',
        r'许多学\S{1,3}[认为出]',
        r'学\S{1,3}[界领]域',
        r'多数研\S{1,3}',
        r'普遍认\S{1,2}',
        r'一般认\S{1,2}',
        r'众所\S{1,2}知',
    ]

    vague_refs = []
    for pat in VAGUE_PATTERNS:
        matches = re.findall(pat, text)
        vague_refs.extend(matches)

    # Real citation patterns: [1], (Author, Year), Author et al.
    real_citation_patterns = [
        r'\[\d+(?:[,，\s]?\d+)*\]',  # [1] or [1,2,3]
        r'[A-Z][a-z]+\s*(?:et\s*al\.?)?\s*[\(（]\d{4}[\)）]',  # Smith (2020)
        r'[\(（][A-Z][a-z]+\s*(?:et\s*al\.?)?[,，]\s*\d{4}[\)）]',  # (Smith, 2020)
        r'[A-Z][a-z]+\s*(?:et\s*al\.?)?[\(（]\d{4}[\)）]',  # 张三(2020)
    ]

    real_citations = []
    for pat in real_citation_patterns:
        matches = re.findall(pat, text)
        real_citations.extend(matches)

    has_citations = len(real_citations) > 0 or len(vague_refs) > 0
    has_specific_refs = len(real_citations) >= 2

    if len(vague_refs) >= 3 and len(real_citations) < 2:
        score = 85.0
        detail = f"存在{len(vague_refs)}处模糊引用(如'{vague_refs[0] if vague_refs else ''}')且缺少具体文献信息，强AI特征"
    elif len(vague_refs) >= 2:
        score = 60.0
        detail = f"使用{len(vague_refs)}处模糊引用，缺乏具体文献支撑"
    elif has_specific_refs and len(vague_refs) == 0:
        score = 10.0
        detail = f"引用规范，包含{len(real_citations)}处具体文献信息，人写特征"
    elif has_specific_refs:
        score = 30.0
        detail = "引用基本规范"
    else:
        score = 45.0
        detail = "无明显引用（可能不适用于当前文本类型）"

    return CitationResult(
        has_citations=has_citations,
        citation_count=len(real_citations) + len(vague_refs),
        has_specific_refs=has_specific_refs,
        vague_refs=vague_refs[:10],
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Dimension 7: Data/Case Specificity
# ============================================================================
def analyze_data_specificity(text: str) -> DataSpecificityResult:
    """
    AI text prefers general descriptions to specific data.
    "approximately 37.2%" = human (precise)
    "about one-third" = AI-like (vague)
    "显著提升""大幅下降" without numbers = strong AI signal
    """
    # Vague quantifier patterns
    VAGUE_QUANTIFIERS = [
        r'大[幅度量]', r'显[著助]', r'明[显现]', r'较大', r'较小',
        r'一定程\S{1,2}', r'某[些个]', r'不少', r'很多', r'大量',
        r'约[为有]?\d+', r'近\d+', r'超过\d+', r'不足\d+',
        r'较[为高多低少]', r'偏[高低]',
    ]

    vague_hits = []
    for pat in VAGUE_QUANTIFIERS:
        matches = re.findall(pat, text)
        vague_hits.extend(matches)

    # Check for specific numbers (percentages, decimals, exact counts)
    specific_number_patterns = [
        r'\d+\.\d+%',  # 37.2%
        r'\d+\.\d+',   # 3.14
        r'\d{3,}',     # numbers >= 100 (likely data)
    ]

    number_count = 0
    for pat in specific_number_patterns:
        matches = re.findall(pat, text)
        number_count += len(matches)

    text_len = len(text)
    number_density = (number_count / text_len * 1000) if text_len > 0 else 0

    has_specific_data = number_density > 3

    if len(vague_hits) >= 5 and not has_specific_data:
        score = 82.0
        detail = f"使用{len(vague_hits)}处模糊量化词且缺乏具体数据，强AI特征"
    elif len(vague_hits) >= 3 and number_density < 2:
        score = 60.0
        detail = f"模糊量化词较多({len(vague_hits)}处)，数据具体性不足"
    elif has_specific_data and len(vague_hits) < 3:
        score = 12.0
        detail = f"数据具体(密度{number_density:.1f}/千字)，人写特征"
    else:
        score = 35.0
        detail = "数据使用基本平衡"

    return DataSpecificityResult(
        has_numbers=number_count > 0,
        number_density=round(number_density, 1),
        has_specific_data=has_specific_data,
        vague_quantifiers=vague_hits[:15],
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Dimension 8: Logical Coherence
# ============================================================================
def analyze_logical_coherence(text: str) -> LogicalCoherenceResult:
    """
    CNKI checks whether every paragraph transition uses explicit connectors.
    AI text: every paragraph has "首先/其次/此外/另外/最后" transitions —
    too perfect, too coherent.
    Human text: some paragraphs just... start. No explicit transition.

    Paradoxically, TOO MUCH coherence = AI signal in CNKI's detection.
    """
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 2:
        return LogicalCoherenceResult(
            paragraph_transitions=0, transition_quality=0,
            score=30.0, detail="段落数不足",
        )

    # Check if each paragraph (except first) starts with a transition phrase
    INTER_PARAGRAPH_TRANSITIONS = [
        r'^(首先|其次|再者|此外|另外|与此同时|另一方面)',
        r'^(基于上|综上|正如前|如前)',
        r'^(值得\S{1,3}[的是])',
        r'^(从\S{1,4}[来看])',
        r'^(在\S{1,4}[基础上])',
        r'^(为[进了]\S{1,4})',
    ]

    transition_count = 0
    for i, p in enumerate(paragraphs[1:], 1):  # skip first paragraph
        for pat in INTER_PARAGRAPH_TRANSITIONS:
            if re.match(pat, p.strip()):
                transition_count += 1
                break

    total_possible = len(paragraphs) - 1
    transition_quality = transition_count / total_possible if total_possible > 0 else 0

    # AI text: transition_quality close to 1.0 (every paragraph explicitly linked)
    # Human text: 0.3-0.6 (some transitions, some not)
    if transition_quality > 0.85:
        score = 80.0
        detail = f"段落衔接过于完美({transition_count}/{total_possible}段有显式过渡)，强AI特征"
    elif transition_quality > 0.6:
        score = 55.0
        detail = f"段落衔接较规整({transition_count}/{total_possible}段)，有一定模板化特征"
    elif transition_quality > 0.3:
        score = 25.0
        detail = "段落过渡自然，部分段落无显式衔接"
    else:
        score = 8.0
        detail = "段落过渡自然多变，典型人写特征"

    return LogicalCoherenceResult(
        paragraph_transitions=transition_count,
        transition_quality=round(transition_quality, 3),
        score=round(score, 1),
        detail=detail,
    )


# ============================================================================
# Complete CNKI Feature Scan
# ============================================================================
def scan_cnki_features(
    text: str,
    mode: Literal["general", "academic", "resume", "social_media"] = "general",
    discipline: str | None = None,
) -> CNKIFeatureReport:
    """Run all 8 CNKI feature dimensions and produce an aggregated report."""

    d1 = analyze_sentence_structure(text)
    d2 = analyze_paragraph_similarity(text)
    d3 = analyze_information_density(text)
    d4 = analyze_connectors(text)
    d5 = analyze_terminology(text, discipline)
    d6 = analyze_citations(text)
    d7 = analyze_data_specificity(text)
    d8 = analyze_logical_coherence(text)

    # Weighted aggregation mimicking CNKI's priority:
    # Sentence structure and connectors are the strongest signals
    weights = {
        "sentence": 0.22,
        "paragraph": 0.15,
        "info_density": 0.10,
        "connectors": 0.20,
        "terminology": 0.08,
        "citations": 0.12 if mode == "academic" else 0.05,
        "data": 0.08,
        "logical": 0.10 if mode == "academic" else 0.05,
    }

    # Redistribute non-academic weight
    if mode != "academic":
        extra = 0.12 + 0.05  # from citations+logical reduction
        weights["sentence"] += extra * 0.35
        weights["connectors"] += extra * 0.35
        weights["info_density"] += extra * 0.30

    # Normalize weights
    total_w = sum(weights.values())
    weights = {k: v / total_w for k, v in weights.items()}

    scores = {
        "sentence": d1.score,
        "paragraph": d2.score,
        "info_density": d3.score,
        "connectors": d4.score,
        "terminology": d5.score,
        "citations": d6.score,
        "data": d7.score,
        "logical": d8.score,
    }

    overall = sum(weights[k] * scores[k] for k in weights)
    overall = round(overall, 1)

    # Determine level
    if overall < 30:
        level = "low"
    elif overall < 70:
        level = "medium"
    else:
        level = "high"

    # Identify high-risk dimensions (score > 60)
    high_risk = []
    dim_labels = {
        "sentence": "句式结构过于均匀",
        "paragraph": "段落结构模板化",
        "info_density": "信息密度过于稳定",
        "connectors": "连接词密度/均匀性过高",
        "terminology": "术语使用过于规整",
        "citations": "引用模糊缺乏具体性",
        "data": "数据/案例缺乏具体性",
        "logical": "段落衔接过于完美",
    }
    for dim, score in scores.items():
        if score > 60:
            high_risk.append(dim_labels[dim])

    # Generate rewrite suggestions based on high-risk dimensions
    suggestions = []
    if d1.score > 60:
        suggestions.append(
            f"句式结构过于均匀(CV={d1.cv:.2f})，需打破句长规律：将部分15-25字句子合并为长句，或将部分展开为短句，使句长变异系数>0.5"
        )
    if d2.score > 60:
        suggestions.append(
            f"段落结构模板化(相似度={d2.mean_similarity:.2f})，需重组段落：有的段落从例子开始，有的直接抛出观点，有的以问题开头"
        )
    if d3.score > 60:
        suggestions.append(
            f"信息密度过于稳定(σ={d3.std_density:.1f})，需增加变化：某些段落加入具体数据和个人观点，某些段落简化为过渡句"
        )
    if d4.score > 60:
        suggestions.append(
            f"连接词过多({d4.total_connectors}个)或分布过于均匀，需删减60%以上的模板连接词，用自然过渡替代"
        )
    if d5.score > 60:
        suggestions.append(
            f"术语使用过于规整，需在适当位置用口语化表达替代部分术语（如'利用'→'用'，'实施'→'做'）"
        )
    if d6.score > 60:
        suggestions.append(
            f"引用过于模糊，需添加具体文献信息（作者、年份、标题），避免使用'有研究表明'等空洞引用"
        )
    if d7.score > 60:
        suggestions.append(
            f"缺乏具体数据支撑，需添加实际数字、百分比、统计结果，减少'显著提升''大幅下降'等模糊表述"
        )
    if d8.score > 60:
        suggestions.append(
            f"段落过渡过于规整，需删除部分显式过渡词，让部分段落直接开始，模拟人类写作的自然跳跃"
        )

    return CNKIFeatureReport(
        sentence_structure=d1,
        paragraph_similarity=d2,
        information_density=d3,
        connectors=d4,
        terminology=d5,
        citations=d6,
        data_specificity=d7,
        logical_coherence=d8,
        overall_cnki_score=overall,
        level=level,
        high_risk_dimensions=high_risk,
        rewrite_suggestions=suggestions,
    )
