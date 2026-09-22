from __future__ import annotations

import argparse

from shared.llm_client import LLMClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the SSH-tunnelled vLLM endpoint")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()
    try:
        answer = LLMClient().chat(
            [{"role": "user", "content": "只回复：课程模型连接正常"}],
            model=args.model,
            max_tokens=32,
            temperature=0,
        )
    except Exception as exc:
        print(f"LLM check failed: {exc}")
        print("Start: ssh -N -L 18002:127.0.0.1:8002 010")
        return 1
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

