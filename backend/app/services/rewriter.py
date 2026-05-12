from typing import Literal
from .llm_client import LLMClient
from .aigc_detector import detect_aigc

BASE_REWRITE_PROMPT = """你是一个专业的文本改写专家，擅长将AI生成的文本改写为更像人类写作的风格。

改写原则：
1. **句式变化**：打破过于规整的句式，混合使用长短句，增加句式的自然变化
2. **个性化表达**：适当加入个人观点、感受或口语化表达，让文本更有"人味"
3. **减少模板化**：避免"首先/其次/最后"、"总而言之"、"此外"等AI常用过渡词
4. **增加细节**：用更具体、更独特的细节替换概括性描述
5. **适度不完美**：人类写作不会100%逻辑严密，允许适度的思维跳跃
6. **保留原意**：核心内容和信息必须完整保留，不能改变原意

请返回JSON格式：
{
  "rewritten_text": "改写后的完整文本",
  "changes_summary": "改动说明，100字以内"
}"""

INTENSITY_PROMPTS = {
    "light": "\n\n改写强度：轻度 - 仅做少量句式调整和词汇替换，保持原有结构，让文本稍微自然一些。",
    "medium": "\n\n改写强度：中度 - 进行句式重组、词汇替换、增加一些个性化表达，使文本明显不同于AI风格。",
    "deep": "\n\n改写强度：深度 - 大幅重构文本结构和表达方式，加入强烈的个人风格，可能改变段落顺序和论证方式。",
}


async def rewrite_text(
    text: str,
    provider: Literal["deepseek", "openai", "auto"] = "auto",
    intensity: str = "medium",
    preserve_terms: bool = False,
) -> dict:
    client = LLMClient(provider)

    system_prompt = BASE_REWRITE_PROMPT + INTENSITY_PROMPTS.get(intensity, "")
    if preserve_terms:
        system_prompt += "\n\n额外要求：保留所有专业术语和技术名词不做改动。"

    result = await client.chat_json(
        system_prompt=system_prompt,
        user_message=f"请改写以下文本，使其更像人类写作：\n\n{text}",
        temperature=0.7 if intensity == "deep" else 0.5,
    )

    rewritten = result.get("rewritten_text", "")
    changes = result.get("changes_summary", "")

    new_score = 0
    try:
        detection = await detect_aigc(rewritten, provider)
        new_score = detection["score"]
    except Exception:
        new_score = -1

    return {
        "rewritten_text": rewritten,
        "changes_summary": changes,
        "new_aigc_score": new_score,
    }
