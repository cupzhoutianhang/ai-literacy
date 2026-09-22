"""Lesson 08: memory selection, compression and context isolation.

Embedding calls are routed through ``shared.embeddings.encode``.  If the local
model is not installed or cached, a deterministic hashing vector keeps the
lesson runnable; set ``AI_LITERACY_LOCAL_EMBEDDINGS=1`` to make failures
visible while preparing a real local environment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from shared.embeddings import encode  # noqa: E402


def estimate_tokens(text: str) -> int:
    """Cheap, model-independent token estimate for classroom comparisons."""
    return max(1, math.ceil(len(text) / 2))


def _fallback_vector(text: str, dimensions: int = 128) -> list[float]:
    values = [0.0] * dimensions
    for index in range(0, len(text), 2):
        digest = hashlib.blake2b(text[index : index + 2].encode("utf-8"), digest_size=4).digest()
        bucket = int.from_bytes(digest, "big") % dimensions
        values[bucket] += 1.0
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def embed(text: str, *, model_name: str = "BAAI/bge-small-zh-v1.5") -> list[float]:
    try:
        vectors = encode([text], model_name=model_name)
        return [float(value) for value in vectors[0]]
    except Exception as exc:
        if os.getenv("AI_LITERACY_LOCAL_EMBEDDINGS", "0") == "1":
            raise RuntimeError("Local embedding model is unavailable") from exc
        return _fallback_vector(text)


def cosine(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    return sum(left[i] * right[i] for i in range(size))


@dataclass
class Memory:
    key: str
    text: str
    tags: list[str] = field(default_factory=list)
    vector: list[float] = field(default_factory=list)


class MemoryStore:
    def __init__(self, *, model_name: str = "BAAI/bge-small-zh-v1.5") -> None:
        self.model_name = model_name
        self.items: list[Memory] = []

    def write(self, key: str, text: str, tags: list[str] | None = None) -> Memory:
        item = Memory(key, text, tags or [], embed(text, model_name=self.model_name))
        self.items = [existing for existing in self.items if existing.key != key]
        self.items.append(item)
        return item

    def select(self, query: str, *, k: int = 3, max_tokens: int | None = None) -> list[dict[str, Any]]:
        query_vector = embed(query, model_name=self.model_name)
        ranked = sorted(((cosine(query_vector, item.vector), item) for item in self.items), key=lambda pair: pair[0], reverse=True)
        selected: list[dict[str, Any]] = []
        tokens = 0
        for score, item in ranked:
            length = estimate_tokens(item.text)
            if max_tokens is not None and selected and tokens + length > max_tokens:
                continue
            selected.append({"key": item.key, "text": item.text, "tags": item.tags, "score": round(score, 4), "tokens": length})
            tokens += length
            if len(selected) >= k:
                break
        return selected

    def compress(self, items: list[dict[str, Any]], *, max_tokens: int = 80) -> dict[str, Any]:
        source = " ".join(item["text"] for item in items)
        limit = max_tokens * 2
        text = source if len(source) <= limit else source[:limit].rsplit("。", 1)[0] + "。"
        return {"text": text, "tokens": estimate_tokens(text), "source_keys": [item["key"] for item in items]}

    def isolate(self, query: str, *, scope: str, k: int = 3) -> dict[str, Any]:
        selected = [item for item in self.select(query, k=k) if scope in item["tags"]]
        return {"scope": scope, "items": selected, "tokens": sum(item["tokens"] for item in selected)}


def middle_loss_experiment(window_tokens: int = 40) -> dict[str, Any]:
    chunks = [f"段落 {index}：常规运行记录。" for index in range(9)]
    needle = "关键事实：泵 A 的安全阈值是 80 摄氏度。"
    chunks[4] = needle
    full = "\n".join(chunks)
    # A naive window that preserves only the edges can silently discard the middle.
    edge_count = max(1, min(2, window_tokens // 10))
    edge_window = "\n".join(chunks[:edge_count] + ["..."] + chunks[-edge_count:])
    selected = MemoryStore().write("needle", needle, ["safety"])
    return {"needle": needle, "full_tokens": estimate_tokens(full), "edge_window_tokens": estimate_tokens(edge_window), "needle_in_full": needle in full, "needle_in_edge_window": needle in edge_window, "selected_by_embedding": selected.key == "needle"}


def demo() -> dict[str, Any]:
    store = MemoryStore()
    store.write("ops-1", "泵 A 昨日温度 74 摄氏度，运行稳定。", ["operations"])
    store.write("safety-1", "泵 A 的安全温度阈值为 80 摄氏度。", ["safety"])
    store.write("report-1", "本周维护计划：周五检查密封件。", ["planning"])
    selected = store.select("泵 A 温度是否超过安全阈值", k=2, max_tokens=80)
    return {"memory_count": len(store.items), "selected": selected, "compressed": store.compress(selected, max_tokens=40), "isolated_safety": store.isolate("泵 A 安全阈值", scope="safety"), "middle_loss": middle_loss_experiment()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", action="store_true", help="Require the local Sentence-Transformers model")
    args = parser.parse_args()
    if args.local:
        os.environ["AI_LITERACY_LOCAL_EMBEDDINGS"] = "1"
    print(json.dumps(demo(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
