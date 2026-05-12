import re
import math
from collections import Counter


def tokenize(text: str) -> list[str]:
    """Simple Chinese + English tokenizer."""
    tokens = []
    for char in text:
        if '一' <= char <= '鿿':
            tokens.append(char)
        elif char.isalnum():
            tokens.append(char.lower())
    return tokens


def ngrams(tokens: list[str], n: int = 3) -> list[str]:
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def cosine_similarity(ngrams_a: list[str], ngrams_b: list[str]) -> float:
    freq_a = Counter(ngrams_a)
    freq_b = Counter(ngrams_b)

    all_keys = set(freq_a.keys()) | set(freq_b.keys())
    dot = sum(freq_a.get(k, 0) * freq_b.get(k, 0) for k in all_keys)
    norm_a = math.sqrt(sum(v ** 2 for v in freq_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in freq_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b) * 100


def split_paragraphs(text: str) -> list[str]:
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if len(p.strip()) > 30]


def local_plagiarism_check(text: str) -> dict:
    """Check internal plagiarism across paragraphs using TF-IDF-like n-gram similarity."""
    paragraphs = split_paragraphs(text)

    if len(paragraphs) < 2:
        return {"similarity_score": 0.0, "similar_sources": [], "details": "文本较短，未发现内部重复"}

    tokens_list = [tokenize(p) for p in paragraphs]
    ngrams_list = [ngrams(t, n=3) for t in tokens_list]

    total_score = 0.0
    similar_pairs = []

    for i in range(len(paragraphs)):
        for j in range(i + 1, len(paragraphs)):
            sim = cosine_similarity(ngrams_list[i], ngrams_list[j])
            if sim > 30:
                similar_pairs.append({
                    "text": paragraphs[j][:100] + ("..." if len(paragraphs[j]) > 100 else ""),
                    "reason": f"与段落{i+1}相似度 {sim:.1f}%",
                    "possible_source_type": "内部重复",
                    "similarity": round(sim, 1),
                })
                total_score = max(total_score, sim)

    return {
        "similarity_score": round(total_score, 1),
        "similar_sources": similar_pairs[:5],
        "details": f"基于文本内部段落相似度分析，共检测{len(paragraphs)}个段落，发现{len(similar_pairs)}处相似内容",
    }
