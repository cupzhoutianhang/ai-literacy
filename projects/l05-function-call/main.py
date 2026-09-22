"""Lesson 05: JSON-schema function calling without a framework.

The example uses a tiny registry and a deterministic router so it works even
when an LLM is unavailable.  ``--llm`` adds a natural-language explanation
through the shared OpenAI-compatible client; the tool invocation itself stays
validated and deterministic.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "sensors.csv"


def load_rows(path: Path = DEFAULT_DATA) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows: list[dict[str, Any]] = []
        for row in csv.DictReader(f):
            row["value"] = float(row["value"])
            rows.append(row)
    return rows


def _latest(rows: list[dict[str, Any]], equipment: str, sensor: str) -> dict[str, Any]:
    matches = [r for r in rows if r["equipment"].lower() == equipment.lower() and r["sensor"].lower() == sensor.lower()]
    if not matches:
        raise ValueError(f"No reading for {equipment}/{sensor}")
    return sorted(matches, key=lambda r: r["timestamp"])[-1]


def query_sensor(rows: list[dict[str, Any]], equipment: str, sensor: str, timestamp: str | None = None) -> dict[str, Any]:
    """Return one reading, with a clear error for an unknown asset."""
    if timestamp:
        for row in rows:
            if row["equipment"].lower() == equipment.lower() and row["sensor"].lower() == sensor.lower() and row["timestamp"] == timestamp:
                return row
        raise ValueError(f"No reading at {timestamp} for {equipment}/{sensor}")
    return _latest(rows, equipment, sensor)


def calculate_pressure_drop(rows: list[dict[str, Any]], equipment: str) -> dict[str, Any]:
    inlet = _latest(rows, equipment, "pressure_in")
    outlet = _latest(rows, equipment, "pressure_out")
    if inlet["unit"] != outlet["unit"]:
        raise ValueError("Pressure units do not match")
    return {
        "equipment": equipment,
        "inlet": inlet["value"],
        "outlet": outlet["value"],
        "drop": round(inlet["value"] - outlet["value"], 3),
        "unit": inlet["unit"],
        "timestamp": max(inlet["timestamp"], outlet["timestamp"]),
    }


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable[..., dict[str, Any]]


class ToolRegistry:
    """A small, inspectable function-calling registry."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def schemas(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}} for t in self._tools.values()]

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        tool = self._tools[name]
        required = tool.parameters.get("required", [])
        missing = [key for key in required if key not in arguments]
        if missing:
            raise ValueError(f"Missing required arguments: {', '.join(missing)}")
        return tool.function(**arguments)


def make_registry(rows: list[dict[str, Any]]) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(Tool(
        "query_sensor", "Read one sensor value for an equipment asset.",
        {"type": "object", "properties": {"equipment": {"type": "string"}, "sensor": {"type": "string"}, "timestamp": {"type": ["string", "null"]}}, "required": ["equipment", "sensor"]},
        lambda equipment, sensor, timestamp=None: query_sensor(rows, equipment, sensor, timestamp),
    ))
    registry.register(Tool(
        "calculate_pressure_drop", "Calculate inlet minus outlet pressure.",
        {"type": "object", "properties": {"equipment": {"type": "string"}}, "required": ["equipment"]},
        lambda equipment: calculate_pressure_drop(rows, equipment),
    ))
    return registry


def route_query(text: str, equipment: str = "pump-A") -> tuple[str, dict[str, Any]]:
    """A transparent stand-in for the model's tool-call decision."""
    lower = text.lower()
    if any(term in lower for term in ("压降", "pressure drop", "进出口")):
        return "calculate_pressure_drop", {"equipment": equipment}
    sensor = "temperature" if any(term in lower for term in ("温度", "temperature")) else "pressure_in"
    if "出口" in text or "outlet" in lower:
        sensor = "pressure_out"
    return "query_sensor", {"equipment": equipment, "sensor": sensor}


def llm_explain(tool_name: str, result: dict[str, Any], question: str) -> str:
    from shared.llm_client import chat

    prompt = f"问题：{question}\n工具：{tool_name}\n结果：{json.dumps(result, ensure_ascii=False)}\n请用一句中文解释结果，只陈述数据支持的结论。"
    return chat([{"role": "system", "content": "你是能源装置数据助手。"}, {"role": "user", "content": prompt}], max_tokens=160)


def run_demo(question: str = "请查询泵 A 的温度", *, use_llm: bool = False) -> dict[str, Any]:
    rows = load_rows()
    registry = make_registry(rows)
    tool_name, arguments = route_query(question)
    result = registry.call(tool_name, arguments)
    output: dict[str, Any] = {"steps": ["observe", "describe", "select", "validate", "invoke", "present"], "question": question, "tool": tool_name, "arguments": arguments, "result": result, "schemas": registry.schemas()}
    if use_llm:
        output["explanation"] = llm_explain(tool_name, result, question)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default="请查询泵 A 的温度")
    parser.add_argument("--llm", action="store_true", help="Ask the shared LLM to explain the tool result")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.question, use_llm=args.llm), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
