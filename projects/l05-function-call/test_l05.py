from __future__ import annotations

from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("l05_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
calculate_pressure_drop, load_rows, make_registry, route_query = main.calculate_pressure_drop, main.load_rows, main.make_registry, main.route_query


def test_pressure_drop_uses_latest_readings() -> None:
    result = calculate_pressure_drop(load_rows(), "pump-A")
    assert result["drop"] == 1.5
    assert result["unit"] == "bar"


def test_schema_registry_and_router() -> None:
    registry = make_registry(load_rows())
    name, args = route_query("请给我泵 A 的压降")
    assert name == "calculate_pressure_drop"
    assert registry.call(name, args)["drop"] == 1.5
    assert registry.schemas()[0]["function"]["name"] == "query_sensor"
