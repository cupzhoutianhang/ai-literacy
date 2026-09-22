from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from main import attention_weights, next_token_probs, predict_next, tokenize  # noqa: E402


def test_tokenize_and_prediction_are_deterministic():
    tokens = tokenize("锅炉 温度 稳定")
    assert tokens == ["锅", "炉", "温", "度", "稳", "定"]
    result = predict_next(["锅炉", "温度", "升高", "锅炉", "温度", "稳定"], "温度", 2)
    assert result[0][0] in {"升高", "稳定"}
    assert abs(sum(next_token_probs(["a", "b", "a"], "a").values()) - 1.0) < 1e-9


def test_attention_sums_to_one():
    weights = attention_weights(["锅炉", "温度", "升高"], "温度")
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert weights["温度"] == max(weights.values())

