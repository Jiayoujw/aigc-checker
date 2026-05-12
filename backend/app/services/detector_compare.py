import asyncio
from .aigc_detector import detect_aigc


async def detect_compare(text: str) -> dict:
    """Run both DeepSeek and OpenAI in parallel."""
    results = await asyncio.gather(
        detect_aigc(text, provider="deepseek"),
        detect_aigc(text, provider="openai"),
        return_exceptions=True,
    )

    def fmt(r):
        if isinstance(r, Exception):
            return {"score": -1, "level": "error", "suspicious_segments": [], "analysis": f"检测失败: {str(r)}"}
        return r

    deepseek_result = fmt(results[0])
    openai_result = fmt(results[1])

    return {
        "deepseek": deepseek_result,
        "openai": openai_result,
        "consensus": _compute_consensus(deepseek_result, openai_result),
    }


def _compute_consensus(a: dict, b: dict) -> dict:
    if a.get("score", -1) < 0 or b.get("score", -1) < 0:
        return {"level": "partial", "avg_score": max(a.get("score", 0), b.get("score", 0)), "agreement": "one_model_failed"}

    diff = abs(a["score"] - b["score"])
    avg = (a["score"] + b["score"]) / 2

    if diff < 15:
        agreement = "high"
    elif diff < 30:
        agreement = "medium"
    else:
        agreement = "low"

    return {"level": "consensus", "avg_score": round(avg, 1), "diff": round(diff, 1), "agreement": agreement}
