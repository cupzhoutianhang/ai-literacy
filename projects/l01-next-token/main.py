"""A tiny, dependency-light next-token prediction laboratory."""
from __future__ import annotations

import argparse
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+|[^\s]")


def tokenize(text: str) -> list[str]:
    """Split Chinese characters, words/numbers, and punctuation into tokens."""
    return TOKEN_RE.findall(text)


def word_counts(tokens: Iterable[str]) -> Counter[str]:
    return Counter(tokens)


def bigram_counts(tokens: Iterable[str]) -> dict[str, Counter[str]]:
    items = list(tokens)
    result: dict[str, Counter[str]] = defaultdict(Counter)
    for previous, current in zip(items, items[1:]):
        result[previous][current] += 1
    return dict(result)


def next_token_probs(tokens: Iterable[str], previous: str, smoothing: float = 0.1) -> dict[str, float]:
    """Return add-``smoothing`` bigram probabilities after ``previous``."""
    vocabulary = sorted(set(tokens))
    if not vocabulary:
        return {}
    counts = bigram_counts(tokens).get(previous, Counter())
    denominator = sum(counts.values()) + smoothing * len(vocabulary)
    return {token: (counts[token] + smoothing) / denominator for token in vocabulary}


def predict_next(tokens: Iterable[str], previous: str, top_k: int = 5) -> list[tuple[str, float]]:
    probs = next_token_probs(tokens, previous)
    return sorted(probs.items(), key=lambda pair: (-pair[1], pair[0]))[:top_k]


def attention_weights(context: list[str], query: str | None = None) -> dict[str, float]:
    """Compute a deterministic toy attention distribution with NumPy.

    Tokens equal to the query receive a larger score; later positions also get
    a small recency bonus. This is a teaching visualization, not a transformer
    attention implementation.
    """
    if not context:
        return {}
    scores = np.array(
        [2.0 * (token == query) + (index + 1) / len(context) for index, token in enumerate(context)],
        dtype=float,
    )
    scores -= scores.max()
    weights = np.exp(scores) / np.exp(scores).sum()
    return {token: float(weight) for token, weight in zip(context, weights)}


def _load_corpus(path: Path) -> list[str]:
    return tokenize(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="锅炉 温度", help="用于预测的上下文；最后一个 token 会作为前文")
    parser.add_argument("--corpus", type=Path, default=Path(__file__).parent / "data/tiny_corpus.txt")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--attention", action="store_true", help="打印 toy attention 权重")
    args = parser.parse_args()

    corpus_tokens = _load_corpus(args.corpus)
    context = tokenize(args.text)
    if not context:
        parser.error("--text 不能为空")
    previous = context[-1]
    print(f"语料 token 数: {len(corpus_tokens)}")
    print("最高频 token:", word_counts(corpus_tokens).most_common(args.top_k))
    print(f"前文 {previous!r} 的下一个 token 预测:")
    for token, probability in predict_next(corpus_tokens, previous, args.top_k):
        print(f"  {token!r}: {probability:.3f}")
    if args.attention:
        print("toy attention:")
        for token, weight in attention_weights(context, previous).items():
            print(f"  {token!r}: {weight:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

