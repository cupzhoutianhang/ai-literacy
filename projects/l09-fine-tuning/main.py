from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "intent_examples.jsonl"


def load_examples(path: Path = DATA) -> list[dict[str, str]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or any(set(row) != {"text", "label"} for row in rows):
        raise ValueError("每行必须是 {text, label} JSON 对象")
    return rows


def train_baseline(rows: list[dict[str, str]]):
    texts = [row["text"] for row in rows]
    labels = [row["label"] for row in rows]
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=max(4, len(set(labels))), random_state=42, stratify=labels
    )
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 4))),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    report = {"accuracy": float(accuracy_score(y_test, predictions))}
    return model, report


def main() -> int:
    parser = argparse.ArgumentParser(description="第九讲：先用轻量基线理解微调数据与评估")
    parser.add_argument("--predict", help="使用基线模型预测一句话")
    args = parser.parse_args()
    rows = load_examples()
    print(f"样例数: {len(rows)}，标签: {sorted({row['label'] for row in rows})}")
    model, report = train_baseline(rows)
    print(f"baseline accuracy: {report['accuracy']:.3f}")
    if args.predict:
        print(f"预测: {args.predict} -> {model.predict([args.predict])[0]}")
    print("\nLoRA 训练不是默认步骤；需要 GPU 和 train_lora.py --run。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
