from typing import Literal
from .llm_client import LLMClient
from .aigc_detector import detect_aigc

SYSTEM_PROMPT = """你是一个专业的文本改写专家，擅长将AI生成的文本改写为更像人类写作的风格。

改写原则：
1. **句式变化**：打破过于规整的句式，混合使用长短句，增加句式的自然变化
2. **个性化表达**：适当加入个人观点、感受或口语化表达，让文本更有"人味"
3. **减少模板化**：避免"首先/其次/最后"、"总而言之"、"此外"等AI常用过渡词
4. **增加细节**：用更具体、更独特的细节替换概括性描述
5. **适度不完美**：人类写作不会100%逻辑严密，允许适度的思维跳跃
6. **保留原意**：核心内容和信息必须完整保留，不能改变原意
7. **控制风格变化幅度**：如果是学术/正式文本，保持正式感但增加自然度；如果是普通文章，可以更口语化

请返回JSON格式：
{
  "rewritten_text": "改写后的完整文本",
  "changes_summary": "改动说明，100字以内"
}"""


async def rewrite_text(
    text: str, provider: Literal["deepseek", "openai", "auto"] = "auto"
) -> dict:
    client = LLMClient(provider)
    result = await client.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"请改写以下文本，使其更像人类写作：\n\n{text}",
        temperature=0.7,
    )

    rewritten = result.get("rewritten_text", "")
    changes = result.get("changes_summary", "")

    # Re-detect AIGC score on rewritten text (use same provider)
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
