from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_default_settings_use_tunnel_and_local_embedding():
    from shared.config import settings

    assert settings.llm_base_url.endswith("/v1")
    assert settings.llm_model
    assert "bge" in settings.embedding_model.lower()

