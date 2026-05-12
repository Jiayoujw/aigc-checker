from .llm_client import LLMClient
from typing import Literal

SYSTEM_PROMPT = """你是一个专业的文本鉴别专家，擅长识别AI生成的文本。

请分析用户提供的文本，判断其是否由AI（如ChatGPT、Claude、文心一言、通义千问等LLM）生成。

分析维度：
1. 词汇多样性：AI文本通常词汇重复度较高，缺乏真正的词汇变化
2. 句式结构：AI文本句式往往过于规整、平衡，缺少自然的句式变化
3. 逻辑连贯性：AI文本逻辑过于完美，缺少人类写作中的跳跃和即兴发挥
4. 表达个性化：AI文本缺乏个人观点、情感色彩和口语化表达
5. 过渡词使用：AI文本常过度使用"首先/其次/最后"、"总而言之"等模板化过渡词
6. 细节丰富度：AI文本喜欢堆砌概括性描述，缺乏具体、独特的细节

请返回JSON格式：
{
  "score": 0-100的数值，表示AI生成概率,
  "level": "low"/"medium"/"high"（low: <30%, medium: 30-70%, high: >70%）,
  "suspicious_segments": [
    {"text": "可疑文本段落", "score": 该段AI概率0-100, "reason": "判定理由"}
  ],
  "analysis": "综合分析，150字以内"
}

注意：suspicious_segments只包含AI痕迹较重的段落（score>50），最多5段。
如果整体文本AI痕迹不明显（score<30），suspicious_segments可以为空数组。"""


async def detect_aigc(
    text: str, provider: Literal["deepseek", "openai", "auto"] = "auto"
) -> dict:
    client = LLMClient(provider)
    result = await client.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"请分析以下文本：\n\n{text}",
        temperature=0.1,
    )

    score = max(0, min(100, result.get("score", 0)))
    level = result.get("level", "medium")
    if level not in ("low", "medium", "high"):
        if score < 30:
            level = "low"
        elif score < 70:
            level = "medium"
        else:
            level = "high"

    return {
        "score": score,
        "level": level,
        "suspicious_segments": result.get("suspicious_segments", []),
        "analysis": result.get("analysis", ""),
    }
