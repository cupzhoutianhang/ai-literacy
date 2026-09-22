"""A small local Markdown RAG pipeline with Chroma persistence and source citations."""
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from shared.config import settings  # noqa: E402
from shared.embeddings import encode  # noqa: E402
from shared.llm_client import LLMClient  # noqa: E402


@dataclass(frozen=True)
class Chunk:
    source: str
    index: int
    text: str


def chunk_markdown(text: str, *, source: str, max_chars: int = 260) -> list[Chunk]:
    """Split Markdown by headings/paragraphs and pack short paragraphs."""
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[Chunk] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if buffer:
                chunks.append(Chunk(source, len(chunks), buffer))
                buffer = ""
            for start in range(0, len(paragraph), max_chars):
                chunks.append(Chunk(source, len(chunks), paragraph[start : start + max_chars]))
            continue
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            chunks.append(Chunk(source, len(chunks), buffer))
            buffer = paragraph
    if buffer:
        chunks.append(Chunk(source, len(chunks), buffer))
    return chunks


def format_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[S{i + 1}] {chunk.text}" for i, chunk in enumerate(chunks))


def stable_id(chunk: Chunk) -> str:
    return hashlib.sha1(f"{chunk.source}:{chunk.index}:{chunk.text}".encode("utf-8")).hexdigest()


def load_chunks(data_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(data_dir.glob("*.md")):
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), source=path.name))
    if not chunks:
        raise ValueError(f"数据目录没有 Markdown 文档：{data_dir}")
    return chunks


def open_collection(persist_dir: Path, *, rebuild: bool):
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError("RAG 需要 Chroma，请安装：pip install 'chromadb>=0.5'") from exc
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    if rebuild:
        try:
            client.delete_collection("safety-procedure")
        except Exception:
            pass
    return client.get_or_create_collection("safety-procedure", metadata={"hnsw:space": "cosine"})


def ensure_index(collection, chunks: list[Chunk], model_name: str) -> None:
    existing = collection.count()
    if existing >= len(chunks):
        return
    try:
        vectors = np.asarray(encode([chunk.text for chunk in chunks], model_name=model_name), dtype=float)
    except RuntimeError as exc:
        raise RuntimeError(f"本地 Embedding 不可用：{exc}\n请安装：pip install sentence-transformers") from exc
    collection.upsert(
        ids=[stable_id(chunk) for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        embeddings=vectors.tolist(),
        metadatas=[{"source": chunk.source, "index": chunk.index} for chunk in chunks],
    )


def retrieve(collection, query: str, *, model_name: str, top_k: int) -> list[Chunk]:
    try:
        query_vector = np.asarray(encode(query, model_name=model_name)[0], dtype=float).tolist()
    except RuntimeError as exc:
        raise RuntimeError(f"本地 Embedding 不可用：{exc}\n请安装：pip install sentence-transformers") from exc
    result = collection.query(query_embeddings=[query_vector], n_results=top_k, include=["documents", "metadatas"])
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    return [Chunk(str(meta.get("source", "unknown")), int(meta.get("index", i)), doc) for i, (doc, meta) in enumerate(zip(documents, metadatas))]


def answer(query: str, chunks: list[Chunk], *, mock_llm: bool = False) -> str:
    context = format_context(chunks)
    if mock_llm:
        return f"根据检索片段，建议先核对现场测点与运行工况，再按规程逐项检查。\n\n来源：\n{context}"
    try:
        response = LLMClient().chat(
            [
                {"role": "system", "content": "你是安全规程助手。只根据给定资料回答，无法确定时明确说资料不足；在相关句末使用 [S1] 等来源标记。"},
                {"role": "user", "content": f"资料：\n{context}\n\n问题：{query}"},
            ],
            temperature=0.1,
            max_tokens=600,
        )
    except RuntimeError as exc:
        raise RuntimeError(f"LLM 调用失败：{exc}\n请安装 openai 并检查 SSH 隧道和 LLM_BASE_URL。") from exc
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="排烟温度升高应该先检查什么？")
    parser.add_argument("--data", type=Path, default=Path(__file__).parent / "data")
    parser.add_argument("--persist-dir", type=Path, default=Path(__file__).parent / "data/chroma")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--model", default=settings.embedding_model)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--mock-llm", action="store_true", help="跳过大模型，输出可核对的演示回答")
    args = parser.parse_args()
    try:
        chunks = load_chunks(args.data)
        collection = open_collection(args.persist_dir, rebuild=args.rebuild)
        ensure_index(collection, chunks, args.model)
        selected = retrieve(collection, args.query, model_name=args.model, top_k=args.top_k)
        print(answer(args.query, selected, mock_llm=args.mock_llm))
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

