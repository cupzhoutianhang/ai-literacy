from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("l07_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
Agent, InspectionTools, deterministic_plan, load_rows = main.Agent, main.InspectionTools, main.deterministic_plan, main.load_rows


def test_deterministic_agent_has_audit_trail() -> None:
    agent = Agent(InspectionTools(load_rows()), max_steps=4)
    result = agent.run("检查泵 A 温度", deterministic_plan("检查泵 A 温度"))
    assert result["completed"]
    assert [item["action"] for item in result["audit"]] == ["read_sensor", "check_alarm"]


def test_whitelist_and_step_limit() -> None:
    agent = Agent(InspectionTools(load_rows()), max_steps=1)
    result = agent.run("demo", [{"tool": "read_sensor", "arguments": {"equipment": "pump-A", "sensor": "temperature"}}, {"tool": "create_ticket", "arguments": {"equipment": "pump-A", "message": "x"}}])
    assert len(result["outputs"]) == 1
    assert result["audit"][-1]["status"] == "max_steps" or len(result["audit"]) == 1
    denied = Agent(InspectionTools(load_rows())).run("demo", [{"tool": "shell", "arguments": {}}])
    assert denied["audit"][0]["status"] == "error"
