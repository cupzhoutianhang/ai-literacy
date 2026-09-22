from __future__ import annotations

from functools import lru_cache
from typing import Iterable


@lru_cache(maxsize=2)
def _model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - environment guidance
        raise RuntimeError(
            "Install sentence-transformers to use local embeddings"
        ) from exc
    return SentenceTransformer(model_name)


def encode(
    texts: str | Iterable[str],
    *,
    model_name: str = "BAAI/bge-small-zh-v1.5",
    normalize: bool = True,
):
    """Encode Chinese text locally; no API key or remote inference is needed."""

    return _model(model_name).encode(
        list(texts) if not isinstance(texts, str) else [texts],
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )

