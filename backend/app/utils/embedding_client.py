"""Embedding 生成工具。

MVP 阶段先提供确定性的本地向量，保证知识库检索链路在没有外部 API 时也能开发和测试。
后续接入真实 Embedding API 时，只需要替换 embed_texts 的内部实现。
"""

import hashlib
import math

from app.core.config import settings

EMBEDDING_DIMENSION = 1536


def embed_texts(texts: list[str]) -> list[list[float]]:
    # 使用哈希词袋生成稳定向量，便于本地开发、测试和数据库写入。
    return [_hash_embedding(text) for text in texts]


def get_embedding_model_name() -> str:
    return settings.embedding_model


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _hash_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSION
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSION
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _tokenize(text: str) -> list[str]:
    # 中文资料常常没有空格，按字符和英文词混合切分，检索质量虽朴素但稳定。
    tokens: list[str] = []
    current = ""
    for char in text.lower():
        if char.isascii() and char.isalnum():
            current += char
            continue
        if current:
            tokens.append(current)
            current = ""
        if not char.isspace():
            tokens.append(char)
    if current:
        tokens.append(current)
    return tokens

