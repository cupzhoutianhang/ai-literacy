"""Turn a process log into a validated structured report with Prompt + Pydantic."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from shared.llm_client import LLMClient  # noqa: E402


class Alert(BaseModel):
    level: str = Field(description="info, warning, or critical")
    message: str


class DailyReport(BaseModel):
    date: date
    unit: str
    summary: str
    alerts: list[Alert] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


def build_prompt(payload: dict[str, Any]) -> list[dict[str, str]]:
    schema = json.dumps(DailyReport.model_json_schema(), ensure_ascii=False, indent=2)
    user_data = json.dumps(payload, ensure_ascii=False, indent=2)
    return [
        {
            "role": "system",
            "content": (
                "你是电厂工艺日报分析员。把输入整理为严格 JSON。只输出 JSON 对象，不要 Markdown、解释或额外字段。"
                f"必须符合这个 JSON Schema：\n{schema}"
            ),
        },
        {"role": "user", "content": user_data},
    ]


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from plain or fenced model output."""
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else cleaned
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"模型没有返回有效 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("模型 JSON 顶层必须是对象")
    return value


def mock_report(payload: dict[str, Any]) -> DailyReport:
    text = payload.get("raw_text", "")
    alert_message = "排烟温度升高，建议检查空预器积灰" if "温度" in text else "暂无明显告警"
    return DailyReport(
        date=payload["date"],
        unit=payload["unit"],
        summary=f"{payload['unit']}运行总体稳定；{text}",
        alerts=[Alert(level="warning", message=alert_message)],
        actions=["复核排烟温度趋势", "检查空预器积灰并记录处理结果"],
        metrics={"排烟温度趋势": 1.0},
    )


def run(payload: dict[str, Any], *, mock: bool = False) -> DailyReport:
    if mock:
        return mock_report(payload)
    try:
        raw = LLMClient().chat(build_prompt(payload), temperature=0.0, max_tokens=800)
    except RuntimeError as exc:
        raise RuntimeError(f"调用 LLM 失败：{exc}\n请安装 openai：pip install openai，并检查 SSH 隧道和 LLM_BASE_URL。") from exc
    try:
        return DailyReport.model_validate(extract_json(raw))
    except (ValueError, ValidationError) as exc:
        raise ValueError(f"结构化结果校验失败：{exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).parent / "data/sample_report.json")
    parser.add_argument("--mock", action="store_true", help="不调用大模型，使用确定性示例输出")
    parser.add_argument("--output", type=Path, help="可选：保存结构化 JSON")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    try:
        report = run(payload, mock=args.mock)
    except (RuntimeError, ValueError, ValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rendered = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

