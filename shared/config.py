from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # The project can still run with process-level environment variables.
    pass


@dataclass(frozen=True)
class Settings:
    """Runtime settings shared by all demos.

    Environment variables are intentionally simple so the same project can run
    locally or through an SSH tunnel to the course server.
    """

    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://127.0.0.1:18002/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "dummy")
    llm_model: str = os.getenv("LLM_MODEL", "main")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"
    )
    data_dir: Path = Path(os.getenv("AI_LITERACY_DATA_DIR", "data"))


settings = Settings()
