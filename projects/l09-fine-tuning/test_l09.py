from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("l09_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
load_examples, train_baseline = main.load_examples, main.train_baseline


def test_dataset_is_balanced_enough_for_demo():
    rows = load_examples()
    labels = {row["label"] for row in rows}
    assert len(rows) >= 8
    assert len(labels) == 4


def test_baseline_can_fit_and_predict():
    model, report = train_baseline(load_examples())
    assert 0 <= report["accuracy"] <= 1
    assert model.predict(["查询储罐泄漏应急步骤"])[0] in {"规程查询", "报告生成", "故障分析", "方案比较"}
