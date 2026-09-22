from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check(name: str, import_name: str, required: bool = True) -> bool:
    ok = importlib.util.find_spec(import_name) is not None
    label = "OK" if ok else ("MISSING" if required else "optional")
    print(f"{name:20} {label}")
    return ok or not required


def main() -> int:
    print(f"Python {sys.version.split()[0]}")
    print(f"Project root: {ROOT}")
    print(f"LLM_BASE_URL: {os.getenv('LLM_BASE_URL', 'http://127.0.0.1:18002/v1')}")
    print("\nDependencies:")
    required = [
        ("numpy", "numpy"),
        ("openai", "openai"),
        ("pydantic", "pydantic"),
        ("sentence-transformers", "sentence_transformers"),
    ]
    optional = [
        ("chromadb", "chromadb"),
        ("mcp", "mcp"),
        ("pypdf", "pypdf"),
        ("pytest", "pytest"),
        ("torch", "torch"),
    ]
    ok = all(check(*item) for item in required)
    for item in optional:
        check(*item, required=False)
    print("\nNext steps:")
    print("  1. Copy .env.example to .env and adjust the model if needed.")
    print("  2. Start the tunnel: ssh -N -L 18002:127.0.0.1:8002 010")
    print("  3. Run a project README example.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

