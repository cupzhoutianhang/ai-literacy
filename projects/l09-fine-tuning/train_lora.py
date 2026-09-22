from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="可选 LoRA 训练入口（默认只做资源检查）")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--run", action="store_true", help="真正加载模型并启动训练")
    args = parser.parse_args()
    requirements = ["torch", "transformers", "datasets", "peft", "trl", "accelerate"]
    missing = []
    for name in requirements:
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        print("缺少可选 LoRA 依赖:", ", ".join(missing))
        print("安装: uv pip install -e \".[finetune]\"")
        return 1
    if not args.run:
        print(f"资源检查通过。模型: {args.model}")
        print("这是演示脚本，使用 --run 才会加载模型；建议在服务器 GPU 上运行。")
        return 0
    print("已通过依赖检查；请根据服务器显存和课程数据量补充 SFTTrainer 配置。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

