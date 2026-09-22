from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("l06_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
LocalMCPClient = main.LocalMCPClient


def test_resources_and_tool_call() -> None:
    client = LocalMCPClient()
    assert len(client.request("resources/list")["resources"]) == 2
    response = client.request("tools/call", name="calculate_pressure_drop", arguments={"equipment": "pump-A"})
    assert response["structuredContent"]["drop"] == 1.5


def test_protocol_lists_tools() -> None:
    tools = LocalMCPClient().request("tools/list")["tools"]
    assert {tool["name"] for tool in tools} == {"query_sensor", "calculate_pressure_drop"}
