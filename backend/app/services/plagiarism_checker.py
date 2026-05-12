import re
import hashlib
from .llm_client import LLMClient

SYSTEM_PROMPT = """你是一个专业的文本查重专家。请分析给定文本，判断其中可能与已发布内容相似的部分。

分析维度：
1. 识别文本中可能是引用、摘抄自已有文献/文章/网络内容的段落
2. 判断文本的原创程度
3. 对重复或相似内容进行标注

请返回JSON格式：
{
  "similarity_score": 0-100的数值，表示预估的重复率,
  "similar_sources": [
    {"text": "疑似重复的文本", "reason": "为什么判定为重复", "possible_source_type": "学术论文/网络文章/书籍/其他"}
  ],
  "details": "综合查重分析，150字以内"
}

注意：
- similar_sources只包含疑似重复的段落（up to 5个）
- 如果没有发现明显的重复内容，similarity_score应较低（<20），similar_sources可以为空数组
- 这是一个基于文本特征的语义判断，主要依据文本风格、表述方式等判断是否有抄袭/重复嫌疑"""


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences for analysis."""
    sentences = re.split(r'(?<=[。！？.!?])\s*', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


async def check_plagiarism(text: str) -> dict:
    """Check text for plagiarism using LLM analysis."""
    client = LLMClient(provider="auto")
    result = await client.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"请对以下文本进行查重分析：\n\n{text}",
        temperature=0.1,
    )

    score = max(0, min(100, result.get("similarity_score", 0)))

    return {
        "similarity_score": score,
        "similar_sources": result.get("similar_sources", []),
        "details": result.get("details", ""),
    }
