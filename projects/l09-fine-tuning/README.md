# L09 微调：工艺文本意图分类

先用 12 条小型能源场景数据训练 TF-IDF + LogisticRegression 基线，观察数据集、标签、训练/验证切分和评估指标。这个基线用于解释“模型学到了什么”，不需要大模型或 GPU。

```powershell
python main.py
python main.py --predict "请查一下换热器压差异常的原因"
python train_lora.py
```

真正的 LoRA 训练是可选路径：在有 GPU 的服务器环境安装 `.[finetune]` 后再运行 `python train_lora.py --run`。不要把模型权重或训练产物提交到 GitHub。

