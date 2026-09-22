from pathlib import Path
import json
import sys
import importlib.util
import pytest

pytest.importorskip("pydantic")

sys.path.insert(0, str(Path(__file__).parents[1]))
spec = importlib.util.spec_from_file_location("l03_main", Path(__file__).parents[1] / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
DailyReport, extract_json, run = main.DailyReport, main.extract_json, main.run


def test_mock_report_is_validated():
    payload = json.loads((Path(__file__).parents[1] / "data/sample_report.json").read_text(encoding="utf-8"))
    report = run(payload, mock=True)
    assert isinstance(report, DailyReport)
    assert report.unit == "2号锅炉"
    assert report.alerts


def test_extract_json_from_fence():
    value = extract_json('结果如下：\n```json\n{"unit": "A"}\n```')
    assert value == {"unit": "A"}
