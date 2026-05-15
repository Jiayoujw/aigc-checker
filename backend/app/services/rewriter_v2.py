"""
Targeted Anti-CNKI Rewrite Engine (rewriter_v2).

Key improvements over rewriter.py:
  1. Pre-rewrite CNKI feature scan → identifies specific high-risk dimensions
  2. Dimension-specific rewrite instructions (not generic "make it sound human")
  3. Closed-loop: rewrite → re-detect → re-rewrite (up to 3 rounds)
  4. Discipline terminology protection with actual term lists
  5. Post-rewrite verification against CNKI features

The rewrite strategy is to systematically reduce each high-risk dimension's
score below CNKI's detection threshold, rather than blindly paraphrasing.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Literal

from .llm_client import LLMClient
from .cnki_feature_scanner import scan_cnki_features, CNKIFeatureReport
from .aigc_detector import detect_aigc


# ---------------------------------------------------------------------------
# Dimension-specific rewrite instruction generators
# ---------------------------------------------------------------------------
def _sentence_structure_fix(report: CNKIFeatureReport) -> str:
    d = report.sentence_structure
    return f"""【句式结构改写】
当前情况：句长高度均匀(CV={d.cv:.2f})，{d.distribution_type}分布，是AI文本的典型特征。
改写要求：
1. 随机选择30-50%的句子进行拆分或合并
2. 将部分15-25字的句子扩展为30-50字长句
3. 将部分句子缩短为3-10字的短句
4. 加入1-2个感叹句或疑问句
5. 目标：句长变异系数>0.5，呈现明显的多峰分布"""


def _paragraph_structure_fix(report: CNKIFeatureReport) -> str:
    d = report.paragraph_similarity
    return f"""【段落结构改写】
当前情况：段落结构高度相似(相似度{d.mean_similarity:.2f})，每个段落遵循相同模板。
改写要求：
1. 重组30-50%段落的内部结构
2. 有的段落直接从例子或数据切入，跳过"主题句"
3. 有的段落以反问结尾，代替标准总结句
4. 有的段落使用简短过渡（1-2句话即可）
5. 打破"主题句→解释→例证→总结"的模板"""


def _info_density_fix(report: CNKIFeatureReport) -> str:
    d = report.information_density
    return f"""【信息密度改写】
当前情况：信息密度稳定在{d.mean_density:.0f}%±{d.std_density:.1f}%，缺少自然波动。
改写要求：
1. 选择1-2个段落，加入具体的个人观点、感受或经历，提高信息密度
2. 选择1-2个段落，简化为自然的过渡，降低信息密度
3. 目标：段落间信息密度标准差>10%"""


def _connector_fix(report: CNKIFeatureReport) -> str:
    d = report.connectors
    return f"""【连接词改写 - 最重要】
当前情况：{d.total_connectors}个模板连接词，{d.per_1000_chars:.1f}个/千字，分布均匀性{d.uniformity_score:.2f}。
改写要求：
1. 删除60-80%的模板连接词（"综上所述""由此可见""值得注意的是""此外""首先/其次/最后"等）
2. 用自然过渡代替："其实""不过""回过头看""换个角度说""有意思的是"
3. 部分段落之间不加任何过渡词，像人写文章一样直接开始
4. 剩余的连接词不要在位置上均匀分布，要集中出现或完全不出现"""


def _terminology_fix(report: CNKIFeatureReport) -> str:
    return """【术语使用改写】
改写要求：
1. 在20-30%的非关键位置，用口语化表达替代术语
   例如："利用机器学习方法"→"用机器学习的方式"
         "实施数据预处理"→"先把数据预处理一下"
         "开展实验验证"→"做了实验来验证"
2. 核心专业术语保留不变
3. 偶尔使用不完美的措辞，模拟人类写作的自然瑕疵"""


def _citation_fix(report: CNKIFeatureReport) -> str:
    d = report.citations
    vague_str = "、".join(d.vague_refs[:3]) if d.vague_refs else ""
    return f"""【引用改写】
当前情况：{len(d.vague_refs)}处模糊引用（如"{vague_str}"），缺乏具体信息。
改写要求：
1. 将"有研究表明""据统计""相关研究显示"改为具体引用
   例如："根据张三等人2023年的研究..."
         "国家统计局2024年数据显示..."
         "参考李四等人在《XXX》期刊上的发现..."
2. 或直接删除无具体来源的引用，改为自己的分析"""


def _data_fix(report: CNKIFeatureReport) -> str:
    d = report.data_specificity
    vague_str = "、".join(d.vague_quantifiers[:5]) if d.vague_quantifiers else ""
    return f"""【数据具体性改写】
当前情况：{len(d.vague_quantifiers)}处模糊量化词（如"{vague_str}"），缺乏具体数据。
改写要求：
1. 将"显著提升"改为"提升了约37.2%"
2. 将"大幅下降"改为"下降了12.5个百分点"
3. 将"一定程度"改为具体范围"在0.3至0.8之间"
4. 确保新增的数据合理且不自相矛盾"""


def _logical_fix(report: CNKIFeatureReport) -> str:
    d = report.logical_coherence
    return f"""【段落衔接改写】
当前情况：{d.paragraph_transitions}/{report.paragraph_similarity.paragraph_count - 1}个段落有显式过渡词，过于完美。
改写要求：
1. 删除40-60%的段落过渡词
2. 有些段落直接用事实陈述开始，无任何过渡
3. 人类的写作不会每段都"首先...其次...此外..."地连起来"""


# Dimension -> fix function mapping
DIMENSION_FIXES = [
    ("sentence_structure", _sentence_structure_fix, 60),
    ("paragraph_similarity", _paragraph_structure_fix, 60),
    ("information_density", _info_density_fix, 60),
    ("connectors", _connector_fix, 50),  # lower threshold — connectors are key
    ("terminology", _terminology_fix, 60),
    ("citations", _citation_fix, 60),
    ("data_specificity", _data_fix, 60),
    ("logical_coherence", _logical_fix, 60),
]


def build_targeted_rewrite_prompt(
    text: str,
    report: CNKIFeatureReport,
    intensity: str = "medium",
) -> str:
    """
    Build a dimension-specific rewrite prompt based on CNKI feature scan results.
    Only includes fixes for dimensions that exceed the detection threshold.
    """
    # Collect fixes for high-risk dimensions
    fix_instructions = []
    triggered_dims = []

    for dim_name, fix_fn, threshold in DIMENSION_FIXES:
        # Get the dimension score from report
        dim_obj = getattr(report, dim_name, None)
        if dim_obj and dim_obj.score >= threshold:
            instruction = fix_fn(report)
            fix_instructions.append(instruction)
            triggered_dims.append(dim_name)

    # If nothing triggered (shouldn't happen), use generic rewrite
    if not fix_instructions:
        return f"""请对以下文本进行改写，使其更像人类写作风格：
1. 打破过于规整的句式
2. 增加个人化和口语化表达
3. 减少模板连接词
4. 保留原意和专业术语

【原文】
{text}

请返回改写后的完整文本。"""

    intensity_boost = {
        "light": "请进行轻度调整，仅针对最突出的1-2个问题进行微调。",
        "medium": "请进行中等力度的改写，系统性地改善上述所有问题。",
        "deep": "请进行深度重写，大幅重构文本，彻底消除所有AI痕迹。可以改变段落顺序、论证方式和整体结构。",
    }

    prompt = f"""你是一个专业的文本改写专家，专门帮助降低文本的AIGC检测率。

【检测分析】
当前文本的预测AIGC得分为{report.overall_cnki_score}分，检测到以下高风险维度：
{chr(10).join(f'- {d}' for d in report.high_risk_dimensions)}

【改写策略 - 请逐条执行】
{chr(10).join(fix_instructions)}

【改写强度】
{intensity_boost.get(intensity, intensity_boost['medium'])}

【核心原则】
- 保留原文的核心内容和关键信息
- 保护专业术语和技术名词不被错误修改
- 改写后读起来要像真人写的，允许适度不完美
- 不是简单同义词替换，而是从句子结构、段落组织、连接方式等底层改变

【原文】
{text}

请返回改写后的完整文本，不要添加任何说明。"""

    return prompt, triggered_dims


# ---------------------------------------------------------------------------
# Closed-loop rewrite orchestrator
# ---------------------------------------------------------------------------
@dataclass
class RewriteResult:
    rewritten_text: str
    original_score: float
    new_score: float
    rounds: int
    score_improvement: float
    changes_summary: str
    triggered_dimensions: list[str]
    dimension_scores_before: dict
    dimension_scores_after: dict


async def rewrite_targeted(
    text: str,
    provider: Literal["deepseek", "openai", "auto"] = "auto",
    intensity: str = "medium",
    target_score: float = 25.0,
    max_rounds: int = 3,
    mode: str = "general",
) -> RewriteResult:
    """
    Closed-loop targeted rewriting:
    1. Scan CNKI features → identify high-risk dimensions
    2. Build targeted rewrite prompt
    3. Rewrite → Re-scan → If score > target → Rewrite again
    4. Max 3 rounds to control cost
    """
    client = LLMClient(provider)

    # Step 1: Initial CNKI scan
    initial_report = scan_cnki_features(text, mode=mode)
    initial_score = initial_report.overall_cnki_score

    # Collect dimension scores before
    dim_scores_before = {
        "sentence_structure": initial_report.sentence_structure.score,
        "paragraph_similarity": initial_report.paragraph_similarity.score,
        "information_density": initial_report.information_density.score,
        "connectors": initial_report.connectors.score,
        "terminology": initial_report.terminology.score,
        "citations": initial_report.citations.score,
        "data_specificity": initial_report.data_specificity.score,
        "logical_coherence": initial_report.logical_coherence.score,
    }

    current_text = text
    current_report = initial_report
    total_triggered_dims = []
    all_changes = []

    for round_num in range(1, max_rounds + 1):
        if current_report.overall_cnki_score <= target_score:
            break

        # Build targeted rewrite prompt
        prompt, triggered = build_targeted_rewrite_prompt(
            current_text, current_report, intensity
        )
        total_triggered_dims.extend(triggered)

        # Execute rewrite
        try:
            response = await client.client.chat.completions.create(
                model=client.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的文本改写专家。只返回改写后的文本，不要添加任何说明。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7 if intensity == "deep" else 0.5,
                max_tokens=min(len(current_text) * 2, 16000),
            )
            rewritten = response.choices[0].message.content
            if not rewritten:
                rewritten = current_text
        except Exception:
            rewritten = current_text

        current_text = rewritten

        # Re-scan to check progress
        current_report = scan_cnki_features(current_text, mode=mode)

        improvement = current_report.overall_cnki_score - initial_score
        all_changes.append(
            f"第{round_num}轮：得分 {current_report.overall_cnki_score} "
            f"({'↓' if improvement < 0 else '↑'}{abs(improvement):.0f}分)"
        )

    # Also run an LLM-based re-detection for the new score estimate
    try:
        llm_detect = await detect_aigc(current_text, provider, mode)
        llm_score = llm_detect["score"]
    except Exception:
        llm_score = current_report.overall_cnki_score

    # Combine CNKI score with LLM score for final estimate
    final_score = round(current_report.overall_cnki_score * 0.6 + llm_score * 0.4, 1)

    # Dimension scores after
    dim_scores_after = {
        "sentence_structure": current_report.sentence_structure.score,
        "paragraph_similarity": current_report.paragraph_similarity.score,
        "information_density": current_report.information_density.score,
        "connectors": current_report.connectors.score,
        "terminology": current_report.terminology.score,
        "citations": current_report.citations.score,
        "data_specificity": current_report.data_specificity.score,
        "logical_coherence": current_report.logical_coherence.score,
    }

    return RewriteResult(
        rewritten_text=current_text,
        original_score=initial_score,
        new_score=final_score,
        rounds=round_num,
        score_improvement=round(initial_score - final_score, 1),
        changes_summary="; ".join(all_changes) if all_changes else "无需改写，原文本AIGC分数已达标",
        triggered_dimensions=list(set(total_triggered_dims)),
        dimension_scores_before=dim_scores_before,
        dimension_scores_after=dim_scores_after,
    )
