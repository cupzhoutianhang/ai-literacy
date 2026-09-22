"""Local embedding similarity and clustering demo for energy terms."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from shared.config import settings  # noqa: E402
from shared.embeddings import encode  # noqa: E402


def cosine_similarity(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=float)
    vector = np.asarray(vector, dtype=float)
    matrix_norm = np.linalg.norm(matrix, axis=1)
    vector_norm = np.linalg.norm(vector)
    denominator = np.maximum(matrix_norm * vector_norm, 1e-12)
    return (matrix @ vector) / denominator


def load_terms(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "term" not in rows[0]:
        raise ValueError("CSV 至少需要包含 term 列")
    return rows


def rank_terms(terms: Sequence[str], query: str, vectors: np.ndarray, query_vector: np.ndarray, top_k: int) -> list[tuple[str, float]]:
    scores = cosine_similarity(vectors, query_vector)
    order = np.argsort(-scores)[:top_k]
    return [(terms[int(index)], float(scores[int(index)])) for index in order]


def cluster_terms(vectors: np.ndarray, n_clusters: int) -> np.ndarray:
    try:
        from sklearn.cluster import KMeans
    except ImportError as exc:
        raise RuntimeError("安装 scikit-learn 后才能进行聚类：pip install scikit-learn") from exc
    count = min(max(1, n_clusters), len(vectors))
    return KMeans(n_clusters=count, random_state=42, n_init=10).fit_predict(vectors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="锅炉温度异常")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--clusters", type=int, default=3)
    parser.add_argument("--model", default=settings.embedding_model)
    parser.add_argument("--data", type=Path, default=Path(__file__).parent / "data/energy_terms.csv")
    args = parser.parse_args()
    rows = load_terms(args.data)
    terms = [row["term"] for row in rows]
    try:
        vectors = np.asarray(encode(terms, model_name=args.model), dtype=float)
        query_vector = np.asarray(encode(args.query, model_name=args.model)[0], dtype=float)
    except RuntimeError as exc:
        print(f"Embedding 初始化失败：{exc}", file=sys.stderr)
        print("请先安装依赖：pip install sentence-transformers", file=sys.stderr)
        return 2

    print(f"查询：{args.query}")
    print("最相似术语：")
    for term, score in rank_terms(terms, args.query, vectors, query_vector, args.top_k):
        print(f"  {term}: {score:.4f}")
    try:
        labels = cluster_terms(vectors, args.clusters)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    print("聚类结果：")
    for label in sorted(set(int(item) for item in labels)):
        members = [term for term, member in zip(terms, labels) if int(member) == label]
        print(f"  cluster-{label}: {'、'.join(members)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

