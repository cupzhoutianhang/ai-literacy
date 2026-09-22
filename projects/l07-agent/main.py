"""Lesson 07: a bounded equipment-inspection agent.

The deterministic planner is the default and is useful for repeatable tests.
``--llm`` asks the shared model for a JSON plan, then validates every proposed
tool against the same whitelist and step budget.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "inspection.csv"


def load_rows() -> list[dict[str, Any]]:
    with DATA.open(encoding="utf-8", newline="") as f:
        return [{**r, "value": float(r["value"])} for r in csv.DictReader(f)]


@dataclass
class AuditEvent:
    step: int
    action: str
    arguments: dict[str, Any]
    status: str
    result: Any = None


class InspectionTools:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def read_sensor(self, equipment: str, sensor: str) -> dict[str, Any]:
        matches = [r for r in self.rows if r["equipment"] == equipment and r["sensor"] == sensor]
        if not matches:
            raise ValueError(f"unknown sensor: {equipment}/{sensor}")
        return sorted(matches, key=lambda r: r["timestamp"])[-1]

    def check_alarm(self, equipment: str, sensor: str, threshold: float) -> dict[str, Any]:
        reading = self.read_sensor(equipment, sensor)
        return {"equipment": equipment, "sensor": sensor, "value": reading["value"], "threshold": threshold, "alarm": reading["value"] >= threshold, "unit": reading["unit"]}

    def create_ticket(self, equipment: str, message: str) -> dict[str, Any]:
        return {"ticket_id": f"DEMO-{equipment.upper()}-001", "equipment": equipment, "message": message, "status": "draft"}


@dataclass
class Agent:
    tools: InspectionTools
    max_steps: int = 6
    allowed_tools: set[str] = field(default_factory=lambda: {"read_sensor", "check_alarm", "create_ticket"})
    audit: list[AuditEvent] = field(default_factory=list)

    def _call(self, step: int, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self.allowed_tools:
            raise PermissionError(f"tool is not whitelisted: {name}")
        function: Callable[..., Any] = getattr(self.tools, name)
        result = function(**arguments)
        self.audit.append(AuditEvent(step, name, arguments, "ok", result))
        return result

    def run(self, task: str, plan: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Execute a plan with failure handling and a hard step limit."""
        plan = plan or deterministic_plan(task)
        outputs: list[Any] = []
        for step, action in enumerate(plan, start=1):
            if step > self.max_steps:
                self.audit.append(AuditEvent(step, "stop", {}, "max_steps"))
                break
            name = action.get("tool", "")
            args = action.get("arguments", {})
            try:
                outputs.append(self._call(step, name, args))
            except Exception as exc:
                self.audit.append(AuditEvent(step, name, args, "error", str(exc)))
                outputs.append({"error": str(exc), "tool": name})
                # A failed tool cannot safely trigger a follow-up action.
                break
        return {"task": task, "outputs": outputs, "audit": [event.__dict__ for event in self.audit], "completed": bool(outputs) and self.audit[-1].status == "ok"}


def deterministic_plan(task: str, equipment: str = "pump-A") -> list[dict[str, Any]]:
    sensor = "temperature" if any(word in task.lower() for word in ("温度", "temperature")) else "pressure_out"
    return [{"tool": "read_sensor", "arguments": {"equipment": equipment, "sensor": sensor}}, {"tool": "check_alarm", "arguments": {"equipment": equipment, "sensor": sensor, "threshold": 80.0}}]


def llm_plan(task: str, model: str | None = None) -> list[dict[str, Any]]:
    from shared.llm_client import chat

    content = chat([{"role": "system", "content": "输出 JSON 数组，每项是 {tool,arguments}。只能使用 read_sensor、check_alarm、create_ticket。"}, {"role": "user", "content": task}], model=model, max_tokens=300)
    try:
        plan = json.loads(content)
        if not isinstance(plan, list):
            raise ValueError("planner output is not a list")
        return plan
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid planner JSON: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", default="检查泵 A 温度是否异常")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--max-steps", type=int, default=6)
    args = parser.parse_args()
    plan = llm_plan(args.task) if args.llm else deterministic_plan(args.task)
    result = Agent(InspectionTools(load_rows()), max_steps=args.max_steps).run(args.task, plan)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
