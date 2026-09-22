from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("l08_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
MemoryStore, estimate_tokens, middle_loss_experiment = main.MemoryStore, main.estimate_tokens, main.middle_loss_experiment


def test_memory_write_select_compress_and_isolate() -> None:
    store = MemoryStore()
    store.write("safety", "泵 A 安全温度阈值是 80 摄氏度。", ["safety"])
    store.write("ops", "泵 A 今天温度 74 摄氏度，运行稳定。", ["operations"])
    selected = store.select("泵 A 安全温度", k=2)
    assert selected and {item["key"] for item in selected} == {"safety", "ops"}
    compressed = store.compress(selected, max_tokens=20)
    assert compressed["tokens"] <= 20
    assert store.isolate("安全阈值", scope="safety")["items"][0]["key"] == "safety"


def test_middle_loss_reports_context_budget() -> None:
    result = middle_loss_experiment(20)
    assert result["needle_in_full"]
    assert result["full_tokens"] >= result["edge_window_tokens"]
    assert estimate_tokens("abc") >= 1
